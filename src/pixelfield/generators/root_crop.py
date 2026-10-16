"""Root crop Asset Generator: harvest-stage Variants as glTF binaries (trimesh).

One generator for Crops with a root body of revolution under a crown of leaves; per-Crop
ranges live in CROPS. Built z up with the origin on the soil surface at the root axis,
then written y up as the glTF spec requires. Ranges are provisional, like the Crop
definitions in crops/.
"""

import json
import math
import random
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial

# ponytail: the only stage generated so far; per-stage ranges in CROPS when a second comes
STAGE = "harvest"
# Each Variant mixes its colors between two ends with one sampled shade, so the library
# holds one shade per Variant; per-Plant hue_shift is not applied (see the Gazebo Exporter).
CROPS = {
    "carrot": {  # Nantes type
        "root_length": (0.15, 0.20),  # meters, crown top to tip
        "shoulder_diameter": (0.025, 0.04),
        "shoulder_height": (0.005, 0.02),  # crown top above the soil
        "root_bend": (0.0, 0.01),  # meters, sideways offset of the tip
        "foliage_height": (0.25, 0.40),  # meters, tallest leaf above the crown
        "leaf_count": (6, 10),
        "root_color": ((225, 105, 25), (245, 140, 40)),
        "leaf_color": ((40, 95, 35), (80, 125, 40)),
        "petiole_color": ((95, 135, 55), (130, 165, 70)),
        "root_profile": "taper",
        "leaf": "divided",
        "leaf_reach": (0.2, 0.6),  # outward reach of a leaf tip, fraction of its rise
        "leaf_arch": 1.1,  # curve control height, fraction of the rise
        "leaf_tip": (0.75, 0.95),  # tip height, fraction of the rise
        "petiole_radius": (0.0015, 0.0007),  # meters, at the crown and at the leaf tip
        "petiole_sides": 3,
    },
    "beetroot": {  # round red table beet (Detroit or Boltardy type)
        "root_length": (0.12, 0.20),  # meters, crown top to the taproot tip
        "shoulder_diameter": (0.05, 0.08),  # widest point of the globe
        "shoulder_height": (0.02, 0.035),  # a third to half of the globe above the soil
        "root_bend": (0.0, 0.015),
        "foliage_height": (0.28, 0.40),
        "leaf_count": (8, 14),
        # linear factors (sRGB in brackets): deep crimson root, magenta stalks, fresh green
        "root_color": ((35, 2, 8), (60, 4, 12)),  # (100-135, 20-30, 45-60)
        "leaf_color": ((30, 80, 12), (45, 110, 20)),  # (95-118, 150-175, 60-80)
        "petiole_color": ((80, 3, 14), (120, 6, 22)),  # (155-185, 30-40, 65-80)
        "root_profile": "globe",
        "leaf": "simple",
        "leaf_reach": (0.35, 0.7),
        "leaf_arch": 0.7,  # stalks fan out in a V, blades keep pointing up and out
        "leaf_tip": (0.9, 1.0),
        "blade_start": (0.4, 0.5),  # blade starts this far along the leaf
        "blade_width": (0.45, 0.6),  # blade width, fraction of the blade length
        "petiole_radius": (0.003, 0.0008),  # the midrib continues the stalk to the leaf tip
        "petiole_sides": 5,
    },
    "radish": {  # long red radish, white at the tip
        "root_length": (0.15, 0.25),
        "shoulder_diameter": (0.025, 0.045),
        "shoulder_height": (0.02, 0.05),  # the red shoulder pushes out of the soil
        "root_bend": (0.0, 0.02),
        "foliage_height": (0.25, 0.38),
        "leaf_count": (6, 10),
        # linear factors (sRGB in brackets): crimson-pink root, pale green stalks, dark green
        "root_color": ((130, 3, 10), (170, 6, 22)),  # (200-212, 25-35, 55-80)
        "tip_color": ((205, 185, 185), (225, 205, 205)),  # (232-243, 222-233, 222-233)
        "tip_start": (0.65, 0.8),  # root fades to the tip color this far down
        "leaf_color": ((22, 65, 9), (40, 95, 16)),  # (80-110, 140-170, 50-70)
        "petiole_color": ((95, 135, 55), (125, 160, 75)),  # (170-190, 190-208, 130-145)
        "root_profile": "spindle",
        "leaf": "lobed",
        "leaf_reach": (0.3, 0.6),
        "leaf_arch": 0.8,
        "leaf_tip": (0.85, 1.0),
        "blade_start": (0.25, 0.35),  # side lobes reach far down the stalk
        "blade_width": (0.4, 0.5),
        "petiole_radius": (0.0035, 0.001),
        "petiole_sides": 5,
    },
}
ROOT_SECTIONS = 20  # facets around the root
ROOT_RINGS = 16  # profile points along the taper
LEAFLET_PAIRS = (5, 7)  # along each leaf, plus one leaflet at the tip
SEGMENT_PAIRS = (3, 4)  # narrow segments along each leaflet, plus one at its tip
LEAFLET_LENGTH = 0.12  # fraction of the leaf length, shrinking toward the tip
SEGMENT_WIDTH = 0.12  # half-width of a segment, fraction of its length
PETIOLE_SEGMENTS = 6
BLADE_STATIONS = 10  # cross-sections along a simple leaf blade, three times that if lobed
BLADE_COLUMNS = 3  # points per side across the blade, plus the midrib
MAX_TRIANGLES = 8000
Z_UP_TO_Y_UP = trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0])


