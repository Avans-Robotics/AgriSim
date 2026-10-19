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
    assert sorted(p.name for p in out.glob("*.glb")) == sorted(
        f"carrot_harvest_v{i:02d}{kind}.glb" for i in range(4) for kind in ("", ".articulated")
    )


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
    root_crop.generate(name, len(list(library.glob("*_v??.glb"))), tmp_path)
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


# plausibility bounds per Crop, grams: root mass and top mass (leaves and petioles)
MASS = {"carrot": ((50, 250), (5, 80)), "beetroot": ((50, 500), (10, 200)),
        "radish": ((30, 300), (5, 150))}  # fmt: skip


@pytest.mark.parametrize("name", list(root_crop.CROPS))
def test_physics_export(name, tmp_path):
    crop = root_crop.CROPS[name]
    paths = root_crop.generate(name, 3, tmp_path)
    sizes = json.loads((tmp_path / "variants.json").read_text())
    for path in paths:
        model = json.loads(path.with_suffix(".physics.json").read_text())
        links = {link["name"]: link for link in model["links"]}
        leaves = (len(links) - 1) // root_crop.PETIOLE_LINKS
        assert len(links) == 1 + leaves * root_crop.PETIOLE_LINKS
        assert crop["leaf_count"][0] <= leaves <= crop["leaf_count"][1]
        root = sizes[path.stem]["root"]
        assert model["root_depth"] == pytest.approx(root["length"] - root["top"], abs=1e-5)

        # a tree hanging from the root, one universal joint per petiole link
        assert sorted(j["child"] for j in model["joints"]) == sorted(set(links) - {"root"})
        assert all(j["parent"] in links and j["type"] == "universal" for j in model["joints"])
        assert all(min(j["stiffness"] + j["damping"]) > 0 for j in model["joints"])

        for link in links.values():
            i = link["inertia"]
            ixx, iyy, izz = i["ixx"], i["iyy"], i["izz"]
            tensor = np.array([[ixx, i["ixy"], i["ixz"]], [i["ixy"], iyy, i["iyz"]],
                               [i["ixz"], i["iyz"], izz]])  # fmt: skip
            assert link["mass"] > 0 and np.linalg.eigvalsh(tensor).min() > 0
            assert ixx + iyy >= izz and iyy + izz >= ixx and izz + ixx >= iyy
            _assert_convex(np.array(link["hull"]["vertices"]), np.array(link["hull"]["faces"]))

        grams = 1000 * np.array([links["root"]["mass"], sum(lk["mass"] for lk in links.values())])
        (root_low, root_high), (top_low, top_high) = MASS[name]
        assert root_low <= grams[0] <= root_high
        assert top_low <= grams[1] - grams[0] <= top_high

        # one mesh per link, named like it, in the link frame (root hull hugs the root mesh)
        scene = trimesh.load(path.with_suffix(".articulated.glb"))
        assert sorted(scene.geometry) == sorted(links)
        visual = (
            scene.geometry["root"].copy().apply_transform(np.linalg.inv(root_crop.Z_UP_TO_Y_UP))
        )
        hull = np.array(links["root"]["hull"]["vertices"])
        assert np.abs(visual.bounds - [hull.min(0), hull.max(0)]).max() < 0.003


def _assert_convex(vertices: np.ndarray, faces: np.ndarray) -> None:
    """Every vertex lies on or behind every face plane, and the hull encloses a volume."""
    a, b, c = (vertices[faces[:, k]] for k in range(3))
    normals = np.cross(b - a, c - a)
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    behind = np.einsum("fk,vk->fv", normals, vertices) - np.einsum("fk,fk->f", normals, a)[:, None]
    assert behind.max() < 1e-5
    assert trimesh.Trimesh(vertices, faces).volume > 0


def test_lettuce_has_no_physics_export(tmp_path):
    from pixelfield.generators import lettuce

    lettuce.generate("lettuce", 1, tmp_path)
    assert not list(tmp_path.glob("*.physics.json"))
