---
status: accepted
---

# Pull-out via an anchored root and a displacement force law

Harvesting must take a realistic force and feel realistic to a controller: the long-term goal is a learned pull policy, trained in simulation and run on a real robot with a small sim-to-real gap. Soil is not simulated. The root of a picked Plant is held by a per-Plant force law that depends only on how far the root has moved up, its Pull-out Curve, and the foliage is a chain of spring-jointed links that the gripper can bend and hold.

## Decision

### Pull-out Curve

With `d` the upward displacement of the root, `v` its upward speed and `F` the resisting force, `F = F_curve(d) + c * v`, where `F_curve` is:

- `0 <= d < d_peak`: `F` rises linearly from 0 to `F_peak`.
- At `d_peak`: `F` drops to `residual_fraction * F_peak`.
- `d_peak <= d < L`: `F` decays linearly to 0, with `L` the root depth: the length of root below the soil (the Variant's `root_depth` times the Plant's scale).
- `d >= L`: the Plant is free.

`F_peak` is the Plant's Pull-out Force from the Manifest. `d_peak` (guess 5 mm) and `residual_fraction` (guess 0.3) are per-Crop knobs in the Crop YAML. Once the root has passed `d_peak` the soil bond is broken, so pushing the root back down does not bring the peak back. A loosened root is held by friction: after the peak the root cannot sink below the highest point it reached (the anchor's lower limit follows it), so a part-pulled root that is let go stays where it is instead of being pushed back by the residual force. `F_peak` is sampled independently of root size until measurements show a correlation. The damping term `c * v` (per-Crop knob `pull_out_damping` in N s/m, default 0) acts only while the root is attached; it is off until measurements at two pull speeds give a value, and turning it on needs no code change. The shape follows measured uprooting curves (a rise to a peak, a sharp drop, then a residual), and its parameters, `c` included, are to be fitted to real pulls ([measurement protocol](../research/measurement-protocol.md)).

### Mechanism in Gazebo

- A picked Plant gets an anchor: a light link in a non-static model, on a vertical prismatic joint to the world at the Plant's position, with its range from 0 to `L`. It must not be a static model: dartsim freezes a body welded to a static model.
- The Plant's root link is welded to the anchor by a `DetachableJoint` entity (`components::DetachableJoint`, type fixed) that our system creates.
- Every physics step the system reads the prismatic joint position `d` and velocity `v` and commands the joint force `-F`. At `d >= L` it removes the `DetachableJoint` and the Plant moves freely.
- Only vertical pull-out is modelled: sideways and rotational motion of the root is rigid until detach. An angled pull is a later knob.
- The system computes the force itself, so the resisting force is known exactly each step. It publishes `d`, `F` and the attached state on a topic.
- The buried root starts inside the soil collision, so the root's collision leaves out the soil's collide bit while attached: otherwise contact forces add to the force law. At detach the system gives it the full bitmask (`CollideBitmaskCmd`), so a dropped Plant lands on the soil.
- The anchor model is removed one step after the weld: dartsim keeps the root in the anchor's skeleton until the weld is gone, so removing both in one step freezes the root.

### Picking a Plant

Plants stay visuals grouped per Pixel ([ADR 0007](0007-gazebo-plants-grouped-per-pixel.md)). A pick of one Plant id:

1. Python (a `pixelfield` command in the Gazebo Exporter) reads the Manifest (Plant pose, scale and Pull-out Force; per-Crop Pull-out Curve knobs) and the Variant physics export, writes the scaled SDF for that one Plant with its Pull-out Curve as a custom element `<pixelfield:pull_out>`, and sends the request with the `gz` CLI: a standard `gz.msgs.EntityFactory` (SDF path, Plant id, pose) on `/world/<world>/pixelfield/pick`, so the SDF file alone describes the pick.
2. A C++ gz-sim system in `src/pixelfield/exporters/gazebo/systems/` removes the grouped visual (`RequestRemoveEntity`), spawns the Plant model (`SdfEntityCreator`), creates the anchor and the weld, then runs the force law.