def generate(crop: str, variants: int, out_dir: Path) -> list[Path]:
    """Write <crop>_harvest_v00.glb ... and variants.json to out_dir, replacing old Variants."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob(f"{crop}_*.glb"):
        old.unlink()
    paths, sizes = [], {}
    for index in range(variants):
        name = f"{crop}_{STAGE}_v{index:02d}"
        meshes, sizes[name] = variant(random.Random(index), CROPS[crop])
        path = out_dir / f"{name}.glb"
        path.write_bytes(to_glb(meshes))
        paths.append(path)
    (out_dir / "variants.json").write_text(json.dumps(sizes, indent=2) + "\n")
    return paths


def variant(rng: random.Random, crop: dict) -> tuple[dict[str, trimesh.Trimesh], dict]:
    """Meshes by part name (z up) and their sizes in meters, for one entry of CROPS."""
    length = rng.uniform(*crop["root_length"])
    radius = rng.uniform(*crop["shoulder_diameter"]) / 2
    top = rng.uniform(*crop["shoulder_height"])
    shade = rng.random()
    root = ROOTS[crop["root_profile"]](length, radius, top, rng.uniform(*crop["root_bend"]))
    if "tip_color" in crop:  # fade to the tip color around tip_start, drawn last
        middle = top - rng.uniform(*crop["tip_start"]) * length
        root.metadata["fade"] = (_mix(crop["tip_color"], shade), middle + 0.1 * length,
                                 middle - 0.1 * length)  # fmt: skip
    root.visual = trimesh.visual.TextureVisuals(material=_material(_mix(crop["root_color"], shade)))
    height = rng.uniform(*crop["foliage_height"])
    petioles, leaves = _foliage(rng, radius, top, height, crop)
    _part(petioles, _mix(crop["petiole_color"], shade))
    _part(leaves, _mix(crop["leaf_color"], shade))
    foliage = np.vstack([petioles.vertices, leaves.vertices])
    sizes = {
        "root": {"length": length, "radius": radius, "top": top},
        "foliage": {
            "height": foliage[:, 2].max(),
            "radius": np.hypot(foliage[:, 0], foliage[:, 1]).max(),
        },
    }
    sizes = {part: {k: round(float(v), 4) for k, v in d.items()} for part, d in sizes.items()}
    return {"root": root, "petioles": petioles, "leaves": leaves}, sizes


def to_glb(meshes: dict[str, trimesh.Trimesh]) -> bytes:
    """All parts as one mesh with one material, so a Plant is a single render item
    (rendering is CPU-bound on render items, docs/design/perf.md). Each part samples its
    own block of a small palette texture; one UV per part keeps the sampling at mip 0."""
    # part colors are linear (glTF baseColorFactor); texture texels are sRGB
    # A part with a "fade" (tip color, z where it starts, z where it ends) gets a vertical
    # gradient in its column and v by height; other parts sample the middle of a flat column.
    parts = list(meshes.values())
    rows = 32 if any("fade" in m.metadata for m in parts) else 8
    linear = np.empty((rows, len(parts), 4))
    uv = []
    for i, mesh in enumerate(parts):
        color = np.array(mesh.visual.material.baseColorFactor) / 255
        v = np.full(len(mesh.vertices), 0.5)
        linear[:, i] = color
        if "fade" in mesh.metadata:
            tip, z0, z1 = mesh.metadata["fade"]
            linear[:, i] = color + np.linspace(0, 1, rows)[:, None] * (np.array(tip) / 255 - color)
            s = np.clip((z0 - mesh.vertices[:, 2]) / (z0 - z1), 0.0, 1.0)
            v = 1 - (0.5 + s * (rows - 1)) / rows  # trimesh flips v to glTF's top-left origin
        uv.append(np.column_stack([np.full(len(v), (i + 0.5) / len(parts)), v]))
    srgb = np.where(linear <= 0.0031308, 12.92 * linear, 1.055 * linear ** (1 / 2.4) - 0.055)
    srgb[..., 3] = linear[..., 3]
    palette = np.repeat(np.round(srgb * 255).astype(np.uint8), 8, axis=1)
    uv = np.vstack(uv)
    merged = trimesh.util.concatenate(
        [trimesh.Trimesh(m.vertices, m.faces, process=False) for m in meshes.values()]
    )
    material = PBRMaterial(baseColorTexture=Image.fromarray(palette, "RGBA"),
                           metallicFactor=0.0, roughnessFactor=0.7, doubleSided=True)  # fmt: skip
    merged.visual = trimesh.visual.TextureVisuals(uv=uv, material=material)
    merged.apply_transform(Z_UP_TO_Y_UP)
    scene = trimesh.Scene()
    scene.add_geometry(merged, node_name="plant", geom_name="plant")
    return scene.export(file_type="glb")


def _taper_root(length: float, radius: float, top: float, bend: float) -> trimesh.Trimesh:
    """Solid of revolution: flat crown with a rounded edge, then a Nantes-like taper."""
    edge = 0.3 * radius
    profile = [(0.0, top)]
    for a in np.linspace(math.pi / 2, 0.0, 5):
        profile.append((radius - edge + edge * math.cos(a), top - edge + edge * math.sin(a)))
    for t in np.linspace(0.0, 1.0, ROOT_RINGS)[1:]:
        r = radius * (1 - 0.6 * t) * math.sqrt(1 - t**4)
        profile.append((r, top - edge - t * (length - edge)))
    return _revolve(profile, length, top, bend)


def _globe_root(length: float, radius: float, top: float, bend: float) -> trimesh.Trimesh:
    """Solid of revolution: small flat crown, a top-shaped globe, then a thin taproot."""
    height, tail = 1.9 * radius, 0.08 * radius  # globe height, taproot radius where it starts
    profile = [(0.0, top)]
    for s in np.linspace(0.0, 1.0, ROOT_RINGS):
        # widest about 40% down, like the photographed beets
        r = max(radius * math.sin(math.pi * (0.12 + 0.88 * s) ** 0.9), tail)
        profile.append((r, top - s * height))
    for t in np.linspace(0.0, 1.0, 6)[1:]:
        profile.append((tail * (1 - t), top - height - t * (length - height)))
    return _revolve(profile, length, top, bend)


def _spindle_root(length: float, radius: float, top: float, bend: float) -> trimesh.Trimesh:
    """Solid of revolution: narrow crown, rounded shoulder, a long taper to a pointed tip."""
    profile = [(0.0, top)]
    for t in np.linspace(0.0, 1.0, 24):
        shoulder = 0.35 + 0.65 * math.sin(min(t / 0.1, 1.0) * math.pi / 2)
        profile.append((radius * shoulder * (1 - t) ** 1.2, top - t * length))
    return _revolve(profile, length, top, bend)


def _revolve(profile, length: float, top: float, bend: float) -> trimesh.Trimesh:
    """Revolve a crown-to-tip profile; the tip bends sideways by `bend`."""
    # tip to crown, so the normals point outward
    mesh = trimesh.creation.revolve(profile[::-1], sections=ROOT_SECTIONS)
    depth = (top - mesh.vertices[:, 2]) / length
    mesh.vertices[:, 0] += bend * depth**2
    return mesh


def _foliage(
    rng: random.Random, radius: float, top: float, height: float, crop: dict
) -> tuple[trimesh.Trimesh, trimesh.Trimesh]:
    """Petiole tubes and leaf blades of all leaves, fanned out from the crown."""
    count = rng.randint(*crop["leaf_count"])
    petioles, blades = [], []
    for i in range(count):
        azimuth = 2 * math.pi * i / count + rng.uniform(-0.3, 0.3)
        out = np.array([math.cos(azimuth), math.sin(azimuth), 0.0])
        rise = height * rng.uniform(0.75, 1.0)
        reach = rise * rng.uniform(*crop["leaf_reach"])
        start = 0.4 * radius * out + [0, 0, top]
        # quadratic Bezier: up and out; with arch above 1 the tip droops back below the peak
        bezier = (start, start + 0.3 * reach * out + [0, 0, crop["leaf_arch"] * rise],
                  start + reach * out + [0, 0, rise * rng.uniform(*crop["leaf_tip"])])  # fmt: skip
        petioles.append(_tube(bezier, crop["petiole_radius"], crop["petiole_sides"]))
        blades.append(LEAVES[crop["leaf"]](rng, bezier, crop))
    return trimesh.util.concatenate(petioles), trimesh.util.concatenate(blades)


def _bezier(curve, t: float) -> tuple[np.ndarray, np.ndarray]:
    """Point and unit tangent of a quadratic Bezier at t."""
    p0, p1, p2 = (np.asarray(p, dtype=float) for p in curve)
    point = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t**2 * p2
    tangent = 2 * (1 - t) * (p1 - p0) + 2 * t * (p2 - p1)
    return point, tangent / np.linalg.norm(tangent)


def _frame(tangent: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Side and up vectors across a curve; the side stays horizontal."""
    side = np.cross([0.0, 0.0, 1.0], tangent)
    side /= np.linalg.norm(side)
    return side, np.cross(tangent, side)


