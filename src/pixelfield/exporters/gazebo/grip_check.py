"""Grip check with the test gripper, run in the system Python with the Gazebo bindings.

Usage: grip_check.py <grip world.sdf> <config json>

The world has the gripper model (gripper.py). Config: plant (model name), request (pick
request for the pull-out system, or null when the Plant is already in the world), settle,
close_speed, hold, lift_accel, jaw_open, speed, lift, wrist_topic. Timeline: jaws open for
`settle` seconds, then they close at close_speed until they stall on the leaf bunch (their
effort limit is the grip force); after the time a full close takes plus `hold`, the gripper
lifts by `lift` meters, its speed ramped up at lift_accel to `speed`, and stops. Prints one
JSON line: whether the pick was accepted, whether any value was NaN, the final world position
of every Plant link, and one row per step: time, gripper lift, gap between the jaw faces, the
wrist force (upward pull on the gripper from its wrist sensor, minus its value before the
jaws close), then d, force and attached from the pull-out system's state topic. Topic values
are matched to the step by sim time (None when nothing was published that step).
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

STEP = 0.001
JAWS = ("jaw_left_joint", "jaw_right_joint")
TARE = 0.05  # seconds from which the wrist force is averaged until the jaws start closing

world_sdf, config = sys.argv[1], json.loads(sys.argv[2])
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
rows, report, joints = [], {"nan": False, "links": {}}, {}


def ms(header):
    return round(header.stamp.sec * 1000 + header.stamp.nsec / 1e6)


def on_state(msg):
    states[ms(msg.header)] = [msg.params["d"].double_value, msg.params["force"].double_value,
                              msg.params["attached"].bool_value]  # fmt: skip


def on_wrist(msg):
    wrist[ms(msg.header)] = msg.force.z


def pre_update(info, ecm):
    if not joints:
        gripper = Model(World(world_entity(ecm)).model_by_name(ecm, "gripper"))
        joints.update({name: Joint(gripper.joint_by_name(ecm, name)) for name in ("lift", *JAWS)})
        for joint in joints.values():
            joint.enable_position_check(ecm, True)
    t = info.iterations * STEP
    for name in JAWS:
        joints[name].set_velocity(ecm, [config["close_speed"] if t >= config["settle"] else 0.0])
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
time.sleep(0.5)  # the last topic messages
tare = [wrist[row[0]] for row in rows if row[0] in wrist and TARE < row[1] <= config["settle"]]
tare = sum(tare) / len(tare) if tare else 0.0
report["rows"] = [row[1:] + [wrist[row[0]] - tare if row[0] in wrist else None]
                  + states.get(row[0], [None] * 3) for row in rows]  # fmt: skip
values = [v for row in report["rows"] for v in row if isinstance(v, float)]
values += [c for p in report["links"].values() for c in p]
report["nan"] = not all(math.isfinite(v) for v in values)
print(json.dumps(report))
