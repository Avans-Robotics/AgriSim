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
        length = float(models[p["id"]].findtext(".//cylinder/length"))
        assert z == pytest.approx(length / 2, abs=1e-4)  # cylinder base on the soil


def test_soil_covers_field_plus_border(mixed):
    world_sdf, manifest = mixed
    soil = next(m for m in ET.parse(world_sdf).iter("model") if m.get("name") == "soil")
    size = [float(v) for v in soil.findtext(".//box/size").split()]
    field = manifest["field"]
    assert size[:2] == pytest.approx([field["cols"] * 0.5 + 1.0, field["rows"] * 0.5 + 1.0])


def test_crops_have_different_colors(mixed):
    world_sdf, manifest = mixed
    models = {m.get("name"): m for m in ET.parse(world_sdf).iter("model")}
    color = {p["crop"]: models[p["id"]].findtext(".//diffuse") for p in manifest["plants"]}
    assert len(set(color.values())) == 2


@pytest.mark.skipif(shutil.which("gz") is None, reason="Gazebo not installed")
def test_world_passes_gz_sdf_check(mixed):
    world_sdf, _ = mixed
    result = subprocess.run(["gz", "sdf", "-k", str(world_sdf)], capture_output=True, text=True)
    assert result.returncode == 0 and "Valid" in result.stdout, result.stdout + result.stderr
