"""Articulated SDF of one picked Plant from its Variant physics export (ADR 0006), a headless
settle check per Variant, the Plant SDFs of a Field written at build time (ADR 0010), and
picking a Plant of a built Field by id (the pull-out system in systems/PullOut.cc does the rest).

The physics export is at scale 1; a Plant of scale s gets lengths times s, masses and joint
stiffnesses times s^3, joint damping times s^4, inertias times s^5 and spring references
times s (gravity torque s^4 over stiffness s^3). The root's collision hull is written as an
OBJ file next to the SDF, petiole links collide as chains of capsules; link visuals are
submeshes of the articulated glb.
"""

import json
import math
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from pixelfield.exporters import gazebo

STEP = 0.001  # seconds per physics step (ADR 0006 stability check)
SETTLE_TIME = 5.0  # seconds of sim time per settle check
SETTLE_AFTER = 2.0  # seconds after which every link must be slower than SETTLE_SPEED
SETTLE_SPEED = 0.001  # meters per second
# The settle check runs in the system Python, which has the Gazebo bindings (python3-gz-sim8);
# the project venv does not.
SYSTEM_PYTHON = "/usr/bin/python3"
SETTLE_SCRIPT = Path(__file__).with_name("settle_check.py")
PULL_SCRIPT = Path(__file__).with_name("pull_check.py")
PULL_SPEED = 0.05  # meters per second, the measurement protocol's suggested pull speed
PULL_AFTER = 0.03  # meters lifted past the root depth before letting go
DROP_TIME = 1.0  # seconds after letting go, so the dropped Plant lands in the log
SYSTEMS_BUILD = Path(__file__).resolve().parents[4] / "build" / "systems"
NAMESPACE = "https://github.com/Avans-Robotics/AgriSim"  # of custom SDF elements
ROOT_BITMASK = 0xFFFF & ~gazebo.SOIL_BITMASK  # the root collides with all but the soil


def plant_model(
    variant: Path,
    scale: float,
    out_dir: Path,
    name: str | None = None,
    write_meshes: bool = True,
    physics: dict | None = None,
) -> ET.Element:
    """Non-static model of one Plant at the origin, root link first.

    `variant` is the library path without extension (assets/library/carrot/carrot_harvest_v00).
    The articulated glb is copied to out_dir/meshes/ and the root hull written to
    out_dir/meshes/<variant name>/root.obj, so the URIs resolve against an SDF in out_dir.
    The meshes are at scale 1, so Plants of one Variant share them: pass write_meshes=False
    once they are written, and the already loaded physics export.
    """
    variant = Path(variant)
    physics = physics or json.loads(variant.with_suffix(".physics.json").read_text())
    meshes = Path(out_dir) / "meshes"
    hulls = meshes / variant.name
    glb = variant.with_suffix(".articulated.glb")
    if write_meshes:
        hulls.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(glb, meshes / glb.name)

    s = scale
    model = ET.Element("model", name=name or variant.name)
    for link in physics["links"]:
        x, y, z, roll, pitch, yaw = link["pose"]
        element = ET.SubElement(model, "link", name=link["name"])
        _text(element, "pose", _join((x * s, y * s, z * s, roll, pitch, yaw)))
        inertial = ET.SubElement(element, "inertial")
        _text(inertial, "pose", _join(tuple(c * s for c in link["com"]) + (0.0, 0.0, 0.0)))
        _text(inertial, "mass", _num(link["mass"] * s**3))
        inertia = ET.SubElement(inertial, "inertia")
        for key, value in link["inertia"].items():
            _text(inertia, key, _num(value * s**5))

        for i, capsule in enumerate(link.get("capsules", [])):
            _capsule(ET.SubElement(element, "collision", name=f"capsule{i}"), capsule, s)
        if "hull" in link:
            obj = hulls / f"{link['name']}.obj"
            if write_meshes:
                _write_obj(obj, link["hull"])
            collision = ET.SubElement(element, "collision", name="collision")
            _mesh(collision, f"meshes/{variant.name}/{obj.name}", s)
        for collision in element.findall("collision") if link["name"] == "root" else []:
            contact = ET.SubElement(ET.SubElement(collision, "surface"), "contact")
            _text(contact, "collide_bitmask", str(ROOT_BITMASK))
        visual = ET.SubElement(element, "visual", name="visual")
        _text(visual, "pose", gazebo._join(gazebo.GLTF_TO_Z_UP))
        mesh = _mesh(visual, f"meshes/{glb.name}", s)
        submesh = ET.SubElement(mesh, "submesh")
        _text(submesh, "name", link["name"])
        _text(submesh, "center", "false")

    for joint in physics["joints"]:
        element = ET.SubElement(model, "joint", name=joint["name"], type=joint["type"])
        _text(element, "parent", joint["parent"])
        _text(element, "child", joint["child"])  # the joint frame is the child link frame
        for tag, axis, k, c, ref in zip(("axis", "axis2"), (joint["axis"], joint["axis2"]),
                                        joint["stiffness"], joint["damping"],
                                        joint["spring_reference"], strict=True):  # fmt: skip
            element_axis = ET.SubElement(element, tag)
            _text(element_axis, "xyz", _join(tuple(axis)))
            dynamics = ET.SubElement(element_axis, "dynamics")
            _text(dynamics, "damping", _num(c * s**4))
            _text(dynamics, "spring_reference", _num(ref * s))
            _text(dynamics, "spring_stiffness", _num(k * s**3))
    return model


