import json
import random
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

trimesh = pytest.importorskip("trimesh")

from pixelfield.exporters import gazebo  # noqa: E402
from pixelfield.generators import root_crop  # noqa: E402

CARROT = root_crop.CROPS["carrot"]
REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def library(tmp_path_factory):
    out = tmp_path_factory.mktemp("carrot")
    return out, root_crop.generate("carrot", 4, out)


def test_same_index_same_bytes():
    a = root_crop.to_glb(root_crop.variant(random.Random(3), CARROT)[0])
    b = root_crop.to_glb(root_crop.variant(random.Random(3), CARROT)[0])
    assert a == b


@pytest.mark.parametrize("name", list(root_crop.CROPS))
def test_variants_within_ranges_and_budget(name, tmp_path):
    crop, out = root_crop.CROPS[name], tmp_path
    paths = root_crop.generate(name, 4, out)
    sizes = json.loads((out / "variants.json").read_text())
    assert list(sizes) == [p.stem for p in paths] == [f"{name}_harvest_v{i:02d}" for i in range(4)]
    for index, path in enumerate(paths):
        parts, _ = root_crop.variant(random.Random(index), crop)
        root, foliage = sizes[path.stem]["root"], sizes[path.stem]["foliage"]
        mesh = parts["root"]
        assert mesh.is_watertight and mesh.volume > 0  # closed, normals outward
        (_, _, z_min), (_, _, z_max) = mesh.bounds
        assert z_max == pytest.approx(root["top"], abs=1e-4)
        assert z_max - z_min == pytest.approx(root["length"], abs=1e-4)
        assert crop["root_length"][0] <= root["length"] <= crop["root_length"][1]
        assert crop["shoulder_height"][0] <= root["top"] <= crop["shoulder_height"][1]
        assert crop["shoulder_diameter"][0] <= 2 * root["radius"] <= crop["shoulder_diameter"][1]
        top = max(parts[part].bounds[1][2] for part in ("petioles", "leaves"))
        assert top == pytest.approx(foliage["height"], abs=1e-4)
        assert 0.8 * crop["foliage_height"][0] <= foliage["height"] <= crop["foliage_height"][1]
        assert parts["leaves"].face_normals[:, 2].min() >= 0  # blades face up

        # the file holds one mesh with one textured material, y up as glTF requires
        (plant,) = trimesh.load(path).geometry.values()
        assert len(plant.faces) == sum(len(p.faces) for p in parts.values())
        assert len(plant.faces) <= root_crop.MAX_TRIANGLES
        assert plant.bounds[1][1] == pytest.approx(foliage["height"], abs=1e-4)
        assert plant.visual.material.baseColorTexture is not None


def test_regenerate_removes_stale_variants(library):
    out, _ = library
    (out / "carrot_v99.glb").write_bytes(b"")
    root_crop.generate("carrot", 4, out)
    assert sorted(p.name for p in out.glob("*.glb")) == [
        f"carrot_harvest_v{i:02d}.glb" for i in range(4)
    ]


def test_preview_has_one_mesh_model_per_variant(library, tmp_path):
    _, paths = library
    world = gazebo.preview(paths, tmp_path)
    uris = [u.text for u in ET.parse(world).iter("uri")]
    assert uris == [str(p.resolve()) for p in paths]
    rolls = [float(v.findtext("pose").split()[3]) for v in ET.parse(world).iter("visual")]
    assert rolls == pytest.approx([1.5708] * len(paths), abs=1e-4)  # y-up glTF stood up


@pytest.mark.parametrize("name", list(root_crop.CROPS))
def test_committed_library_matches_generator(name, tmp_path):
    """Catches a generator change committed without regenerating the Asset Library."""
    library = REPO / "assets" / "library" / name
    root_crop.generate(name, len(list(library.glob("*.glb"))), tmp_path)
    for path in tmp_path.iterdir():
        assert path.read_bytes() == (library / path.name).read_bytes(), path.name


def test_radish_root_fades_to_a_white_tip(tmp_path):
    (path,) = root_crop.generate("radish", 1, tmp_path)
    (plant,) = trimesh.load(path).geometry.values()
    image = np.asarray(plant.visual.material.baseColorTexture.convert("RGB"))

    def texel(vertex: int) -> np.ndarray:
        u, v = plant.visual.uv[vertex]  # trimesh flips v to the bottom-left origin
        height, width, _ = image.shape
        return image[min(int((1 - v) * height), height - 1), int(u * width)]

    tip, crown = np.argmin(plant.vertices[:, 1]), np.argmax(plant.visual.uv[:, 1])
    assert texel(tip).min() > 180  # near white
    red = texel(crown)
    assert red[0] > 150 and red[1] < 80  # crimson
