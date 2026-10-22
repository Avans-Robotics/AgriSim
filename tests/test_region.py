"""Active Region of the pull-out system (ADR 0010): boxes placed by hand pick Plants."""

import csv
import json
import math
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from pixelfield.cli import main
from pixelfield.exporters import gazebo
from pixelfield.exporters.gazebo import plant

REPO = Path(__file__).resolve().parents[1]
SYSTEM = plant.SYSTEMS_BUILD / "libPixelfieldPullOut.so"
SCRIPT = Path(__file__).with_name("region_check.py")
PAD = gazebo.ACTIVE_REGION_PADDING
HALF = 0.01  # half the size of a probe box, meters
TURNED = 0.04  # half the size of the probe turned in its link
needs_system = pytest.mark.skipif(not SYSTEM.is_file(),
                                  reason="pull-out system not built (see CLAUDE.md)")  # fmt: skip


@pytest.fixture(scope="module")
def field(tmp_path_factory):
    out = tmp_path_factory.mktemp("field") / "carrot_pixel"
    main(["build", str(REPO / "examples" / "carrot_pixel.yaml"), "-o", str(out),
          "--crops", str(REPO / "crops")])  # fmt: skip
    return out


def table(field):
    rows = csv.DictReader((field / "plants" / "plants.tsv").open(), delimiter="\t")
    return {row["id"]: {k: float(v) for k, v in row.items() if k != "id"} for row in rows}


def run(field, probes, pick=None, steps=50):
    path = os.pathsep.join(filter(None, [str(plant.SYSTEMS_BUILD),
                                         os.environ.get("GZ_SIM_SYSTEM_PLUGIN_PATH")]))  # fmt: skip
    result = subprocess.run(
        [plant.SYSTEM_PYTHON, str(SCRIPT), str(field / "world.sdf"),
         json.dumps({"probes": probes, "steps": steps, "pick": pick})],
        capture_output=True, text=True, check=True,
        env={**os.environ, "GZ_SIM_SYSTEM_PLUGIN_PATH": path,
             "GZ_PARTITION": f"pixelfield-{os.getpid()}"},
    )  # fmt: skip
    return json.loads(result.stdout.strip().splitlines()[-1])


def meets(plants, centre, half):
    """Plants whose crown cylinder meets an axis-aligned box plus the padding."""
    lo = [c - h - PAD for c, h in zip(centre, half, strict=True)]
    hi = [c + h + PAD for c, h in zip(centre, half, strict=True)]
    hits = set()
    for name, p in plants.items():
        dx = max(lo[0] - p["x"], 0, p["x"] - hi[0])
        dy = max(lo[1] - p["y"], 0, p["y"] - hi[1])
        if p["z"] <= hi[2] and p["z"] + p["height"] >= lo[2] and dx**2 + dy**2 <= p["crown"] ** 2:
            hits.add(name)
    return hits


def probe(name, x, y, z, offset=(0.0, 0.0, 0.0), half=HALF, yaw=0.0):
    """A cube of side 2 half centred at (x, y, z), turned by yaw in its link, the link moved
    by -offset."""
    return {"name": name, "pose": [x - offset[0], y - offset[1], z - offset[2]],
            "size": [2 * half] * 3, "offset": [*offset, 0.0, 0.0, yaw]}  # fmt: skip


@needs_system
def test_boxes_pick_the_plants_whose_crown_footprint_they_meet(field):
    plants = table(field)
    cx = sum(p["x"] for p in plants.values()) / len(plants)
    cy = sum(p["y"] for p in plants.values()) / len(plants)
    a = min(plants, key=lambda n: (plants[n]["x"] - cx) ** 2 + (plants[n]["y"] - cy) ** 2)
    west = min(plants, key=lambda n: plants[n]["x"])
    east = max(plants, key=lambda n: plants[n]["x"])
    top = max(p["height"] for p in plants.values())
    z = 0.1  # inside every footprint's height
    pa, pw, pe = plants[a], plants[west], plants[east]
    # Each box: centre and what it should pick.
    boxes = {
        # Over the middle Plant, through a collision offset from its link.
        "inside": ((pa["x"], pa["y"], z), (0.3, 0.0, 0.0)),
        "above": ((pa["x"], pa["y"], top + PAD + HALF + 0.01), (0.0, 0.0, 0.0)),
        # West of the westmost Plant, its padded box 1 mm inside the crown, then 1 mm outside.
        "edge_in": ((pw["x"] - pw["crown"] - PAD - HALF + 0.001, pw["y"], z), (0.0, 0.0, 0.0)),
        "edge_out": ((pe["x"] + pe["crown"] + PAD + HALF + 0.001, pe["y"], z), (0.0, 0.0, 0.0)),
        "outside": ((-1.0, -1.0, z), (0.0, 0.0, 0.0)),
    }
    expected = {name: meets(plants, centre, (HALF,) * 3) for name, (centre, _) in boxes.items()}
    assert a in expected["inside"] and west in expected["edge_in"]
    assert not expected["above"] and not expected["outside"] and east not in expected["edge_out"]
    probes = [probe(name, *centre, offset) for name, (centre, offset) in boxes.items()]
    # A cube turned 45 degrees about z in its link reaches TURNED * sqrt(2) in x and y: from
    # the west, 2 mm into the padded crown of the northmost Plant. gz-sim's own link box gives
    # it no width in x.
    north = max(plants, key=lambda n: plants[n]["y"])
    pn, reach = plants[north], TURNED * 2**0.5
    centre = (pn["x"] - pn["crown"] - PAD - reach + 0.002, pn["y"], z)
    probes.append(probe("turned", *centre, half=TURNED, yaw=math.pi / 4))
    assert north not in set().union(*expected.values())
    expected["turned"] = meets(plants, centre, (reach, reach, TURNED))
    assert north in expected["turned"]

    r = run(field, probes, pick=a)
    assert set(r["picked"]) == set().union(*expected.values())
    assert a in r["picked"] and west in r["picked"] and east not in r["picked"]
    assert north in r["picked"]
    assert r["requested"] is False  # the region picked it first: a Plant is picked once


@needs_system
def test_field_models_never_pick(field):
    plants = table(field)
    first = next(iter(plants))
    # Soil, Pixel, cameras, then a Picked Plant and its anchor: only the Plant asked for.
    r = run(field, [], pick=first, steps=200)
    assert r["requested"] is True and r["picked"] == [first]


def test_the_world_sets_the_region_knobs(field):
    element = ET.parse(field / "world.sdf").find(".//plugin[@name='pixelfield::PullOut']")
    assert float(element.findtext("padding")) == PAD
    assert element.findtext("footprint") == "crown"
