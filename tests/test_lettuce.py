import json
import random
from pathlib import Path

import pytest

trimesh = pytest.importorskip("trimesh")

from pixelfield.generators import lettuce  # noqa: E402

LETTUCE = lettuce.CROPS["lettuce"]
REPO = Path(__file__).resolve().parents[1]


def test_variants_within_ranges_and_budget(tmp_path):
    paths = lettuce.generate("lettuce", 4, tmp_path)
    sizes = json.loads((tmp_path / "variants.json").read_text())
    assert list(sizes) == [p.stem for p in paths] == [f"lettuce_harvest_v{i:02d}" for i in range(4)]
    for path in paths:
        foliage = sizes[path.stem]["foliage"]
        low, high = LETTUCE["head_height"]  # nominal: cupping and frills add a little
        assert 0.8 * low <= foliage["height"] <= 1.15 * high
        assert foliage["radius"] < foliage["height"]  # an upright head, not a flat rosette
        (plant,) = trimesh.load(path).geometry.values()
        assert len(plant.faces) <= lettuce.MAX_TRIANGLES
        assert plant.bounds[1][1] == pytest.approx(foliage["height"], abs=1e-4)  # y up
        assert plant.bounds[0][1] >= 0  # nothing below the soil


def test_committed_library_matches_generator(tmp_path):
    """Catches a generator change committed without regenerating the Asset Library."""
    library = REPO / "assets" / "library" / "lettuce"
    lettuce.generate("lettuce", len(list(library.glob("*.glb"))), tmp_path)
    for path in tmp_path.iterdir():
        assert path.read_bytes() == (library / path.name).read_bytes(), path.name


def test_upright_leaf_is_rejected():
    with pytest.raises(ValueError, match="straight up"):
        lettuce.variant(random.Random(0), LETTUCE | {"inner_tilt": 0.0})
