---
status: accepted
---

# Dataset rendering is separate from closed-loop simulation

Camera images for training detectors should look as close to reality as possible, but Gazebo is a real-time rasterizer and cannot reach path-traced quality. So the two roles are separated: Gazebo runs the closed loop (robot, manipulator, harvesting) with its camera sensors tuned as far as reasonable (ogre2, VCT global illumination, PBR materials, camera noise), while a later Blender Exporter can render the same Field Layout offline for photorealistic datasets with exact labels from the Manifest.

## Consequences

- The Gazebo world is not the only source of training images, and its visual quality target is "good enough to close the loop", matching the level of the Intrinsic AI for Industry Challenge.
- Comparing detectors trained on Gazebo renders, Blender renders and real images becomes a natural experiment (see the paper section of the design spec).
- This only works because of ADR 0001: every renderer reads the same Field Layout.