Any number of Plants can be picked at once, each Plant id once per running world; a part-pulled Plant stays anchored and blocks nothing. The state topic is `/world/<world>/pixelfield/pull_out` (`gz.msgs.Param`: plant, d, force, attached), published every step while attached. All per-step logic is C++. The Python SDF build runs once per pick; it moves to C++ if pick latency matters in M5. The system only spawns, holds and detaches picked Plants: choosing which Plants near the robot become dynamic is not part of it. Amended in M5 by [ADR 0010](0010-active-region.md): Plant SDFs are written at build time, the state topic publishes only while a Plant is being pulled plus one message per event, and the system picks Plants near any robot link itself.

### Plant model

- **Root**: one rigid link. Its collision is the convex hull of a low-poly copy of the generator's root profile, so a shoulder grip works too.
- **Foliage**: per leaf, a chain of 3 petiole links joined by universal joints (two bending axes, twist rigid) with `spring_stiffness`, `spring_reference` and `damping`. The generated shape is taken as the shape under gravity: each joint's `spring_reference` is set so the spring torque balances the gravity torque of the rest of the leaf at that shape (at most about 0.12 rad), so a spawned Plant keeps its Variant's look and does not sag on spawn. With a reference of 0, carrot leaves (nearly upright on soft springs) leaned up to 10 cm and needed about 4.5 s to settle. Stiffness per joint is `k = E * I / l`, with `I = pi * D^4 / 64` from the petiole diameter `D`, `l` the segment length and `E` the per-Crop `petiole_modulus` (guess about 500 MPa, measured for taro petioles; no carrot data found). Damping per joint and axis is `c = 2 * zeta * sqrt(k * J)`, with `J` the inertia of the rest of the leaf about that axis and the per-Crop damping ratio `zeta` (guess 0.1 to 0.3).
- **Collision**: each petiole segment collides as a chain of 2 capsules along chords of its curve, each as thick as the petiole where it starts (M5d; it was the convex hull of the curved segment until then, see Consequences). Leaf blades are visual only; their mass goes to the last petiole link of their leaf.
- About 25 links per carrot. The main grip is the leaf bunch at the crown.

### Variant physics export

Engine-agnostic. The root crop Asset Generator writes next to each Variant's `.glb`:

- `<variant>.physics.json`: links (pose, mass, center of mass, inertia, and a collision in the link frame: the root's convex hull as vertices and faces, a petiole link's capsules as the centres of their end caps and their radius), joints (type, axes, stiffness, damping), root length and root depth, all at scale 1;
- `<variant>.articulated.glb`: the visual of each link as its own mesh, named like the link and in the link frame.

