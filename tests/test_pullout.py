"""Picking a Plant of a built Field and the pull-out system (ADR 0006)."""

import csv
import json
import shutil
import statistics
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import trimesh

from pixelfield.cli import main
from pixelfield.core.spec import load_crop
from pixelfield.exporters import gazebo
from pixelfield.exporters.gazebo import plant

REPO = Path(__file__).resolve().parents[1]
SYSTEM = plant.SYSTEMS_BUILD / "libPixelfieldPullOut.so"


@pytest.fixture(scope="module")
def field(tmp_path_factory):
    out = tmp_path_factory.mktemp("field") / "carrot_pixel"
    main(["build", str(REPO / "examples" / "carrot_pixel.yaml"), "-o", str(out),
          "--crops", str(REPO / "crops")])  # fmt: skip
    return out


def curve(force, d_peak, residual_fraction, depth, d, broken):
    """Pull-out Curve of ADR 0006, without damping."""
    if broken:
        return residual_fraction * force * (depth - max(d, d_peak)) / (depth - d_peak)
    return force * max(d, 0.0) / d_peak


def test_manifest_has_the_pull_out_curve(field):
    manifest = json.loads((field / "manifest.json").read_text())
    assert manifest["crops"]["carrot"] == {
        "library": "assets/library/carrot",
        "pull_out_curve": {"d_peak": 0.005, "residual_fraction": 0.3, "pull_out_damping": 0.0},
        "row_direction": 0.0,
    }
    assert load_crop(REPO / "crops" / "lettuce.yaml").pull_out_curve is None  # cut, not pulled


def test_build_writes_the_sdf_of_every_root_crop_plant(field):
    manifest = json.loads((field / "manifest.json").read_text())
    plants = manifest["plants"]
    assert sorted(f.stem for f in (field / "plants").glob("*.sdf")) == sorted(
        p["id"] for p in plants
    )
    for p in plants:
        request = plant.plant_info(field, p["id"])
        sdf = Path(request["sdf_filename"])
        assert sdf == (field / "plants" / f"{p['id']}.sdf").resolve()
        model = ET.parse(sdf).getroot().find("model")
        assert model.get("name") == p["id"]
        pose = [float(v) for v in model.findtext("pose").split()]
        assert pose == [p["pose"][k] for k in ("x", "y", "z")] + [0.0, 0.0, p["pose"]["yaw"]]
        element = model.find(f"{{{plant.NAMESPACE}}}pull_out")
        assert float(element.get("f_peak")) == p["pull_out_force"]
        assert float(element.get("depth")) == pytest.approx(request["depth"])
        root = model.find("link[@name='root']")
        assert root.findtext("collision/surface/contact/collide_bitmask") == str(plant.ROOT_BITMASK)
        # Leaves touch the soil through bit 1; no Plant collision has the soil-only bit 0.
        leaves = [c for link in model.iter("link") if link.get("name") != "root"
                  for c in link.iter("collision")]  # fmt: skip
        assert leaves and all(c.findtext("surface/contact/collide_bitmask")
                              == str(gazebo.PLANT_BITMASK) for c in leaves)  # fmt: skip
        assert gazebo.PLANT_BITMASK & gazebo.SOIL_BITMASK and not plant.ROOT_BITMASK & 0x3
        assert not gazebo.PLANT_BITMASK & 0x1 and not plant.ROOT_BITMASK & 0x1
        # The root hull and the articulated glb are shared per Variant, scaled by the model.
        uri = root.findtext("collision/geometry/mesh/uri")
        assert uri == f"meshes/{p['variant']}/root.obj" and (field / "plants" / uri).is_file()
        assert root.findtext("collision/geometry/mesh/scale") == " ".join([repr(p["scale"])] * 3)
    variants = {p["variant"] for p in plants}
    assert {d.name for d in (field / "plants" / "meshes").iterdir() if d.is_dir()} == variants
    if shutil.which("gz"):
        subprocess.run(["gz", "sdf", "-k", str(sdf)], check=True, capture_output=True)


