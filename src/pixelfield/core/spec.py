"""Loading Field Specs and Crop definitions from YAML."""

import dataclasses
import hashlib
import math
import random
from dataclasses import dataclass
from pathlib import Path

import yaml

EMPTY = "."
VENUE_MIN_FLOOR = 0.5  # meters of pavers around the soil, room for the Venue's stone wall


@dataclass(frozen=True)
class PlantingPattern:
    row_spacing: float
    in_row_spacing: float
    margin: float
    row_direction: float
    jitter: float
    missing_rate: float


@dataclass(frozen=True)
class PullOutCurve:
    """Per-Crop knobs of the Pull-out Curve (ADR 0006); the peak is each Plant's Pull-out Force."""

    d_peak: float  # meters of root travel to the peak
    residual_fraction: float  # force right after the peak, fraction of the peak
    pull_out_damping: float  # N s/m


@dataclass(frozen=True)
class Crop:
    name: str
    planting: PlantingPattern
    scale: tuple[float, float]
    yaw: tuple[float, float]
    pull_out_force: tuple[float, float]
    variants: int
    library: str  # Asset Library folder of this Crop's Variants, relative to ROOT or absolute
    stage: str  # growth stage slot in Variant names, e.g. carrot_harvest_v07
    pull_out_curve: PullOutCurve | None = None  # root crops only


@dataclass(frozen=True)
class Venue:
    """Greenhouse around the Field, for looks only: paver floor, glass, frame, low stone wall."""

    size: tuple[float, float]  # meters, x by y; the ridge runs along y
    center: tuple[float, float]  # Field coordinates
    wall: str  # "west" or "east": the long side with the low stone wall

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """(west, south, east, north) in Field coordinates; all paved but the soil."""
        (w, d), (x, y) = self.size, self.center
        return x - w / 2, y - d / 2, x + w / 2, y + d / 2


@dataclass(frozen=True)
class FieldSpec:
    pixel_size: float
    seed: int
    grid: tuple[tuple[str | None, ...], ...]  # Crop name per Pixel, row 0 is north, None is empty
    row_direction: float | None  # Field-wide override of each Crop's default
    path_gap: tuple[int, float] | None  # (every_n_cols, width): bare soil between column groups
    sha256: str
    border: float = 0.5  # meters of textured soil around the Field
    venue: Venue | None = None

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
    def path_gaps(self) -> list[tuple[float, float]]:
        """x range (west, east) of each Path Gap, west to east."""
        if not self.path_gap:
            return []
        n = self.path_gap[0]
        return [(self.column_x(c - 1) + self.pixel_size, self.column_x(c))
                for c in range(n, self.cols, n)]  # fmt: skip

    @property
    def width(self) -> float:
        return self.column_x(self.cols - 1) + self.pixel_size

    @property
    def depth(self) -> float:
        return self.rows * self.pixel_size


def load_crop(path: Path) -> Crop:
    data = yaml.safe_load(Path(path).read_text())
    variation = data["variation"]
    curve = data["physics"].get("pull_out_curve")
    if curve and not (curve["d_peak"] > 0 and 0 <= curve["residual_fraction"] <= 1
                      and curve["pull_out_damping"] >= 0):  # fmt: skip
        raise ValueError("pull_out_curve needs d_peak above 0, residual_fraction in [0, 1] "
                         "and pull_out_damping of at least 0")  # fmt: skip
    return Crop(
        name=data["name"],
        planting=PlantingPattern(**data["planting"]),
        scale=tuple(variation["scale"]),
        yaw=tuple(variation["yaw"]),
        pull_out_force=tuple(data["physics"]["pull_out_force"]),
        variants=data["assets"].get("variants", 24),
        library=data["assets"].get("library", f"assets/library/{data['name']}"),
        stage=data["assets"].get("stage", "harvest"),
        pull_out_curve=PullOutCurve(**curve) if curve else None,
    )


def load_field_spec(path: Path) -> FieldSpec:
    raw = Path(path).read_bytes()
    data = yaml.safe_load(raw)
    path_gap = None
    if "path_gap" in data:
        path_gap = int(data["path_gap"]["every_n_cols"]), float(data["path_gap"]["width"])
        if path_gap[0] < 1 or path_gap[1] <= 0:
            raise ValueError("path_gap needs every_n_cols of at least 1 and a width above 0")
    border = data.get("border", 0.5)
    if type(border) not in (int, float) or not 0 <= border < math.inf:  # bool is no number
        raise ValueError("border needs a number of meters, at least 0")
    seed = int(data.get("seed", 0))
    if "random" in data and "grid" in data:
        raise ValueError("a Field Spec has either grid or random, not both")
    grid = _random_grid(data["random"], seed) if "random" in data else _drawn_grid(data)

    spec = FieldSpec(
        pixel_size=float(data.get("pixel_size", 0.5)),
        seed=seed,
        grid=grid,
        row_direction=data.get("row_direction"),
        path_gap=path_gap,
        sha256=hashlib.sha256(raw).hexdigest(),
        border=float(border),
    )
    if "venue" in data:
        spec = dataclasses.replace(spec, venue=_venue(data["venue"], spec))
    return spec


def _venue(data: dict, spec: FieldSpec) -> Venue:
    message = "venue needs size [x, y] up to 1000 m, optionally center [x, y] and wall west or east"
    try:
        size, center = data["size"], data.get("center", [spec.width / 2, spec.depth / 2])
        wall = data.get("wall", "west")
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError(message) from error
    pairs = (size, center)
    if not all(type(p) is list and len(p) == 2 and all(type(v) in (int, float) for v in p)
               for p in pairs) or wall not in ("west", "east"):  # fmt: skip
        raise ValueError(message)  # bool and str are no numbers
    if not (all(0 < v <= 1000 for v in size) and all(math.isfinite(v) for v in center)):
        raise ValueError(message)
    venue = Venue(size=tuple(map(float, size)), center=tuple(map(float, center)), wall=wall)
    west, south, east, north = venue.bounds
    pad = spec.border + VENUE_MIN_FLOOR
    if not (west <= -pad and south <= -pad and east >= spec.width + pad
            and north >= spec.depth + pad):  # fmt: skip
        raise ValueError(f"venue must hold the Field, its Border and {VENUE_MIN_FLOOR} m of floor")
    return venue


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
