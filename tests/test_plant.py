"""Articulated SDF of one Plant from the Variant physics export (ADR 0006)."""

import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from pixelfield.exporters.gazebo import plant

REPO = Path(__file__).resolve().parents[1]
CARROT = REPO / "assets" / "library" / "carrot" / "carrot_harvest_v00"
ROOT_CROPS = ("carrot", "beetroot", "radish")
VARIANTS = sorted(p.with_suffix("").with_suffix("")
                  for crop in ROOT_CROPS
                  for p in (REPO / "assets" / "library" / crop).glob("*.physics.json"))  # fmt: skip


def _floats(element, tag):
    return [float(v) for v in element.findtext(tag).split()]


def test_plant_model_scales_the_physics_export(tmp_path):
    physics = json.loads(CARROT.with_suffix(".physics.json").read_text())
    s = 1.1
    model = plant.plant_model(CARROT, s, tmp_path)
    links = {link.get("name"): link for link in model.iter("link")}
    assert list(links) == [link["name"] for link in physics["links"]]
    for expected in physics["links"]:
        link = links[expected["name"]]
        assert _floats(link, "pose") == pytest.approx(
            [v * s for v in expected["pose"][:3]] + expected["pose"][3:]
        )
        inertial = link.find("inertial")
        assert float(inertial.findtext("mass")) == pytest.approx(expected["mass"] * s**3)
        assert _floats(inertial, "pose")[:3] == pytest.approx([c * s for c in expected["com"]])
        for key, value in expected["inertia"].items():
            assert float(inertial.find("inertia").findtext(key)) == pytest.approx(value * s**5)
        obj = tmp_path / link.find("collision").find("geometry").find("mesh").findtext("uri")
        lines = obj.read_text().splitlines()
        assert sum(line.startswith("v ") for line in lines) == len(expected["hull"]["vertices"])
        assert sum(line.startswith("vn ") for line in lines) == len(expected["hull"]["vertices"])
        assert sum(line.startswith("f ") for line in lines) == len(expected["hull"]["faces"])
        submesh = link.find("visual").find("geometry").find("mesh").find("submesh")
        assert submesh.findtext("name") == expected["name"]
    joints = {joint.get("name"): joint for joint in model.iter("joint")}
    for expected in physics["joints"]:
        joint = joints[expected["name"]]
        assert joint.get("type") == "universal"
        assert joint.findtext("parent") == expected["parent"]
        assert joint.findtext("child") == expected["child"]
        for i, tag in enumerate(("axis", "axis2")):
            dynamics = joint.find(tag).find("dynamics")
            assert float(dynamics.findtext("spring_stiffness")) == pytest.approx(
                expected["stiffness"][i] * s**3
            )
            assert float(dynamics.findtext("damping")) == pytest.approx(
                expected["damping"][i] * s**4
            )
    assert (tmp_path / "meshes" / "carrot_harvest_v00.articulated.glb").is_file()


@pytest.mark.skipif(shutil.which("gz") is None, reason="Gazebo not installed")
def test_settle_world_is_valid_sdf(tmp_path):
    world = plant.settle_world(CARROT, tmp_path)
    weld = [j for j in ET.parse(world).iter("joint") if j.get("name") == "weld"]
    assert [(j.findtext("parent"), j.findtext("child")) for j in weld] == [("world", "root")]
    result = subprocess.run(["gz", "sdf", "-k", str(world)], capture_output=True, text=True)
    assert result.returncode == 0 and "Valid" in result.stdout, result.stdout + result.stderr


# About 4 s per Variant, 5 minutes for all of them: PIXELFIELD_SLOW=1 uv run pytest -k settles
@pytest.mark.skipif(not os.environ.get("PIXELFIELD_SLOW"), reason="slow, set PIXELFIELD_SLOW=1")
@pytest.mark.parametrize("variant", VARIANTS, ids=lambda v: v.name)
def test_variant_settles(variant, tmp_path):
    report = plant.settle(plant.settle_world(variant, tmp_path))
    assert report["settled"], report
