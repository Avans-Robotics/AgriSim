"""Gazebo Harmonic world: flat soil, a sun and one static model per Pixel of Plants.

Plants use their Variant mesh, copied into `meshes/` next to world.sdf so the output folder
is self-contained. Crops without Variants in their library fall back to a cylinder. Root crop
Plants also get their articulated SDF in `plants/`, loaded by the pull-out system on a pick.
"""

import math
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from pixelfield.core.layout import FieldLayout, to_manifest
from pixelfield.exporters.colors import crop_colors

SDF_VERSION = "1.9"
SOIL_THICKNESS = 0.02  # of the tile visuals
# CC0 PBR soil (ambientCG Ground048) and its tiles with dry patches baked in (see
# generators/soil.py), copied into textures/ next to world.sdf.
SOIL_TEXTURES = Path("assets/library/textures/soil")
SOIL_TILES = Path("assets/library/textures/soil_tiles")
SOIL_ATLAS = 4  # soil tiles per side of the baked atlas; tile (i, j) uses (i % 4, j % 4)
SOIL_TILE = 1.0  # meters covered by one soil tile
# Stand-in cylinder for Crops without Variants yet; radius from the Planting Pattern.
STAND_IN_RADIUS = 0.4  # fraction of the smallest planting spacing
STAND_IN_HEIGHT = 0.1  # meters, before Plant scale
# Sun from the south-east at 40 degrees elevation, for consistent shadows in renders.
SUN_ELEVATION = math.radians(40)
SUN_AZIMUTH = math.radians(135)  # compass bearing the light comes from, clockwise from north
# VCT global illumination, applied by the Sensors system to camera sensors only.
GI_RESOLUTION = 32  # voxels per axis; more is sharper bounce light but costs VRAM
GI_BOUNCES = 6
# Placeholder render cameras until the real Amiga camera is known (spec open item 1).
CAMERA_SIZE = (1920, 1080)
CAMERA_HFOV = math.radians(60)
# name: (pitch down, meters from the Field centre); both look north. The top camera sits high
# enough to frame a whole Pixel plus overhanging leaves (vertical FOV is only 36 degrees).
CAMERAS = {"top": (math.pi / 2, 1.7), "oblique": (math.pi / 4, 1.0)}
RENDER_DIR = "renders"  # camera save path, relative to the cwd of `render`
# Gazebo loads glTF as is, but Variant files are y up (glTF spec); this roll stands them up.
GLTF_TO_Z_UP = (0.0, 0.0, 0.0, math.pi / 2, 0.0, 0.0)
SYSTEMS = {
    "gz-sim-physics-system": "gz::sim::systems::Physics",
    "gz-sim-user-commands-system": "gz::sim::systems::UserCommands",
    "gz-sim-scene-broadcaster-system": "gz::sim::systems::SceneBroadcaster",
}
WORLD_NAME = "pixelfield"
# Our pull-out system (ADR 0006), built into build/systems/ and found through
# GZ_SIM_SYSTEM_PLUGIN_PATH; a world without it still runs, gz only logs that it is missing.
PULL_OUT_SYSTEM = ("PixelfieldPullOut", "pixelfield::PullOut")
# A picked root starts below the soil plane, so it must not collide with the soil: the soil
# keeps bit 0 only and root collisions leave it out (plant.ROOT_BITMASK) until the detach.
SOIL_BITMASK = 0x1
# Active Region (ADR 0010): meters added around every robot link's box, and the footprint
# radius of a root crop Plant, "crown" (its root's widest point) or "foliage" (its leaves' reach).
# Seconds per physics step of every world we write (dartsim): the ADR 0006 stability checks
# and the grip run at it (the scripted pull at its own plant.PULL_STEP). 2 ms runs the 10 x 10
# Field with a gripper among Picked Plants at the camera ceiling, with the checks as at 1 ms;
# 4 ms gains nothing past the cameras and lost the strongest beetroot's grip (perf.md, M5d).
PHYSICS_STEP = 0.002
ACTIVE_REGION_PADDING = 0.05
ACTIVE_REGION_FOOTPRINT = "crown"