def _tube(curve, radius: tuple[float, float], n: int) -> trimesh.Trimesh:
    """Thin open tube with n sides along the curve, tapering from the crown to the tip."""
    vertices, faces = [], []
    for j, t in enumerate(np.linspace(0.0, 1.0, PETIOLE_SEGMENTS + 1)):
        point, tangent = _bezier(curve, t)
        side, up = _frame(tangent)
        r = radius[0] + t * (radius[1] - radius[0])
        for k in range(n):
            a = 2 * math.pi * k / n
            vertices.append(point + r * (math.cos(a) * side + math.sin(a) * up))
        if j:
            for k in range(n):
                a, b = (j - 1) * n + k, (j - 1) * n + (k + 1) % n
                faces += [(a, b, b + n), (a, b + n, a + n)]
    return trimesh.Trimesh(vertices, faces, process=False)


def _leaflets(rng: random.Random, curve, crop: dict) -> trimesh.Trimesh:
    """Leaflet pairs along the outer part of the leaf plus one at the tip."""
    _, _, tip = curve
    leaf_length = np.linalg.norm(np.asarray(tip) - curve[0])
    vertices, faces = [], []
    pairs = rng.randint(*LEAFLET_PAIRS)
    spots = [(t, s) for t in np.linspace(0.35, 0.95, pairs) for s in (-1, 1)] + [(1.0, 0)]
    for t, s in spots:
        base, tangent = _bezier(curve, t)
        side, up = _frame(tangent)
        # leaflets point forward and outward, shrinking toward the tip
        direction = s * side * math.cos(0.7) + tangent * (math.sin(0.7) if s else 1.0) - 0.2 * up
        direction /= np.linalg.norm(direction)
        length = leaf_length * LEAFLET_LENGTH * (1.1 - 0.5 * t) * rng.uniform(0.85, 1.15)
        across = np.cross(up, direction)
        # each leaflet is divided again: narrow segment pairs along a short midrib
        k, rib = len(vertices), 0.03 * length * np.cross(up, direction)
        vertices += [base + rib, base + length * direction, base - rib]
        faces.append((k, k + 1, k + 2))
        pairs = rng.randint(*SEGMENT_PAIRS)
        for tt, ss in [(u, v) for u in np.linspace(0.1, 0.8, pairs) for v in (-1, 1)] + [(1.0, 0)]:
            start = base + tt * length * direction
            angle = 0.9 * ss
            u = math.cos(angle) * direction + math.sin(angle) * across
            v = np.cross(up, u)
            segment = 0.45 * length * (1.1 - 0.5 * tt) * rng.uniform(0.8, 1.2)
            w = SEGMENT_WIDTH * segment
            k = len(vertices)
            vertices += [start, start + 0.4 * segment * u + w * v, start + segment * u,
                         start + 0.4 * segment * u - w * v]  # fmt: skip
            faces += [(k, k + 1, k + 2), (k, k + 2, k + 3)]
    return _face_up(trimesh.Trimesh(vertices, faces, process=False))


