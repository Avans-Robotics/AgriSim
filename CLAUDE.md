# pixelfield

Pixel farming field generator for robot simulation. Gazebo first, simulator-agnostic core.

## Read first

- `docs/design/spec.md`: goals, architecture, formats, milestones, open questions.
- `CONTEXT.md`: glossary. Use its terms exactly (Field, Pixel, Crop, Plant, Planting Pattern, Field Spec, Field Layout, Manifest, Asset Library, Variant, Asset Generator, Exporter).
- `docs/adr/`: accepted decisions. Do not reverse one without discussing it; record new hard-to-reverse decisions as a new ADR.

## Architecture rules

- `src/pixelfield/core/` never imports simulator or renderer code. It is deterministic for a given seed.
- Simulator-specific code lives only in `src/pixelfield/exporters/<name>/`.
- Extension points are plain dicts keyed by name (`EXPORTERS`, `GENERATORS`). No plugin frameworks.
- Plants reuse Variants from `assets/library/`; never generate a unique mesh per Plant.
- Units SI, z up, x east, y north, Field origin at the south-west corner.

## Workflow

- Build in small chunks (see the M1 chunk table in the spec), each ending in something checkable by hand plus tests.
- One branch per chunk from main (`m1a-core`, `m1b-gazebo`, ...). Merging to main is done by the maintainer after review.

## Environment

- Ubuntu 24.04, Python 3.12, ROS 2 Jazzy, Gazebo Harmonic (gz-sim 8).
- GPU: NVIDIA RTX PRO 1000 Blackwell, 8 GB VRAM. Watch VRAM with large Fields.
- Known issue: sourcing ROS Jazzy sets `GZ_CONFIG_PATH` to `/opt/ros/jazzy/opt/sdformat_vendor/share/gz` only, so `gz` lists just `sdf` and `gz sim` is missing (PATH is not the cause; both `gz` binaries behave the same). Fix, after `source /opt/ros/jazzy/setup.bash` in `~/.bashrc`: `export GZ_CONFIG_PATH="$GZ_CONFIG_PATH:/usr/share/gz"`.
- Known issue: any newer gz-msgs (e.g. `libgz-msgs12`) installed next to Harmonic puts a second `.gz_desc` in `/usr/share/gz/protos/`, and every gz program prints hundreds of `libprotobuf ERROR ... File already exists in database`. `GZ_DESCRIPTOR_PATH` does not help (it adds, never replaces). Keep only Harmonic's gz-msgs10 installed.
- Known issue: `libEGL warning: egl: failed to create dri2 screen` comes from Mesa probing the NVIDIA GPU. Fix: `export __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json`.
- Known issue: hybrid graphics (Intel iGPU + NVIDIA, PRIME on-demand), so the gz GUI renders on Intel by default (nvidia-smi shows about 100 MiB with gz open). Fix in `~/.bashrc`, gz only: `gz() { __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia command gz "$@"; }`. Headless rendering (`pixelfield render`) already uses NVIDIA through the EGL setting above.
- Known issue: after an NVIDIA driver upgrade (apt or unattended-upgrades), the new userspace libraries no longer match the loaded kernel module until a reboot: `nvidia-smi` fails with `Failed to initialize NVML: Driver/library version mismatch` and GPU rendering breaks. Fix: reboot. Perf numbers can also shift after a driver or kernel upgrade, so re-measure a known row before comparing with older rows in `docs/design/perf.md`.
- Keep gz-rendering 8.3.0 or newer and gz-sim 8.15.0 or newer: with 8.2.3 and 8.14.0 the 10 x 10 Field with a 30 Hz camera ran at 0.6x instead of about 0.95x (`docs/design/perf.md`).
- Known issue: OpenBLAS picks its matrix kernels per CPU (AVX512 kernels on newer CPUs, for example some GitHub runners), which changes the last bits of numpy matrix products and so the generated Variants. `pixelfield/__init__.py` pins `OPENBLAS_CORETYPE=Haswell` before numpy loads; a script that imports numpy before `pixelfield` must set it itself, or the committed library check fails on such CPUs.
- pixelfield needs no ROS (ADR 0009): robot repositories (for example `amiga_ros2`) bring ROS 2, `ros_gz` and the robot, and load pixelfield worlds.

## Commands

- Install: `uv sync`
- Build a world: `uv run pixelfield build examples/carrot_pixel.yaml` (writes `out/carrot_pixel/`: manifest.json, field.svg, world.sdf, meshes/, textures/)
- Open it: `gz sim out/carrot_pixel/world.sdf`
- Render camera images headless: `uv run pixelfield render out/carrot_pixel/world.sdf` (writes `renders/top.png`, `renders/oblique.png`, about 12 s)
- Regenerate a Crop's Variants: `uv run pixelfield generate <crop>` for carrot, beetroot, radish or lettuce (needs `uv sync --extra generate` or the dev group; preview: `gz sim out/<crop>_variants/world.sdf`). Rebuild worlds afterwards; a test fails if the committed library no longer matches its generator.
- Rebake the soil tiles: `uv run python -m pixelfield.generators.soil` (writes `assets/library/textures/soil_tiles/`, about 7 s)
- All four M3 Crops side by side: `uv run pixelfield build examples/m3_crops.yaml`
- Settle check of an articulated root crop Variant, headless (about 4 s each, writes `out/settle_<variant>/world.sdf` to open in `gz sim`): `uv run pixelfield settle assets/library/carrot/carrot_harvest_v00`
- Build the C++ pull-out system (about 5 s; Field worlds load it from `GZ_SIM_SYSTEM_PLUGIN_PATH`, without it gz logs that the plugin is missing): `cmake -S src/pixelfield/exporters/gazebo/systems -B build/systems && cmake --build build/systems`, then `export GZ_SIM_SYSTEM_PLUGIN_PATH=$PWD/build/systems` before `gz sim`
- Pick a Plant in a running Field world (spawns it articulated, anchored to its Pull-out Curve): `uv run pixelfield pick out/carrot_pixel r0c0-000`
- Scripted pull of a Plant, headless (about 6 s, writes `out/carrot_pixel/picks/<plant id>/pull.csv`): `uv run pixelfield pull out/carrot_pixel r0c0-000`
- Pull a Plant by its leaf bunch with the test gripper, headless (about 8 s, writes `out/carrot_pixel/picks/<plant id>/grip.csv` with the wrist force): `uv run pixelfield grip out/carrot_pixel r0c0-000`; a weak grip that slips: `--force 5 --lift 0.06`
- Squeeze check of a root crop Variant, headless (about 3.5 s): `uv run pixelfield squeeze assets/library/carrot/carrot_harvest_v00`
- Tests: `uv run pytest` (the scripted pull and gripper pull tests are skipped until the pull-out system is built); the settle check of all 72 root crop Variants (about 5 minutes): `PIXELFIELD_SLOW=1 uv run pytest -k settles`; their squeeze check (about 4 minutes): `PIXELFIELD_SLOW=1 uv run pytest -k squeezed`
- Lint: `uv run ruff check . && uv run ruff format --check .`
- Validate SDF: `gz sdf -k <world.sdf>`
