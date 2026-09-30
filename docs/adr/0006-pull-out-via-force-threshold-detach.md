---
status: proposed
---

# Plant pull-out via a force-threshold detach

Harvesting must require a realistic force to pull a Plant out. Gazebo has no joint that breaks at a force threshold, and simulating soil is out of reach. The planned approach: each Plant is held to the ground by a joint managed by the gz-sim `DetachableJoint` system, and a small custom gz-sim system reads the joint wrench and publishes on the detach topic once the pull exceeds that Plant's Pull-out Force. Pull-out Force is drawn per Plant from the Crop's range (for carrots about 15 to 26 N in loosened soil, up to 140 N in compact soil) and stored in the Field Layout, so other simulators can implement the same behavior their own way.

Status is `proposed` until milestone M4 settles the details (for example whether a spring or friction phase before the detach is needed, and how to keep thousands of jointed Plants cheap).

## Considered Options

- **Soil simulation (particles, deformable terrain).** Far too expensive for fields of thousands of Plants.
- **Plants as static models with scripted removal.** Cheap, but no force feedback for the manipulator, which defeats the purpose.
