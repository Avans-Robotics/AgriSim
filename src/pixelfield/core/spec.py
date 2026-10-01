"""Loading Field Specs and Crop definitions from YAML."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

EMPTY = "."


@dataclass(frozen=True)
class PlantingPattern:
    row_spacing: float
    in_row_spacing: float
    margin: float
    row_direction: float
    jitter: float
    missing_rate: float


@dataclass(frozen=True)
class Crop:
    name: str
    planting: PlantingPattern
    scale: tuple[float, float]
    yaw: tuple[float, float]
    pull_out_force: tuple[float, float]
    variants: int
    library: str  # Asset Library folder of this Crop's Variants


@dataclass(frozen=True)
class FieldSpec:
    pixel_size: float
    seed: int
    grid: tuple[tuple[str | None, ...], ...]  # Crop name per Pixel, row 0 is north, None is empty
    row_direction: float | None  # Field-wide override of each Crop's default
    sha256: str

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0])


def load_crop(path: Path) -> Crop:
    data = yaml.safe_load(Path(path).read_text())
    variation = data["variation"]
    return Crop(
        name=data["name"],
        planting=PlantingPattern(**data["planting"]),
        scale=tuple(variation["scale"]),
        yaw=tuple(variation["yaw"]),
        pull_out_force=tuple(data["physics"]["pull_out_force"]),
        variants=data["assets"].get("variants", 24),
        library=data["assets"].get("library", f"assets/library/{data['name']}"),
    )


def load_field_spec(path: Path) -> FieldSpec:
    raw = Path(path).read_bytes()
    data = yaml.safe_load(raw)
    if "random" in data:
        raise ValueError("random Field Specs are not supported yet (planned for M2)")
    if "path_gap" in data:
        raise ValueError("path_gap is not supported yet (planned for M2)")

    legend = {str(k): v for k, v in data["legend"].items()}
    grid = []
    for line in data["grid"].splitlines():
        row = []
        for char in line.split():
            if char == EMPTY:
                row.append(None)
            elif char in legend:
                row.append(legend[char])
            else:
                raise ValueError(f"grid character {char!r} is not in the legend")
        if row:
            grid.append(tuple(row))
    if not grid:
        raise ValueError("grid is empty")
    if len({len(row) for row in grid}) != 1:
        raise ValueError("all grid rows must have the same number of Pixels")

    return FieldSpec(
        pixel_size=float(data.get("pixel_size", 0.5)),
        seed=int(data.get("seed", 0)),
        grid=tuple(grid),
        row_direction=data.get("row_direction"),
        sha256=hashlib.sha256(raw).hexdigest(),
    )
