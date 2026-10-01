import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from pixelfield.cli import main

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def mixed(tmp_path_factory):
    out = tmp_path_factory.mktemp("mixed")
    main(["build", str(REPO / "examples" / "mixed.yaml"), "-o", str(out),
          "--crops", str(REPO / "crops")])  # fmt: skip
    manifest = json.loads((out / "manifest.json").read_text())
    return out / "world.sdf", manifest


def test_one_model_per_plant_at_its_pose(mixed):
    world_sdf, manifest = mixed
    models = {m.get("name"): m for m in ET.parse(world_sdf).iter("model")}
    plants = manifest["plants"]
    assert set(models) == {p["id"] for p in plants} | {"soil"}
    for p in plants:
        x, y, z, _, _, yaw = map(float, models[p["id"]].findtext("pose").split())
        assert (x, y, yaw) == pytest.approx((p["pose"]["x"], p["pose"]["y"], p["pose"]["yaw"]),
                                            abs=1e-3)  # fmt: skip
        length = models[p["id"]].findtext(".//cylinder/length")
        base = z - float(length) / 2 if length else z  # Variant origin is on the soil surface
        assert base == pytest.approx(0.0, abs=1e-4)


def test_soil_covers_field_plus_border(mixed):
    world_sdf, manifest = mixed
    soil = next(m for m in ET.parse(world_sdf).iter("model") if m.get("name") == "soil")
    size = [float(v) for v in soil.findtext(".//box/size").split()]
    field = manifest["field"]
    assert size[:2] == pytest.approx([field["cols"] * 0.5 + 1.0, field["rows"] * 0.5 + 1.0])


def test_carrots_use_copied_variant_meshes_and_lettuce_falls_back(mixed):
    world_sdf, manifest = mixed
    models = {m.get("name"): m for m in ET.parse(world_sdf).iter("model")}
    for p in manifest["plants"]:
        model = models[p["id"]]
        if p["crop"] == "lettuce":  # no lettuce Variants yet
            assert model.find(".//cylinder") is not None
            continue
        assert model.findtext(".//mesh/uri") == f"meshes/{p['variant']}.glb"
        assert (world_sdf.parent / "meshes" / f"{p['variant']}.glb").is_file()
        scale = [float(v) for v in model.findtext(".//mesh/scale").split()]
        assert scale == pytest.approx([p["scale"]] * 3, abs=1e-3)  # Manifest rounds to 3


@pytest.mark.skipif(shutil.which("gz") is None, reason="Gazebo not installed")
def test_world_passes_gz_sdf_check(mixed):
    world_sdf, _ = mixed
    result = subprocess.run(["gz", "sdf", "-k", str(world_sdf)], capture_output=True, text=True)
    assert result.returncode == 0 and "Valid" in result.stdout, result.stdout + result.stderr


def test_sun_from_south_east_and_vct_gi_on_sensors(mixed):
    world_sdf, _ = mixed
    world = ET.parse(world_sdf).getroot().find("world")
    dx, dy, dz = map(float, world.findtext("light/direction").split())
    assert dx < 0 < dy and dx == pytest.approx(-dy)  # light travels north-west
    assert dz / (dx**2 + dy**2) ** 0.5 == pytest.approx(-0.839, abs=1e-3)  # tan 40 degrees
    gi = world.find("plugin[@name='gz::sim::systems::Sensors']/global_illumination")
    assert gi.get("type") == "vct" and gi.findtext("enabled") == "true"
    assert world.find("scene/sky") is not None
