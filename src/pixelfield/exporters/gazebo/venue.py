"""Venue of a Field in Gazebo: a glasshouse with a paver floor around the soil, for looks only.

Four visuals in one static model and no collisions (the soil plane is the ground everywhere):
the floor, the glass and the frame as OBJ meshes written next to world.sdf, and the low stone
wall as a box. One mesh per part keeps the visual count low however big the greenhouse is.
"""

import math
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from pixelfield import ROOT
from pixelfield.core.spec import FieldSpec
from pixelfield.exporters.gazebo import _join, _model, _text

# Baked by generators/pavers.py (PAVER and PERIOD there), copied into textures/.
PAVER_TEXTURE = ROOT / "assets" / "library" / "textures" / "pavers" / "color.jpg"
PAVER = 0.6  # meters per paver side
PAVER_PERIOD = 4  # pavers per texture side
# Rough guesses of the Avans greenhouse, not measured; it is only for looks.
GUTTER_HEIGHT = 4.0  # meters, top of the side walls
ROOF_PITCH = math.radians(25)
BAY = 3.0  # meters, at most, between frame posts
BEAM = 0.08  # meters, side of the frame's square profile
STONE_WALL = (0.25, 0.6)  # meters, thickness and height; spec.VENUE_MIN_FLOOR leaves room
GLASS_TRANSPARENCY = 0.85
FRAME_RGBA = (0.75, 0.76, 0.78, 1.0)
STONE_RGBA = (0.55, 0.52, 0.48, 1.0)
GLASS_RGBA = (0.85, 0.92, 0.95, 1.0)


def add(world: ET.Element, spec: FieldSpec, out_dir: Path) -> None:
    venue = spec.venue
    west, south, east, north = venue.bounds
    middle = (west + east) / 2
    ridge = GUTTER_HEIGHT + (east - west) / 2 * math.tan(ROOF_PITCH)
    meshes, textures = Path(out_dir) / "meshes", Path(out_dir) / "textures"
    meshes.mkdir(parents=True, exist_ok=True)
    textures.mkdir(parents=True, exist_ok=True)
    link = _model(world, "venue", (0.0, 0.0, 0.0, 0.0))  # mesh vertices in Field coordinates

    # Floor: the venue's rectangle minus the soil, as up to four strips. The texture repeats
    # every PAVER_PERIOD pavers, its joints aligned with the soil's south-west corner.
    b = spec.border
    soil = (-b, -b, spec.width + b, spec.depth + b)
    strips = [(west, south, east, soil[1]), (west, soil[3], east, north),
              (west, soil[1], soil[0], soil[3]), (soil[2], soil[1], east, soil[3])]  # fmt: skip
    obj = _Obj()
    repeat = PAVER_PERIOD * PAVER
    for x0, y0, x1, y1 in strips:
        if x1 > x0 and y1 > y0:
            corners = [(x0, y0, 0.0), (x1, y0, 0.0), (x1, y1, 0.0), (x0, y1, 0.0)]
            uvs = [((x - soil[0]) / repeat, (y - soil[1]) / repeat) for x, y, _ in corners]
            obj.face(corners, uvs)
    shutil.copy(PAVER_TEXTURE, textures / "pavers.jpg")
    floor = _mesh_visual(link, "floor", obj.write(meshes / "venue_floor.obj"))
    material = ET.SubElement(floor, "material")
    for tag in ("ambient", "diffuse"):
        _text(material, tag, "1 1 1 1")  # let the albedo map set the color
    metal = ET.SubElement(ET.SubElement(material, "pbr"), "metal")
    _text(metal, "albedo_map", "textures/pavers.jpg")  # resolved against world.sdf
    _text(metal, "metalness", "0")
    _text(metal, "roughness", "0.9")

    # Glass: side walls above the stone wall, gable ends and roof, seen from both sides.
    sill = {side: STONE_WALL[1] if venue.wall == side else 0.0 for side in ("west", "east")}
    obj = _Obj()
    for x, side in ((west, "west"), (east, "east")):
        obj.face([(x, south, sill[side]), (x, north, sill[side]), (x, north, GUTTER_HEIGHT),
                  (x, south, GUTTER_HEIGHT)], double=True)  # fmt: skip
    for y in (south, north):
        obj.face([(west, y, 0.0), (east, y, 0.0), (east, y, GUTTER_HEIGHT), (middle, y, ridge),
                  (west, y, GUTTER_HEIGHT)], double=True)  # fmt: skip
    for x in (west, east):
        obj.face([(x, south, GUTTER_HEIGHT), (middle, south, ridge), (middle, north, ridge),
                  (x, north, GUTTER_HEIGHT)], double=True)  # fmt: skip
    glass = _mesh_visual(link, "glass", obj.write(meshes / "venue_glass.obj"), GLASS_RGBA)
    _text(glass, "transparency", str(GLASS_TRANSPARENCY))
    _text(glass, "cast_shadows", "false")  # the sun shines through

    # Frame: posts and rafters every bay, gutters and ridge along y, posts in the gable ends.
    obj = _Obj()
    bays = math.ceil((north - south) / BAY)
    for k in range(bays + 1):
        y = south + k * (north - south) / bays
        for x in (west, east):
            obj.beam((x, y, 0.0), (x, y, GUTTER_HEIGHT))
            obj.beam((x, y, GUTTER_HEIGHT), (middle, y, ridge))
    for x, z in ((west, GUTTER_HEIGHT), (east, GUTTER_HEIGHT), (middle, ridge)):
        obj.beam((x, south, z), (x, north, z))
    spans = math.ceil((east - west) / BAY)
    for i in range(1, spans):
        x = west + i * (east - west) / spans
        roof = GUTTER_HEIGHT + ((east - west) / 2 - abs(x - middle)) * math.tan(ROOF_PITCH)
        for y in (south, north):
            obj.beam((x, y, 0.0), (x, y, roof))
    _mesh_visual(link, "frame", obj.write(meshes / "venue_frame.obj"), FRAME_RGBA)

    thickness, height = STONE_WALL
    x = west + thickness / 2 if venue.wall == "west" else east - thickness / 2
    wall = ET.SubElement(link, "visual", name="stone_wall")
    _text(wall, "pose", _join((x, (south + north) / 2, height / 2, 0.0, 0.0, 0.0)))
    box = ET.SubElement(ET.SubElement(wall, "geometry"), "box")
    _text(box, "size", _join((thickness, north - south - 0.02, height)))  # ends off the glass
    wall.append(_color(STONE_RGBA))


