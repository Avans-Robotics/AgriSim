"""Field Spec plus Crops to Field Layout, and the Field Layout as a Manifest dict."""

import math
import random
from dataclasses import asdict, dataclass

from pixelfield.core.spec import Crop, FieldSpec, PlantingPattern

MANIFEST_FORMAT_VERSION = 1
ROBOT_INTERFACE_VERSION = 1  # spec section 14; a breaking change raises it


@dataclass(frozen=True)
class Pixel:
    row: int
    col: int
    crop: str | None
    origin: tuple[float, float]  # south-west corner, meters


@dataclass(frozen=True)
class Plant:
    id: str
    crop: str
    pixel: tuple[int, int]
    variant: str
    x: float
    y: float
    z: float
    yaw: float
    scale: float
    pull_out_force: float


@dataclass(frozen=True)
class FieldLayout:
    spec: FieldSpec
    crops: dict[str, Crop]  # the Crops used in this Field, by name
    pixels: tuple[Pixel, ...]
    plants: tuple[Plant, ...]


def planting_positions(
    pattern: PlantingPattern, pixel_size: float, row_direction: float
) -> list[tuple[float, float]]:
    """Nominal Plant positions relative to the Pixel centre, before any randomness.

    Rows run along `row_direction` and are centred in the Pixel. Positions outside the
    square inset by `margin` are dropped, so rotated rows get shorter towards the corners.
    """
    half = pixel_size / 2 - pattern.margin
    if half < 0:
        return []
    c, s = math.cos(row_direction), math.sin(row_direction)
    extent = half * (abs(c) + abs(s))  # half-width of the inset square, along or across the rows

    def offsets(spacing: float) -> list[float]:
        n = int(2 * extent / spacing + 1e-9) + 1
        return [(i - (n - 1) / 2) * spacing for i in range(n)]

    positions = []
    for across in offsets(pattern.row_spacing):
        for along in offsets(pattern.in_row_spacing):
            x = along * c - across * s
            y = along * s + across * c
            if abs(x) <= half + 1e-9 and abs(y) <= half + 1e-9:
                positions.append((x, y))
    return positions


def build_layout(spec: FieldSpec, crops: dict[str, Crop]) -> FieldLayout:
    pixels, plants = [], []
    for row, names in enumerate(spec.grid):
        for col, name in enumerate(names):
            origin = (spec.column_x(col), (spec.rows - 1 - row) * spec.pixel_size)
            pixels.append(Pixel(row, col, name, origin))
            if name is not None:
                plants += _plant_pixel(spec, crops[name], row, col, origin)
    return FieldLayout(spec, crops, tuple(pixels), tuple(plants))


def _plant_pixel(
    spec: FieldSpec, crop: Crop, row: int, col: int, origin: tuple[float, float]
) -> list[Plant]:
    pattern = crop.planting
    direction = pattern.row_direction if spec.row_direction is None else spec.row_direction
    # One generator per Pixel: editing one Pixel leaves the Plants of all others unchanged.
    rng = random.Random(f"{spec.seed}:{row}:{col}")
    half = spec.pixel_size / 2 - pattern.margin
    cx, cy = origin[0] + spec.pixel_size / 2, origin[1] + spec.pixel_size / 2

    plants = []
    for i, (x, y) in enumerate(planting_positions(pattern, spec.pixel_size, direction)):
        # Draw every value for every position, so a missing Plant does not shift the others.
        missing = rng.random() < pattern.missing_rate
        dx, dy = rng.gauss(0, pattern.jitter), rng.gauss(0, pattern.jitter)
        variant = rng.randrange(crop.variants)
        yaw = rng.uniform(*crop.yaw)
        scale = rng.uniform(*crop.scale)
        force = rng.uniform(*crop.pull_out_force)
        if missing:
            continue
        # ponytail: clamping keeps the margin exact; Plants pile up on the edge only if jitter
        # approaches the margin, resample instead if a Crop ever needs that.
        x = min(max(x + dx, -half), half)
        y = min(max(y + dy, -half), half)
        plants.append(
            Plant(
                id=f"r{row}c{col}-{i:03d}",
                crop=crop.name,
                pixel=(row, col),
                variant=f"{crop.name}_{crop.stage}_v{variant:02d}",
                x=cx + x,
                y=cy + y,
                z=0.0,
                yaw=yaw,
                scale=scale,
                pull_out_force=force,
            )
        )
    return plants


def to_manifest(layout: FieldLayout) -> dict:
    spec = layout.spec
    return {
        "format_version": MANIFEST_FORMAT_VERSION,
        "robot_interface": ROBOT_INTERFACE_VERSION,
        "field": {
            "pixel_size": spec.pixel_size,
            "rows": spec.rows,
            "cols": spec.cols,
            "width": round(spec.width, 6),
            "depth": round(spec.depth, 6),
            "path_gap": (
                {"every_n_cols": spec.path_gap[0], "width": spec.path_gap[1]}
                if spec.path_gap
                else None
            ),
            "path_gaps": [[round(x0, 6), round(x1, 6)] for x0, x1 in spec.path_gaps],
            "border": spec.border,
            "seed": spec.seed,
            "spec_sha256": spec.sha256,
        },
        "crops": {
            name: {
                "library": crop.library,
                "pull_out_curve": asdict(crop.pull_out_curve) if crop.pull_out_curve else None,
            }
            for name, crop in sorted(layout.crops.items())
        },
        "pixels": [
            {
                "row": p.row,
                "col": p.col,
                "crop": p.crop,
                "origin": [round(p.origin[0], 6), round(p.origin[1], 6)],
            }
            for p in layout.pixels
        ],
        "plants": [
            {
                "id": p.id,
                "crop": p.crop,
                "pixel": list(p.pixel),
                "variant": p.variant,
                "pose": {
                    "x": round(p.x, 4),
                    "y": round(p.y, 4),
                    "z": round(p.z, 4),
                    "yaw": round(p.yaw, 4),
                },
                "scale": round(p.scale, 4),  # the picked Plant matches its visual
                "pull_out_force": round(p.pull_out_force, 2),
            }
            for p in layout.plants
        ],
    }
