"""Test gripper for pulling a root crop Plant by its leaf bunch (ADR 0006, M4e).

A non-static model `gripper`: a carriage on a vertical prismatic `lift` joint to the world, a
palm fixed to it through a wrist force-torque sensor, and two box jaws on prismatic joints
that close along world x, centred GRIP_HEIGHT above the crown. Lift and jaws are driven per
step by grip_check.py through joint velocity commands, which dartsim runs as servos limited by
the joint's effort limit: the jaws close at CLOSE_SPEED and, once they touch the leaf bunch,
squeeze it with exactly their effort limit, the grip force. The wrist force is the sensor's
vertical force, tared before the jaws close.

The gripper only goes into a headless copy of a world for a test; Field worlds never have it.
"""

import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from pixelfield.exporters.gazebo import plant

GRIP_HEIGHT = 0.03  # meters above the crown, the ADR 0006 squeeze check
JAW_SIZE = (0.01, 0.10, 0.02)  # meters: thickness (along x), width, height
JAW_OPEN = 0.06  # meters from the centre to each open jaw face; leaf bunches reach 3.3 cm
JAW_MASS = 0.1  # kg per jaw
PALM_MASS = 0.3  # kg, below the wrist sensor
CARRIAGE_MASS = 0.5  # kg, above it
JAW_MU = 1.0  # friction of the jaw pads on petioles, guess
# N per jaw: friction holds 2 * JAW_MU * 20 = 40 N, above any carrot (26 N), below the about
# 43 N that damages a carrot.
GRIP_FORCE = 20.0
WEAK_GRIP = 5.0  # N per jaw: friction holds about 10 N, below the weakest carrot (15 N)
CLOSE_SPEED = 0.05  # meters per second per jaw
LIFT_ACCEL = 0.5  # m/s^2, ramps the lift speed up and down: gripper inertia below 0.5 N
LIFT_EFFORT = 1000.0  # N, effort limit of the lift: a stiff arm
GUI_WAIT = 8.0  # seconds a --gui grip holds its jaws open while the GUI loads the scene
GUI_LINGER = 30.0  # seconds a --gui grip keeps the world running after the pull
WRIST_TOPIC = "/pixelfield/gripper/wrist"  # gz.msgs.Wrench of the wrist sensor
SETTLE = 0.1  # seconds before the jaws start closing
HOLD = 0.3  # seconds after the time a full close takes before the lift starts
SQUEEZE_TIME = 1.0  # seconds the squeeze check holds the bunch
GRIP_SCRIPT = Path(__file__).with_name("grip_check.py")


def gripper_model(x: float, y: float, z: float, grip_force: float) -> ET.Element:
    """Gripper with its jaw centre at (x, y, z) and open jaws."""
    model = ET.Element("model", name="gripper")
    _text(model, "pose", plant._join((x, y, z, 0.0, 0.0, 0.0)))
    # The arm: a carriage on the lift. The wrist sensor sits on the fixed joint to the palm
    # (gz's ForceTorque sensor needs a parent link, so it cannot sit on the lift joint).
    for name, mass in (("carriage", CARRIAGE_MASS), ("palm", PALM_MASS)):
        _inertial(ET.SubElement(model, "link", name=name), mass, 1e-3)
    _prismatic(model, "lift", "world", "carriage", (0.0, 0.0, 1.0), -1.0, 1.0, LIFT_EFFORT)
    wrist = ET.SubElement(model, "joint", name="wrist", type="fixed")
    _text(wrist, "parent", "carriage")
    _text(wrist, "child", "palm")
    # The force of the carriage on the palm, so a pull on the Plant reads positive.
    sensor = ET.SubElement(wrist, "sensor", name="wrist", type="force_torque")
    _text(sensor, "always_on", "true")
    _text(sensor, "update_rate", plant._num(1 / plant.STEP))
    _text(sensor, "topic", WRIST_TOPIC)
    force_torque = ET.SubElement(sensor, "force_torque")
    _text(force_torque, "frame", "child")
    _text(force_torque, "measure_direction", "parent_to_child")
    ET.SubElement(model, "plugin", filename="gz-sim-forcetorque-system",
                  name="gz::sim::systems::ForceTorque")  # fmt: skip

    thickness, width, height = JAW_SIZE
    for side, sign in (("left", -1.0), ("right", 1.0)):
        jaw = ET.SubElement(model, "link", name=f"jaw_{side}")
        _text(
            jaw, "pose", plant._join((sign * (JAW_OPEN + thickness / 2), 0.0, 0.0, 0.0, 0.0, 0.0))
        )
        _inertial(jaw, JAW_MASS, 1e-4)
        for tag in ("collision", "visual"):
            element = ET.SubElement(jaw, tag, name=tag)
            box = ET.SubElement(ET.SubElement(element, "geometry"), "box")
            _text(box, "size", plant._join(JAW_SIZE))
        friction = ET.SubElement(ET.SubElement(jaw.find("collision"), "surface"), "friction")
        ode = ET.SubElement(friction, "ode")
        _text(ode, "mu", plant._num(JAW_MU))
        _text(ode, "mu2", plant._num(JAW_MU))
        # Position 0 is open, JAW_OPEN closed with the faces at the centre.
        _prismatic(model, f"jaw_{side}_joint", "palm", f"jaw_{side}", (-sign, 0.0, 0.0), 0.0,
                   JAW_OPEN, grip_force)  # fmt: skip
    return model


