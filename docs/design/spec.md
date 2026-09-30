# Design spec: pixel farming field generator

Status: draft, design phase. Capitalised terms (Field, Pixel, Crop, Plant, ...) are defined in [CONTEXT.md](../../CONTEXT.md). Decisions with lasting impact are recorded in [docs/adr/](../adr/). Background research is in [docs/research/prior-art.md](../research/prior-art.md).

## 1. Goal

Generate pixel farming Fields for robot simulation, realistic enough to:

1. train and test camera-based crop detection (target: the visual level of the Intrinsic AI for Industry Challenge Gazebo environment, not photorealism), and
2. let a simulated Farm-ng Amiga with a manipulator harvest Plants, including a realistic Pull-out Force.

The primary simulator is Gazebo. The tools must stay usable for other simulators and renderers (Isaac Sim, MuJoCo, Blender) later. The codebase must be easy for colleagues and students to understand, extend and iterate on.

## 2. Scope

In scope:

- Field Spec input: a hand-drawn Pixel grid or a random Field request.
- Planting Patterns inside Pixels with realistic randomness.
- An Asset Library of Crop Variants, starting with carrots.
- A Gazebo Exporter producing a static world plus a Manifest.
- Pull-out physics for harvesting (milestone M4).
- Docker packaging of the simulation stack.

Out of scope for now:

- Growth stages: all Plants are harvest-ready (with size variation).
- Weeds: to be added later as just another Crop.
- Runtime spawning of Plants (for example via a ROS 2 service): only static world generation.
- The Amiga robot model and manipulator: a separate plan (M5).
- Terrain relief (ridges, furrows): flat soil first.

## 3. Architecture

```
Field Spec (YAML)
   |  resolve: hand-drawn grid, or random grid from seed
   v
Pixel grid --> Planting Pattern (per Crop) --> Field Layout
                                                (Pixels + Plants: id, Crop, Variant, pose, scale, properties)
                                                   |
             Asset Library  <--  Asset Generators  |
             (Variants per Crop, .glb)             |
                    \                              |
                     +------> Exporter (gazebo now; blender, isaac, mujoco later)
                                   |
                                   v
                     world folder + Manifest (manifest.json)
```

Rules (see [ADR 0001](../adr/0001-simulator-agnostic-core.md)):

- The core (`src/pixelfield/core/`) has no simulator imports, uses plain dataclasses and pure functions, and is deterministic for a given seed.
- Random mode produces the same Pixel grid structure as a hand-drawn spec, so everything after resolving is shared.
- Extension points are plain dictionaries keyed by name, no plugin framework:
  - `EXPORTERS = {"gazebo": ...}` in `src/pixelfield/exporters/`
  - `GENERATORS = {"carrot": ...}` in `src/pixelfield/generators/`
- Adding a Crop means: a Crop definition YAML in `crops/` plus Variants in `assets/library/<crop>/` (from a generator or dropped in by hand).
- Adding a simulator means: one Exporter module. The core does not change.

## 4. Coordinates and units

- SI units: meters, kilograms, newtons, radians.
- Right-handed, z up, following ROS REP-103: x east, y north.
- Field origin is the south-west corner of the Field at ground level.
- The first line of a hand-drawn grid is the northernmost Pixel row, so the spec reads like a map.
- Pixel `(row 0, col 0)` is the top-left character in the spec (north-west corner of the Field).
- Example: in a 3-row Field with 0.5 m Pixels, row 0 spans y = 1.0 to 1.5 m.

## 5. Field Spec

A YAML file. `pixel_size` defaults to 0.5 m, the size used in the WUR pixel cropping trials.

Hand-drawn grid:

```yaml
pixel_size: 0.5          # meters, square Pixels
seed: 42                 # same seed gives the same Field Layout
legend:                  # one character per Crop, "." is an Empty Pixel
  C: carrot
  L: lettuce
grid: |
  C C . L
  C L C .
  . C L C
path_gap:                # optional, off when absent
  every_n_cols: 2
  width: 0.3
```

Random Field:

```yaml
pixel_size: 0.5
seed: 7
random:
  rows: 4
  cols: 6
  crops:                 # relative weights
    carrot: 2
    lettuce: 1
  empty_fraction: 0.1
  no_same_neighbour: true  # optional: no two adjacent Pixels share a Crop
```

Optional Field-wide `row_direction` (radians) overrides each Crop's default.

## 6. Crop definition

One YAML file per Crop in `crops/`. Values below are provisional starting points, to be tuned against real field data.