def settle_world(variant: Path, out_dir: Path, scale: float = 1.0) -> Path:
    """World with one Plant whose root is welded to the world, on a soil plane, 1 ms step."""
    sdf = ET.Element("sdf", version=gazebo.SDF_VERSION)
    world = ET.SubElement(sdf, "world", name="settle")
    physics = ET.SubElement(world, "physics", name="1ms", type="dart")
    _text(physics, "max_step_size", _num(STEP))
    _text(physics, "real_time_factor", "1")
    for filename, name in gazebo.SYSTEMS.items():
        ET.SubElement(world, "plugin", filename=filename, name=name)
    world.append(gazebo._sun())

    soil = ET.SubElement(world, "model", name="soil")
    _text(soil, "static", "true")
    link = ET.SubElement(soil, "link", name="link")
    for tag in ("collision", "visual"):
        plane = ET.SubElement(ET.SubElement(ET.SubElement(link, tag, name=tag), "geometry"),
                              "plane")  # fmt: skip
        _text(plane, "normal", "0 0 1")
        _text(plane, "size", "1 1")

    model = plant_model(variant, scale, out_dir, name="plant")
    weld = ET.SubElement(model, "joint", name="weld", type="fixed")
    _text(weld, "parent", "world")
    _text(weld, "child", "root")
    world.append(model)

    ET.indent(sdf)
    path = Path(out_dir) / "world.sdf"
    ET.ElementTree(sdf).write(path, encoding="unicode", xml_declaration=True)
    return path


def settle(world_sdf: Path, seconds: float = SETTLE_TIME, after: float = SETTLE_AFTER) -> dict:
    """Run a settle world headless; returns the check's report (see settle_check.py).

    `settled` is true when no link speed or pose is NaN and every link is slower than
    SETTLE_SPEED from `after` seconds on.
    """
    steps = round(seconds / STEP)
    result = subprocess.run(
        [SYSTEM_PYTHON, str(SETTLE_SCRIPT), Path(world_sdf).name, "plant", str(steps),
         str(round(after / STEP))],
        cwd=Path(world_sdf).resolve().parent, capture_output=True, text=True, check=True,
    )  # fmt: skip
    report = json.loads(result.stdout.strip().splitlines()[-1])
    report["settled"] = not report["nan"] and report["max_speed_after"] < SETTLE_SPEED
    return report