The root hull lives inside the JSON rather than as a separate mesh file; an Exporter writes the mesh file its engine needs. Capsules are given by their cap centres (MuJoCo's `fromto`); the Gazebo Exporter turns them into a pose and a length. Masses and stiffnesses come from the Variant geometry plus per-Crop material constants (densities, `petiole_modulus`, damping ratio). These are generation-time inputs, so they sit in the generator's per-Crop table next to the geometry ranges, as ranges sampled per Variant, each marked with its source or `guess`; the runtime Pull-out Curve knobs stay in the Crop YAML. Exporters only translate the file to their engine (Gazebo SDF now, MuJoCo later) and apply the Plant's scale `s` consistently: lengths by `s`, masses and joint stiffnesses by `s^3`, joint damping by `s^4`, inertias by `s^5`, spring references by `s`. Per-Plant values (Pull-out Force, scale) stay in the Manifest.

### Stability check

Per Variant, in a headless world for about 5 s of sim time at a 1 ms step:

- settling: every link slower than 1 mm/s after 2 s, no NaN;
- squeeze: box jaws closing 3 cm above the crown hold every petiole link, none tunnels out.

The step size is a knob if a Variant fails. It runs as a slow test, skipped by default. The squeeze uses the test gripper (`exporters/gazebo/gripper.py`): jaw servos limited to the grip force, 20 N per jaw by default, with friction 1 on the jaws (a guess).

### Scope

Root crops only: carrot, then beetroot and radish through the same generator. Lettuce stays static, since it is cut, not pulled. Loose soil only.

## Why

- **Realism where the policy feels it.** The policy observes low-dimensional state (gripper pose and width, wrist force, crown position and a leaf bunch estimate from separate perception), so what matters is the force on the gripper over the pull and how the leaf bunch bends and slips. Both are cheap lumped models whose parameters can be measured on real Plants and randomized per Plant.
- **Established practice.** Sim-to-real plant manipulation uses simple plant models plus randomization (PCAP: spring-jointed branches; Find the Fruit: FEM plus randomization). No learned uprooting work was found.
- **No particle soil.** DEM and MPM root pull-out studies are geotechnics, far too costly per step, and need soil parameters we cannot measure in the field.
- **A force law instead of a break.** Gazebo has no joint that breaks at a force, and a `DetachableJoint` has no force readout. Computing the force from displacement avoids both and gives a curve, not just a threshold.
- **Universal joints.** dartsim honours springs on both axes of a universal joint, but not on ball joints. A revolute joint bends in one plane only.
- **Engine-agnostic export.** Training is expected to move to MuJoCo later (spec section 12), and Gazebo must reproduce the same Plant and force law for end-to-end tests of the trained policy.
- **C++ per step.** A Python loop over gz-transport each step is too slow and its timing is not tied to the physics step.

## Not in M4

- **Crown tear-off.** The tops of a carrot detach at 212 to 243 N, against 20 to 22 N to pull it out of loosened soil (Nath et al. 2019), so in loose soil the tops never tear. In undisturbed soil (118 to 149 N) the margin is only about 1.6x; tear-off returns with compact soil, as a second force law on the crown.
- **Soil state per Pixel** (loose or compact).
- **Grip damage limit**: carrots are damaged at about 43 to 45 N of grip; only noted in the Crop YAML.
- **Angled pulls.**
- **Calibration**: every parameter is a literature value or a guess until the measurement protocol has run. M4 Plants are uncalibrated.

## Considered Options

- **Force-threshold detach** (the earlier proposal): a `DetachableJoint` that breaks once its wrench exceeds the Pull-out Force. No force-displacement shape, and the wrench is not available on a `DetachableJoint`.
- **Soil simulation** (particles, deformable terrain) or **our own simulator or soil plugin**: costly, and the parameters are not measurable.
- **Cosserat rods or FEM for foliage**: heavier, and not portable to MuJoCo Warp (flex is experimental there, plugins are unsupported).
- **Static Plants with scripted removal**: no force feedback for the manipulator.

## Consequences

- Each Variant gets a second committed export, kept fresh by tests like the `.glb`.
- The root crop generator must keep parts per leaf: today it merges them per part type.
- Removing a grouped visual with `RequestRemoveEntity` reaches a running GUI through the world state (checked in M4d), although the server's scene info keeps listing it.
- Known limit, accepted in M4e: a petiole segment collided as the convex hull of its curved shape, wider than the petiole where it bends, and the hulls stepped at the joints. Jaws sliding up the leaf bunch could wedge there and hold more than friction allows, so a weak grip sometimes still broke the soil bond.
- Changed in M5d: petiole segments collide as chains of capsules. The M5d spike (Plants of a carrot Pixel picked at once, overlapping foliage, physics only) showed mesh hull contact between neighbouring Plants to be both slow and violent: 4 Plants ran at 0.17x real time with leaf tips shoved 34 mm in 0.5 s at up to 8 cm/s under ODE, the collision detector gz-sim gives dartsim by default. One capsule per segment: 1.74x and 0.8 mm, but the chord misses the bend of a carrot petiole by up to 14.3 mm (median 5.6 mm, over the 24 carrot Variants). Two capsules per segment (`CAPSULES_PER_LINK`): 1.0x and 0.7 mm, off the petiole's centre line by at most 3.7 mm (carrot; beetroot 1.4 mm, radish 1.9 mm); the rendered petiole tube follows the same chords, so collision and visual agree. Capsules also remove the wedging: a 5 N grip lifted 0.2 m slipped on 6 of 6 carrots with the bond intact (d at most 3.3 mm, d_peak 5 mm), where the hulls had broken the bond on some. The physics export's `format_version` went from 1 to 2 with this change.