def grip_world(
    world_sdf: Path, grip: tuple[float, float, float], grip_force: float, realtime: bool = False
) -> Path:
    """Headless copy of a world with the gripper, next to it so mesh URIs still resolve.

    Without the Sensors system, like the scripted pull, and unthrottled (real_time_factor 0)
    unless `realtime`, for watching it in a GUI.
    """
    world_sdf = Path(world_sdf)
    text = world_sdf.read_text()
    if not realtime:
        text = re.sub(r"<real_time_factor>[^<]*<", "<real_time_factor>0<", text)
    text = re.sub(r'<plugin filename="gz-sim-sensors-system".*?</plugin>', "", text, flags=re.S)
    model = ET.tostring(gripper_model(*grip, grip_force), encoding="unicode")
    path = world_sdf.with_name(".grip_fast.sdf")
    path.write_text(text.replace("</world>", model + "</world>", 1))
    return path


def grip(
    world_dir: Path,
    plant_id: str,
    grip_force: float = GRIP_FORCE,
    speed: float = plant.PULL_SPEED,
    lift: float | None = None,
    gui: bool = False,
) -> dict:
    """Pull a Plant of a built Field by its leaf bunch, headless, or in real time with a
    `gz sim -g` GUI attached when `gui` (it waits GUI_WAIT for the GUI, keeps the world running
    GUI_LINGER after the pull, then closes the GUI).

    Picks the Plant, closes the jaws GRIP_HEIGHT above its crown with `grip_force` per jaw and
    lifts the gripper by `lift` meters (default PULL_AFTER past the root depth) at `speed`.
    Writes picks/<plant id>/grip.csv (time, gripper lift, gap between the jaws, wrist force,
    then d, force, attached from the system's state topic). The report adds the pick request, the
    peak wrist force while attached, d at detach (None if it never detached), the largest d,
    the slip (gripper lift minus d at the end) and the Plant's weight.
    """
    world_dir = Path(world_dir)
    request = plant.plant_info(world_dir, plant_id)
    lift = request["depth"] + plant.PULL_AFTER if lift is None else lift
    for name, value in (("lift speed", speed), ("lift", lift), ("grip force", grip_force)):
        if not value > 0:  # also refuses NaN
            raise ValueError(f"the {name} must be above 0")
    x, y, z, _ = request["pose"]
    crown = max(v[2] for v in request["root_hull"])
    world = grip_world(world_dir / "world.sdf", (x, y, z + crown + GRIP_HEIGHT), grip_force, gui)
    config = {"plant": plant_id, "request": request, "speed": speed, "lift": lift}
    if gui:
        # The world runs during the wait: a GUI gets the scene only from a running server.
        config.update(settle=SETTLE + GUI_WAIT, linger=GUI_LINGER)
    report = _run(world, config, gui)
    rows = report.pop("rows")
    log = world_dir / "picks" / plant_id / "grip.csv"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("time,lift,gap,wrist_force,d,force,attached\n"
                   + "".join(",".join("" if v is None else repr(v) for v in row) + "\n"
                             for row in rows))  # fmt: skip
    attached = [row for row in rows if row[6]]
    detach = next((row for row in rows if row[6] is False), None)
    # The state topic is silent while the root rests, so the last d is the last one sent.
    d_end = attached[-1][4] if attached else 0.0
    return {
        **request,
        **report,
        "peak_wrist": max((row[3] for row in attached if row[3] is not None), default=0.0),
        "detach_d": detach[4] if detach else None,
        "max_d": max((row[4] for row in attached), default=0.0),
        "slip": rows[-1][1] - d_end if not detach else None,
        "weight": request["mass"] * 9.8,
        "log": log,
    }


