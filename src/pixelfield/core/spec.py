"""Loading Field Specs and Crop definitions from YAML."""

import hashlib
import random
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
    path_gap: tuple[int, float] | None  # (every_n_cols, width): bare soil between column groups
    sha256: str

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0])

    def column_x(self, col: int) -> float:
        """West edge of a Pixel column; Path Gaps push the columns east of them."""
        gaps = col // self.path_gap[0] if self.path_gap else 0
        return col * self.pixel_size + gaps * (self.path_gap[1] if self.path_gap else 0.0)

    @property
    def width(self) -> float:
        return self.column_x(self.cols - 1) + self.pixel_size

    @property
    def depth(self) -> float:
        return self.rows * self.pixel_size


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
    path_gap = None
    if "path_gap" in data:
        path_gap = int(data["path_gap"]["every_n_cols"]), float(data["path_gap"]["width"])
        if path_gap[0] < 1 or path_gap[1] <= 0:
            raise ValueError("path_gap needs every_n_cols of at least 1 and a width above 0")
    seed = int(data.get("seed", 0))
    if "random" in data and "grid" in data:
        raise ValueError("a Field Spec has either grid or random, not both")
    grid = _random_grid(data["random"], seed) if "random" in data else _drawn_grid(data)

    return FieldSpec(
        pixel_size=float(data.get("pixel_size", 0.5)),
        seed=seed,
        grid=grid,
        row_direction=data.get("row_direction"),
        path_gap=path_gap,
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def _drawn_grid(data: dict) -> tuple[tuple[str | None, ...], ...]:
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
    return tuple(grid)


def _random_grid(request: dict, seed: int) -> tuple[tuple[str | None, ...], ...]:
    """Exactly round(empty_fraction * Pixels) Empty Pixels, the rest drawn by Crop weight.

    With no_same_neighbour, no two Pixels sharing an edge hold the same Crop; this skews the
    weights a little. Its own random stream, so the planting streams do not depend on it.
    """
    rows, cols = int(request["rows"]), int(request["cols"])
    weights = {str(name): float(w) for name, w in (request.get("crops") or {}).items()}
    empty_fraction = float(request.get("empty_fraction", 0.0))
    if rows < 1 or cols < 1:
        raise ValueError("random rows and cols must be at least 1")
    if not weights or min(weights.values()) <= 0:
        raise ValueError("random crops need at least one Crop, every weight above 0")
    if not 0 <= empty_fraction < 1:
        raise ValueError("random empty_fraction must be at least 0 and below 1")

    rng = random.Random(f"{seed}:grid")
    empty = set(rng.sample(range(rows * cols), round(empty_fraction * rows * cols)))
    cells = [divmod(i, cols) for i in range(rows * cols) if i not in empty]
    grid: list[list[str | None]] = [[None] * cols for _ in range(rows)]

    # Fill row by row. options[i] holds the untried Crops of cells[i], in weighted random order;
    # a dead end steps back to the previous cell and tries its next Crop.
    # ponytail: plain backtracking, exponential in the worst case; fine here because only the
    # north and west neighbours are filled when a cell is drawn. Smarter search if that changes.
    options: list[list[str]] = []
    while len(options) < len(cells):
        row, col = cells[len(options)]
        taken = set()
        if request.get("no_same_neighbour"):
            taken = {grid[row - 1][col] if row else None, grid[row][col - 1] if col else None}
        options.append(_weighted_order(rng, {n: w for n, w in weights.items() if n not in taken}))
        while options and not options[-1]:
            options.pop()
        if not options:
            raise ValueError("no grid satisfies no_same_neighbour with these Crops")
        row, col = cells[len(options) - 1]
        grid[row][col] = options[-1].pop(0)
    return tuple(tuple(row) for row in grid)


def _weighted_order(rng: random.Random, weights: dict[str, float]) -> list[str]:
    """All names, ordered by repeated weighted draws without replacement."""
    order, left = [], dict(weights)
    while left:
        name = rng.choices(list(left), list(left.values()))[0]
        order.append(name)
        del left[name]
    return order