def export(layout: FieldLayout, out_dir: Path) -> Path:
    spec = layout.spec
    sdf = ET.Element("sdf", version=SDF_VERSION)
    world = ET.SubElement(sdf, "world", name=WORLD_NAME)
    physics = ET.SubElement(world, "physics", name="step", type="dart")
    _text(physics, "max_step_size", str(PHYSICS_STEP))
    _text(physics, "real_time_factor", "1")
    for filename, name in SYSTEMS.items():
        ET.SubElement(world, "plugin", filename=filename, name=name)
    pull_out = ET.SubElement(world, "plugin", filename=PULL_OUT_SYSTEM[0], name=PULL_OUT_SYSTEM[1])
    _text(pull_out, "padding", str(ACTIVE_REGION_PADDING))
    _text(pull_out, "footprint", ACTIVE_REGION_FOOTPRINT)
    world.append(_sensors())
    world.append(_scene())
    world.append(_sun())

    # Collision is a plane at z = 0 (about 2 km wide in dartsim), so a robot does not drive off
    # the world; the textured tiles cover the Field plus the Border (spec section 5).
    width, depth = spec.width, spec.depth
    soil_size = (width + 2 * spec.border, depth + 2 * spec.border)
    soil = _model(world, "soil", (width / 2, depth / 2, 0.0, 0.0))
    collision = ET.SubElement(soil, "collision", name="collision")
    plane = ET.SubElement(ET.SubElement(collision, "geometry"), "plane")
    _text(plane, "normal", "0 0 1")
    _text(plane, "size", _join(soil_size))  # not the collision extent
    contact = ET.SubElement(ET.SubElement(collision, "surface"), "contact")
    _text(contact, "collide_bitmask", str(SOIL_BITMASK))
    # A box maps the texture once per face, so the visual is a grid of SOIL_TILE squares
    # centred on the soil, top face at z = 0; the outer tiles may overhang the Border a little.
    textures = Path(out_dir) / "textures"
    textures.mkdir(parents=True, exist_ok=True)
    shutil.copy(SOIL_TEXTURES / "normal.jpg", textures)  # shared; color and roughness are baked
    shutil.copytree(SOIL_TILES, textures / "tiles", dirs_exist_ok=True)
    nx, ny = (math.ceil(size / SOIL_TILE) for size in soil_size)
    for i in range(nx):
        for j in range(ny):
            visual = ET.SubElement(soil, "visual", name=f"tile_{i}_{j}")
            offset = ((i - (nx - 1) / 2) * SOIL_TILE, (j - (ny - 1) / 2) * SOIL_TILE)
            _text(visual, "pose", _join(offset + (-SOIL_THICKNESS / 2, 0.0, 0.0, 0.0)))
            box = ET.SubElement(ET.SubElement(visual, "geometry"), "box")
            _text(box, "size", _join((SOIL_TILE, SOIL_TILE, SOIL_THICKNESS)))
            visual.append(_soil_material(i % SOIL_ATLAS, j % SOIL_ATLAS))

    for name, (pitch, distance) in CAMERAS.items():
        world.append(_camera(name, (width / 2, depth / 2), pitch, distance))

    # One static model per Pixel holding its Plants as visuals: thousands of separate models
    # stall the Physics system (RTF 0.3 on 10 x 10 Pixels); one per Pixel runs at 1.0 (ADR 0007).
    colors = {crop: _rgba(hex_color) for crop, hex_color in crop_colors(layout).items()}
    meshes, copied = Path(out_dir) / "meshes", set()
    origins = {(pixel.row, pixel.col): pixel.origin for pixel in layout.pixels}
    links = {}  # (row, col): link of that Pixel's model, created at its first Plant
    for p in layout.plants:
        ox, oy = origins[p.pixel]
        if p.pixel not in links:
            links[p.pixel] = _model(world, "r{}c{}".format(*p.pixel), (ox, oy, 0.0, 0.0))
        link = links[p.pixel]
        visual = ET.SubElement(link, "visual", name=p.id)
        mesh = Path(layout.crops[p.crop].library) / f"{p.variant}.glb"
        if mesh.is_file():
            # ponytail: hue_shift ignored here, glb materials can't be tinted per Plant
            # without replacing them; add a per-Plant material if renders look too uniform.
            if mesh not in copied:  # copy each build so a regenerated library is picked up
                meshes.mkdir(exist_ok=True)
                shutil.copyfile(mesh, meshes / mesh.name)
                copied.add(mesh)
            # Roll stands the y-up glTF up, then yaw turns it about z (SDF applies roll first).
            _text(visual, "pose", _join((p.x - ox, p.y - oy, p.z, GLTF_TO_Z_UP[3], 0.0, p.yaw)))
            geometry = ET.SubElement(ET.SubElement(visual, "geometry"), "mesh")
            _text(geometry, "uri", f"meshes/{mesh.name}")  # resolved against world.sdf
            _text(geometry, "scale", _join((p.scale,) * 3))
            continue
        pattern = layout.crops[p.crop].planting
        radius = STAND_IN_RADIUS * min(pattern.row_spacing, pattern.in_row_spacing) * p.scale
        height = STAND_IN_HEIGHT * p.scale
        _text(visual, "pose", _join((p.x - ox, p.y - oy, p.z + height / 2, 0.0, 0.0, p.yaw)))
        cylinder = ET.SubElement(ET.SubElement(visual, "geometry"), "cylinder")
        _text(cylinder, "radius", f"{radius:.4f}")
        _text(cylinder, "length", f"{height:.4f}")
        visual.append(_material(colors[p.crop]))

    ET.indent(sdf)
    path = Path(out_dir) / "world.sdf"
    ET.ElementTree(sdf).write(path, encoding="unicode", xml_declaration=True)
    from pixelfield.exporters.gazebo import plant  # it imports this module

    plant.write_plants(to_manifest(layout), out_dir)  # the Manifest's rounded scale and pose
    return path


