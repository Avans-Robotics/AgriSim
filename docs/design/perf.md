# Performance record

Budget (spec section 12, item 8): at least 0.5x real time on the development laptop with a 10 x 10 Pixel Field and an active camera; target 1.0x or better. Add a row whenever a change may move the numbers.

Laptop: Intel Arrow Lake iGPU plus NVIDIA RTX PRO 1000 Blackwell (8 GB), Ubuntu 24.04, Gazebo Harmonic.

## Results

| Date | Commit | World | Plants / models | Camera setup | RTF | Camera rate (wall) | VRAM (gz / GPU total) |
|---|---|---|---|---|---|---|---|
| 2026-10-01 | M2a, from AGENT_LOG | hand-drawn 10 x 10 carrot | 3,058 / 103 | as built, server | 1.00 | not measured | 514 MiB total |
| 2026-10-01 | M2a, from AGENT_LOG | same, GUI on NVIDIA | 3,058 / 103 | as built | 1.00 (99.97%) | not measured | about 960 MiB total |
| 2026-10-02 | 639fa54 | `random_10x10.yaml`, server | 2,760 / 93 | as built: 2 cameras at 2 Hz, PNG saving, VCT GI | 1.00 | 2.0 Hz | 435 / 613 MiB |
| 2026-10-02 | 639fa54 | same, cameras at 30 Hz | 2,760 / 93 | 30 Hz, PNG saving, GI | 0.002 | 2.2 Hz | 435 / 613 MiB |
| 2026-10-02 | 639fa54 | same | 2,760 / 93 | 30 Hz, no saving, GI | 0.05 | 16.8 Hz | 435 / 613 MiB |
| 2026-10-02 | 639fa54 | same | 2,760 / 93 | 30 Hz, no saving, no GI | 1.00 | 18.9 Hz | 609 MiB total |
| 2026-10-02 | 639fa54 | `carrot_pixel.yaml`, server | 33 / 4 | 30 Hz, no saving, GI | 1.00 | 27.5 Hz | 435 / 613 MiB |
| pending | 639fa54 | `random_10x10.yaml`, GUI on NVIDIA | 2,760 / 93 | as built | | | |

Build time of `random_10x10.yaml`: 0.12 s, output 8.8 MB.

Reading the numbers:

- The world as built meets the budget, but only because its placeholder cameras run at 2 Hz.
- At a robot-like 30 Hz, VCT GI is the cost, and it grows with the Field: the single Pixel keeps 1.0x with GI, 10 x 10 drops to 0.05x. Without GI, 10 x 10 stays at 1.0x.
- Saving every frame as PNG costs another factor of about 20; saving is for `pixelfield render`, not for a robot camera.
- Unexplained: with GI at 30 Hz the camera publishes 16.8 frames per wall second while RTF is 0.05, which do not fit together. Re-check before relying on that row.
- Without GI, the sensor drops frames (18.9 of 30 Hz) instead of slowing the simulation.

## How to measure

Run from a shell where `GZ_CONFIG_PATH` and the EGL vendor are set (CLAUDE.md, known issues).

```bash
uv run pixelfield build examples/random_10x10.yaml        # build time from the shell, e.g. /usr/bin/time
cd out/random_10x10
gz sim -s -r --headless-rendering world.sdf &             # server only
gz topic -e -t /camera/top > /dev/null &                  # cameras without a subscriber may not render
gz topic -e -t /camera/oblique > /dev/null &
sleep 40                                                  # warm-up
gz topic -e -n 1 -t /world/pixelfield/stats | grep real_time_factor   # take three readings
gz topic -f -t /camera/oblique                            # camera rate per wall second
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
nvidia-smi --query-gpu=memory.used --format=csv,noheader
```

Camera variants are copies of `world.sdf` in `out/`, edited by hand: `<update_rate>` 2 to 30, `<save enabled="false">`, and the `<global_illumination>` block removed. Stop gz from a script file, not with `pkill -f "gz sim"` typed into a shell whose own command line contains that text.

GUI: `gz sim world.sdf` with the PRIME offload `gz` function from `~/.bashrc`, press Play, read RTF in the bottom-right corner, `nvidia-smi` for VRAM.
