import json
import math
from pathlib import Path

import pytest

from pixelfield.cli import main
from pixelfield.core.layout import build_layout, planting_positions, to_manifest
from pixelfield.core.spec import load_crop, load_field_spec

REPO = Path(__file__).resolve().parents[1]
CARROT = load_crop(REPO / "crops" / "carrot.yaml")


def layout_of(tmp_path, grid, extra=""):
    path = tmp_path / "spec.yaml"
    path.write_text(f"seed: 42\nlegend:\n  C: carrot\n{extra}grid: |\n{grid}")
    spec = load_field_spec(path)
    return build_layout(spec, {"carrot": CARROT})


def test_carrot_pixel_has_three_rows_of_eleven():
    positions = planting_positions(CARROT.planting, 0.5, 0.0)
    assert len(positions) == 33
    assert sorted({round(y, 3) for _, y in positions}) == [-0.15, 0.0, 0.15]


def test_same_seed_same_layout(tmp_path):
    assert layout_of(tmp_path, "  C C\n") == layout_of(tmp_path, "  C C\n")


def test_different_seed_different_layout(tmp_path):
    path = tmp_path / "other.yaml"
    path.write_text("seed: 7\nlegend:\n  C: carrot\ngrid: |\n  C\n")
    other = build_layout(load_field_spec(path), {"carrot": CARROT})
    assert layout_of(tmp_path, "  C\n").plants != other.plants


def test_row_zero_is_north(tmp_path):
    layout = layout_of(tmp_path, "  C .\n  . C\n")
    north = [p for p in layout.plants if p.pixel == (0, 0)]
    south = [p for p in layout.plants if p.pixel == (1, 1)]
    assert north and south
    assert all(p.x < 0.5 and p.y > 0.5 for p in north)
    assert all(p.x > 0.5 and p.y < 0.5 for p in south)
    assert layout.pixels[0].origin == (0.0, 0.5)


@pytest.mark.parametrize("direction", ["", "row_direction: 0.7\n"])
def test_plants_stay_inside_the_margin(tmp_path, direction):
    layout = layout_of(tmp_path, "  C C C\n  C C C\n", extra=direction)
    margin = CARROT.planting.margin
    for p in layout.plants:
        row, col = p.pixel
        x0, y0 = col * 0.5, (1 - row) * 0.5
        assert x0 + margin - 1e-9 <= p.x <= x0 + 0.5 - margin + 1e-9
        assert y0 + margin - 1e-9 <= p.y <= y0 + 0.5 - margin + 1e-9


def test_row_direction_rotates_rows(tmp_path):
    positions = planting_positions(CARROT.planting, 0.5, math.pi / 2)
    assert sorted({round(x, 3) for x, _ in positions}) == [-0.15, 0.0, 0.15]


def test_missing_rate_is_roughly_respected(tmp_path):
    layout = layout_of(tmp_path, "  C C C C C C C C C C\n" * 10)
    expected = 100 * len(planting_positions(CARROT.planting, 0.5, 0.0))
    missing = 1 - len(layout.plants) / expected
    assert abs(missing - CARROT.planting.missing_rate) < 0.02


def test_editing_one_pixel_keeps_the_others(tmp_path):
    a = layout_of(tmp_path, "  C C\n")
    b = layout_of(tmp_path, "  C .\n")
    assert [p for p in a.plants if p.pixel == (0, 0)] == list(b.plants)


def test_bad_specs_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="legend"):
        layout_of(tmp_path, "  C X\n")
    with pytest.raises(ValueError, match="same number"):
        layout_of(tmp_path, "  C C\n  C\n")
    with pytest.raises(ValueError, match="M2"):
        layout_of(tmp_path, "  C\n", extra="path_gap: {every_n_cols: 1, width: 0.3}\n")
    with pytest.raises(ValueError, match="not both"):
        layout_of(tmp_path, "  C\n", extra="random: {rows: 1, cols: 1, crops: {carrot: 1}}\n")


def random_spec(tmp_path, request, seed=7):
    path = tmp_path / "random.yaml"
    path.write_text(f"seed: {seed}\nrandom: {request}\n")
    return load_field_spec(path)