def squeeze(
    variant: Path, out_dir: Path, scale: float = 1.0, grip_force: float = GRIP_FORCE
) -> dict:
    """ADR 0006 squeeze check: jaws close GRIP_HEIGHT above the crown of a Plant whose root is
    welded to the world and hold for SQUEEZE_TIME.

    The report has the gap between the jaws, `escaped`: the leaves whose petiole does not
    cross the grip height between the jaw faces (a 1 mm allowance for contact
    penetration), and `held`: no NaN, every leaf between the jaws, gap above zero.
    """
    if not grip_force > 0:
        raise ValueError("the grip force must be above 0")
    variant = Path(variant)
    physics = json.loads(variant.with_suffix(".physics.json").read_text())
    root = next(link for link in physics["links"] if link["name"] == "root")
    crown = max(v[2] for v in root["hull"]["vertices"]) * scale
    world = plant.settle_world(variant, out_dir, scale)
    fast = grip_world(world, (0.0, 0.0, crown + GRIP_HEIGHT), grip_force)
    report = _run(fast, {"plant": "plant", "request": None, "speed": 0.0, "lift": 0.0,
                         "hold": SQUEEZE_TIME})  # fmt: skip
    gap = report["rows"][-1][2]
    pose = report["links"]
    escaped = []
    leaves = sorted({name.split("_")[0] for name in pose if name.startswith("leaf")})
    for leaf in leaves:
        (ax, ay, az), (bx, by, bz) = pose[f"{leaf}_link0"], pose[f"{leaf}_link1"]
        z = crown + GRIP_HEIGHT
        if not min(az, bz) <= z <= max(az, bz) or az == bz:
            escaped.append(leaf)
            continue
        t = (z - az) / (bz - az)
        px, py = ax + t * (bx - ax), ay + t * (by - ay)
        if not (abs(px) <= gap / 2 + 0.001 and abs(py) <= JAW_SIZE[1] / 2):
            escaped.append(leaf)
    return {"gap": gap, "leaves": len(leaves), "escaped": escaped, "nan": report["nan"],
            "held": not report["nan"] and not escaped and gap > 0.0}  # fmt: skip


def _run(world: Path, config: dict, gui: bool = False) -> dict:
    """Run grip_check.py on a grip world in the system Python; returns its report. With `gui`,
    a `gz sim -g` in the same partition shows it."""
    path = os.pathsep.join(filter(None, [str(plant.SYSTEMS_BUILD),
                                         os.environ.get("GZ_SIM_SYSTEM_PLUGIN_PATH")]))  # fmt: skip
    config = {"step": plant.STEP, "settle": SETTLE, "close_speed": CLOSE_SPEED, "hold": HOLD,
              "lift_accel": LIFT_ACCEL, "jaw_open": JAW_OPEN, "wrist_topic": WRIST_TOPIC,
              **config}  # fmt: skip
    # Own partition: Field worlds share a name, so runs would see each other's topics.
    env = {**os.environ, "GZ_SIM_SYSTEM_PLUGIN_PATH": path,
           "GZ_PARTITION": f"pixelfield-{os.getpid()}"}  # fmt: skip
    viewer = None
    try:
        if gui:
            viewer = subprocess.Popen(["gz", "sim", "-g"], env=env)
        result = plant.run_check(
            [plant.SYSTEM_PYTHON, str(GRIP_SCRIPT), world.name, json.dumps(config)],
            cwd=world.parent, env=env,
        )  # fmt: skip
    finally:
        world.unlink()
        if viewer:
            viewer.terminate()
            try:
                viewer.wait(timeout=5)
            except subprocess.TimeoutExpired:
                viewer.kill()
    return json.loads(result.stdout.strip().splitlines()[-1])


def _prismatic(model, name, parent, child, axis, lower, upper, effort) -> ET.Element:
    joint = ET.SubElement(model, "joint", name=name, type="prismatic")
    _text(joint, "parent", parent)
    _text(joint, "child", child)
    element = ET.SubElement(joint, "axis")
    _text(element, "xyz", plant._join(axis))
    limit = ET.SubElement(element, "limit")
    _text(limit, "lower", plant._num(lower))
    _text(limit, "upper", plant._num(upper))
    _text(limit, "effort", plant._num(effort))
    return joint


def _inertial(link: ET.Element, mass: float, inertia: float) -> None:
    element = ET.SubElement(link, "inertial")
    _text(element, "mass", plant._num(mass))
    moments = ET.SubElement(element, "inertia")
    for key in ("ixx", "iyy", "izz"):
        _text(moments, key, plant._num(inertia))


def _text(parent: ET.Element, tag: str, text: str) -> None:
    ET.SubElement(parent, tag).text = text
