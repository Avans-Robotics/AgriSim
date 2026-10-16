import numpy as np
import pytest

Image = pytest.importorskip("PIL.Image")

from pixelfield.generators import soil  # noqa: E402

TILES = soil.TEXTURES / "soil_tiles"


def _tile(i: int, j: int) -> np.ndarray:
    return np.asarray(Image.open(TILES / f"tile_{i}_{j}_color.jpg"), dtype=float)


def test_neighbouring_atlas_tiles_join_without_seams():
    """In the gz box mapping row 0 is a tile's east edge and column 0 its north edge."""
    n = soil.PERIOD
    for i in range(n):
        for j in range(n):
            tile, east, north = _tile(i, j), _tile((i + 1) % n, j), _tile(i, (j + 1) % n)
            inside = np.abs(tile[0] - tile[1]).mean()  # step between two rows in one tile
            assert np.abs(tile[0] - east[-1]).mean() < 1.5 * inside
            assert np.abs(tile[:, 0] - north[:, -1]).mean() < 1.5 * inside
