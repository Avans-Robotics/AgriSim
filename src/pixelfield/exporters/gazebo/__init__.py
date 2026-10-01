"""Gazebo Harmonic world: flat soil, a sun and one static model per Plant.

Plants use their Variant mesh, copied into `meshes/` next to world.sdf so the output folder
is self-contained. Crops without Variants in their library fall back to a cylinder.
"""

import math
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from pixelfield.core.layout import FieldLayout
from pixelfield.exporters.colors import crop_colors

SDF_VERSION = "1.9"
SOIL_BORDER = 0.5  # meters of soil around the Field
SOIL_THICKNESS = 0.02
SOIL_RGBA = (0.35, 0.25, 0.17, 1.0)
# Stand-in cylinder for Crops without Variants yet; radius from the Planting Pattern.
STAND_IN_RADIUS = 0.4  # fraction of the smallest planting spacing
STAND_IN_HEIGHT = 0.1  # meters, before Plant scale
# Sun from the south-east at 40 degrees elevation, for consistent shadows in renders.
SUN_ELEVATION = math.radians(40)
SUN_AZIMUTH = math.radians(135)  # compass bearing the light comes from, clockwise from north
# VCT global illumination, applied by the Sensors system to camera sensors only.
GI_RESOLUTION = 32  # voxels per axis; more is sharper bounce light but costs VRAM
GI_BOUNCES = 6
# Gazebo loads glTF as is, but Variant files are y up (glTF spec); this roll stands them up.
GLTF_TO_Z_UP = (0.0, 0.0, 0.0, math.pi / 2, 0.0, 0.0)
SYSTEMS = {
    "gz-sim-physics-system": "gz::sim::systems::Physics",
    "gz-sim-user-commands-system": "gz::sim::systems::UserCommands",
    "gz-sim-scene-broadcaster-system": "gz::sim::systems::SceneBroadcaster",
}


def export(layout: FieldLayout, out_dir: Path) -> Path:
    spec = layout.spec
    sdf = ET.Element("sdf", version=SDF_VERSION)
    world = ET.SubElement(sdf, "world", name="pixelfield")
    for filename, name in SYSTEMS.items():
        ET.SubElement(world, "plugin", filename=filename, name=name)
    world.append(_sensors())
    world.append(_scene())
    world.append(_sun())

    width, depth = spec.cols * spec.pixel_size, spec.rows * spec.pixel_size
    soil_size = (width + 2 * SOIL_BORDER, depth + 2 * SOIL_BORDER, SOIL_THICKNESS)
    soil_pose = (width / 2, depth / 2, -SOIL_THICKNESS / 2, 0.0)
    soil = _model(world, "soil", soil_pose)
    for tag in ("collision", "visual"):
        element = ET.SubElement(soil, tag, name=tag)
        box = ET.SubElement(ET.SubElement(element, "geometry"), "box")
        _text(box, "size", _join(soil_size))
        if tag == "visual":
            element.append(_material(SOIL_RGBA))

    colors = {crop: _rgba(hex_color) for crop, hex_color in crop_colors(layout).items()}
    meshes, copied = Path(out_dir) / "meshes", set()
    for p in layout.plants:
        mesh = Path(layout.crops[p.crop].library) / f"{p.variant}.glb"
        if mesh.is_file():
            # ponytail: hue_shift ignored here, glb materials can't be tinted per Plant
            # without replacing them; add a per-Plant material if renders look too uniform.
            if mesh not in copied:  # copy each build so a regenerated library is picked up
                meshes.mkdir(exist_ok=True)
                shutil.copyfile(mesh, meshes / mesh.name)
                copied.add(mesh)
            link = _model(world, p.id, (p.x, p.y, p.z, p.yaw))
            visual = ET.SubElement(link, "visual", name="visual")
            _text(visual, "pose", _join(GLTF_TO_Z_UP))
            geometry = ET.SubElement(ET.SubElement(visual, "geometry"), "mesh")
            _text(geometry, "uri", f"meshes/{mesh.name}")  # resolved against world.sdf
            _text(geometry, "scale", _join((p.scale,) * 3))
            continue
        pattern = layout.crops[p.crop].planting
        radius = STAND_IN_RADIUS * min(pattern.row_spacing, pattern.in_row_spacing) * p.scale
        height = STAND_IN_HEIGHT * p.scale
        link = _model(world, p.id, (p.x, p.y, p.z + height / 2, p.yaw))
        visual = ET.SubElement(link, "visual", name="visual")
        cylinder = ET.SubElement(ET.SubElement(visual, "geometry"), "cylinder")
        _text(cylinder, "radius", f"{radius:.4f}")
        _text(cylinder, "length", f"{height:.4f}")
        visual.append(_material(colors[p.crop]))

    ET.indent(sdf)
    path = Path(out_dir) / "world.sdf"
    ET.ElementTree(sdf).write(path, encoding="unicode", xml_declaration=True)
    return path


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
    _text(scene, "ambient", "0.4 0.4 0.4 1")
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


def _rgba(hex_color: str) -> tuple[float, ...]:
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)) + (1.0,)


def _join(values: tuple[float, ...]) -> str:
    return " ".join(f"{v:.4f}".rstrip("0").rstrip(".") for v in values)


def _text(parent: ET.Element, tag: str, text: str) -> None:
    ET.SubElement(parent, tag).text = text