def render(world_sdf: Path, iterations: int = 5000) -> list[Path]:
    """Run the world headless and save one image per camera as renders/<camera>.png.

    Cameras only save while something subscribes to their topic, so a `gz topic` echo runs
    per camera. A few thousand iterations are needed before the render thread delivers frames.
    """
    out = Path(world_sdf).resolve().parent
    renders = out / RENDER_DIR
    shutil.rmtree(renders, ignore_errors=True)
    echo = [["gz", "topic", "-e", "-t", f"/camera/{name}"] for name in CAMERAS]
    subscribers = [subprocess.Popen(cmd, stdout=subprocess.DEVNULL) for cmd in echo]
    try:
        subprocess.run(["gz", "sim", "-s", "-r", "--headless-rendering", "--iterations",
                        str(iterations), Path(world_sdf).name], cwd=out, check=True)  # fmt: skip
    finally:
        for subscriber in subscribers:
            subscriber.terminate()
    images = []
    for name in CAMERAS:
        frames = sorted((renders / name).glob("*.png"),
                        key=lambda f: int(re.findall(r"\d+", f.stem)[-1]))  # fmt: skip
        if not frames:
            raise RuntimeError(f"camera {name} saved no images; try more iterations")
        images.append(frames[-1].replace(renders / f"{name}.png"))
        shutil.rmtree(renders / name)
    return images


def preview(meshes: list[Path], out_dir: Path, spacing: float = 0.15) -> Path:
    """World with one static model per Variant mesh in a row along x, no soil, for checking."""
    sdf = ET.Element("sdf", version=SDF_VERSION)
    world = ET.SubElement(sdf, "world", name="variants")
    for filename, name in SYSTEMS.items():
        ET.SubElement(world, "plugin", filename=filename, name=name)
    world.append(_sun())
    for i, mesh in enumerate(meshes):
        link = _model(world, Path(mesh).stem, (i * spacing, 0.0, 0.0, 0.0))
        visual = ET.SubElement(link, "visual", name="visual")
        _text(visual, "pose", _join(GLTF_TO_Z_UP))
        geometry = ET.SubElement(ET.SubElement(visual, "geometry"), "mesh")
        _text(geometry, "uri", str(Path(mesh).resolve()))

    ET.indent(sdf)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    path = Path(out_dir) / "world.sdf"
    ET.ElementTree(sdf).write(path, encoding="unicode", xml_declaration=True)
    return path


def _model(world: ET.Element, name: str, pose: tuple[float, float, float, float]) -> ET.Element:
    """Static model at (x, y, z, yaw); returns its single link."""
    model = ET.SubElement(world, "model", name=name)
    _text(model, "static", "true")
    x, y, z, yaw = pose
    _text(model, "pose", _join((x, y, z, 0.0, 0.0, yaw)))
    return ET.SubElement(model, "link", name="link")


