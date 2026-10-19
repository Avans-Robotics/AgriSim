"""Picking a Plant of a built Field and the pull-out system (ADR 0006)."""

import csv
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from pixelfield.cli import main
from pixelfield.core.spec import load_crop
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
    }
    assert load_crop(REPO / "crops" / "lettuce.yaml").pull_out_curve is None  # cut, not pulled


def test_pick_sdf_carries_the_curve(field):
    manifest = json.loads((field / "manifest.json").read_text())
    p = manifest["plants"][0]
    request = plant.pick_sdf(field, p["id"])
    sdf = Path(request["sdf_filename"])
    assert sdf == (field / "picks" / p["id"] / "plant.sdf").resolve()
    model = ET.parse(sdf).getroot().find("model")
    assert model.get("name") == p["id"]
    element = model.find(f"{{{plant.NAMESPACE}}}pull_out")
    assert float(element.get("f_peak")) == p["pull_out_force"]
    assert float(element.get("depth")) == pytest.approx(request["depth"])
    root = model.find("link[@name='root']")
    assert root.findtext("collision/surface/contact/collide_bitmask") == str(plant.ROOT_BITMASK)
    assert request["pose"] == [p["pose"][k] for k in ("x", "y", "z", "yaw")]
    if shutil.which("gz"):
        subprocess.run(["gz", "sdf", "-k", str(sdf)], check=True, capture_output=True)


@pytest.mark.skipif(not SYSTEM.is_file(), reason="pull-out system not built (see CLAUDE.md)")
def test_scripted_pull_follows_the_curve_and_detaches(field):
    manifest = json.loads((field / "manifest.json").read_text())
    p = manifest["plants"][0]
    c = manifest["crops"]["carrot"]["pull_out_curve"]
    r = plant.pull(field, p["id"])
    assert r["requested"] and r["visual_before"] is True and r["visual_after"] is False

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
    assert float(rows[-1]["d"]) == pytest.approx(held, abs=0.0005)  # 1 s after letting go
    assert rows[-1]["attached"] == "True"
