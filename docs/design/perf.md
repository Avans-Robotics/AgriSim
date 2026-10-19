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

Build time of `random_10x10.yaml`: 0.12 s, output 8.8 MB.

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