def _camera(name: str, target: tuple[float, float], pitch: float, distance: float) -> ET.Element:
    """Static camera `distance` from target, south of it, pitched down towards it."""
    model = ET.Element("model", name=f"camera_{name}")
    _text(model, "static", "true")
    x, y = target[0], target[1] - distance * math.cos(pitch)
    _text(model, "pose", _join((x, y, distance * math.sin(pitch), 0.0, pitch, math.pi / 2)))
    sensor = ET.SubElement(ET.SubElement(model, "link", name="link"), "sensor", name="camera",
                           type="camera")  # fmt: skip
    camera = ET.SubElement(sensor, "camera")
    _text(camera, "horizontal_fov", f"{CAMERA_HFOV:.4f}")
    image = ET.SubElement(camera, "image")
    _text(image, "width", str(CAMERA_SIZE[0]))
    _text(image, "height", str(CAMERA_SIZE[1]))
    clip = ET.SubElement(camera, "clip")
    _text(clip, "near", "0.02")
    _text(clip, "far", "50")
    save = ET.SubElement(camera, "save", enabled="true")
    _text(save, "path", f"{RENDER_DIR}/{name}")
    _text(sensor, "always_on", "true")
    _text(sensor, "update_rate", "2")
    _text(sensor, "topic", f"camera/{name}")
    return model


def _sun() -> ET.Element:
    sun = ET.Element("light", type="directional", name="sun")
    _text(sun, "cast_shadows", "true")
    _text(sun, "pose", "0 0 10 0 0 0")
    _text(sun, "diffuse", "0.8 0.8 0.8 1")
    _text(sun, "specular", "0.2 0.2 0.2 1")
    horizontal = math.cos(SUN_ELEVATION)  # light travels away from the sun's bearing
    direction = (-horizontal * math.sin(SUN_AZIMUTH), -horizontal * math.cos(SUN_AZIMUTH),
                 -math.sin(SUN_ELEVATION))  # fmt: skip
    _text(sun, "direction", _join(direction))
    return sun


def _scene() -> ET.Element:
    scene = ET.Element("scene")
    _text(scene, "ambient", "0.1 0.1 0.1 1")  # low, so GI bounce light fills the shadows
    _text(scene, "background", "0.7 0.8 0.9 1")
    ET.SubElement(scene, "sky")
    _text(scene, "grid", "false")
    return scene


def _sensors() -> ET.Element:
    """Sensors system with VCT global illumination, values from gz-sim's GI example world."""
    sensors = ET.Element("plugin", filename="gz-sim-sensors-system",
                         name="gz::sim::systems::Sensors")  # fmt: skip
    _text(sensors, "render_engine", "ogre2")
    gi = ET.SubElement(sensors, "global_illumination", type="vct")
    for tag, value in [("enabled", "true"), ("resolution", _join((GI_RESOLUTION,) * 3)),
                       ("octant_count", "1 1 1"), ("bounce_count", str(GI_BOUNCES)),
                       ("high_quality", "true"), ("anisotropic", "true"),
                       ("thin_wall_counter", "1.0"), ("conserve_memory", "false"),
                       ("debug_vis_mode", "none")]:  # fmt: skip
        _text(gi, tag, value)
    return sensors


def _material(rgba: tuple[float, ...]) -> ET.Element:
    material = ET.Element("material")
    for tag in ("ambient", "diffuse"):
        _text(material, tag, _join(rgba))
    return material


def _soil_material(i: int, j: int) -> ET.Element:
    """Atlas tile (i, j); neighbouring atlas tiles join without seams, the normals are shared."""
    material = ET.Element("material")
    for tag in ("ambient", "diffuse"):
        _text(material, tag, "1 1 1 1")  # let the albedo map set the color
    metal = ET.SubElement(ET.SubElement(material, "pbr"), "metal")
    for tag, path in [("albedo_map", f"tiles/tile_{i}_{j}_color"), ("normal_map", "normal"),
                      ("roughness_map", f"tiles/tile_{i}_{j}_roughness")]:  # fmt: skip
        _text(metal, tag, f"textures/{path}.jpg")  # resolved against world.sdf
    _text(metal, "metalness", "0")
    return material


def _rgba(hex_color: str) -> tuple[float, ...]:
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)) + (1.0,)


def _join(values: tuple[float, ...]) -> str:
    return " ".join(f"{v:.4f}".rstrip("0").rstrip(".") for v in values)


def _text(parent: ET.Element, tag: str, text: str) -> None:
    ET.SubElement(parent, tag).text = text