def _mesh_visual(link: ET.Element, name: str, path: Path, rgba=None) -> ET.Element:
    visual = ET.SubElement(link, "visual", name=name)
    mesh = ET.SubElement(ET.SubElement(visual, "geometry"), "mesh")
    _text(mesh, "uri", f"meshes/{path.name}")  # resolved against world.sdf
    if rgba:
        visual.append(_color(rgba))
    return visual


def _color(rgba: tuple[float, ...]) -> ET.Element:
    material = ET.Element("material")
    for tag in ("ambient", "diffuse"):
        _text(material, tag, _join(rgba))
    return material


class _Obj:
    """Wavefront OBJ of flat faces, one normal per face."""

    def __init__(self):
        self.lines: list[str] = []
        self.counts = [0, 0, 0]  # vertices, texture coordinates, normals written

    def face(self, points, uvs=None, double=False) -> None:
        """Convex polygon, counter-clockwise seen from its front; double adds the back face."""
        a, b, c = points[0], points[1], points[2]
        u = [q - p for p, q in zip(a, b, strict=True)]
        v = [q - p for p, q in zip(a, c, strict=True)]
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        length = math.sqrt(sum(x * x for x in n))
        self.lines += [f"v {_join(p)}" for p in points]
        self.lines += [f"vt {_join(uv)}" for uv in uvs or []]
        self.lines.append(f"vn {_join(tuple(x / length for x in n))}")
        first, uv0, normal = self.counts[0] + 1, self.counts[1] + 1, self.counts[2] + 1
        self.counts = [self.counts[0] + len(points), self.counts[1] + len(uvs or []),
                       self.counts[2] + 1]  # fmt: skip
        refs = [f"{first + i}/{uv0 + i if uvs else ''}/{normal}" for i in range(len(points))]
        self.lines.append("f " + " ".join(refs))
        if double:
            self.face(points[::-1], uvs[::-1] if uvs else None)

    def beam(self, p0, p1) -> None:
        """Box of square BEAM profile from p0 to p1."""
        d = [q - p for p, q in zip(p0, p1, strict=True)]
        length = math.sqrt(sum(x * x for x in d))
        d = [x / length for x in d]
        # two unit axes across the beam: s horizontal (or along x for a vertical beam), t = d x s
        s = (-d[1], d[0], 0.0) if abs(d[2]) < 0.99 else (1.0, 0.0, 0.0)
        norm = math.sqrt(sum(x * x for x in s))
        s = [x / norm for x in s]
        t = (d[1] * s[2] - d[2] * s[1], d[2] * s[0] - d[0] * s[2], d[0] * s[1] - d[1] * s[0])
        h = BEAM / 2

        def corner(end, i, j):
            return tuple(e + h * (i * a + j * b) for e, a, b in zip(end, s, t, strict=True))

        ring = [(1, 1), (-1, 1), (-1, -1), (1, -1)]  # counter-clockwise about d
        for (i0, j0), (i1, j1) in zip(ring, ring[1:] + ring[:1], strict=True):
            self.face([corner(p0, i0, j0), corner(p0, i1, j1), corner(p1, i1, j1),
                       corner(p1, i0, j0)])  # fmt: skip
        self.face([corner(p1, i, j) for i, j in ring])
        self.face([corner(p0, i, j) for i, j in ring[::-1]])

    def write(self, path: Path) -> Path:
        path.write_text("\n".join(self.lines) + "\n")
        return path