def _simple_blade(rng: random.Random, curve, crop: dict) -> trimesh.Trimesh:
    """One ovate blade with a blunt tip: widest about 40% along, rounded towards the tip."""
    return _blade(rng, curve, crop, lambda rng: lambda u: math.sin(math.pi * u**0.75) ** 0.6,
                  BLADE_STATIONS)  # fmt: skip


def _lobed_blade(rng: random.Random, curve, crop: dict) -> trimesh.Trimesh:
    """Lyrate blade: a large rounded end lobe and smaller side lobes down the stalk."""

    def outline(rng: random.Random):
        pairs = rng.randint(2, 4)

        def width(u: float) -> float:
            end = math.sin(math.pi * ((u - 0.45) / 0.55) ** 0.8) ** 0.6 if u > 0.45 else 0.0
            side = (0.25 + 0.9 * u) * abs(math.sin(math.pi * pairs * u / 0.5)) ** 0.7
            return max(end, side if u < 0.5 else 0.0)

        return width

    return _blade(rng, curve, crop, outline, 3 * BLADE_STATIONS)


def _blade(rng: random.Random, curve, crop: dict, outline, stations: int) -> trimesh.Trimesh:
    """Blade on the outer part of the leaf, slightly cupped, with a wavy margin.

    The stalk tube runs on to the tip as the midrib, so the blade spans both sides of it.
    `outline(rng)` returns the half-width (0 to 1) as a function of u, 0 at the blade base
    and 1 at the tip.
    """
    _, _, tip = curve
    leaf_length = np.linalg.norm(np.asarray(tip) - curve[0])
    start = rng.uniform(*crop["blade_start"])
    half_width = 0.5 * rng.uniform(*crop["blade_width"]) * (1 - start) * leaf_length
    cup = 0.15 * half_width
    wave, phase = 0.06 * half_width, rng.uniform(0.0, 2 * math.pi)
    shape = outline(rng)
    n = 2 * BLADE_COLUMNS + 1
    vertices, faces = [], []
    for j, t in enumerate(np.linspace(start, 1.0, stations)):
        point, tangent = _bezier(curve, t)
        side, up = _frame(tangent)
        u = (t - start) / (1 - start)
        w = half_width * shape(u)
        for k in range(-BLADE_COLUMNS, BLADE_COLUMNS + 1):
            a = k / BLADE_COLUMNS
            # cupped across, wavy at the margin, both fading to the base and the tip
            margin = wave * math.sin(9 * u + phase + 2 * a) if abs(k) == BLADE_COLUMNS else 0
            lift = (cup * a**2 + margin) * w / half_width
            vertices.append(point + a * w * side + lift * up)
        if j:
            for k in range(n - 1):
                a, b = (j - 1) * n + k, j * n + k
                faces += [(a, b, b + 1), (a, b + 1, a + 1)]
    return _face_up(trimesh.Trimesh(vertices, faces, process=False))


def _face_up(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    down = mesh.face_normals[:, 2] < 0  # blades face up, for the lighting on single faces
    mesh.faces[down] = mesh.faces[down][:, ::-1]
    return mesh


ROOTS = {"taper": _taper_root, "globe": _globe_root, "spindle": _spindle_root}
LEAVES = {"divided": _leaflets, "simple": _simple_blade, "lobed": _lobed_blade}


def _mix(ends: tuple[tuple[int, ...], tuple[int, ...]], shade: float) -> tuple[int, ...]:
    return tuple(round(a + shade * (b - a)) for a, b in zip(*ends, strict=True)) + (255,)


def _part(mesh: trimesh.Trimesh, rgba: tuple[int, ...]) -> trimesh.Trimesh:
    mesh.visual = trimesh.visual.TextureVisuals(material=_material(rgba, double_sided=True))
    return mesh


def _material(rgba: tuple[int, ...], double_sided: bool = False) -> PBRMaterial:
    return PBRMaterial(
        baseColorFactor=rgba, metallicFactor=0.0, roughnessFactor=0.7, doubleSided=double_sided
    )