```yaml
name: carrot
planting:                # the Planting Pattern inside one Pixel
  row_spacing: 0.15      # meters between rows
  in_row_spacing: 0.04   # meters between Plants in a row
  margin: 0.04           # meters from Pixel edge to the outermost Plants
  row_direction: 0.0     # radians, 0 = rows run east-west
  jitter: 0.01           # meters, random offset per Plant (std dev)
  missing_rate: 0.08     # fraction of positions with no Plant (failed germination)
variation:               # sampled per Plant
  scale: [0.85, 1.15]
  yaw: [0.0, 6.283]
  hue_shift: [-0.03, 0.03]
physics:
  pull_out_force: [15.0, 26.0]   # newtons, loosened soil (see prior-art.md)
assets:
  library: assets/library/carrot
  generator: carrot      # key in GENERATORS, optional
  variants: 24
collision:               # simple shapes, the visual mesh is only for rendering
  root: capsule
  foliage: cylinder
```

## 7. Field Layout and Manifest

The Field Layout is the only thing Exporters read. It is written next to every exported world as `manifest.json` and is the ground truth for detection labels and harvest evaluation. Draft structure:

```json
{
  "format_version": 1,
  "field": {"pixel_size": 0.5, "rows": 3, "cols": 4, "seed": 42, "spec_sha256": "..."},
  "pixels": [
    {"row": 0, "col": 0, "crop": "carrot", "origin": [0.0, 1.0]}
  ],
  "plants": [
    {
      "id": "r0c0-017",
      "crop": "carrot",
      "pixel": [0, 0],
      "variant": "carrot_v07",
      "pose": {"x": 0.12, "y": 1.31, "z": 0.0, "yaw": 2.4},
      "scale": 1.04,
      "pull_out_force": 21.3
    }
  ]
}
```

Plant ids are stable for a given spec and seed, so results from different runs can be compared.

## 8. Assets

See [ADR 0003](../adr/0003-committed-asset-library.md) and [ADR 0004](../adr/0004-cropcraft-as-asset-source.md).

- Each Crop has 24 Variants (default) as `.glb` with PBR materials, committed to `assets/library/<crop>/`.
- Every Variant has a detailed visual mesh and simple collision shapes (capsule and cylinder). Convex hulls per Variant are a later option if grasping needs them.
- Carrot Variants: a tapered orange root, mostly below ground with the shoulder visible, plus a crown of divided leaves. Root length, root diameter, foliage height and leaf count vary per Variant.
- Default Asset Generator: pure Python with `trimesh`. A Blender generator may replace it for a Crop if the results look too crude, writing into the same library format.
- Non-carrot Crops and weeds: exported once from CropCraft's Blender library to `.glb`.
- Soil: a flat plane with a CC0 PBR soil texture (ambientCG or Poly Haven, 1 to 2K), committed to `assets/library/textures/`.
- Library size estimate: about 5 MB per Crop. Move to Git LFS if the library passes about 100 MB.

## 9. Rendering

See [ADR 0005](../adr/0005-dataset-rendering-separate-from-simulation.md).

- Gazebo camera sensors are tuned for realism: ogre2, VCT global illumination, PBR materials, shadows, camera noise and distortion.
- Render cameras match the real camera used for data collection (model, resolution, field of view, mounting height and angle).
- Realism check: a headless run saves images from fixed cameras (top-down and oblique) to compare against photos of real carrot Pixels.
- Later: a Blender Exporter renders the same Field Layout offline for photorealistic datasets.

## 10. Physics

- Until M4, Plants are static models.
- M4 implements Pull-out Force as proposed in [ADR 0006](../adr/0006-pull-out-via-force-threshold-detach.md).
- Target Field size: up to about 10 x 10 Pixels (thousands of Plants). Performance is measured in M2. M4 decides how to keep that many Plants cheap (for example only Plants near the robot become dynamic).

## 11. Milestones

Each milestone is done only when its check has been run and observed. Work proceeds in small chunks, each ending in something that can be checked by hand (a file to open, an image, a world in Gazebo) plus automated tests. Nothing is built ahead of the chunk that needs it.

M1 chunks:

| Chunk | Content | Check |
|---|---|---|
| M1a | Repo tooling (uv, ruff, pytest, CI) and core: Field Spec to Field Layout to Manifest, with primitive stand-in Plants | `pixelfield build` writes `manifest.json` and a top-down SVG of Plant positions; core tests pass |
| M1b | Fix local `gz`, Gazebo Exporter with soil plane and primitive Plants | The generated world opens in Gazebo, `gz sdf -k` passes |
| M1c | First Crop Asset Generator (carrot) writing Variants to the Asset Library | Variants open in Gazebo or a glTF viewer and look like the Crop |
| M1d | Exporter uses Variants; lighting (VCT GI), cameras, headless render script | Rendered images look like a real Pixel of the Crop |
| M1e | Docker image | A colleague runs the world from the image |

| # | Content | Done when |
|---|---|---|
| M0 | Design spec, ADRs, glossary, repo structure | Spec agreed, open questions resolved or deferred |
| M1 | One carrot Pixel end to end: repo tooling (uv, ruff, pytest, CI), core (Field Spec, Pixel grid, Planting Pattern, Field Layout, Manifest), carrot Asset Generator and library, Gazebo Exporter (soil, sun, VCT GI, cameras), headless render check, Docker image, fixing the local `gz` PATH conflict and installing `ros-jazzy-ros-gz` | `pixelfield build examples/carrot_pixel.yaml` creates a world, Gazebo opens it, camera images show a believable carrot Pixel, core tests pass |
| M2 | Multi-Pixel Fields, random mode, Path Gaps, performance measurement | A 10 x 10 random Field loads in Gazebo, frame rate and VRAM recorded |
| M3 | More Crops (CropCraft import, candidate lettuce and onion), iterate on looks | At least three Crops render believably side by side |
| M4 | Pull-out physics (custom gz-sim system plus `DetachableJoint`) | A test pull detaches a Plant within its Pull-out Force range |
| M5 | Amiga and manipulator integration | Separate plan |
| M6 | Blender Exporter and sim-to-real experiments | Detectors trained on each image source evaluated on real images |

Real-field image collection (our own field, possibly WUR) is planned around M2 to M3, so camera parameters can be matched early.

## 12. Resolved questions and open items

Resolved:

1. **Pixel boundaries**: soil runs continuously between Pixels; Pixels are not visibly marked.
2. **Row direction**: a default per Crop, overridable by an optional Field-wide setting. Per-Pixel overrides only if real fields need them.
3. **Random mode rules**: weights plus an optional `no_same_neighbour: true`.
4. **Path Gaps**: "every N columns, width W", off by default.
5. **Detection labels**: Gazebo segmentation and bounding-box camera sensors in M2, YOLO export first.
6. **Soil appearance**: one texture in M1, mild variation (blending 2 to 3 textures) in M3.
7. **Crops for M3**: lettuce, onion and one CropCraft import (bean) as placeholders, to be replaced by the crops of the real field when known.
8. **Performance budget**: at least 0.5x real time on the development laptop with a 10 x 10 Pixel Field and an active camera; target 1.0x or better.
9. **License**: AGPL-3.0 is intended, so that commercial users contribute back. Relicensing later needs agreement of all copyright holders, which gets harder as outside contributions accumulate.
10. **Name**: package `pixelfield`, repository AgriSim. The simulation may later also cover row crops and conventional single-crop fields; the name can be revisited then.
11. **Crop placeholder values**: the carrot values in section 6 stand until measured in the real field. Carrots are only the first Crop; nothing in the core may be carrot-specific.

Open (deferred):

1. **Real camera** on the Amiga (model, resolution, field of view, mounting height and angle). Not needed until render cameras are matched to real data; M1 uses a generic placeholder camera.
2. **Real field values** for Planting Patterns and harvest sizes, per Crop.
3. **Row crops and single-crop fields**: out of scope now. The core should not assume Pixels are small, so a large "Pixel" with one Crop or a row layout stays possible later.

## 13. Publication angle

Existing work (CropCraft) generates row-based fields for Gazebo Classic and renders its datasets in Blender. Its authors list simulators beyond Gazebo, soil variation, vegetation deformation and richer labels as future work. This project can contribute:

1. Field generation for pixel cropping, which no existing tool supports.
2. Harvestable Plants: per-Plant Pull-out Force based on literature values, and a gz-sim uprooting system. No prior Gazebo work was found.
3. A simulator-agnostic design on current Gazebo (gz-sim), with a ground-truth Manifest.
4. A sim-to-real evaluation: detectors trained on Gazebo renders, Blender renders and real images, tested on real pixel field images.

Point 4 decides the strength of the paper: without real-world validation it is a tool paper (workshop, SoftwareX, JOSS), with it a stronger conference or journal paper. The design already supports it through seeded, reproducible runs, a versioned Asset Library and the Manifest.
