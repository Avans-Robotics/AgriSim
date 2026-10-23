"""Active Region check, run in the system Python with the Gazebo bindings (test_region.py).

Usage: region_check.py <world.sdf> <config json>

Config: probes (static models added to a copy of the world, each one box link: name, pose
[x, y, z] of the link, size [x, y, z] of its boxes, offsets: [x, y, z, roll, pitch, yaw] of
each box's collision in the link), steps, pick (a Plant id to request by id after the first step,
or null), moves (optional, [{"at": step, "probe": name, "to": [x, y, z]}]), snapshot
(optional step at which to also report the visuals as visuals_then). Prints one JSON
line: the root crop Plants that are models at the end, the pick reply (null without a pick),
the state topic's events as [plant, event, sim time] in order, and the Plants whose static
visual is in their Pixel model at the end.
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

world_sdf, config = Path(sys.argv[1]), json.loads(sys.argv[2])
rows = (world_sdf.parent / "plants" / "plants.tsv").read_text().splitlines()[1:]
ids = [row.split("\t")[0] for row in rows]


def probe(name, pose, size, offsets):
    j = " ".join
    boxes = "".join(f'<collision name="box{i}"><pose>{j(map(str, offset))}</pose>'
                    f"<geometry><box><size>{j(map(str, size))}</size></box></geometry>"
                    "</collision>" for i, offset in enumerate(offsets))  # fmt: skip
    return (f'<model name="{name}"><static>true</static><pose>{j(map(str, pose))} 0 0 0</pose>'
            f'<link name="link">{boxes}</link></model>')  # fmt: skip


copy = world_sdf.with_name(".region.sdf")
models = "".join(probe(**p) for p in config["probes"])
text = re.sub(r"<real_time_factor>[^<]*<", "<real_time_factor>0<", world_sdf.read_text())
copy.write_text(text.replace("</world>", models + "</world>", 1))
set_verbosity(1)
fixture = TestFixture(str(copy))
picked, visuals, visuals_then, events = [], [], [], []
moves = {m["at"]: m for m in config.get("moves", [])}


def on_state(msg):
    if "event" in msg.params:
        t = msg.header.stamp.sec + msg.header.stamp.nsec / 1e9
        events.append([msg.params["plant"].string_value, msg.params["event"].string_value, t])


def pre_update(info, ecm):
    move = moves.get(info.iterations)
    if move:
        model = Model(World(world_entity(ecm)).model_by_name(ecm, move["probe"]))
        model.set_world_pose_cmd(ecm, gz.math7.Pose3d(*move["to"], 0, 0, 0))


def post_update(info, ecm):
    world = World(world_entity(ecm))
    picked[:] = [i for i in ids if world.model_by_name(ecm, i)]
    links = [Link(link) for i in {i.split("-")[0] for i in ids}
             for link in Model(world.model_by_name(ecm, i)).links(ecm)]  # fmt: skip
    visuals[:] = [i for i in ids if any(link.visual_by_name(ecm, i) for link in links)]
    if info.iterations == config.get("snapshot"):
        visuals_then[:] = visuals


fixture.on_pre_update(pre_update)
fixture.on_post_update(post_update)
fixture.finalize()
server = fixture.server()
node = Node()
node.subscribe(Param, "/world/pixelfield/pixelfield/pull_out", on_state)
try:
    server.run(True, 1, False)
    requested = None
    if config["pick"]:
        request = StringMsg(data=config["pick"])
        topic = "/world/pixelfield/pixelfield/pick"
        ok, reply = node.request(topic, request, StringMsg, Boolean, 5000)
        requested = bool(ok and reply.data)
    server.run(True, config["steps"] - 1, False)
    time.sleep(0.5)  # the last state messages
finally:
    copy.unlink()
print(json.dumps({"picked": picked, "requested": requested, "events": events,
                  "visuals": visuals, "visuals_then": visuals_then}))  # fmt: skip
