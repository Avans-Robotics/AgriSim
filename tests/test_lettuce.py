import json
import random
from pathlib import Path

import pytest

trimesh = pytest.importorskip("trimesh")

from pixelfield.generators import lettuce, root_crop  # noqa: E402

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


def test_committed_library_matches_generator():
    """Catches a generator change committed without regenerating the Asset Library."""
    committed = REPO / "assets" / "library" / "lettuce" / f"lettuce_{root_crop.STAGE}_v00.glb"
    parts, _ = lettuce.variant(random.Random(0), LETTUCE)
    assert committed.read_bytes() == root_crop.to_glb(parts)