def test_plant_table_has_position_and_footprint(field):
    plants = json.loads((field / "manifest.json").read_text())["plants"]
    rows = list(csv.DictReader((field / "plants" / "plants.tsv").open(), delimiter="\t"))
    assert [row["id"] for row in rows] == [p["id"] for p in plants]
    for p, row in zip(plants, rows, strict=True):
        assert [float(row[k]) for k in "xyz"] == [p["pose"][k] for k in "xyz"]
        # Independent footprint: every root hull vertex and capsule cap centre (plus the
        # capsule radius) in the model frame through trimesh's Euler angles (static x, y, z:
        # SDF's roll, pitch, yaw).
        physics = json.loads((REPO / "assets" / "library" / "carrot" / p["variant"])
                             .with_suffix(".physics.json").read_text())  # fmt: skip
        points = []  # (x, y, z, how far the collision reaches past the point)
        for link in physics["links"]:
            matrix = trimesh.transformations.euler_matrix(*link["pose"][3:], "sxyz")
            matrix[:3, 3] = link["pose"][:3]
            shapes = [(link["hull"]["vertices"], 0)] if "hull" in link else []
            shapes += [([c["from"], c["to"]], c["radius"]) for c in link.get("capsules", [])]
            for local, r in shapes:
                points += [(*v, r) for v in trimesh.transform_points(local, matrix).tolist()]
        radius = max((x * x + y * y) ** 0.5 + r for x, y, _, r in points) * p["scale"]
        height = max(z + r for _, _, z, r in points) * p["scale"]
        assert float(row["radius"]) == pytest.approx(radius, rel=1e-9)
        assert float(row["height"]) == pytest.approx(height, rel=1e-9)
        assert 0.05 < radius < 0.3 and 0.1 < height < 0.5  # a carrot's foliage
        root = next(link for link in physics["links"] if link["name"] == "root")
        crown = max((x * x + y * y) ** 0.5 for x, y, _ in root["hull"]["vertices"]) * p["scale"]
        assert float(row["crown"]) == pytest.approx(crown, rel=1e-9)
        assert 0.005 < crown < 0.05  # a carrot's shoulder


def test_lettuce_gets_no_plant_sdf(tmp_path):
    out = tmp_path / "m3_crops"
    main(["build", str(REPO / "examples" / "m3_crops.yaml"), "-o", str(out),
          "--crops", str(REPO / "crops")])  # fmt: skip
    plants = json.loads((out / "manifest.json").read_text())["plants"]
    root_crops = {p["id"] for p in plants if p["crop"] != "lettuce"}
    assert root_crops and len(root_crops) < len(plants)
    assert {f.stem for f in (out / "plants").glob("*.sdf")} == root_crops
    rows = list(csv.DictReader((out / "plants" / "plants.tsv").open(), delimiter="\t"))
    assert {row["id"] for row in rows} == root_crops
    lettuce = next(p["id"] for p in plants if p["crop"] == "lettuce")
    with pytest.raises(ValueError, match="not a root crop Plant"):
        plant.plant_info(out, lettuce)


@pytest.mark.skipif(not SYSTEM.is_file(), reason="pull-out system not built (see CLAUDE.md)")
def test_scripted_pull_follows_the_curve_and_detaches(field):
    manifest = json.loads((field / "manifest.json").read_text())
    p = manifest["plants"][0]
    c = manifest["crops"]["carrot"]["pull_out_curve"]
    r = plant.pull(field, p["id"])
    assert r["requested"] and r["visual_before"] is True and r["visual_after"] is False
    assert [event for _, event in r["events"]] == ["picked", "peak_passed", "detached"]

    rows = list(csv.DictReader(r["log"].open()))
    attached = [row for row in rows if row["attached"] == "True"]
    assert all(row["d"] for row in rows[1 : len(attached) + 2])  # every step up to the detach
    broken = False
    for row in attached:
        d = float(row["d"])
        broken = broken or d >= c["d_peak"]
        expected = curve(p["pull_out_force"], c["d_peak"], c["residual_fraction"], r["depth"], d,
                         broken)  # fmt: skip
        assert float(row["force"]) == pytest.approx(expected, abs=0.01)

    assert r["detach_d"] == pytest.approx(r["depth"], abs=0.001)
    assert r["peak_force"] == pytest.approx(p["pull_out_force"], rel=0.02)
    low, high = load_crop(REPO / "crops" / "carrot.yaml").pull_out_force
    assert low <= r["peak_pull"] - r["weight"] <= high * 1.05  # what the gripper feels
    assert max(float(row["lift"]) for row in rows) > r["depth"] + 0.02  # free after the detach
    assert r["landed_bottom"] > -0.003  # dropped, it lands on the soil instead of sinking in


