# Performance record

Budget (spec section 12, item 8): at least 0.5x real time on the development laptop with a 10 x 10 Pixel Field and an active camera; target 1.0x or better. Add a row whenever a change may move the numbers.

Laptop: Intel Arrow Lake iGPU plus NVIDIA RTX PRO 1000 Blackwell (8 GB), Ubuntu 24.04, Gazebo Harmonic.

## Results

RTF is averaged: simulation time elapsed over a 20 s wall-clock window after warm-up. Single `real_time_factor` readings from `/stats` jump between 0.04 and 1.0 in the same run when cameras block the simulation, so they are not used.

| Date | Commit | World | Plants / models | Camera setup | Avg RTF | VRAM (gz / GPU total) |
|---|---|---|---|---|---|---|
| 2026-10-01 | M2a, from AGENT_LOG | hand-drawn 10 x 10 carrot, server | 3,058 / 103 | as built | 1.00 (single reading) | 514 MiB total |
| 2026-10-01 | M2a, from AGENT_LOG | same, GUI on NVIDIA | 3,058 / 103 | as built | 1.00 (99.97%, GUI) | about 960 MiB total |
| 2026-10-02 | 639fa54 | `random_10x10.yaml`, server | 2,760 / 93 | as built: 2 cameras 1920 x 1080 at 2 Hz, PNG saving, VCT GI | 1.00 | 435 / 613 MiB |
| 2026-10-02 | 639fa54 | same | 2,760 / 93 | 30 Hz, PNG saving, GI | 0.07 | 435 / 613 MiB |
| 2026-10-02 | 639fa54 | same | 2,760 / 93 | 30 Hz, no saving, GI | 0.60 | 435 / 613 MiB |
| 2026-10-02 | 639fa54 | same | 2,760 / 93 | 30 Hz, no saving, GI `high_quality` and `anisotropic` off | 0.62 | not measured |
| 2026-10-02 | 639fa54 | same | 2,760 / 93 | 30 Hz, no saving, no GI | 0.66 | 609 MiB total |
| 2026-10-02 | 639fa54 | `carrot_pixel.yaml`, server | 33 / 4 | 30 Hz, no saving, GI | 0.97 | 435 / 613 MiB |
| 2026-10-16 | a1a4eff | `random_10x10.yaml`, GUI on NVIDIA | 2,760 / 93 | as built | 1.00 (99.95% or higher, GUI reading, not averaged) | 399 server + 446 GUI / 983 MiB total |
| 2026-10-16 | c2ac344 | `random_10x10.yaml`, server, driver 595.99, kernel 7.0.0-38 | 2,760 / 93 | 30 Hz, no saving, GI (re-run of the 0.60 row) | 0.37 | 435 / 546 MiB |
| 2026-10-16 | c2ac344 | same | 2,760 / 93 | OAK-D rig, pose A at the west Field edge | 0.51 | 384 / 495 MiB |
| 2026-10-16 | c2ac344 | same | 2,760 / 93 | OAK-D rig, pose A over the Field centre | 0.50 | 384 / 495 MiB |
| 2026-10-16 | c2ac344 | same | 2,760 / 93 | OAK-D rig, nadir over the Field centre | 0.50 | 384 / 495 MiB |
| 2026-10-16 | c2ac344 | same | 2,760 / 93 | OAK-D rig, nadir, no GI | 0.53 | 495 MiB total |
| 2026-10-16 | c2ac344 | same | 2,760 / 93 | OAK-D rig, nadir, sun `cast_shadows` off | 0.62 | 311 / 422 MiB |
| 2026-10-16 | c2ac344 | `carrot_pixel.yaml`, server, same system | 33 / 4 | OAK-D rig, nadir | 0.83 | 384 / 495 MiB |
| 2026-10-16 | m3b, one mesh per Variant | `random_10x10.yaml`, server, same system | 2,760 / 93 | OAK-D rig, nadir | 0.61 | 384 / 495 MiB |
| 2026-10-16 | m3b, one mesh per Variant | same | 2,760 / 93 | OAK-D rig, pose A at the west Field edge | 0.59 | 384 / 495 MiB |
| 2026-10-16 | m3b, gz-rendering 8.3.0, gz-sim 8.15.0 | `random_10x10.yaml`, server | 2,760 / 93 | 30 Hz, no saving, GI (the 0.37 row) | 0.95 | 435 / 546 MiB |
| 2026-10-16 | same | same | 2,760 / 93 | OAK-D rig, nadir | 0.96 | 384 / 495 MiB |
| 2026-10-16 | same | same | 2,760 / 93 | OAK-D rig, pose A at the west Field edge | 0.92 | 384 / 495 MiB |
| 2026-10-16 | same | `carrot_pixel.yaml`, server | 32 / 4 | OAK-D rig, nadir | 1.01 | 380 / 491 MiB |
| 2026-10-22 | 2977ae1 (M5d), driver 595.99, kernel 7.0.0-38 | `random_10x10.yaml`, server | 2,760 / 93 | OAK-D rig, nadir (re-run of the 0.96 row) | 0.96 | 818 MiB total |
| 2026-10-22 | same | same, plus the test gripper (static, jaws open, 3 cm above the crown of mid-Pixel carrot r5c4-032 under the camera): 5 Picked Plants | 2,760 / 93 | OAK-D rig, nadir | 0.21 (FAIL, budget 0.5) | 818 MiB total |
| 2026-10-22 | same, root collisions of the Plant SDFs set to 0 by hand | same, 5 Picked Plants | 2,760 / 93 | OAK-D rig, nadir | 0.64 | 818 MiB total |
| 2026-10-22 | 857951b, roots never overlap (layout) | `random_10x10.yaml`, server | 2,713 / 93 | OAK-D rig, nadir, no gripper | 0.97 | 578 MiB total |
| 2026-10-22 | same, 1 ms step | same, test gripper over the carrot nearest the camera: 5 Picked Plants | 2,713 / 93 | OAK-D rig, nadir | 0.58 | 579 MiB total |
| 2026-10-22 | same, 2 ms step | same | 2,713 / 93 | OAK-D rig, nadir | 0.97 | 579 MiB total |
| 2026-10-22 | same, 4 ms step | same | 2,713 / 93 | OAK-D rig, nadir | 1.00 | 579 MiB total |

