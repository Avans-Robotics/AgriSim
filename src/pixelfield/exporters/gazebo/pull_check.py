"""Scripted pull of one picked Plant, run in the system Python with the Gazebo bindings.

Usage: pull_check.py <world.sdf> <request json> <steps> <speed> <release> <step>

Loads a Field world (without its Sensors system), picks the Plant by its id, then lifts the
Plant's root at <speed> m/s with a stiff spring-damper force, as a gripper holding the root
would, and lets go once the lift target passes <release> meters (0: never lifts), so
the Plant drops. The lift is a vertical force only, so a detached Plant can tip over. Prints
one JSON line: whether the request was accepted, whether the Plant's grouped visual exists
before and after, and one row per step after the spawn: time, lift, pull force, the lowest
point of the root's collision hull (world z), then d, force and attached from the system's state
topic, matched to the step by its time stamp (None when no state was published that step),
and the state topic's events as [sim time, event].
"""

import json
import re
import sys
import time
from pathlib import Path

import gz.math7
from gz.common5 import set_verbosity
from gz.msgs10.boolean_pb2 import Boolean
from gz.msgs10.param_pb2 import Param
from gz.msgs10.stringmsg_pb2 import StringMsg
from gz.sim8 import Link, Model, TestFixture, World, world_entity
from gz.transport13 import Node

PULL_STIFFNESS = 5000.0  # N/m, gripper on the root: about 5 mm lag at 25 N
PULL_DAMPING = 30.0  # N s/m, on the speed relative to the lift target

world_sdf, request = sys.argv[1], json.loads(sys.argv[2])
steps, speed, release = int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
step = sys.argv[6]  # seconds per physics step, whatever the world's
name = request["name"]
hull = request["root_hull"]  # root collision hull vertices in the root link frame
fast = Path(world_sdf).with_name(".pull_fast.sdf")
text = Path(world_sdf).read_text()
text = re.sub(r"<real_time_factor>[^<]*<", "<real_time_factor>0<", text)
text = re.sub(r"<max_step_size>[^<]*<", f"<max_step_size>{step}<", text)
text = re.sub(r'<plugin filename="gz-sim-sensors-system".*?</plugin>', "", text, flags=re.S)
fast.write_text(text)

set_verbosity(1)
fixture = TestFixture(str(fast))
node = Node()
states = {}  # state topic messages by sim time in ms; delivered in another thread
events = []
rows, pull = [], {"root": None, "z0": None, "t0": None, "force": 0.0}
visual = {}


def on_state(msg):
    if msg.params["plant"].string_value != name:
        return  # another Picked Plant
    ms = round(msg.header.stamp.sec * 1000 + msg.header.stamp.nsec / 1e6)
    states[ms] = [msg.params["d"].double_value, msg.params["force"].double_value,
                  msg.params["attached"].bool_value]  # fmt: skip
    if "event" in msg.params:
        events.append([ms / 1000, msg.params["event"].string_value])


def grouped_visual(ecm):
    world = World(world_entity(ecm))
    pixel = Model(world.model_by_name(ecm, name.split("-")[0]))
    return any(Link(link).visual_by_name(ecm, name) for link in pixel.links(ecm))


def pre_update(info, ecm):
    if "before" not in visual:
        visual["before"] = grouped_visual(ecm)
    if pull["root"] is None:
        model = World(world_entity(ecm)).model_by_name(ecm, name)
        if not model:
            return
        root = Link(Model(model).link_by_name(ecm, "root"))
        root.enable_velocity_checks(ecm, True)
        pull.update(root=root, z0=root.world_pose(ecm).pos().z(), t0=info.iterations)
        return
    root = pull["root"]
    velocity = root.world_linear_velocity(ecm)
    if velocity is None:
        return
    t = (info.iterations - pull["t0"]) * info.dt.total_seconds()
    lift = root.world_pose(ecm).pos().z() - pull["z0"]
    force = PULL_STIFFNESS * (speed * t - lift) - PULL_DAMPING * (velocity.z() - speed)
    if release <= 0 or speed * t > release:
        force = 0.0
    root.add_world_force(ecm, gz.math7.Vector3d(0.0, 0.0, force))
    pull["force"] = force


def post_update(info, ecm):
    visual["after"] = grouped_visual(ecm)
    if pull["root"] is None:
        return
    t = (info.iterations - pull["t0"]) * info.dt.total_seconds()
    lift = pull["root"].world_pose(ecm).pos().z() - pull["z0"]
    pose = pull["root"].world_pose(ecm)
    bottom = min(pose.rot().rotate_vector(gz.math7.Vector3d(*v)).z() for v in hull) + pose.pos().z()
    rows.append([round(info.sim_time.total_seconds() * 1000), t, lift, pull["force"], bottom])


fixture.on_pre_update(pre_update)
fixture.on_post_update(post_update)
fixture.finalize()
server = fixture.server()
server.run(True, 1, False)
world_name = re.search(r'<world name="([^"]+)"', text).group(1)
node.subscribe(Param, f"/world/{world_name}/pixelfield/pull_out", on_state)
ok, reply = node.request(f"/world/{world_name}/pixelfield/pick", StringMsg(data=name), StringMsg,
                         Boolean, 5000)  # fmt: skip
try:
    server.run(True, steps, False)
    time.sleep(0.5)  # the last state messages
finally:
    fast.unlink()
rows = [row[1:] + states.get(row[0], [None] * 3) for row in rows]
print(json.dumps({"requested": bool(ok and reply.data), "visual_before": visual.get("before"),
                  "visual_after": visual.get("after"), "rows": rows,
                  "events": sorted(events)}))  # fmt: skip