def write_plants(manifest: dict, out_dir: Path) -> int:
    """Write the SDF of every root crop Plant to out_dir/plants/<id>.sdf, plus the table
    plants/plants.tsv the pull-out system reads at load; returns the number of Plants written.

    Each model is named by its Plant id, at its pose in the Field, and carries its Pull-out
    Curve as <pixelfield:pull_out>; hull meshes and articulated glb files are shared per
    Variant in plants/meshes/. Table columns: id, x, y, z (the Plant's pose), footprint radius
    (the farthest collision point from the crown axis), footprint height (the top of the
    highest collision above the Plant's z) and crown radius (the root's widest point from its
    axis), all scaled. Plants of Crops without a Pull-out
    Curve (lettuce) or without a Variant physics export get no file.
    """
    plants_dir = Path(out_dir) / "plants"
    shutil.rmtree(plants_dir, ignore_errors=True)  # no stale files from an earlier spec
    plants_dir.mkdir(parents=True)
    variants = {}  # library path: (physics export, footprint radius and height at scale 1)
    rows = ["id\tx\ty\tz\tradius\theight\tcrown"]
    for p in manifest["plants"]:
        crop = manifest["crops"][p["crop"]]
        variant = Path(crop["library"]) / p["variant"]
        if crop["pull_out_curve"] is None or not variant.with_suffix(".physics.json").is_file():
            continue
        first = variant not in variants
        if first:
            physics = json.loads(variant.with_suffix(".physics.json").read_text())
            variants[variant] = physics, _footprint(physics)
        physics, (radius, height, crown) = variants[variant]
        curve, s, pose = crop["pull_out_curve"], p["scale"], p["pose"]
        model = plant_model(variant, s, plants_dir, name=p["id"], write_meshes=first,
                            physics=physics)  # fmt: skip
        ET.SubElement(model, "pose").text = _join((pose["x"], pose["y"], pose["z"], 0.0, 0.0,
                                                   pose["yaw"]))  # fmt: skip
        ET.SubElement(model, "pixelfield:pull_out", f_peak=_num(p["pull_out_force"]),
                      d_peak=_num(curve["d_peak"]),
                      residual_fraction=_num(curve["residual_fraction"]),
                      damping=_num(curve["pull_out_damping"]),
                      depth=_num(physics["root_depth"] * s))  # fmt: skip
        sdf = ET.Element("sdf", {"version": gazebo.SDF_VERSION, "xmlns:pixelfield": NAMESPACE})
        sdf.append(model)
        ET.indent(sdf)
        ET.ElementTree(sdf).write(plants_dir / f"{p['id']}.sdf", encoding="unicode",
                                  xml_declaration=True)  # fmt: skip
        rows.append("\t".join([p["id"], *(_num(v) for v in (pose["x"], pose["y"], pose["z"],
                                                            radius * s, height * s,
                                                            crown * s))]))  # fmt: skip
    (plants_dir / "plants.tsv").write_text("\n".join(rows) + "\n")
    return len(rows) - 1


def _footprint(physics: dict) -> tuple[float, float, float]:
    """Radius about the crown axis, top of the collisions and the root's radius about the crown
    axis, in the model frame at scale 1."""
    cx, cy = next(link["pose"][:2] for link in physics["links"] if link["name"] == "root")
    radius = height = crown = 0.0
    for link in physics["links"]:
        x, y, z, roll, pitch, yaw = link["pose"]
        if link["name"] == "root":
            crown = max(
                math.hypot(*_rotate(v, roll, pitch, yaw)[:2]) for v in link["hull"]["vertices"]
            )
        # A capsule reaches its radius past its cap centres, in every direction.
        points = [(v, 0.0) for v in link.get("hull", {}).get("vertices", [])]
        points += [(v, c["radius"]) for c in link.get("capsules", []) for v in (c["from"], c["to"])]
        for v, r in points:
            dx, dy, dz = _rotate(v, roll, pitch, yaw)
            radius = max(radius, math.hypot(x + dx - cx, y + dy - cy) + r)
            height = max(height, z + dz + r)
    return radius, height, crown


