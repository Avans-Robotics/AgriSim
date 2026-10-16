import numpy as np
import pytest

Image = pytest.importorskip("PIL.Image")

from pixelfield.exporters import gazebo  # noqa: E402
from pixelfield.generators import soil  # noqa: E402

TILES = soil.TEXTURES / "soil_tiles"


def _lowpass(i: int, j: int) -> np.ndarray:
    """A tile at 32 px per meter: the texture grain averages out, the dry patches stay."""
    image = Image.open(TILES / f"tile_{i}_{j}_color.jpg").resize((32, 32), Image.BOX)
    return np.asarray(image, dtype=float)


def _seams(tile, east, north) -> tuple[float, float]:
    """Edge step to each neighbour over the step one pixel inside, in the same direction.

    In the gz box mapping row 0 is a tile's east edge and column 0 its north edge.
    """
    east_ratio = np.abs(tile[0] - east[-1]).mean() / np.abs(tile[0] - tile[1]).mean()
    north_ratio = np.abs(tile[:, 0] - north[:, -1]).mean() / np.abs(tile[:, 0] - tile[:, 1]).mean()
    return east_ratio, north_ratio


def test_neighbouring_atlas_tiles_join_without_seams():
    n = soil.PERIOD
    tiles = {(i, j): _lowpass(i, j) for i in range(n) for j in range(n)}
    for (i, j), tile in tiles.items():
        east_ratio, north_ratio = _seams(tile, tiles[(i + 1) % n, j], tiles[i, (j + 1) % n])
        assert east_ratio < 2.0 and north_ratio < 2.0, (i, j)


def test_exporter_uses_the_baked_atlas_size():
    assert gazebo.SOIL_ATLAS == soil.PERIOD
    assert len(list(TILES.glob("tile_*_color.jpg"))) == soil.PERIOD**2
