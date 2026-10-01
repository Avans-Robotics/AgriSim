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
MAX_TRIANGLES = 3000

ROOT_COLOR = (237, 120, 30, 255)
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
    sizes = {"root": {"length": round(length, 4), "radius": round(radius, 4), "top": round(top, 4)}}
    return {"root": root}, sizes


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


def _material(rgba: tuple[int, ...]) -> PBRMaterial:
    return PBRMaterial(baseColorFactor=rgba, metallicFactor=0.0, roughnessFactor=0.7)