Build time of `random_10x10.yaml`: 0.12 s, output 8.8 MB.

Build time and `out/` size with the Plant SDFs written at build (M5c, ADR 0010), `pixelfield build`, wall clock:

| Date | Field | Plants | Build | `out/` | of which `plants/` |
|---|---|---|---|---|---|
| 2026-10-20 | `amiga_10x10.yaml` before M5c (main) | 2,760 | 0.15 s | 19 MB | none |
| 2026-10-20 | `amiga_10x10.yaml` | 2,760 | 4.3 s | 152 MB | 129 MB of SDFs |
| 2026-10-20 | `random_10x10.yaml` | 2,760 | 4.2 s | 152 MB | 129 MB of SDFs |
| 2026-10-20 | 10 x 10 carrot Field (hand-drawn, M2a) | 3,058 | 4.7 s | 165 MB | 142 MB of SDFs |

ADR 0010 estimated about 10 s and 100 MB: the build is faster, the files 1.4x larger (46 KB per Plant on average; carrot v00 alone was 34 KB). Shared hull meshes and glb files add about 1 MB.

Reading the numbers:

- As built (2 Hz placeholder cameras) the 10 x 10 Field runs at 1.0x.
- With two full-HD cameras at 30 Hz it runs at 0.6x: above the 0.5x budget, below the 1.0x target. The simulation waits for the cameras, so each camera delivers about 30 x RTF frames per second.
- VCT GI costs about 10% (0.60 vs 0.66); lowering its quality settings barely helps.
- Saving every frame as PNG drops it to 0.07x; saving is for `pixelfield render` only.
- CiVCT (GI only around the camera) is not available: Harmonic's Sensors system logs `GI CI VCT is not supported`.

### OAK-D rig (M3a, 2026-10-16)

The robot camera is an OAK-D Pro. The rig stands in for it with one RGB `camera` (1920 x 1080, HFOV 66 degrees, 30 Hz) and one `depth_camera` (640 x 400, HFOV 80 degrees, 30 Hz, a single depth sensor instead of rendering the stereo pair), 1.0 m high. Pose A: pitched 45 degrees down, looking east along the rows (the planned mount at the Amiga front). Nadir: looking straight down (the current mount).

