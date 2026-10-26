"""Active Region of the pull-out system (ADR 0010): boxes placed by hand pick Plants."""

import csv
import json
import math
import os
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


def run(field, probes, pick=None, steps=50, moves=(), snapshot=None):
    path = os.pathsep.join(filter(None, [str(plant.SYSTEMS_BUILD),
                                         os.environ.get("GZ_SIM_SYSTEM_PLUGIN_PATH")]))  # fmt: skip
    result = plant.run_check(
        [plant.SYSTEM_PYTHON, str(SCRIPT), str(field / "world.sdf"),
         json.dumps({"probes": probes, "steps": steps, "pick": pick, "moves": list(moves),
                     "snapshot": snapshot})],
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
            "size": [2 * half] * 3, "offsets": [[*offset, 0.0, 0.0, yaw]]}  # fmt: skip


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

    # Two cubes in one link, west and east of the Pixel, like the wheel forks of a robot base
    # straddling a bed: the box of the whole link would hold every Plant at that y, each
    # cube's box holds none.
    west_x = pw["x"] - pw["crown"] - PAD - HALF - 0.01
    east_x = pe["x"] + pe["crown"] + PAD + HALF + 0.01
    mid = (west_x + east_x) / 2
    span = {"name": "span", "pose": [mid, pa["y"], z], "size": [2 * HALF] * 3,
            "offsets": [[west_x - mid, 0, 0, 0, 0, 0], [east_x - mid, 0, 0, 0, 0, 0]]}  # fmt: skip
    probes.append(span)
    assert a in meets(plants, (mid, pa["y"], z), ((east_x - west_x) / 2 + HALF, HALF, HALF))
    expected["span"] = meets(plants, (west_x, pa["y"], z), (HALF,) * 3) | meets(
        plants, (east_x, pa["y"], z), (HALF,) * 3
    )
    assert not expected["span"]

    # A soil-only box (collide bitmask 0x1, like a wheel meant to drive over beds) right over
    # the southmost Plant, which no other box reaches, picks nothing.
    south = min(plants, key=lambda n: plants[n]["y"])
    ps = plants[south]
    assert south not in set().union(*expected.values())
    assert south in meets(plants, (ps["x"], ps["y"], z), (HALF,) * 3)  # if it could touch
    probes.append({**probe("soil_only", ps["x"], ps["y"], z), "bitmask": 1})
    expected["soil_only"] = set()

    r = run(field, probes, pick=a)
    assert set(r["picked"]) == set().union(*expected.values())
    assert a in r["picked"] and west in r["picked"] and east not in r["picked"]
    assert north in r["picked"]
    assert r["requested"] is False  # the region picked it first: a Plant is picked once


@needs_system
def test_field_models_never_pick(field):
    plants = table(field)
    first = next(iter(plants))
    # Soil, Pixel, cameras, then a Picked Plant and its anchor: only the Plant asked for. It
    # rests for 3 s untouched, but a Plant picked by id is never unpicked.
    r = run(field, [], pick=first, steps=round(3.0 / gazebo.PHYSICS_STEP))
    assert r["requested"] is True and r["picked"] == [first]
    assert [event for _, event, _ in r["events"]] == ["picked"]


