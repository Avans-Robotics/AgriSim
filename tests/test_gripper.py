"""Test gripper: squeeze check (ADR 0006) and pulling a Plant by its leaf bunch (M4e)."""

import csv
import json
import os
import shutil
import statistics
import subprocess
from pathlib import Path

import pytest
import yaml

from pixelfield.cli import main
from pixelfield.core.spec import load_crop
from pixelfield.exporters.gazebo import gripper, plant

REPO = Path(__file__).resolve().parents[1]
CARROT = REPO / "assets" / "library" / "carrot" / "carrot_harvest_v00"
VARIANTS = sorted(p.with_suffix("").with_suffix("")
                  for crop in ("carrot", "beetroot", "radish")
                  for p in (REPO / "assets" / "library" / crop).glob("*.physics.json"))  # fmt: skip
SYSTEM = plant.SYSTEMS_BUILD / "libPixelfieldPullOut.so"
needs_gz = pytest.mark.skipif(not shutil.which("gz"), reason="Gazebo not installed")
needs_system = pytest.mark.skipif(not SYSTEM.is_file(),
                                  reason="pull-out system not built (see CLAUDE.md)")  # fmt: skip


@pytest.fixture(scope="module")
def sparse_crops(tmp_path_factory):
    """The Crops with one root crop Plant per Pixel, about 0.5 m apart: the Active Region picks
    no neighbour, so a grip pulls only its own Plant."""
    crops = tmp_path_factory.mktemp("sparse") / "crops"
    shutil.copytree(REPO / "crops", crops)
    for name in ("carrot", "beetroot", "radish"):
        path = crops / f"{name}.yaml"
        crop = yaml.safe_load(path.read_text())
        crop["planting"].update(margin=0.2, row_spacing=0.5, in_row_spacing=0.5, missing_rate=0.0)
        path.write_text(yaml.safe_dump(crop))
    return crops


def build(example, out, crops):
    main(["build", str(REPO / "examples" / example), "-o", str(out), "--crops", str(crops)])
    return out


@pytest.fixture(scope="module")
def field(tmp_path_factory, sparse_crops):
    return build("carrot_pixel.yaml", tmp_path_factory.mktemp("field") / "carrot", sparse_crops)


@pytest.fixture(scope="module")
def dense(tmp_path_factory):
    return build("carrot_pixel.yaml", tmp_path_factory.mktemp("dense") / "carrot", REPO / "crops")


@needs_gz
def test_grip_world_is_valid_sdf(tmp_path):
    world = gripper.grip_world(plant.settle_world(CARROT, tmp_path), (0.0, 0.0, 0.04), 20.0)
    result = subprocess.run(["gz", "sdf", "-k", str(world)], capture_output=True, text=True)
    assert result.returncode == 0 and "Valid" in result.stdout, result.stdout + result.stderr


@needs_gz
def test_squeeze_holds_every_leaf(tmp_path):
    report = gripper.squeeze(CARROT, tmp_path)
    assert report["held"], report
    assert report["leaves"] == 8 and report["gap"] < 0.02


@needs_system
def test_a_pull_by_the_tops_detaches_within_the_pull_out_force_range(field):
    p = json.loads((field / "manifest.json").read_text())["plants"][0]
    r = gripper.grip(field, p["id"])
    assert r["requested"] and not r["nan"]
    assert r["detach_d"] == pytest.approx(r["depth"], abs=0.001)
    low, high = load_crop(REPO / "crops" / "carrot.yaml").pull_out_force
    pulled = r["peak_wrist"] - r["weight"]  # what the soil held
    assert low <= pulled <= high * 1.05
    assert pulled == pytest.approx(p["pull_out_force"], rel=0.05)


@needs_system
def test_a_weak_grip_slips(field):
    manifest = json.loads((field / "manifest.json").read_text())
    p = manifest["plants"][0]
    r = gripper.grip(field, p["id"], gripper.WEAK_GRIP)
    assert r["requested"] and r["detach_d"] is None
    assert r["max_d"] < manifest["crops"]["carrot"]["pull_out_curve"]["d_peak"]  # bond holds
    assert r["slip"] > 0.05
    rows = list(csv.DictReader(r["log"].open()))
    sliding = [float(row["wrist_force"]) for row in rows
               if row["wrist_force"] and float(row["lift"]) > 0.02]  # fmt: skip
    expected = 2 * gripper.JAW_MU * gripper.WEAK_GRIP  # friction of both jaws at slip
    assert statistics.median(sliding) == pytest.approx(expected, rel=0.25)


@needs_system
def test_a_grip_in_a_full_pixel_pulls_the_target_past_its_neighbours(dense):
    """The Active Region picks the Plants around the jaws, so their leaves collide instead of
    passing through. Jaws closing across the row, as wide as the target's bunch, pull the
    target out; its neighbours are pushed but keep their soil bond."""
    manifest = json.loads((dense / "manifest.json").read_text())
    p = manifest["plants"][0]
    r = gripper.grip(dense, p["id"])
    neighbours = {name: d for name, d in r["plants"].items() if name != p["id"]}
    assert r["requested"] and not r["nan"] and neighbours
    assert r["detach_d"] == pytest.approx(r["depth"], abs=0.001)
    assert max(neighbours.values()) < manifest["crops"]["carrot"]["pull_out_curve"]["d_peak"]


@needs_system
def test_the_strongest_beetroot_needs_a_stronger_grip(tmp_path, sparse_crops):
    out = build("m3_crops.yaml", tmp_path / "m3_crops", sparse_crops)
    plants = json.loads((out / "manifest.json").read_text())["plants"]
    p = max((p for p in plants if p["crop"] == "beetroot"), key=lambda p: p["pull_out_force"])
    weak = gripper.grip(out, p["id"])
    # The default grip does not get it out: friction holds 40 N; the root slips out of the grip.
    assert weak["requested"] and weak["detach_d"] is None and weak["slip"] > 0.02
    # A grip whose friction holds the Pull-out Force plus the weight, with a 1.5x margin.
    force = 1.5 * (p["pull_out_force"] + weak["weight"]) / (2 * gripper.JAW_MU)
    r = gripper.grip(out, p["id"], force)
    assert r["detach_d"] == pytest.approx(r["depth"], abs=0.001)
    assert r["peak_wrist"] - r["weight"] == pytest.approx(p["pull_out_force"], rel=0.05)


# About 3.5 s per Variant, 4 minutes for all: PIXELFIELD_SLOW=1 uv run pytest -k squeezed
@pytest.mark.skipif(not os.environ.get("PIXELFIELD_SLOW"), reason="slow, set PIXELFIELD_SLOW=1")
@pytest.mark.parametrize("variant", VARIANTS, ids=lambda v: v.name)
def test_variant_is_squeezed(variant, tmp_path):
    report = gripper.squeeze(variant, tmp_path)
    assert report["held"], report