- The same world file that gave 0.60x on 2026-10-02 now gives 0.37x. Between the two runs the NVIDIA driver went from 595.84 to 595.99 and the kernel from 7.0.0-34 to 7.0.0-38; the cause is not isolated. Compare only rows measured on the same system.
- The OAK-D rig runs the 10 x 10 Field at 0.50x, right at the budget, and 0.83x on a single Pixel. The pose does not matter: the west edge view along 6 m of rows and the nadir view of about one Pixel give the same RTF.
- The cost comes from Plants outside the view. The sun's shadow pass draws every Plant in the Field (shadows off: 0.62x); the rest is per-object work.
- During the nadir run the GPU sits at about 16% utilization at a low clock, while one gz server thread runs at 100% of a CPU core. Rendering is CPU-bound on the number of render items (each carrot Variant has 3 meshes with their own material, so about 8,300 items), not on triangles.
- Conclusion: triangle LOD would not help and is not part of M3. Levers that do reduce CPU work: fewer meshes per Variant (one mesh, one material), a shorter shadow distance, or merging a Pixel's Plants into one render mesh.
- m3b merged each Variant into one mesh with one material (ADR 0008): 3x fewer render items, 0.50x to 0.61x (nadir) and 0.51x to 0.59x (pose A at the edge), renders unchanged.
- Upgrading gz-rendering 8.2.3 to 8.3.0 and gz-sim 8.14.0 to 8.15.0 lifts the 10 x 10 Field with the OAK-D rig to 0.92x to 0.96x, with cameras delivering 28 to 30 frames per second; the single Pixel reaches 1.0x. gz-rendering 8.3.0 stops pre-rendering every visual's children twice per frame (gz-rendering PR #1309) and turns off Ogre worker threads that occupied CPU cores (PR #1307); gz-sim 8.15.0 speeds up entity lookups. Keep at least these versions.
- With this, per-Pixel merging or an active region (only nearby Plants detailed) is not needed for a 10 x 10 Field. Revisit for larger Fields or for M4, where only the grasped Plant needs dynamics.

### Active Region (M5d, 2026-10-22)

The perf check is a scenario (ADR 0010): the test gripper grasping a mid-Pixel carrot in the 10 x 10 Field with the OAK-D rig at nadir. The gripper stands static at its grasp pose, jaws open; the Active Region picks the 5 Plants around it.

- With picks the cost is physics, not rendering. Without Sensors, unthrottled: the empty Field runs at 37x, the same 5 Plants picked by id without the gripper at 0.24x, with the gripper 0.26x.
- Each of the 5 Plants alone runs at 5.6 to 8.6x. Together, two of them (r5c4-029 and r5c4-030, crowns 2.3 cm apart, crown radii 2.0 and 2.1 cm) have overlapping roots. Both roots are welded to their anchors, so the contact can never resolve: a leaf of r5c4-030 keeps moving at up to 15 cm/s and the pair runs at 0.31x; with the two root collisions off it runs at 2.6x.
- Overlapping roots are common: in `random_10x10` 654 pairs of root crop Plants are closer than the sum of their crown radii, 1,231 of 2,760 Plants (in-row spacing 4 cm, jitter 1 cm, crown radii 1.2 to 2.2 cm).
- With every root's collision off, the scenario runs at 0.64x, and the full carrot Pixel spike (32 Plants, physics only) at 0.089x instead of 0.036x.
- Fix: the Planting Pattern keeps roots from overlapping (spec section 6); touching is allowed. Switching the root contact off instead was rejected: overlapping roots are unphysical, and with root-root contact off (collide bits per root) a carrot's leaves start inside its neighbour's root, which aborted gz (ODE AABB assertion) at 1 ms.
- Physics step sweep with the overlapping layout (scenario at 1, 2, 4 ms: 0.23x, 0.42x, 0.72x; settle, squeeze, pull and grip checks at each): everything held up to 4 ms except the strongest beetroot's 45.8 N grip slipping at 4 ms; the scripted pull's stiff lift force overshoots from 4 ms, so it runs at its own 1 ms step. Weak 20 N grips on 12 sparse Plants peak within 1 to 3 N of each other at 1 and 2 ms, except one beetroot whose leaf bunch wedges (40.6 N at 1 ms, 60.1 N at 2 ms); wedging past friction happens at 1 ms too.
- With the layout fixed, 2 ms reaches the camera ceiling, so Field worlds use 2 ms (`gazebo.PHYSICS_STEP`).

### Amiga from amiga_ros2 (M5e, 2026-10-23)

