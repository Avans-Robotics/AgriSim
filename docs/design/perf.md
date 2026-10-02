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
| pending | 639fa54 | `random_10x10.yaml`, GUI on NVIDIA | 2,760 / 93 | as built | | |

Build time of `random_10x10.yaml`: 0.12 s, output 8.8 MB.

Reading the numbers:

- As built (2 Hz placeholder cameras) the 10 x 10 Field runs at 1.0x.
- With two full-HD cameras at 30 Hz it runs at 0.6x: above the 0.5x budget, below the 1.0x target. The simulation waits for the cameras, so each camera delivers about 30 x RTF frames per second.
- VCT GI costs about 10% (0.60 vs 0.66); lowering its quality settings barely helps. The cost is rendering 2,760 detailed Plants twice per frame step.
- Saving every frame as PNG drops it to 0.07x; saving is for `pixelfield render` only.
- CiVCT (GI only around the camera) is not available: Harmonic's Sensors system logs `GI CI VCT is not supported`.

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
