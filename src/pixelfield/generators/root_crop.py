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
    },
}
ROOT_SECTIONS = 20  # facets around the root
ROOT_RINGS = 16  # profile points along the taper
LEAFLET_PAIRS = (5, 7)  # along each leaf, plus one leaflet at the tip
SEGMENT_PAIRS = (3, 4)  # narrow segments along each leaflet, plus one at its tip
LEAFLET_LENGTH = 0.12  # fraction of the leaf length, shrinking toward the tip
SEGMENT_WIDTH = 0.12  # half-width of a segment, fraction of its length
PETIOLE_SIDES = 3
PETIOLE_SEGMENTS = 6
PETIOLE_RADIUS = (0.0015, 0.0007)  # meters, at the crown and at the leaf tip
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
    root = _root(length, radius, top, rng.uniform(*crop["root_bend"]))
    root.visual = trimesh.visual.TextureVisuals(material=_material(_mix(crop["root_color"], shade)))
    height = rng.uniform(*crop["foliage_height"])
    petioles, leaves = _foliage(rng, radius, top, height, crop["leaf_count"])
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
    linear = np.array([[m.visual.material.baseColorFactor for m in meshes.values()]]) / 255
    srgb = np.where(linear <= 0.0031308, 12.92 * linear, 1.055 * linear ** (1 / 2.4) - 0.055)
    srgb[..., 3] = linear[..., 3]
    palette = np.repeat(np.repeat(np.round(srgb * 255).astype(np.uint8), 8, axis=0), 8, axis=1)
    colors = linear[0]
    uv = np.vstack([
        np.tile([(i + 0.5) / len(colors), 0.5], (len(mesh.vertices), 1))
        for i, mesh in enumerate(meshes.values())
    ])  # fmt: skip
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


def _root(length: float, radius: float, top: float, bend: float) -> trimesh.Trimesh:
    """Solid of revolution: flat crown with a rounded edge, then a Nantes-like taper."""
    edge = 0.3 * radius
    profile = [(0.0, top)]
    for a in np.linspace(math.pi / 2, 0.0, 5):
        profile.append((radius - edge + edge * math.cos(a), top - edge + edge * math.sin(a)))
    for t in np.linspace(0.0, 1.0, ROOT_RINGS)[1:]:
        r = radius * (1 - 0.6 * t) * math.sqrt(1 - t**4)
        profile.append((r, top - edge - t * (length - edge)))
    # tip to crown, so the normals point outward
    mesh = trimesh.creation.revolve(profile[::-1], sections=ROOT_SECTIONS)
    depth = (top - mesh.vertices[:, 2]) / length
    mesh.vertices[:, 0] += bend * depth**2
    return mesh


def _foliage(
    rng: random.Random, radius: float, top: float, height: float, leaf_count: tuple[int, int]
) -> tuple[trimesh.Trimesh, trimesh.Trimesh]:
    """Petiole tubes and leaflet blades of all leaves, fanned out from the crown."""
    count = rng.randint(*leaf_count)
    petioles, blades = [], []
    for i in range(count):
        azimuth = 2 * math.pi * i / count + rng.uniform(-0.3, 0.3)
        out = np.array([math.cos(azimuth), math.sin(azimuth), 0.0])
        rise = height * rng.uniform(0.75, 1.0)
        reach = rise * rng.uniform(0.2, 0.6)
        start = 0.4 * radius * out + [0, 0, top]
        # quadratic Bezier: up and out, the tip droops back below the peak
        bezier = (start, start + 0.3 * reach * out + [0, 0, 1.1 * rise],
                  start + reach * out + [0, 0, rise * rng.uniform(0.75, 0.95)])  # fmt: skip
        petioles.append(_tube(bezier))
        blades.append(_leaflets(rng, bezier))
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


def _tube(curve) -> trimesh.Trimesh:
    """Thin open tube along the curve, tapering from the crown to the tip."""
    vertices, faces, n = [], [], PETIOLE_SIDES
    for j, t in enumerate(np.linspace(0.0, 1.0, PETIOLE_SEGMENTS + 1)):
        point, tangent = _bezier(curve, t)
        side, up = _frame(tangent)
        r = PETIOLE_RADIUS[0] + t * (PETIOLE_RADIUS[1] - PETIOLE_RADIUS[0])
        for k in range(n):
            a = 2 * math.pi * k / n
            vertices.append(point + r * (math.cos(a) * side + math.sin(a) * up))
        if j:
            for k in range(n):
                a, b = (j - 1) * n + k, (j - 1) * n + (k + 1) % n
                faces += [(a, b, b + n), (a, b + n, a + n)]
    return trimesh.Trimesh(vertices, faces, process=False)


def _leaflets(rng: random.Random, curve) -> trimesh.Trimesh:
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
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    down = mesh.face_normals[:, 2] < 0  # blades face up, for the lighting on single faces
    mesh.faces[down] = mesh.faces[down][:, ::-1]
    return mesh


def _mix(ends: tuple[tuple[int, ...], tuple[int, ...]], shade: float) -> tuple[int, ...]:
    return tuple(round(a + shade * (b - a)) for a, b in zip(*ends, strict=True)) + (255,)


def _part(mesh: trimesh.Trimesh, rgba: tuple[int, ...]) -> trimesh.Trimesh:
    mesh.visual = trimesh.visual.TextureVisuals(material=_material(rgba, double_sided=True))
    return mesh


def _material(rgba: tuple[int, ...], double_sided: bool = False) -> PBRMaterial:
    return PBRMaterial(
        baseColorFactor=rgba, metallicFactor=0.0, roughnessFactor=0.7, doubleSided=double_sided
    )
