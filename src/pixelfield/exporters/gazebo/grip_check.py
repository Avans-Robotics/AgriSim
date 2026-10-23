"""Grip check with the test gripper, run in the system Python with the Gazebo bindings.

Usage: grip_check.py <grip world.sdf> <config json>

The world has the gripper model (gripper.py). Config: plant (model name), request (pick
request for the pull-out system, or null when the Plant is already in the world), step, settle,
close_speed, hold, lift_accel, jaw_open, speed, lift, wrist_topic, optionally linger (seconds
the world keeps running after the pull, for a GUI). Timeline: jaws open for
`settle` seconds, then they close at close_speed until they stall on the leaf bunch (their
effort limit is the grip force); after the time a full close takes plus `hold`, the gripper
lifts by `lift` meters, its speed ramped up at lift_accel to `speed`, and stops. Prints one
JSON line: whether the pick was accepted, whether any value was NaN, the final world position
of every Plant link, every Picked Plant heard on the state topic with its largest d, and one
row per step: time, gripper lift, gap between the jaw faces, the wrist force (upward pull on
the gripper from its wrist sensor, minus its value before the jaws close), then d, force and
attached from the pull-out system's state topic. Topic values are matched to the step by sim
time (None when nothing was published that step).
"""

import json
import math
import re
import sys
import time
from pathlib import Path

import gz.math7  # noqa: F401, world_pose returns Pose3d only once it is loaded
from gz.common5 import set_verbosity
from gz.msgs10.boolean_pb2 import Boolean
from gz.msgs10.param_pb2 import Param
from gz.msgs10.stringmsg_pb2 import StringMsg
from gz.msgs10.wrench_pb2 import Wrench
from gz.sim8 import Joint, Link, Model, TestFixture, World, world_entity
from gz.transport13 import Node

JAWS = ("jaw_left_joint", "jaw_right_joint")
JAW_LINK = 200.0  # 1/s: a jaw 0.25 mm ahead of the other backs off at the closing speed
TARE = 0.05  # seconds from which the wrist force is averaged until the jaws start closing

world_sdf, config = sys.argv[1], json.loads(sys.argv[2])
STEP = config["step"]  # seconds per physics step of the world
request = config["request"]
start_lift = config["settle"] + config["jaw_open"] / config["close_speed"] + config["hold"]
lift_time = config["lift"] / config["speed"] + config["speed"] / config["lift_accel"] \
    if config["lift"] else 0.0  # fmt: skip
steps = round((start_lift + lift_time) / STEP)
text = Path(world_sdf).read_text()

set_verbosity(1)
fixture = TestFixture(world_sdf)
node = Node()
# Topic messages by sim time in ms; gz-transport delivers them in another thread.
states, wrist = {}, {}
rows, report, joints = [], {"nan": False, "links": {}, "plants": {}}, {}
picked = []  # whether the Plant is a model at the end
stepped = []  # steps that ran: none when the world did not load


def ms(header):
    return round(header.stamp.sec * 1000 + header.stamp.nsec / 1e6)


def on_state(msg):
    plant, d = msg.params["plant"].string_value, msg.params["d"].double_value
    report["plants"][plant] = max(report["plants"].get(plant, 0.0), d)
    if plant != config["plant"]:
        return  # a neighbour the Active Region picked
    states[ms(msg.header)] = [msg.params["d"].double_value, msg.params["force"].double_value,
                              msg.params["attached"].bool_value]  # fmt: skip


def on_wrist(msg):
    wrist[ms(msg.header)] = msg.force.z


def pre_update(info, ecm):
    stepped[:] = [info.iterations]
    if not joints:
        gripper = Model(World(world_entity(ecm)).model_by_name(ecm, "gripper"))
        joints.update({name: Joint(gripper.joint_by_name(ecm, name)) for name in ("lift", *JAWS)})
        for joint in joints.values():
            joint.enable_position_check(ecm, True)
    t = info.iterations * STEP
    # The jaws act as if linked, like a parallel gripper's rack and pinion: a jaw ahead of the
    # other is slowed or backed off. Two force-capped servos alone push equally on a held bunch
    # and leave the pair free to slide along the closing axis, which shook a pulled-out Plant.
    left, right = ((joints[name].position(ecm) or [0.0])[0] for name in JAWS)
    close = config["close_speed"] if t >= config["settle"] else 0.0
    for name, ahead in zip(JAWS, (left - right, right - left), strict=True):
        joints[name].set_velocity(ecm, [close - JAW_LINK * ahead])
    position = (joints["lift"].position(ecm) or [0.0])[0]
    lift = 0.0
    if config["lift"] and t >= start_lift and position < config["lift"]:
        lift = min(config["speed"], config["lift_accel"] * (t - start_lift + STEP),
                   math.sqrt(2 * config["lift_accel"] * (config["lift"] - position)))  # fmt: skip
    joints["lift"].set_velocity(ecm, [lift])


def post_update(info, ecm):
    position = joints["lift"].position(ecm)
    jaws = [joints[name].position(ecm) for name in JAWS]
    if not position or not all(jaws):
        return
    gap = 2 * config["jaw_open"] - jaws[0][0] - jaws[1][0]
    rows.append([round(info.sim_time.total_seconds() * 1000), info.iterations * STEP,
                 position[0], gap])  # fmt: skip
    if info.iterations == steps:
        model = Model(World(world_entity(ecm)).model_by_name(ecm, config["plant"]))
        picked.append(model.valid(ecm))
        for entity in model.links(ecm):
            link = Link(entity)
            p = link.world_pose(ecm).pos()
            report["links"][link.name(ecm)] = (p.x(), p.y(), p.z())


fixture.on_pre_update(pre_update)
fixture.on_post_update(post_update)
fixture.finalize()
server = fixture.server()
world_name = re.search(r'<world name="([^"]+)"', text).group(1)
node.subscribe(Param, f"/world/{world_name}/pixelfield/pull_out", on_state)
node.subscribe(Wrench, config["wrist_topic"], on_wrist)
server.run(True, 1, False)
report["requested"] = None
if request:
    topic = f"/world/{world_name}/pixelfield/pick"
    ok, reply = node.request(topic, StringMsg(data=request["name"]), StringMsg, Boolean, 5000)
    report["requested"] = bool(ok and reply.data)
server.run(True, steps - 1, False)
if not stepped:
    sys.exit("grip_check: no simulation step ran, the world did not load (errors above)")
if config.get("linger"):
    server.run(True, round(config["linger"] / STEP), False)  # to look around in the GUI
# The Active Region may have picked the Plant under the jaws before the request came.
report["requested"] = report["requested"] or bool(request and picked)
time.sleep(0.5)  # the last topic messages
tare = [wrist[row[0]] for row in rows if row[0] in wrist and TARE < row[1] <= config["settle"]]
tare = sum(tare) / len(tare) if tare else 0.0
report["rows"] = [row[1:] + [wrist[row[0]] - tare if row[0] in wrist else None]
                  + states.get(row[0], [None] * 3) for row in rows]  # fmt: skip
values = [v for row in report["rows"] for v in row if isinstance(v, float)]
values += [c for p in report["links"].values() for c in p]
report["nan"] = not all(math.isfinite(v) for v in values)
print(json.dumps(report))
