---
status: proposed
---

# Plant pull-out via a force-threshold detach

Harvesting must require a realistic force to pull a Plant out. Gazebo has no joint that breaks at a force threshold, and simulating soil is out of reach. The planned approach: each Plant is held to the ground by a joint managed by the gz-sim `DetachableJoint` system, and a small custom gz-sim system reads the joint wrench and publishes on the detach topic once the pull exceeds that Plant's Pull-out Force. Pull-out Force is drawn per Plant from the Crop's range (for carrots about 15 to 26 N in loosened soil, up to 140 N in compact soil) and stored in the Field Layout, so other simulators can implement the same behavior their own way.

Status is `proposed` until milestone M4 settles the details (for example whether a spring or friction phase before the detach is needed, and how to keep thousands of jointed Plants cheap). Gazebo groups Plants per Pixel (ADR 0007), so a picked Plant must first be spawned as its own model and its grouped visual removed by the custom system.

## Candidates for M4

Not decided; inputs for the M4 grill. Sources in [prior-art.md](../research/prior-art.md) (plant physics, soil).

- **Precedent.** OrchardBench holds apples on tethers that detach at literature pull forces, the same pattern as this ADR. No uprooting simulation was found anywhere.
- **Leaves as a pseudo-rigid-body chain.** 3 to 5 rigid links joined by revolute joints with `<spring_stiffness>` and `<damping>` in plain SDF, built by the Asset Generator from the Variant geometry. Validated in the field for blueberry canes (MuJoCo). Gives the gripper real contact and bending without a plugin. Cosserat rods (Gazebo Plants, code on request) and FEM (Isaac) are heavier alternatives.
- **Spring phase before the detach.** The root yields a few millimetres under load before breaking free, so a force controller feels something realistic. No source yet for the slip distance.
- **Soil state per Pixel** (loosened or compact) selects the Pull-out Force range from the Crop definition (carrot about 25 N loosened, 140 N compact).
- **Grip damage limit.** Carrots damage at about 43 to 45 N; exceeding it could flag the pick as damaged.
- **Stability and contact check per Variant.** Spawn the Plant alone, check the spring chain stays stable under gravity and a gripper does not pass through thin links. Gazebo contact with thin compliant links can jitter or tunnel; test this first.

## Considered Options

- **Soil simulation (particles, deformable terrain).** Far too expensive for fields of thousands of Plants.
- **Plants as static models with scripted removal.** Cheap, but no force feedback for the manipulator, which defeats the purpose.
