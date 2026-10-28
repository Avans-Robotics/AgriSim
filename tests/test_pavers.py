import numpy as np
import pytest

Image = pytest.importorskip("PIL.Image")

from pixelfield.exporters.gazebo import venue  # noqa: E402
from pixelfield.generators import pavers  # noqa: E402


def test_exporter_maps_the_baked_pavers():
    assert (venue.PAVER, venue.PAVER_PERIOD) == (pavers.PAVER, pavers.PERIOD)
    assert venue.PAVER_TEXTURE == pavers.OUT_DIR / "color.jpg"


def test_committed_texture_matches_its_generator_with_joints_on_the_edges(tmp_path):
    fresh = np.asarray(Image.open(pavers.generate(tmp_path)), dtype=float)
    committed = np.asarray(Image.open(venue.PAVER_TEXTURE), dtype=float)
    assert np.abs(fresh - committed).mean() < 1.0  # jpeg may differ by a level here and there
    gray = committed.mean(axis=2)
    step = pavers.SIZE // pavers.PERIOD
    for line in (gray[0], gray[-1], gray[:, 0], gray[:, step], gray[:, -step - 1]):
        assert line.mean() < 0.7 * gray.mean()  # a joint, so the texture tiles without seams
