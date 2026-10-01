"""Gazebo Harmonic world: flat soil, a sun and one static primitive model per Plant."""

import xml.etree.ElementTree as ET
from pathlib import Path

from pixelfield.core.layout import FieldLayout
from pixelfield.exporters.colors import crop_colors

SDF_VERSION = "1.9"
SOIL_BORDER = 0.5  # meters of soil around the Field
SOIL_THICKNESS = 0.02
SOIL_RGBA = (0.35, 0.25, 0.17, 1.0)
# ponytail: stand-in cylinder until Variants replace it (M1d); radius from the Planting Pattern.
STAND_IN_RADIUS = 0.4  # fraction of the smallest planting spacing
STAND_IN_HEIGHT = 0.1  # meters, before Plant scale
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
    for p in layout.plants:
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
    _text(sun, "direction", "-0.5 0.1 -0.9")
    return sun


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
