import json
import math
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from pixelfield.cli import main
from pixelfield.exporters import gazebo
from pixelfield.exporters.gazebo import plant

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


def test_soil_collision_is_a_plane_on_the_soil_bit(mixed):
    world_sdf, _ = mixed
    soil = next(m for m in ET.parse(world_sdf).iter("model") if m.get("name") == "soil")
    collision = soil.find("link/collision")
    assert collision.findtext("geometry/plane/normal") == "0 0 1"
    assert float(soil.findtext("pose").split()[2]) == 0.0  # the plane is the ground, z = 0
    assert collision.findtext("surface/contact/collide_bitmask") == str(gazebo.SOIL_BITMASK)


def _ground_world(world_sdf, name, box_xyz, box_size, mu=None, gravity=(0.0, 0.0, -9.81)):
    """The Field's soil model alone, plus a 1 kg box, unthrottled, physics only."""
    sdf = ET.Element("sdf", version=gazebo.SDF_VERSION)
    world = ET.SubElement(sdf, "world", name=name)
    physics = ET.SubElement(world, "physics", name="1ms", type="dart")
    ET.SubElement(physics, "max_step_size").text = "0.001"
    ET.SubElement(physics, "real_time_factor").text = "0"
    ET.SubElement(world, "gravity").text = " ".join(map(str, gravity))
    for filename, plugin in gazebo.SYSTEMS.items():
        ET.SubElement(world, "plugin", filename=filename, name=plugin)
    world.append(next(m for m in ET.parse(world_sdf).iter("model") if m.get("name") == "soil"))
    box = ET.SubElement(world, "model", name="box")
    ET.SubElement(box, "pose").text = " ".join(map(str, (*box_xyz, 0, 0, 0)))
    link = ET.SubElement(box, "link", name="link")
    inertial = ET.SubElement(link, "inertial")
    ET.SubElement(inertial, "mass").text = "1"
    a, b, c = (v * v / 12 for v in box_size)
    inertia = ET.SubElement(inertial, "inertia")
    for tag, value in (("ixx", b + c), ("iyy", a + c), ("izz", a + b)):
        ET.SubElement(inertia, tag).text = str(value)
    collision = ET.SubElement(link, "collision", name="collision")
    ET.SubElement(ET.SubElement(collision, "geometry"), "box")
    collision.find("geometry/box").append(ET.Element("size"))
    collision.find("geometry/box/size").text = " ".join(map(str, box_size))
    if mu is not None:
        ode = ET.SubElement(ET.SubElement(ET.SubElement(collision, "surface"), "friction"), "ode")
        ET.SubElement(ode, "mu").text = ET.SubElement(ode, "mu2").text = str(mu)
    path = world_sdf.with_name(f"{name}.sdf")
    ET.ElementTree(sdf).write(path, encoding="unicode", xml_declaration=True)
    result = subprocess.run(
        [plant.SYSTEM_PYTHON, str(plant.SETTLE_SCRIPT), path.name, "box", "1000", "800"],
        cwd=path.parent, capture_output=True, text=True, check=True,
    )  # fmt: skip
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.mark.skipif(shutil.which("gz") is None, reason="Gazebo not installed")
def test_a_box_dropped_beyond_the_border_lands(mixed):
    world_sdf, manifest = mixed
    x = -manifest["field"]["border"] - 1.0  # 1 m west of the textured soil
    report = _ground_world(world_sdf, "drop", (x, 0.0, 0.5), (0.1, 0.1, 0.1))
    assert report["max_travel"] == pytest.approx(0.45, abs=0.01)  # rests at z = 0.05; falls 4.9 m
    # Resting contact reads just under 1 mm/s in DART; a box falling for 1 s reaches 9.8 m/s.
    assert report["max_speed_after"] < 0.01 and not report["nan"]


