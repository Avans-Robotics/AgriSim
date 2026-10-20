---
status: accepted
---

# Target Gazebo Harmonic with ROS 2 Jazzy, distributed via Docker

The target stack is Gazebo Harmonic (gz-sim 8) with ROS 2 Jazzy: the officially recommended pairing, LTS until 2029, and already installed on the main development machine. Development happens natively; a Docker image with the same stack (plus `ros_gz`, GPU and X11 support) is the supported way for colleagues and students to run the simulation. Generating a Field needs no Docker, since the core is plain Python.

Amended in M5 by [ADR 0009](0009-robot-free-world-provider.md): pixelfield itself needs no ROS. Running a Field with a robot happens in the robot repository's image, which installs pixelfield; a pixelfield image, if built, needs only Gazebo.

## Considered Options

- **Gazebo Jetty with ROS 2 Lyrical.** Newest LTS (until 2031), but requires a reinstall and gains nothing needed now. Because of ADR 0001 only the Gazebo Exporter would need to change when upgrading.
- **Docker-only development.** Slower iteration on visuals. Docker is a packaging choice, not a stack choice, so it is added on top of the native stack instead.
- **Gazebo Classic.** End of life; rejected even though some prior art (CropCraft) targets it.
