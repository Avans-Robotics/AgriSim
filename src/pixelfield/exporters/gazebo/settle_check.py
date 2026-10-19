"""Settle check of one Plant model, run in the system Python with the Gazebo bindings.

Usage: settle_check.py <world.sdf> <model> <steps> <after steps>

Runs the world unthrottled for <steps> physics steps and prints one JSON line: the largest
link speed (m/s) from step <after> on, whether any link speed or position was NaN, the
fastest link, and how far each link ended up from its start (largest, in meters).
"""

import json
import math
import re
import sys
from pathlib import Path

import gz.math7  # noqa: F401  (registers Pose3d and Vector3d return types)
from gz.common5 import set_verbosity
from gz.sim8 import Link, Model, TestFixture, World, world_entity

world_sdf, model_name, steps, after = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
# Same world, but as fast as the CPU allows; mesh URIs resolve against the same folder.
fast = Path(world_sdf).with_name(".settle_fast.sdf")
text = Path(world_sdf).read_text()
fast.write_text(re.sub(r"<real_time_factor>[^<]*<", "<real_time_factor>0<", text))

set_verbosity(1)
fixture = TestFixture(str(fast))
links, start = [], {}
report = {"max_speed_after": 0.0, "fastest_link": None, "nan": False, "max_travel": 0.0}


def pre_update(info, ecm):
    if links:
        return
    model = Model(World(world_entity(ecm)).model_by_name(ecm, model_name))
    for entity in model.links(ecm):
        link = Link(entity)
        link.enable_velocity_checks(ecm, True)
        links.append(link)


def post_update(info, ecm):
    for link in links:
        position = link.world_pose(ecm).pos()
        velocity = link.world_linear_velocity(ecm)
        name = link.name(ecm)
        if position is None or velocity is None:
            continue
        p = (position.x(), position.y(), position.z())
        speed = velocity.length()
        if not all(math.isfinite(v) for v in p + (speed,)):
            report["nan"] = True
            continue
        start.setdefault(name, p)
        report["max_travel"] = max(report["max_travel"], math.dist(p, start[name]))
        if info.iterations >= after and speed > report["max_speed_after"]:
            report["max_speed_after"], report["fastest_link"] = speed, name


fixture.on_pre_update(pre_update)
fixture.on_post_update(post_update)
fixture.finalize()
fixture.server().run(True, steps, False)
fast.unlink()
report["links"] = len(links)
print(json.dumps(report))
