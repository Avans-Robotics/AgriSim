import json
import random
import xml.etree.ElementTree as ET

import pytest

trimesh = pytest.importorskip("trimesh")

from pixelfield.exporters import gazebo  # noqa: E402
from pixelfield.generators import carrot  # noqa: E402


@pytest.fixture(scope="module")
def library(tmp_path_factory):
    out = tmp_path_factory.mktemp("carrot")
    return out, carrot.generate(4, out)


def test_same_index_same_bytes():
    a = carrot.to_glb(carrot.variant(random.Random(3))[0])
    b = carrot.to_glb(carrot.variant(random.Random(3))[0])
    assert a == b


def test_variants_within_ranges_and_budget(library):
    out, paths = library
    sizes = json.loads((out / "variants.json").read_text())
    assert list(sizes) == [p.stem for p in paths] == [f"carrot_v{i:02d}" for i in range(4)]
    for path in paths:
        root = sizes[path.stem]["root"]
        scene = trimesh.load(path)
        assert sum(len(m.faces) for m in scene.geometry.values()) <= carrot.MAX_TRIANGLES
        mesh = scene.geometry["root"]
        assert mesh.is_watertight and mesh.volume > 0  # closed, normals outward
        # y up in the file: the crown top is above the soil, the root hangs down y
        (_, y_min, _), (_, y_max, _) = mesh.bounds
        assert y_max == pytest.approx(root["top"], abs=1e-4)
        assert y_max - y_min == pytest.approx(root["length"], abs=1e-4)
        assert carrot.ROOT_LENGTH[0] <= root["length"] <= carrot.ROOT_LENGTH[1]
        assert carrot.SHOULDER_HEIGHT[0] <= root["top"] <= carrot.SHOULDER_HEIGHT[1]
        assert carrot.SHOULDER_DIAMETER[0] <= 2 * root["radius"] <= carrot.SHOULDER_DIAMETER[1]
        foliage = sizes[path.stem]["foliage"]
        top = max(scene.geometry[part].bounds[1][1] for part in ("petioles", "leaves"))
        assert top == pytest.approx(foliage["height"], abs=1e-4)
        assert 0.8 * carrot.FOLIAGE_HEIGHT[0] <= foliage["height"] <= carrot.FOLIAGE_HEIGHT[1]
        assert scene.geometry["leaves"].face_normals[:, 1].min() >= 0  # blades face up (y)


def test_regenerate_removes_stale_variants(library):
    out, _ = library
    (out / "carrot_v99.glb").write_bytes(b"")
    carrot.generate(4, out)
    assert sorted(p.name for p in out.glob("*.glb")) == [f"carrot_v{i:02d}.glb" for i in range(4)]


def test_preview_has_one_mesh_model_per_variant(library, tmp_path):
    _, paths = library
    world = gazebo.preview(paths, tmp_path)
    uris = [u.text for u in ET.parse(world).iter("uri")]
    assert uris == [str(p.resolve()) for p in paths]
    rolls = [float(v.findtext("pose").split()[3]) for v in ET.parse(world).iter("visual")]
    assert rolls == pytest.approx([1.5708] * len(paths), abs=1e-4)  # y-up glTF stood up