@needs_system
def test_plants_left_alone_turn_static_and_can_be_picked_again(field):
    plants = table(field)
    west = min(plants, key=lambda n: plants[n]["x"])
    east = max(plants, key=lambda n: plants[n]["x"])
    pw, pe = plants[west], plants[east]
    step = gazebo.PHYSICS_STEP
    away, back, end = round(0.2 / step), round(8.0 / step), round(8.2 / step)
    probes = [probe("leaving", pe["x"], pe["y"], 0.1), probe("staying", pw["x"], pw["y"], 0.1)]
    moves = [
        {"at": away, "probe": "leaving", "to": [-1.0, -1.0, 0.1]},
        {"at": back, "probe": "leaving", "to": [pe["x"], pe["y"], 0.1]},
    ]
    r = run(field, probes, steps=end, moves=moves, snapshot=back - 1)
    near_east = meets(plants, (pe["x"], pe["y"], 0.1), (HALF,) * 3)
    near_west = meets(plants, (pw["x"], pw["y"], 0.1), (HALF,) * 3)
    assert east in near_east and not near_east & near_west  # the two groups are apart
    events = {}
    for plant_id, event, _ in r["events"]:
        events.setdefault(plant_id, []).append(event)
    # The robot left: its Plants came to rest, turned static, and were picked again on return.
    for plant_id in near_east:
        assert events[plant_id] == ["picked", "unpicked", "picked"], plant_id
    # Still under a robot link: never unpicked.
    for plant_id in near_west:
        assert events[plant_id] == ["picked"], plant_id
    assert set(r["picked"]) == near_east | near_west
    assert set(r["visuals_then"]) == set(plants) - near_west  # static again before the return
    assert set(r["visuals"]) == set(plants) - near_east - near_west
    # A rebuilt static visual has a new name, so a gz GUI that missed a removal cannot crash on
    # a duplicate (PullOut.cc, kRepickDelay).
    untouched = set(plants) - near_east - near_west
    assert set(r["visual_names_then"]) == untouched | {f"{i}~1" for i in near_east}
    assert set(r["visual_names"]) == untouched


def test_the_world_sets_the_region_knobs(field):
    element = ET.parse(field / "world.sdf").find(".//plugin[@name='pixelfield::PullOut']")
    assert float(element.findtext("padding")) == PAD
    assert element.findtext("footprint") == "crown"


@needs_system
def test_an_unpicked_plant_waits_a_second_before_it_is_picked_again(field):
    # The gz GUI leaves a ghost of a static visual rebuilt and removed in the same frame, then
    # crashes on the next unpick of that Plant, so a robot returning right away waits.
    plants = table(field)
    east = max(plants, key=lambda n: plants[n]["x"])
    pe = plants[east]
    step = gazebo.PHYSICS_STEP
    probes = [probe("visitor", pe["x"], pe["y"], 0.1)]
    away = [{"at": round(0.2 / step), "probe": "visitor", "to": [-1.0, -1.0, 0.1]}]
    first = run(field, probes, steps=round(8.0 / step), moves=away)
    unpicked = {p: t for p, event, t in first["events"] if event == "unpicked"}
    assert east in unpicked  # the group comes to rest within 8 s, as in the test above
    back = max(unpicked.values()) + 0.1  # inside the cooldown of the last one unpicked
    leave = back + 1.5  # after every re-pick
    moves = [*away, {"at": round(back / step), "probe": "visitor", "to": [pe["x"], pe["y"], 0.1]},
             {"at": round(leave / step), "probe": "visitor", "to": [-1.0, -1.0, 0.1]}]  # fmt: skip
    r = run(field, probes, steps=round((leave + 8.0) / step), moves=moves)
    events = {}
    for plant_id, event, t in r["events"]:
        events.setdefault(plant_id, []).append((event, t))
    assert any(t + plant.REPICK_DELAY > back for t in unpicked.values())  # one still cooling
    for plant_id, t_unpick in unpicked.items():
        assert [e for e, _ in events[plant_id]][:3] == ["picked", "unpicked", "picked"], plant_id
        # Picked again at the first region check (every 10 ms) once both the probe is back and
        # the cooldown is over.
        due = max(t_unpick + plant.REPICK_DELAY, back)
        assert due <= events[plant_id][2][1] < due + 0.05, plant_id
    # Left alone again: each rebuild has a new name, and every Plant has one static visual.
    twice = {i for i, e in events.items() if [event for event, _ in e].count("unpicked") == 2}
    assert east in twice
    names = r["visual_names"]
    assert len(names) == len({n.split("~")[0] for n in names}) == len(plants)
    assert {f"{i}~2" for i in twice} <= set(names)
