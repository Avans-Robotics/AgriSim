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
- `ros-jazzy-ros-gz` is not installed yet; deferred until a chunk needs ROS topics.

## Commands

- Install: `uv sync`
- Build a world: `uv run pixelfield build examples/carrot_pixel.yaml` (writes `out/carrot_pixel/`: manifest.json, field.svg, world.sdf, meshes/, textures/)
- Open it: `gz sim out/carrot_pixel/world.sdf`
- Render camera images headless: `uv run pixelfield render out/carrot_pixel/world.sdf` (writes `renders/top.png`, `renders/oblique.png`, about 12 s)
- Regenerate carrot Variants: `uv run pixelfield generate carrot` (needs `uv sync --extra generate` or the dev group; preview: `gz sim out/carrot_variants/world.sdf`)
- Tests: `uv run pytest`
- Lint: `uv run ruff check . && uv run ruff format --check .`
- Validate SDF: `gz sdf -k <world.sdf>`