# Soil mu is the default 1; gravity is tilted to a slope (tan). With the lower of the two mu
# the box slides once the slope passes it; the product, the larger or the mean of the two
# would hold in at least one of the first two cases (spec section 12, item 6).
@pytest.mark.skipif(shutil.which("gz") is None, reason="Gazebo not installed")
@pytest.mark.parametrize(("box_mu", "slope", "slides"), [(0.3, 0.5, True), (2.0, 1.3, True),
    (2.0, 0.8, False), (0.3, 0.25, False), (1.0, 0.95, False), (1.0, 1.05, True)])  # fmt: skip
def test_contact_friction_is_the_lower_of_the_two_surfaces(mixed, box_mu, slope, slides):
    world_sdf, _ = mixed
    angle = math.atan(slope)
    gravity = (9.81 * math.sin(angle), 0.0, -9.81 * math.cos(angle))
    # Flat box, so it slides before it tips over (tips only beyond a slope of 10).
    report = _ground_world(world_sdf, "friction", (0.0, 0.0, 0.01), (0.2, 0.2, 0.02),
                           mu=box_mu, gravity=gravity)  # fmt: skip
    assert (report["max_travel"] > 0.1) == slides and (report["max_travel"] < 0.005) != slides


def test_crop_without_variants_falls_back_to_a_cylinder(tmp_path):
    crops = tmp_path / "crops"
    crops.mkdir()
    shutil.copy(REPO / "crops" / "carrot.yaml", crops)
    lettuce = (REPO / "crops" / "lettuce.yaml").read_text()
    (crops / "lettuce.yaml").write_text(lettuce.replace("assets/library/lettuce", str(tmp_path)))
    out = tmp_path / "out"
    main(["build", str(REPO / "examples" / "mixed.yaml"), "-o", str(out), "--crops", str(crops)])
    manifest = json.loads((out / "manifest.json").read_text())
    visuals = _plant_visuals(out / "world.sdf")
    for p in manifest["plants"]:
        model = visuals[p["id"]][0]
        assert (model.find(".//cylinder") is not None) == (p["crop"] == "lettuce")


def test_plants_use_copied_variant_meshes(mixed):
    world_sdf, manifest = mixed
    visuals = _plant_visuals(world_sdf)
    for p in manifest["plants"]:
        model = visuals[p["id"]][0]
        assert model.findtext(".//mesh/uri") == f"meshes/{p['variant']}.glb"
        assert (world_sdf.parent / "meshes" / f"{p['variant']}.glb").is_file()
        scale = [float(v) for v in model.findtext(".//mesh/scale").split()]
        assert scale == pytest.approx([p["scale"]] * 3, abs=1e-4)  # Manifest rounds to 4


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


def test_soil_visual_is_textured_tiles_covering_field_plus_border(mixed):
    world_sdf, manifest = mixed
    field = manifest["field"]
    soil = next(m for m in ET.parse(world_sdf).iter("model") if m.get("name") == "soil")
    tiles = soil.findall("link/visual")
    xs = [float(t.findtext("pose").split()[0]) for t in tiles]
    ys = [float(t.findtext("pose").split()[1]) for t in tiles]
    tops = {float(t.findtext("pose").split()[2]) + float(t.findtext(".//box/size").split()[2]) / 2
            for t in tiles}  # fmt: skip
    assert tops == {0.0}
    border = 2 * field["border"]
    assert max(xs) - min(xs) + 1.0 >= field["width"] + border  # 1 m tiles
    assert max(ys) - min(ys) + 1.0 >= field["depth"] + border
    for tile in tiles:
        i, j = (int(n) % gazebo.SOIL_ATLAS for n in tile.get("name").split("_")[1:])
        uri = tile.findtext(".//albedo_map")
        assert (
            uri == f"textures/tiles/tile_{i}_{j}_color.jpg" and (world_sdf.parent / uri).is_file()
        )
        assert tile.findtext(".//normal_map") == "textures/normal.jpg"  # shared


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