def _rotate(v: list[float], roll: float, pitch: float, yaw: float) -> tuple[float, ...]:
    """v rotated by SDF roll, pitch, yaw (about fixed x, then y, then z)."""
    x, y, z = v
    y, z = y * math.cos(roll) - z * math.sin(roll), y * math.sin(roll) + z * math.cos(roll)
    x, z = x * math.cos(pitch) + z * math.sin(pitch), -x * math.sin(pitch) + z * math.cos(pitch)
    x, y = x * math.cos(yaw) - y * math.sin(yaw), x * math.sin(yaw) + y * math.cos(yaw)
    return x, y, z


def plant_info(world_dir: Path, plant_id: str) -> dict:
    """What the scripted pull and grip need about one root crop Plant of a built Field.

    Returns name, sdf_filename (plants/<plant id>.sdf, written by build), pose (x, y, z, yaw),
    the Plant's Pull-out Force, and its root depth, mass and root hull vertices, all scaled.
    """
    world_dir = Path(world_dir)
    manifest = json.loads((world_dir / "manifest.json").read_text())
    p = next((p for p in manifest["plants"] if p["id"] == plant_id), None)
    if p is None:
        raise ValueError(f"no Plant {plant_id} in {world_dir / 'manifest.json'}")
    sdf = world_dir / "plants" / f"{plant_id}.sdf"
    if not sdf.is_file():
        raise ValueError(f"no {sdf}: {plant_id} is not a root crop Plant, or the world was "
                         "built before pick by id, rebuild it")  # fmt: skip
    crop = manifest["crops"][p["crop"]]
    physics = json.loads((Path(crop["library"]) / p["variant"]).with_suffix(".physics.json")
                         .read_text())  # fmt: skip
    s = p["scale"]
    root = next(link for link in physics["links"] if link["name"] == "root")
    pose = p["pose"]
    return {
        "sdf_filename": str(sdf.resolve()),
        "name": plant_id,
        "pose": [pose["x"], pose["y"], pose["z"], pose["yaw"]],
        "pull_out_force": p["pull_out_force"],
        "depth": physics["root_depth"] * s,
        "mass": sum(link["mass"] for link in physics["links"]) * s**3,
        "root_hull": [[c * s for c in v] for v in root["hull"]["vertices"]],
    }


def pick(world_dir: Path, plant_id: str) -> bool:
    """Pick one Plant in a running Field world by its id; true when the system accepted it."""
    if not (Path(world_dir) / "plants" / f"{plant_id}.sdf").is_file():
        raise ValueError(f"{plant_id} is not a root crop Plant of {world_dir}, or the world was "
                         "built before pick by id, rebuild it")  # fmt: skip
    result = subprocess.run(
        ["gz", "service", "-s", f"/world/{gazebo.WORLD_NAME}/pixelfield/pick",
         "--reqtype", "gz.msgs.StringMsg", "--reptype", "gz.msgs.Boolean",
         "--timeout", "5000", "--req", f"data: {json.dumps(plant_id)}"],
        capture_output=True, text=True,
    )  # fmt: skip
    return "data: true" in result.stdout