The M5e check: in the `amiga-ros:jazzy` image (gz-sim 8.15.0, gz-rendering 8.2.3; `/dev/dri` passed in, EGL fails on the NVIDIA node), pixelfield installed from tag `v0.5.0` as in the README, `amiga_10x10.yaml` built, amiga_ros2's `gazebo.launch.py` with `gz_args:="-s -r --headless-rendering <world.sdf>"` (server only, cameras not subscribed). The spawn pose needs a copy of the launch file with `-x 2.024 -y 1.5 -Y 1.5707963` (wheels in the first two Path Gaps, heading north); the unchanged launch spawns at the Field origin. RTF from single `/stats` readings, which stay steady here since no camera blocks the simulation; sim time kept pace with them.

| Commit | Scenario | Picked Plants | RTF |
|---|---|---|---|
| a2c6a96 | Field without the pull-out system, unchanged launch (Amiga at the origin) | none | 1.00 |
| a2c6a96 | Unchanged launch: the Amiga spawns at the origin, one wheel and fork on the carrots of r8c0 and r8c1 | 27 to 28, crushed, never unpicked | 0.003 |
| a2c6a96 | Spawned in the gaps, standing 20 s, then driving north at 0.3 m/s for 10 m (twice) | 1 standing, 3 while driving, all 3 unpicked | 0.95 to 1.03 |
| 6616cd5 (per-link box) | Spawned in the gaps, standing | 144 | 0.001 to 0.01 |
| a2c6a96 | Spawned in the gaps, then moved 20 cm east by `set_pose` and back | 33, of which 28 unpicked 24 s later | about 0.2, back towards 1.0 as they unpick |

Wheel rig over a carrot row (robot interface 2, `carrot_pixel.yaml`, physics only, unthrottled, one Pixel): a 7 kg wheel under a 30 kg load on a free suspension, driven at 0.3 m/s along the middle row. RTF is the average over the run.

| Wheel collide bitmask | Picked Plants | Wheel rides up | RTF |
|---|---|---|---|
| default (0xFFFF) | 10 | 2.3 cm | 0.09 average, 0.03 in the row |
| 0x1 (soil only) | none | 0 | 2.1 |

Spike variants on robot interface 1 bits (same rig): leaves kept off the soil, wheel still touching Plants: 0.07 to 0.1x in the row; wheel touching only soil and leaves, not roots: 0.03x; wheel touching nothing but soil, 10 Picked Plants with their leaves on the soil: 0.23x, with leaves off the soil: about 1x. The cost is the heavy wheel pressing gram-light leaves into the soil; Picked Plants alone cost too, so a soil-only wheel that picks none is the fast case. No explosion was seen in 2 to 4 s of sim with this rig; the user saw carrots fly and the Amiga vanish while driving into the carrots, not reproduced yet.

- A robot must spawn in the Path Gaps or in the Border, not on Plants: a wheel spawned inside anchored roots crushes them, and bent Plants stay picked.
- In every launch, the empty world too, the `joint_state_broadcaster` spawner timed out ("Switch controller timed out after 5 seconds") and only `lite6_traj_controller` was active; driving does not depend on it (gz DiffDrive). An amiga_ros2 matter.

Rig worlds are hand-edited copies of `world.sdf` (camera models replaced by one model with both sensors). Subscribe to both `/oakd/rgb` and `/oakd/depth`.

## How to measure

Run from a shell where `GZ_CONFIG_PATH` and the EGL vendor are set (CLAUDE.md, known issues).

```bash
uv run pixelfield build examples/random_10x10.yaml        # build time from the shell, e.g. /usr/bin/time
cd out/random_10x10
gz sim -s -r --headless-rendering world.sdf &             # server only
gz topic -e -t /camera/top > /dev/null &                  # cameras without a subscriber may not render
gz topic -e -t /camera/oblique > /dev/null &
sleep 30                                                  # warm-up
gz topic -e -n 1 -t /world/pixelfield/stats               # note sim_time, wait 20 s, read again:
                                                          # avg RTF = sim time elapsed / 20 s
gz topic -f -t /camera/oblique                            # camera rate per wall second
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
nvidia-smi --query-gpu=memory.used --format=csv,noheader
```

Camera variants are copies of `world.sdf` in `out/`, edited by hand: `<update_rate>` 2 to 30, `<save enabled="false">`, and the `<global_illumination>` block removed. Stop gz from a script file, not with `pkill -f "gz sim"` typed into a shell whose own command line contains that text.

GUI: `gz sim world.sdf` with the PRIME offload `gz` function from `~/.bashrc`, press Play, read RTF in the bottom-right corner, `nvidia-smi` for VRAM.
