import json
import math
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


def _plant_visuals(world_sdf):
    """Plant id: (visual, its model's pose) for every Plant visual in the Pixel models."""
    visuals = {}
    for model in ET.parse(world_sdf).iter("model"):
        pose = [float(v) for v in model.findtext("pose").split()]
        for visual in model.iter("visual"):
            visuals[visual.get("name")] = (visual, pose)
    return visuals


def test_one_model_per_pixel_with_plants_at_their_pose(mixed):
    world_sdf, manifest = mixed
    models = {m.get("name") for m in ET.parse(world_sdf).iter("model")}
    plants = manifest["plants"]
    pixels = {p["id"].split("-")[0] for p in plants}
    assert models == pixels | {"soil", "camera_top", "camera_oblique"}
    visuals = _plant_visuals(world_sdf)
    for p in plants:
        visual, (mx, my, mz, *_) = visuals[p["id"]]
        x, y, z, _, _, yaw = map(float, visual.findtext("pose").split())
        assert (mx + x, my + y, yaw) == pytest.approx(
            (p["pose"]["x"], p["pose"]["y"], p["pose"]["yaw"]), abs=1e-3)  # fmt: skip
        length = visual.findtext(".//cylinder/length")
        base = mz + z - float(length) / 2 if length else mz + z  # Variant origin on the soil
        assert base == pytest.approx(0.0, abs=1e-4)


def test_soil_covers_field_plus_border(mixed):
    world_sdf, manifest = mixed
    soil = next(m for m in ET.parse(world_sdf).iter("model") if m.get("name") == "soil")
    size = [float(v) for v in soil.findtext(".//box/size").split()]
    field = manifest["field"]
    assert size[:2] == pytest.approx([field["cols"] * 0.5 + 1.0, field["rows"] * 0.5 + 1.0])


def test_carrots_use_copied_variant_meshes_and_lettuce_falls_back(mixed):
    world_sdf, manifest = mixed
    visuals = _plant_visuals(world_sdf)
    for p in manifest["plants"]:
        model = visuals[p["id"]][0]
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


def test_soil_visual_is_textured_tiles_covering_the_collision_box(mixed):
    world_sdf, _ = mixed
    soil = next(m for m in ET.parse(world_sdf).iter("model") if m.get("name") == "soil")
    sx, sy, _ = map(float, soil.findtext("link/collision//box/size").split())
    tiles = soil.findall("link/visual")
    xs = [float(t.findtext("pose").split()[0]) for t in tiles]
    ys = [float(t.findtext("pose").split()[1]) for t in tiles]
    assert max(xs) - min(xs) + 1.0 >= sx and max(ys) - min(ys) + 1.0 >= sy  # 1 m tiles
    for tile in tiles:
        uri = tile.findtext(".//albedo_map")
        assert uri == "textures/color.jpg" and (world_sdf.parent / uri).is_file()


def test_cameras_look_at_field_centre(mixed):
    world_sdf, manifest = mixed
    models = {m.get("name"): m for m in ET.parse(world_sdf).iter("model")}
    field = manifest["field"]
    centre = (field["cols"] * 0.5 / 2, field["rows"] * 0.5 / 2, 0.0)
    for name in ("top", "oblique"):
        x, y, z, _, pitch, yaw = map(float, models[f"camera_{name}"].findtext("pose").split())
        # forward axis of a camera with this pitch and yaw, from its pose to the centre
        forward = (
            math.cos(pitch) * math.cos(yaw),
            math.cos(pitch) * math.sin(yaw),
            -math.sin(pitch),
        )
        to_centre = [c - p for c, p in zip(centre, (x, y, z), strict=True)]
        distance = {"top": 1.7, "oblique": 1.0}[name]
        assert to_centre == pytest.approx([distance * f for f in forward], abs=1e-3)
        assert models[f"camera_{name}"].findtext(".//save/path") == f"renders/{name}"


@pytest.mark.skipif(shutil.which("gz") is None, reason="Gazebo not installed")
def test_render_saves_one_image_per_camera(tmp_path):
    main(["build", str(REPO / "examples" / "carrot_pixel.yaml"), "-o", str(tmp_path),
          "--crops", str(REPO / "crops")])  # fmt: skip
    main(["render", str(tmp_path / "world.sdf")])
    assert sorted(p.name for p in (tmp_path / "renders").iterdir()) == ["oblique.png", "top.png"]