def test_random_grid_is_reproducible_with_exact_empty_count(tmp_path):
    request = "{rows: 10, cols: 10, crops: {carrot: 2, lettuce: 1}, empty_fraction: 0.1}"
    grid = random_spec(tmp_path, request).grid
    assert grid == random_spec(tmp_path, request).grid
    assert grid != random_spec(tmp_path, request, seed=8).grid
    cells = [name for row in grid for name in row]
    assert (len(grid), len(grid[0]), cells.count(None)) == (10, 10, 10)
    assert {"carrot", "lettuce"} <= set(cells)


@pytest.mark.parametrize("seed", range(20))
def test_no_same_neighbour_holds(tmp_path, seed):
    request = ("{rows: 8, cols: 8, crops: {carrot: 1, lettuce: 1}, empty_fraction: 0.2, "
               "no_same_neighbour: true}")  # fmt: skip
    grid = random_spec(tmp_path, request, seed).grid
    for r in range(8):
        for c in range(8):
            if grid[r][c]:
                assert grid[r][c] not in (r and grid[r - 1][c], c and grid[r][c - 1])


@pytest.mark.parametrize(
    ("request_", "match"),
    [
        ("{rows: 1, cols: 2, crops: {carrot: 1}, no_same_neighbour: true}", "no grid"),
        ("{rows: 0, cols: 2, crops: {carrot: 1}}", "rows and cols"),
        ("{rows: 1, cols: 2, crops: {carrot: 0}}", "weight"),
        ("{rows: 1, cols: 2, crops: {carrot: 1}, empty_fraction: 1}", "empty_fraction"),
    ],
)
def test_bad_random_requests_are_rejected(tmp_path, request_, match):
    with pytest.raises(ValueError, match=match):
        random_spec(tmp_path, request_)


def test_random_and_drawn_grid_give_the_same_plants(tmp_path):
    spec = random_spec(
        tmp_path, "{rows: 2, cols: 3, crops: {carrot: 1}, empty_fraction: 0.3}", seed=42
    )
    drawn = "\n".join("  " + " ".join("C" if name else "." for name in row) for row in spec.grid)
    layout = build_layout(spec, {"carrot": CARROT})
    assert layout.plants == layout_of(tmp_path, drawn + "\n").plants


def test_build_writes_manifest_and_svg(tmp_path):
    out = tmp_path / "out"
    main(["build", str(REPO / "examples" / "carrot_pixel.yaml"), "-o", str(out),
          "--crops", str(REPO / "crops")])  # fmt: skip
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["field"]["rows"] == manifest["field"]["cols"] == 1
    assert len(manifest["field"]["spec_sha256"]) == 64
    assert manifest["plants"][0]["id"].startswith("r0c0-")
    assert manifest["plants"][0]["variant"].startswith("carrot_v")
    svg = (out / "field.svg").read_text()
    assert svg.count("</circle>") == len(manifest["plants"])  # legend circles self-close
    assert f"carrot ({len(manifest['plants'])})" in svg
    assert "empty Pixel" not in svg
    assert 'id="frame"' in svg
    assert svg.count("V500.0") == 4  # 0.5 m Pixel, 10 cm grid: 4 inner vertical lines


def test_manifest_matches_layout(tmp_path):
    layout = layout_of(tmp_path, "  C .\n")
    manifest = to_manifest(layout)
    assert [p["crop"] for p in manifest["pixels"]] == ["carrot", None]
    assert len(manifest["plants"]) == len(layout.plants)


def test_two_crops_in_one_field():
    spec = load_field_spec(REPO / "examples" / "mixed.yaml")
    lettuce = load_crop(REPO / "crops" / "lettuce.yaml")
    layout = build_layout(spec, {"carrot": CARROT, "lettuce": lettuce})
    assert len(planting_positions(lettuce.planting, 0.5, 0.0)) == 4
    for p in layout.plants:
        assert p.crop == spec.grid[p.pixel[0]][p.pixel[1]]
        assert p.variant.startswith(p.crop + "_v")
    assert {p.pixel for p in layout.plants if p.crop == "lettuce"} == {(0, 1), (1, 0), (1, 2)}
    assert not [p for p in layout.plants if p.pixel == (0, 2)]
