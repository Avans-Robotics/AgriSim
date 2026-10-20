---
status: accepted
---

# pixelfield is a robot-free world provider

pixelfield generates Fields and the Plant physics in them; it holds no robot. A robot (the Farm-ng Amiga with a UFactory Lite 6 arm and Gripper Lite, or any other) lives in its own repository, which assembles its description, controllers and ROS 2 bringup for both the real robot and simulation, and launches a pixelfield world with its robot spawned into it. pixelfield has no ROS dependency: everything it offers is gz-native and documented as the robot interface (spec section 14).

Layers, each depending only on the ones below:

```
harvest task layer (behaviour, perception, policy, end-to-end tests)
   |  generic interfaces: a MoveIt planning group, a gripper command, a TCP frame, Twist,
   |  pixelfield topics bridged to ROS 2
   v
robot repo (amiga_ros2): one concrete robot, real and simulated
   |  assembly description, controllers, MoveIt, Docker image, ros_gz_bridge config,
   |  sim launch that takes any world
   +--> amiga_description: the bare Amiga base and its Gazebo drive
   +--> vendor descriptions: xarm_description (Lite 6, Gripper Lite), OAK-D macro
   +--> pixelfield (runtime only): world.sdf, Manifest, gz systems
```

## Decision

- No robot model, robot launch file or ROS package in this repository. The only robot-specific content allowed is data, for example an example Field Spec whose Path Gaps fit a given wheel track.
- The robot interface is gz-native: a fixed world name `pixelfield`, the pick service, the pull-out state topic, the Manifest, `GZ_SIM_SYSTEM_PLUGIN_PATH` for the systems, and the frame conventions. It carries a version number, so a breaking change is visible to robot repos.
- Two worlds on one machine are separated with `GZ_PARTITION`, as for any gz world, not with per-Field world names.
- A robot repo gets pixelfield by cloning a tagged release in its Docker image, installing the Python package and building the gz systems against its own gz-sim. No PyPI or Debian package while one robot repo consumes it.
- The robot repo owns the ROS 2 control stack, the `ros_gz_bridge` configuration, gripper and wheel physics (friction, `WheelSlip`) and oracle perception from the Manifest.

## Why

- **Common practice.** World and robot are separate in ROS 2 simulation stacks: `ur_simulation_gz` takes a `world_file`, Clearpath's simulator a `world`, the TurtleBot3 and Nav2 demos a world argument. A world generator that knows about robots is rare.
- **One robot description.** The simulated robot must load the same description and controllers as the real one, or sim results do not transfer. A copy in pixelfield would drift from the robot repo.
- **ROS stays out of a uv project.** Robot descriptions need xacro, ros2_control parameters and controller files. Pulling them in would add colcon and Jazzy to pixelfield for what is a few lines of bridge configuration in the robot repo.
- **Any robot.** Students with another robot reuse the Fields unchanged; changing the arm, camera or base is a change in the robot repo only.

## Considered Options

- **Robots inside pixelfield.** A second copy of the robot that drifts, and ROS inside pixelfield.
- **Optional robots shipped with pixelfield.** The same, multiplied by each robot.
- **A Field Spec key pointing at a robot description.** pixelfield would have to run xacro and inject ros2_control plugins into the world, so it would depend on ROS.
- **A small ROS 2 package in pixelfield** (bridge config, Manifest publisher, pick wrapper). Pulls colcon into pixelfield for little code; move the bridge into a shared package only if a second robot repo needs the same one.
- **Per-Field world names.** Every bridge and spawn command would need the name as an argument, for nothing `GZ_PARTITION` does not already give.

## Consequences

- The M5 milestone in this repository covers only what the world provider needs (spec section 11); driving, the arm and harvesting with the real robot model are planned in the robot repo.
- End-to-end harvest tests live in the robot repo. pixelfield's own tests stay robot-free, with the M4e test gripper as the stand-in robot.
- The pixelfield Docker image (ADR 0002) stays deferred: the robot repo's image is the image that runs Fields with a robot.
- Manifest library paths must resolve without running from the repository root, so an installed pixelfield works inside a robot image.
