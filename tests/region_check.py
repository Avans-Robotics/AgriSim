"""Active Region check, run in the system Python with the Gazebo bindings (test_region.py).

Usage: region_check.py <world.sdf> <config json>

Config: probes (static models added to a copy of the world, each one box link: name, pose
[x, y, z] of the link, size [x, y, z] of its box, offset [x, y, z, roll, pitch, yaw] of the
box's collision in the link), steps, pick (a Plant id to request by id after the first step,
or null). Prints one JSON line: the root crop Plants that are models at the end, and the pick
reply (null without a pick).
"""

import json
import sys
from pathlib import Path

from gz.common5 import set_verbosity
from gz.msgs10.boolean_pb2 import Boolean
from gz.msgs10.stringmsg_pb2 import StringMsg
from gz.sim8 import TestFixture, World, world_entity
from gz.transport13 import Node

world_sdf, config = Path(sys.argv[1]), json.loads(sys.argv[2])
rows = (world_sdf.parent / "plants" / "plants.tsv").read_text().splitlines()[1:]
ids = [row.split("\t")[0] for row in rows]


def probe(name, pose, size, offset):
    j = " ".join
    return (f'<model name="{name}"><static>true</static><pose>{j(map(str, pose))} 0 0 0</pose>'
            f'<link name="link"><collision name="box"><pose>{j(map(str, offset))}</pose>'
            f"<geometry><box><size>{j(map(str, size))}</size></box></geometry></collision>"
            "</link></model>")  # fmt: skip


copy = world_sdf.with_name(".region.sdf")
models = "".join(probe(**p) for p in config["probes"])
copy.write_text(world_sdf.read_text().replace("</world>", models + "</world>", 1))
set_verbosity(1)
fixture = TestFixture(str(copy))
picked = []


def post_update(info, ecm):
    world = World(world_entity(ecm))
    picked[:] = [i for i in ids if world.model_by_name(ecm, i)]


fixture.on_post_update(post_update)
fixture.finalize()
server = fixture.server()
try:
    server.run(True, 1, False)
    requested = None
    if config["pick"]:
        request = StringMsg(data=config["pick"])
        topic = "/world/pixelfield/pixelfield/pick"
        ok, reply = Node().request(topic, request, StringMsg, Boolean, 5000)
        requested = bool(ok and reply.data)
    server.run(True, config["steps"] - 1, False)
finally:
    copy.unlink()
print(json.dumps({"picked": picked, "requested": requested}))
