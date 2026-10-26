---
status: accepted
---

# Active Region: Plants near any robot link become Picked Plants

Static Plants are visuals without collision (ADR 0007), so a robot passes through them. In M4e the test gripper slid through the neighbours of the Plant it pulled. In M5 any robot, arm or driving base, must touch the Plants it reaches, without naming its parts to pixelfield. The pull-out system (ADR 0006) therefore picks Plants by itself: every root crop Plant that any robot link reaches becomes a Picked Plant.

## Decision

### Trigger

- Every link of every model that is not part of the Field triggers the Active Region. Field models are known to the system: the soil, the Pixel models `r<row>c<col>`, the cameras, the Picked Plants and their anchors. No configuration, no robot names.
- Every 10 ms of sim time the system takes the world axis-aligned bounding box of each collision of each such link (the collision's box in the link's frame, turned into the world: a little larger than the collision when it is rotated), inflated by padding (default 0.05 m, the plugin element `<padding>`), and picks every root crop Plant whose footprint intersects one of the boxes. One box per collision, not one per link (amended in M5e): the Amiga's base link holds its low wheel forks and its high cross tubes, so one box around the link reached from 0.15 m to the top of the robot across its whole track: standing over a bed with its wheels in the Path Gaps it picked 144 carrots, which the tubes at 0.61 m never touch, and ran at about 0.01x. With a box per collision it picks 1 and runs at 1.0x (`docs/design/perf.md`). Collisions that cannot touch a Plant are skipped (amended in M5e, robot interface 2): collide bit 0 belongs to the soil alone, Plant collisions lack it, so a collision with bitmask 0x1 (a wheel meant to drive over beds) picks nothing. A 37 kg wheel rig driven along a carrot row with the default bitmask picks 10 Plants and runs at 0.03x, squeezing gram-light leaves against the soil; with 0x1 it picks none and runs at 2x (physics only, one Pixel). The footprint is a vertical cylinder around the crown, from the soil up to the top of the foliage, with the crown radius (the root's widest point) as its radius, from the Variant physics export and the Plant's scale. `<footprint>foliage</footprint>` uses the foliage reach as the radius instead, as first planned; the M5d spike showed that too costly (see Contact between Plants). It is 3D, so a chassis passing high over a bed picks nothing. Every collision is checked against every Plant of the table (about 150k cheap tests per check on a 10 x 10 Field); bucketing per Pixel waits until that shows in the perf rows.
- Unpick (built in M5d): a Plant the region picked turns back into its static visual when its bond is intact (not past the peak, d under 0.1 mm), all its links have moved slower than 1 mm/s for 2 s, no padded box of a robot link's collision meets its footprint, and every link is within 1 cm of where it was just after the spawn (the static visual's pose), so the switch shows no visible jump. A Plant that was pulled, or that a robot left bent, stays picked. The weld goes first and the models a step later, as on detach; the visual is rebuilt from the Pixel model's SDF, and an `unpicked` event goes out. An unpicked Plant can be picked again. A Plant picked through the pick service is never unpicked: someone asked for it.
- The pick service stays: a robot repo can still pick Plants by id itself.
- Lettuce is cut, not pulled, and has no articulated model: robots still pass through it. Lettuce as an obstacle is a later item.

### Plant SDFs written at build time

The system runs in C++ and cannot call the Python Plant SDF builder. `pixelfield build` writes the scaled SDF of every root crop Plant to `out/<field>/plants/<id>.sdf` (hull meshes shared per Variant), plus a plain table the system reads at load (id, position, footprint radius and height). A pick by the system or by the service loads that file; the Python `pick` command only sends the Plant id.

Measured cost: 3.3 ms and 34 KB per carrot Plant, so about 10 s of build and 100 MB in `out/` for the 10 x 10 carrot Field (3,058 Plants). Measured in M5c: 4.7 s and 142 MB of Plant SDFs (46 KB per Plant on average over the 24 Variants), see [perf.md](../design/perf.md). Ceiling: past about 10 x 10 Pixels, or when build time hurts, write one scale-1 SDF per Variant instead and let the system apply the Plant's scale at spawn.

### Contact between Plants

Picked Plants collide with each other, as real neighbouring leaves push each other. Their foliage overlaps at rest (carrot foliage reaches 0.12 to 0.20 m from the crown at 4 cm spacing in the row), so neighbours picked together start with interpenetrating collisions.

The M5d spike picked Plants of a carrot Pixel at once in a headless world (physics only, 1 ms step, no cameras) and failed:

| Plants | Petiole collision | Real-time factor | Leaf tip drift |
|---|---|---|---|
| 4 | convex mesh hulls (M4) | 0.17 | 34 mm in 0.5 s, up to 8 cm/s |
| 4 | 2 capsules per petiole link (M5d) | 1.0 | 0.7 mm in 0.5 s |
| 32 | mesh hulls | below 0.02 | violent |
| 32 | 2 capsules per link | 0.036 | median 0.1 mm, max 6 mm over 3 s, settling |
| 32 | mesh hulls, no contact between Plants | 0.15 | none |
| 32 | no petiole collisions, all joints fixed | 0.34 | none |

- The guess that DART corrects penetration at about 1 mm/s was wrong for mesh hulls: ODE collision detection (gz-sim's default for dartsim) shoved them apart at up to 8 cm/s. Capsules separate gently, so petioles now collide as capsules (ADR 0006, amended).
- Contact between many overlapping Plants is solved as one problem and dominates the cost. A Picked Plant also costs about 0.15 ms per step without any contact, about half of it per-link bookkeeping.
- The planned fallback, one model per Pixel with `self_collide` off, is the "no contact between Plants" row: 0.15x for one full Pixel before cameras. Rejected, not built.
- With the foliage footprint the test gripper over a mid-Pixel carrot picks all 32 Plants of its Pixel; with the crown footprint it picks 4 to 7. Hence the crown footprint: the cost is that leaves of unpicked neighbours still pass through a robot.

### State topic

With many Picked Plants a per-step message per Plant (1 kHz each) floods gz-transport and the ROS bridge. The state topic `/world/pixelfield/pixelfield/pull_out` carries a Plant's state only while it is being pulled (its root moves or the force is non-zero), plus one message per event: picked, peak passed, detached. A resting Picked Plant is silent. In M5c "being pulled" became "d or the force changed since the last message", so a root held still by a robot or by the post-peak ratchet is silent too, and events are ordinary state messages with an extra `event` parameter, so a consumer reads one message type. Poses of Picked Plants need nothing new: they are ordinary models on the standard `dynamic_pose/info` topic.

## Why

- **Any robot, zero configuration.** A gripper reaching into a Pixel, a wheel rolling over a bed and a sagging hose all touch Plants. Naming trigger links per robot breaks that.
- **The check is cheap.** A robot has tens of links, each looked up against a few Pixels through the grid. The cost is in the Picked Plants (25 to 43 links each), which the perf check measures.
- **One implementation of Plant scaling.** Writing SDFs at build reuses the Python builder that M4c and M4d validated; a C++ copy of the scaling rules would need a parity test.

## Considered Options

- **Configured trigger links** (for example `amiga::link_tcp`). Fewer picks, but every robot must name its parts.
- **Only the robot repo calls the pick service.** Every robot reimplements the region and the neighbour pass-through stays by default.
- **A Python sidecar process that builds SDFs on request.** An extra process every robot user must start.
- **No contact between Plants through collide bits.** Two shapes collide when their bitmasks share a bit and a robot has 0xFFFF by default, so each Plant needs its own bit among neighbours. Carrot foliage overlaps 30 to 56 neighbours; 15 free bits are far too few.
- **Robots set a dedicated bit.** Breaks zero configuration.
- **Publishing at a fixed rate.** Still about 10,000 messages per second at 100 Picked Plants and 100 Hz, and it breaks the per-step log M4d validated.

## Consequences

- A robot link picks a Plant only when one of its collision boxes comes within the padding plus the crown radius (about 7 cm for a carrot) of the crown, so wheels in Path Gaps pick only Plants that close to them.
- Leaves of Plants that are not picked still pass through a robot, also when they overlap a Picked Plant's leaves.
- Picked neighbours shift their leaves slightly after a pick while overlapping capsules separate (median 0.1 mm, at most 6 mm over 3 s with 32 Plants).
- A test gripper with 10 cm wide jaws grabs the leaf bunch of an in-row neighbour 4 cm away too, and pulls it.
- Amends ADR 0006: picks no longer build the SDF at request time, the state topic publishes only while a Plant is being pulled plus events, and choosing which Plants near the robot become dynamic is now the system's job.
- Perf budget, changed after the spike: at least 0.5x real time with the test gripper grasping a mid-Pixel carrot in the 10 x 10 Field with the OAK-D rig (`docs/design/perf.md`). Raised after review: the scenario should run as fast as the cameras allow (the rig alone runs at 0.97x), 0.8x at least, for a live Amiga showcase. Met in M5d with roots that never overlap in the layout (spec section 6) and a 2 ms physics step: 0.97x. 30 Picked Plants at 0.5x is out of reach: even resting and apart they cost about 4.5 ms per step. Unpick keeps Picked Plants from piling up behind a driving robot.