@pytest.mark.skipif(not SYSTEM.is_file(), reason="pull-out system not built (see CLAUDE.md)")
def test_a_part_pulled_root_stays_where_it_is_released(field):
    plant_id = json.loads((field / "manifest.json").read_text())["plants"][1]["id"]
    r = plant.pull(field, plant_id, release=0.05)  # past the peak, well before the root depth
    assert r["requested"] and r["detach_d"] is None
    rows = [row for row in csv.DictReader(r["log"].open()) if row["d"]]
    held = max(float(row["d"]) for row in rows)
    assert held > 0.04
    # The topic goes silent once the root rests, so a root sinking after the release would show.
    assert float(rows[-1]["d"]) == pytest.approx(held, abs=0.0005)
    assert rows[-1]["attached"] == "True"


@pytest.mark.skipif(not SYSTEM.is_file(), reason="pull-out system not built (see CLAUDE.md)")
def test_a_fast_pull_detaches_without_aborting_the_physics(field):
    # At 20 m/s the root passes the end of its slide in one step; a ratchet limit set there
    # used to put the lower limit above the upper one, which aborts dartsim.
    plant_id = json.loads((field / "manifest.json").read_text())["plants"][3]["id"]
    r = plant.pull(field, plant_id, speed=20.0)
    assert r["detach_d"] is not None and r["detach_d"] >= r["depth"]
    assert [event for _, event in r["events"]] == ["picked", "peak_passed", "detached"]


@pytest.mark.skipif(not SYSTEM.is_file(), reason="pull-out system not built (see CLAUDE.md)")
def test_a_resting_picked_plant_is_silent(field):
    plant_id = json.loads((field / "manifest.json").read_text())["plants"][2]["id"]
    r = plant.pull(field, plant_id, release=0.0)  # picked, never lifted, 1 s
    assert r["requested"]
    states = [row for row in csv.DictReader(r["log"].open()) if row["d"]]
    assert len(states) == 1 and r["events"] == [[pytest.approx(r["events"][0][0]), "picked"]]
    assert len(list(csv.DictReader(r["log"].open()))) > 900


@pytest.mark.skipif(not SYSTEM.is_file(), reason="pull-out system not built (see CLAUDE.md)")
def test_pull_out_damping_adds_c_times_v(tmp_path):
    damping = 50.0  # N s/m: 2.5 N at the 5 cm/s pull
    crops = tmp_path / "crops"
    shutil.copytree(REPO / "crops", crops)
    yaml = crops / "carrot.yaml"
    yaml.write_text(
        yaml.read_text().replace("pull_out_damping: 0.0", f"pull_out_damping: {damping}")
    )
    out = tmp_path / "carrot_pixel"
    main(["build", str(REPO / "examples" / "carrot_pixel.yaml"), "-o", str(out), "--crops",
          str(crops)])  # fmt: skip
    manifest = json.loads((out / "manifest.json").read_text())
    p = manifest["plants"][0]
    c = manifest["crops"]["carrot"]["pull_out_curve"]
    assert c["pull_out_damping"] == damping
    r = plant.pull(out, p["id"])
    assert r["detach_d"] == pytest.approx(r["depth"], abs=0.001)

    rows = [row for row in csv.DictReader(r["log"].open()) if row["attached"] == "True"]
    broken, damped = False, []
    for previous, row in zip(rows, rows[1:], strict=False):
        d = float(row["d"])
        broken = broken or d >= c["d_peak"]
        # The system reads d and v at the start of a step; dartsim moves d by v times the step.
        v = (d - float(previous["d"])) / plant.PULL_STEP
        law = curve(p["pull_out_force"], c["d_peak"], c["residual_fraction"], r["depth"], d,
                    broken)  # fmt: skip
        assert float(row["force"]) - law == pytest.approx(damping * v, abs=0.01)
        damped.append(float(row["force"]) - law)
    # At the pull speed for most of the pull; the root jumps up when the force drops at the peak.
    assert statistics.median(damped) == pytest.approx(damping * plant.PULL_SPEED, rel=0.05)
