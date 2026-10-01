"""Carrot Asset Generator: harvest-stage carrot Variants as glTF binaries (trimesh).

Built z up with the origin on the soil surface at the root axis, then written y up as the
glTF spec requires. Ranges are provisional, like crops/carrot.yaml (Nantes type).
"""

import json
import math
import random
from pathlib import Path

import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

ROOT_LENGTH = (0.15, 0.20)  # meters, crown top to tip
SHOULDER_DIAMETER = (0.025, 0.04)
SHOULDER_HEIGHT = (0.005, 0.02)  # crown top above the soil
ROOT_BEND = (0.0, 0.01)  # meters, sideways offset of the tip
ROOT_SECTIONS = 20  # facets around the root
ROOT_RINGS = 16  # profile points along the taper
FOLIAGE_HEIGHT = (0.25, 0.40)  # meters, tallest leaf above the crown
LEAF_COUNT = (6, 10)
LEAFLET_PAIRS = (4, 6)  # along each leaf, plus one leaflet at the tip
LOBES = (3, 5)  # per leaflet, a fan of narrow blades
PETIOLE_SIDES = 3
PETIOLE_SEGMENTS = 6
PETIOLE_RADIUS = (0.0015, 0.0007)  # meters, at the crown and at the leaf tip
MAX_TRIANGLES = 3000

ROOT_COLOR = (237, 120, 30, 255)
LEAF_COLOR = (55, 110, 35, 255)
PETIOLE_COLOR = (110, 150, 60, 255)
Z_UP_TO_Y_UP = trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0])


def generate(variants: int, out_dir: Path) -> list[Path]:
    """Write carrot_v00.glb ... and variants.json to out_dir, replacing old Variants."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("carrot_v*.glb"):
        old.unlink()
    paths, sizes = [], {}
    for index in range(variants):
        name = f"carrot_v{index:02d}"
        meshes, sizes[name] = variant(random.Random(index))
        path = out_dir / f"{name}.glb"
        path.write_bytes(to_glb(meshes))
        paths.append(path)
    (out_dir / "variants.json").write_text(json.dumps(sizes, indent=2) + "\n")
    return paths


def variant(rng: random.Random) -> tuple[dict[str, trimesh.Trimesh], dict]:
    """Meshes by part name (z up) and their sizes in meters for collision shapes."""
    length = rng.uniform(*ROOT_LENGTH)
    radius = rng.uniform(*SHOULDER_DIAMETER) / 2
    top = rng.uniform(*SHOULDER_HEIGHT)
    root = _root(length, radius, top, rng.uniform(*ROOT_BEND))
    petioles, leaves = _foliage(rng, radius, top, rng.uniform(*FOLIAGE_HEIGHT))
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
    scene = trimesh.Scene()
    for name, mesh in meshes.items():
        scene.add_geometry(
            mesh.copy().apply_transform(Z_UP_TO_Y_UP), node_name=name, geom_name=name
        )
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
    mesh.visual = trimesh.visual.TextureVisuals(material=_material(ROOT_COLOR))
    return mesh


def _foliage(
    rng: random.Random, radius: float, top: float, height: float
) -> tuple[trimesh.Trimesh, trimesh.Trimesh]:
    """Petiole tubes and leaflet blades of all leaves, fanned out from the crown."""
    count = rng.randint(*LEAF_COUNT)
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
    return (
        _part(trimesh.util.concatenate(petioles), PETIOLE_COLOR),
        _part(trimesh.util.concatenate(blades), LEAF_COLOR),
    )


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
        length = leaf_length * 0.2 * (1.1 - 0.5 * t) * rng.uniform(0.85, 1.15)
        across = np.cross(up, direction)
        lobes = rng.randint(*LOBES)
        for spread in np.linspace(-0.6, 0.6, lobes):
            u = math.cos(spread) * direction + math.sin(spread) * across
            v = np.cross(up, u)
            lobe = length * (1 - 0.3 * abs(spread) / 0.6)
            k = len(vertices)
            vertices += [base, base + 0.5 * lobe * u + 0.12 * lobe * v, base + lobe * u,
                         base + 0.5 * lobe * u - 0.12 * lobe * v]  # fmt: skip
            faces += [(k, k + 1, k + 2), (k, k + 2, k + 3)]
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    down = mesh.face_normals[:, 2] < 0  # blades face up, for the lighting on single faces
    mesh.faces[down] = mesh.faces[down][:, ::-1]
    return mesh


def _part(mesh: trimesh.Trimesh, rgba: tuple[int, ...]) -> trimesh.Trimesh:
    mesh.visual = trimesh.visual.TextureVisuals(material=_material(rgba, double_sided=True))
    return mesh


def _material(rgba: tuple[int, ...], double_sided: bool = False) -> PBRMaterial:
    return PBRMaterial(
        baseColorFactor=rgba, metallicFactor=0.0, roughnessFactor=0.7, doubleSided=double_sided
    )
