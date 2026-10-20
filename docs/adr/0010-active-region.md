---
status: accepted
---

# Active Region: Plants near any robot link become Picked Plants

Static Plants are visuals without collision (ADR 0007), so a robot passes through them. In M4e the test gripper slid through the neighbours of the Plant it pulled. In M5 any robot, arm or driving base, must touch the Plants it reaches, without naming its parts to pixelfield. The pull-out system (ADR 0006) therefore picks Plants by itself: every root crop Plant that any robot link reaches becomes a Picked Plant.

## Decision

### Trigger

- Every link of every model that is not part of the Field triggers the Active Region. Field models are known to the system: the soil, the Pixel models `r<row>c<col>`, the cameras, the Picked Plants and their anchors. No configuration, no robot names.
- Every few physics steps (about every 10 ms) the system takes each such link's world axis-aligned bounding box, inflated by padding (default 0.05 m, a knob), finds the Pixels it overlaps, and picks every root crop Plant in them whose footprint intersects the box. The footprint is a vertical cylinder around the crown, from the soil up to the top of the foliage, with the foliage radius as its radius (both from the Variant physics export and the Plant's scale). It is 3D, so a chassis passing high over a bed picks nothing.
- Once picked, a Plant stays picked: a resting Picked Plant costs links but no logic. Returning untouched Plants to their static visual ("unpick") is added only if the perf check fails.
- The pick service stays: a robot repo can still pick Plants by id itself.
- Lettuce is cut, not pulled, and has no articulated model: robots still pass through it. Lettuce as an obstacle is a later item.

### Plant SDFs written at build time

The system runs in C++ and cannot call the Python Plant SDF builder. `pixelfield build` writes the scaled SDF of every root crop Plant to `out/<field>/plants/<id>.sdf` (hull meshes shared per Variant), plus a plain table the system reads at load (id, position, footprint radius and height). A pick by the system or by the service loads that file; the Python `pick` command only sends the Plant id.

Measured cost: 3.3 ms and 34 KB per carrot Plant, so about 10 s of build and 100 MB in `out/` for the 10 x 10 carrot Field (3,058 Plants). Ceiling: past about 10 x 10 Pixels, or when build time hurts, write one scale-1 SDF per Variant instead and let the system apply the Plant's scale at spawn.

### Contact between Plants

Picked Plants collide with each other, as real neighbouring leaves push each other. Their foliage overlaps at rest (carrot foliage reaches 0.12 to 0.20 m from the crown at 4 cm spacing in the row), so neighbours picked together start with interpenetrating hulls. DART corrects penetration with a capped velocity (about 1 mm/s, from memory of its contact solver, unverified), so they should drift apart gently rather than jump. The cost to watch is the contact problem per step, since touching neighbours are solved together.

M5d starts with a spike: pick a full carrot Pixel (about 31 Plants) and record the leaf drift and the RTF. If that fails, the fallback is one model per Pixel holding its Picked Plants: model `self_collide` off removes contact inside a Pixel, and colouring Pixels with collide bits separates neighbouring Pixels (foliage reaches at most one Pixel, so 9 bits). The fallback depends on adding links to an existing model at runtime and on DetachableJoint welds inside one skeleton, both untested.

### State topic

With many Picked Plants a per-step message per Plant (1 kHz each) floods gz-transport and the ROS bridge. The state topic `/world/pixelfield/pixelfield/pull_out` carries a Plant's state only while it is being pulled (its root moves or the force is non-zero), plus one message per event: picked, peak passed, detached. A resting Picked Plant is silent. Poses of Picked Plants need nothing new: they are ordinary models on the standard `dynamic_pose/info` topic.

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

- Wheels in Path Gaps do pick Plants: foliage at the edge of a column group reaches to within a few centimetres of a wheel. These picks count in the perf budget.
- Picked neighbours may shift their leaves slightly after a pick while overlapping hulls separate.
- Amends ADR 0006: picks no longer build the SDF at request time, the state topic publishes only while a Plant is being pulled plus events, and choosing which Plants near the robot become dynamic is now the system's job.
- UNVERIFIED until M5d runs: the leaf drift and contact cost of neighbours picked together, and the RTF with many Picked Plants (pass: at least 0.5x with 30 Picked Plants, 10 x 10 Field, OAK-D rig, `docs/design/perf.md`).
