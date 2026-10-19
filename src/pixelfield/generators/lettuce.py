"""Lettuce Asset Generator: romaine (cos) heads at harvest as glTF binaries (trimesh).

A rosette of leaves in a golden-angle spiral: outer leaves long, darker and leaning out,
inner leaves shorter, paler, upright and cupped around the heart. Each leaf has a pale
midrib, a crinkled surface and a frilly margin. Reuses the root crop generator's curves,
palette texture and file writing; ranges are provisional, like crops/lettuce.yaml.
"""

import math
import random
from pathlib import Path

import numpy as np
import trimesh

from pixelfield.generators import root_crop

CROPS = {
    "lettuce": {  # romaine (cos)
        "head_height": (0.22, 0.32),  # meters, about the tallest leaf tip above the soil
        "leaf_count": (18, 26),
        "outer_tilt": (0.35, 0.6),  # radians from vertical, outermost leaf
        "inner_tilt": 0.1,  # radians from vertical, innermost leaf
        "leaf_width": (0.45, 0.6),  # widest point, fraction of the leaf length
        # linear factors (sRGB in brackets): green outer leaves, pale heart, whitish midribs
        "outer_color": ((38, 90, 12), (60, 115, 20)),  # (108-135, 160-180, 60-80)
        "inner_color": ((115, 160, 45), (145, 185, 65)),  # (180-200, 210-225, 118-140)
        "rib_color": ((180, 200, 135), (205, 220, 160)),  # (220-232, 230-240, 192-210)
    },
}
INNER_FRACTION = 0.35  # the youngest leaves form the pale heart
STATIONS = 12  # cross-sections along a leaf
COLUMNS = 4  # points per side across a leaf, plus the midrib
RIB_RADIUS = (0.004, 0.001)  # meters, at the base and at the tip
RIB_SIDES = 4
MAX_TRIANGLES = 8000


def generate(crop: str, variants: int, out_dir: Path) -> list[Path]:
    """Write <crop>_harvest_v00.glb ... and variants.json to out_dir, replacing old Variants."""
    return root_crop.generate(crop, variants, out_dir, table=CROPS, make=variant)


def variant(rng: random.Random, crop: dict) -> tuple[dict[str, trimesh.Trimesh], dict]:
    """Meshes by part name (z up) and their sizes in meters, for one entry of CROPS."""
    height = rng.uniform(*crop["head_height"])
    count = rng.randint(*crop["leaf_count"])
    outer_tilt = rng.uniform(*crop["outer_tilt"])
    shade = rng.random()
    outer, inner, rib = [], [], []
    for i in range(count):
        age = 1 - i / (count - 1)  # 1 for the outermost (oldest) leaf, 0 for the heart
        azimuth = i * math.radians(137.5) + rng.uniform(-0.15, 0.15)
        out = np.array([math.cos(azimuth), math.sin(azimuth), 0.0])
        tilt = crop["inner_tilt"] + age**1.5 * (outer_tilt - crop["inner_tilt"])
        length = height * (0.6 + 0.45 * age) * rng.uniform(0.9, 1.05) / math.cos(0.5 * tilt)
        base = 0.01 * (0.3 + age) * out + [0, 0, 0.005]
        tip = base + length * (math.sin(tilt) * out + [0, 0, math.cos(tilt)])
        # quadratic Bezier: leaves rise from the base, then lean out to the tip
        curve = (base, base + 0.5 * length * np.array([0, 0, 1.0]) + 0.2 * (tip - base), tip)
        width = rng.uniform(*crop["leaf_width"]) * length * (0.75 + 0.25 * age)
        (outer if age > INNER_FRACTION else inner).append(_leaf(rng, curve, width, age))
        radius = (RIB_RADIUS[0] * (0.5 + age), RIB_RADIUS[1])
        rib.append(root_crop._tube(curve, radius, RIB_SIDES))
    parts = {"outer": outer, "inner": inner, "rib": rib}
    meshes = {name: trimesh.util.concatenate(m) for name, m in parts.items()}
    for name, mesh in meshes.items():
        root_crop._part(mesh, root_crop._mix(crop[f"{name}_color"], shade))
    points = np.vstack([m.vertices for m in meshes.values()])
    sizes = {"foliage": {"height": points[:, 2].max(),
                         "radius": np.hypot(points[:, 0], points[:, 1]).max()}}  # fmt: skip
    sizes = {part: {k: round(float(v), 4) for k, v in d.items()} for part, d in sizes.items()}
    return meshes, sizes


def _leaf(rng: random.Random, curve, width: float, age: float) -> trimesh.Trimesh:
    """Obovate blade around the midrib curve: cupped towards the heart, crinkled, frilly."""
    half = width / 2
    cup = half * (0.25 + 0.5 * (1 - age))  # the heart wraps more tightly
    crinkle, frill = 0.0025, 0.005
    phase = rng.uniform(0.0, 2 * math.pi)
    n = 2 * COLUMNS + 1
    vertices, faces = [], []
    for j, t in enumerate(np.linspace(0.0, 1.0, STATIONS)):
        point, tangent = root_crop._bezier(curve, t)
        side, up = root_crop._frame(tangent)  # up points into the head for leaning leaves
        w = half * math.sin(math.pi * t**1.4) ** 0.3  # widest about 60% along, rounded tip
        for k in range(-COLUMNS, COLUMNS + 1):
            a = k / COLUMNS
            bumps = crinkle * math.sin(7 * t + phase) * math.sin(3 * a + phase)
            edge = frill * math.sin(16 * t + phase + 3 * a) * t if abs(k) == COLUMNS else 0.0
            lift = (cup * a**2 + bumps + edge) * w / half
            vertices.append(point + a * w * side + lift * up)
        if j:
            for k in range(n - 1):
                a, b = (j - 1) * n + k, j * n + k
                faces += [(a, b, b + 1), (a, b + 1, a + 1)]
    return trimesh.Trimesh(vertices, faces, process=False)
