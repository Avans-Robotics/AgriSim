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
- Known issue: the ROS-vendored `gz` in `/opt/ros/jazzy/opt/gz_tools_vendor/bin` shadows the system `gz`, so `gz sim` fails until PATH is fixed. `ros-jazzy-ros-gz` is not installed yet.

## Commands (planned, from milestone M1)

- Install: `uv sync`
- Build a world: `uv run pixelfield build examples/carrot_pixel.yaml`
- Tests: `uv run pytest`
- Lint: `uv run ruff check . && uv run ruff format --check .`
- Validate SDF: `gz sdf -k <world.sdf>`