def pull(
    world_dir: Path, plant_id: str, speed: float = PULL_SPEED, release: float | None = None
) -> dict:
    """Scripted pull, headless: pick a Plant of a built Field and lift its root at `speed`.

    Lets go at a lift of `release` meters (default PULL_AFTER past the root depth) and logs
    DROP_TIME more, so the Plant drops or, released before the detach, stays. Writes
    the log to picks/<plant id>/pull.csv (time, lift, pull force, bottom: the root's lowest
    point, then d, force, attached from the system's state topic; d is read at the start of
    the step, lift at its end; the state topic is silent while the root rests, so those rows
    have no d). The report adds the request, the state topic's events ([sim time, event]),
    whether the grouped visual was there before and after, the peak pull and soil forces, the
    Plant's weight, d at detach (None if it never detached) and the root's lowest point at the
    end (landed_bottom).
    """
    if speed <= 0:
        raise ValueError("the pull speed must be above 0")
    world_dir = Path(world_dir)
    request = plant_info(world_dir, plant_id)
    release = request["depth"] + PULL_AFTER if release is None else release
    steps = round((release / speed + DROP_TIME) / STEP)
    path = os.pathsep.join(filter(None, [str(SYSTEMS_BUILD),
                                         os.environ.get("GZ_SIM_SYSTEM_PLUGIN_PATH")]))  # fmt: skip
    result = subprocess.run(
        # By absolute path from the caller's cwd: the system finds plants/ from the world file.
        [SYSTEM_PYTHON, str(PULL_SCRIPT), str((world_dir / "world.sdf").resolve()),
         json.dumps(request), str(steps), repr(speed), repr(release)],
        capture_output=True, text=True, check=True,
        # Own partition: Field worlds share a name, so runs would see each other's topics.
        env={**os.environ, "GZ_SIM_SYSTEM_PLUGIN_PATH": path,
             "GZ_PARTITION": f"pixelfield-{os.getpid()}"},
    )  # fmt: skip
    report = json.loads(result.stdout.strip().splitlines()[-1])
    rows = report.pop("rows")
    log = world_dir / "picks" / plant_id / "pull.csv"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("time,lift,pull_force,bottom,d,force,attached\n"
                   + "".join(",".join("" if v is None else repr(v) for v in row) + "\n"
                             for row in rows))  # fmt: skip
    attached = [row for row in rows if row[6]]
    detach = next((row for row in rows if row[6] is False), None)
    return {
        **request,
        **report,
        "peak_pull": max((row[2] for row in attached), default=0.0),
        "peak_force": max((row[5] for row in attached), default=0.0),
        "weight": request["mass"] * 9.8,
        "detach_d": detach[4] if detach else None,
        "landed_bottom": rows[-1][3] if rows else None,
        "log": log,
    }


def _mesh(parent: ET.Element, uri: str, scale: float) -> ET.Element:
    mesh = ET.SubElement(ET.SubElement(parent, "geometry"), "mesh")
    _text(mesh, "uri", uri)  # resolved against the SDF file
    _text(mesh, "scale", _join((scale,) * 3))
    return mesh


def _capsule(collision: ET.Element, capsule: dict, scale: float) -> None:
    """SDF capsule between two cap centres (its axis is the collision frame's z), scaled."""
    a = [c * scale for c in capsule["from"]]
    b = [c * scale for c in capsule["to"]]
    dx, dy, dz = (q - p for p, q in zip(a, b, strict=True))
    centre = tuple((p + q) / 2 for p, q in zip(a, b, strict=True))
    # Pitch tips z towards the axis, then yaw turns it about z.
    _text(collision, "pose", _join(centre + (0.0, math.atan2(math.hypot(dx, dy), dz),
                                             math.atan2(dy, dx))))  # fmt: skip
    shape = ET.SubElement(ET.SubElement(collision, "geometry"), "capsule")
    _text(shape, "radius", _num(capsule["radius"] * scale))
    _text(shape, "length", _num(math.dist(a, b)))


def _write_obj(path: Path, hull: dict) -> None:
    """OBJ of a convex hull. dartsim drops a collision mesh without normals, so each vertex
    gets the direction from the hull's centroid as its normal."""
    vertices = hull["vertices"]
    center = [sum(v[i] for v in vertices) / len(vertices) for i in range(3)]
    lines = [f"v {x!r} {y!r} {z!r}" for x, y, z in vertices]
    for v in vertices:
        d = [a - b for a, b in zip(v, center, strict=True)]
        n = math.hypot(*d) or 1.0
        lines.append("vn " + " ".join(repr(a / n) for a in d))
    lines += [f"f {a + 1}//{a + 1} {b + 1}//{b + 1} {c + 1}//{c + 1}" for a, b, c in hull["faces"]]
    path.write_text("\n".join(lines) + "\n")


def _num(value: float) -> str:
    """Full precision: masses and inertias of petiole links go down to 1e-10."""
    return repr(float(value)) if math.isfinite(value) else str(value)


def _join(values: tuple[float, ...]) -> str:
    return " ".join(_num(v) for v in values)


def _text(parent: ET.Element, tag: str, text: str) -> None:
    ET.SubElement(parent, tag).text = text
