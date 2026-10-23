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
- Runtime spawning of new Plants: only static world generation. Existing root crop Plants become Picked Plants at runtime (M4, and the Active Region in M5).
- Robot models, controllers and ROS 2: they live in robot repositories that load pixelfield worlds ([ADR 0009](../adr/0009-robot-free-world-provider.md), section 14).
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
             (Variants per Crop, .glb              |
              + physics export from M4)            |
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
border: 0.5              # optional, meters of textured soil around the Field
```

A Path Gap of `width` meters follows every `every_n_cols` Pixel columns, only between column groups (never at the west or east edge). Pixels stay whole and the columns east of a gap shift east, so the Field gets wider; the soil covers the gaps. Path Gaps also work with a random Field.

For a robot whose wheels run in the Path Gaps, the gap centres are `every_n_cols * pixel_size + width` apart, so `width = wheel_track - every_n_cols * pixel_size`. With 0.5 m Pixels the Amiga's 1.524 m wheel track needs `every_n_cols: 2, width: 0.524` (`examples/amiga_10x10.yaml`); the outer wheels run on the Border. The Manifest lists each gap's x range, so a robot repo does not redo this arithmetic.

The Border (default 0.5 m) is textured soil around the Field, room for a robot to drive in and turn; a Field meant for driving uses for example `border: 2.0`. Beyond it the ground continues as an invisible plane, so a robot never falls off the world.

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

Random mode details:

- `empty_fraction` is exact: `round(empty_fraction * rows * cols)` Pixels are Empty, the rest are drawn by weight.
- `no_same_neighbour` compares Pixels that share an edge; Empty Pixels never clash. It skews the weights (with two Crops the Field becomes close to a checkerboard). If no grid satisfies it, building fails with an error.
- The grid is drawn from its own random stream, so a hand-drawn copy of a random grid gives the same Plants.

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
  pull_out_curve:                # M4, ADR 0006
    d_peak: 0.005                # meters of root travel to the peak, guess
    residual_fraction: 0.3       # force right after the peak, fraction of the peak, guess
    pull_out_damping: 0.0        # N s/m, speed effect, off until measured
assets:
  library: assets/library/carrot
  generator: carrot      # key in GENERATORS, optional
  variants: 24
  stage: harvest         # growth stage slot in Variant names, optional (ADR 0008)
```

## 7. Field Layout and Manifest

The Field Layout is the only thing Exporters read. It is written next to every exported world as `manifest.json` and is the ground truth for detection labels and harvest evaluation. Draft structure:

```json
{
  "format_version": 1,
  "robot_interface": 1,
  "field": {"pixel_size": 0.5, "rows": 3, "cols": 4, "width": 2.3, "depth": 1.5,
            "path_gap": {"every_n_cols": 2, "width": 0.3}, "path_gaps": [[1.0, 1.3]],
            "border": 0.5, "seed": 42, "spec_sha256": "..."},
  "crops": {
    "carrot": {"library": "assets/library/carrot",
               "pull_out_curve": {"d_peak": 0.005, "residual_fraction": 0.3, "pull_out_damping": 0.0}}
  },
  "pixels": [
    {"row": 0, "col": 0, "crop": "carrot", "origin": [0.0, 1.0]}
  ],
  "plants": [
    {
      "id": "r0c0-017",
      "crop": "carrot",
      "pixel": [0, 0],
      "variant": "carrot_harvest_v07",
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
- Variants are named `<crop>_<stage>_v<NN>` (for example `carrot_harvest_v07`), see [ADR 0008](../adr/0008-variant-naming-with-growth-stage.md). The `.glb` is one mesh with one material, for the static Field only.
- Plants in the static Field have no collision. For M4 the root crop generator also writes an engine-agnostic physics export per Variant ([ADR 0006](../adr/0006-pull-out-via-anchored-root-and-force-law.md)): `<variant>.physics.json` (links with masses, inertias and collisions: a convex hull for the root, capsules for the petiole links; joints with stiffness, damping and a spring reference that holds the generated shape against gravity; root length and depth; at scale 1) plus `<variant>.articulated.glb` (one visual mesh per link). The root is one link whose hull is a low-poly copy of the root profile; each leaf is 3 petiole links joined by spring-loaded universal joints. Leaf blades are visual plus mass only. Masses and stiffnesses come from the geometry plus per-Crop material constants in the generator's table, each marked with its source or `guess`. Exporters only translate the file and apply the Plant's scale.
- Carrot Variants: a tapered orange root, mostly below ground with the shoulder visible, plus a crown of divided leaves. Root length, root diameter, foliage height and leaf count vary per Variant.
- Beetroot Variants: a top-shaped crimson globe with a thin taproot, a third to half above ground, plus red-magenta stalks fanning out in a V with simple ovate blades (wavy margin, red midrib). Globe size, foliage height and leaf count vary per Variant.
- Radish Variants (long red): a slender crimson-pink spindle fading to white at the tip, its shoulder a few cm above ground, plus pale green stalks with lyrate leaves (a large end lobe and small side lobes). Root size, fade point, foliage height and leaf count vary per Variant.
- Lettuce Variants (romaine): an upright head of leaves in a golden-angle spiral, outer leaves darker and leaning out, a pale cupped heart, whitish midribs, crinkled surfaces and frilly margins. Head height, leaf count and lean vary per Variant. Own generator (`lettuce`), sharing the root crop generator's palette and file writing.
- Default Asset Generator: pure Python with `trimesh`. A Blender generator may replace it for a Crop if the results look too crude, writing into the same library format.
- Root crops (carrot, beetroot, long red radish) share one generator, `root_crop`, with per-Crop ranges. Head lettuce (romaine) has its own generator, `lettuce`. Weeds: exported once from CropCraft's Blender library to `.glb`.
- Soil: a flat plane of 1 m tiles with CC0 PBR soil textures (ambientCG), committed to `assets/library/textures/`. A moist base soil (Ground048) is blended with milder dry patches of a second soil (Ground066) and a faint moisture tint into a baked 4 x 4 atlas of tiles (`generators/soil.py`); its masks are periodic over the atlas, so tiles join without seams and the pattern repeats every 4 m. Normals stay the base soil's.
- Library size estimate: about 5 MB per Crop. Move to Git LFS if the library passes about 100 MB.

## 9. Rendering

See [ADR 0005](../adr/0005-dataset-rendering-separate-from-simulation.md).

- Gazebo camera sensors are tuned for realism: ogre2, VCT global illumination, PBR materials, shadows, camera noise and distortion.
- Render cameras match the real camera used for data collection (model, resolution, field of view, mounting height and angle).
- Realism check: a headless run saves images from fixed cameras (top-down and oblique) to compare against photos of real carrot Pixels.
- Later: a Blender Exporter renders the same Field Layout offline for photorealistic datasets.

## 10. Physics

- Plants are static by default. In Gazebo they are visuals grouped in one static model per Pixel ([ADR 0007](../adr/0007-gazebo-plants-grouped-per-pixel.md)): one model per Plant stalls the Physics system at 10 x 10 Pixels.
- M4 makes picked root crop Plants dynamic, one model each ([ADR 0006](../adr/0006-pull-out-via-anchored-root-and-force-law.md)): a C++ gz-sim system removes its grouped visual, spawns it as an articulated model (rigid root, spring-jointed petiole chains), welds the root to an anchor on a vertical prismatic joint, and applies the Plant's Pull-out Curve as a joint force until the root has travelled its own length, then detaches it. Lettuce stays static (cut, not pulled).
- Soil is not simulated: loose soil only, no soil state per Pixel, no crown tear-off in M4. All Plant physics parameters are uncalibrated until the [measurement protocol](../research/measurement-protocol.md) has run.
- M5 adds the Active Region ([ADR 0010](../adr/0010-active-region.md)): every root crop Plant whose footprint (a cylinder from the soil to the top of its foliage) meets the bounding box of any robot link (any link of a model that is not part of the Field, plus 0.05 m of padding) becomes a Picked Plant, so any robot touches the Plants it reaches. Plant SDFs are written at build time; Picked Plants collide with robots and with each other.
- Soil collision is a plane at z = 0 on the soil collide bit (M5); its textured part covers the Field plus the Border. dartsim makes the plane about 2 km wide (a box lands at x = 1040 m and falls at 1060 m, measured in M5b), so for a robot on a Field it has no edge.
- Target Field size: up to about 10 x 10 Pixels (thousands of Plants). Performance is measured in M2 and recorded in [perf.md](perf.md).

## 11. Milestones

Each milestone is done only when its check has been run and observed. Work proceeds in small chunks, each ending in something that can be checked by hand (a file to open, an image, a world in Gazebo) plus automated tests. Nothing is built ahead of the chunk that needs it.

M1 chunks:

| Chunk | Content | Check |
|---|---|---|
| M1a | Repo tooling (uv, ruff, pytest, CI) and core: Field Spec to Field Layout to Manifest, with primitive stand-in Plants | `pixelfield build` writes `manifest.json` and a top-down SVG of Plant positions; core tests pass |
| M1b | Fix local `gz`, Gazebo Exporter with soil plane and primitive Plants | The generated world opens in Gazebo, `gz sdf -k` passes |
| M1c | First Crop Asset Generator (carrot) writing Variants to the Asset Library | Variants open in Gazebo or a glTF viewer and look like the Crop |
| M1d | Exporter uses Variants; lighting (VCT GI), cameras, headless render script | Rendered images look like a real Pixel of the Crop |

M4 chunks (decisions in [ADR 0006](../adr/0006-pull-out-via-anchored-root-and-force-law.md)):

| Chunk | Content | Check |
|---|---|---|
| M4a | ADR 0006 rewrite, spec updates, measurement protocol, Pull-out Curve in the glossary | The maintainer reads the docs |
| M4b | The root crop generator writes `<variant>.physics.json` (with convex hulls) and `<variant>.articulated.glb`; material constants with source or `guess`; library regenerated for carrot, beetroot and radish | Tests (deterministic, fresh, hulls convex, masses plausible); a PIL sketch of the hulls |
| M4c | Python writes the scaled SDF of one Plant (universal joints with springs); a settle check world per Variant | One Variant settles in Gazebo; a slow test over all 72 root crop Variants (needs a slot) |
| M4d | C++ gz-sim system in `exporters/gazebo/systems/`: pick request, remove the grouped visual, spawn, anchor with prismatic joint and `DetachableJoint`, force law, state topic; a scripted pull via ApplyLinkWrench | Logged `F(d)` follows the Pull-out Curve; detach happens with a peak inside the Pull-out Force range; the visual is gone in the GUI |
| M4e | Test gripper: box jaws on prismatic joints plus a lift, driven as joint velocity servos whose effort limit is the grip force (a JointPositionController takes its target over gz-transport, out of step with the physics), and a wrist force-torque sensor; squeeze test; a full pull by the leaf bunch | A test pull by the tops detaches the Plant within its Pull-out Force range; a weak grip slips |

M5 chunks (decisions in [ADR 0009](../adr/0009-robot-free-world-provider.md) and [ADR 0010](../adr/0010-active-region.md)). Only the world provider's side: driving, the arm and harvesting with the real robot model are planned in the robot repository (`amiga_ros2`).

| Chunk | Content | Check |
|---|---|---|
| M5a | Design: ADR 0009 and 0010, the robot interface (section 14), M5 and M7 in the milestones, glossary (Picked Plant, Active Region, Border) | The maintainer reads the docs |
| M5b | Ground for robots: soil collision as an infinite plane, Field Spec `border`, Manifest `field.path_gaps` and `robot_interface` version, `examples/amiga_10x10.yaml` | The example builds; its SVG shows the gaps where the Manifest says; a box dropped beyond the Border lands; a pick and pull still pass (root bitmask unchanged); tests |
| M5c | Pick by id: `build` writes `plants/<id>.sdf` for root crop Plants plus the table the system reads, the system loads the file, Python `pick` sends only the id; the state topic publishes on change plus events; a scripted pull with non-zero `pull_out_damping` | `pixelfield pick` in a running world; `gz topic -e` is silent for a resting Picked Plant; `pull.csv` unchanged; build time and `out/` size recorded |
| M5d | Active Region in the pull-out system: any non-Field link's box plus padding picks the root crop Plants whose footprint it meets. Starts with a spike: a full carrot Pixel picked at once (leaf drift, RTF); if it fails, the per-Pixel model fallback of ADR 0010 | The M4e test gripper pulling one carrot pushes its neighbours instead of passing through (GUI, by the maintainer). In a slot: settle check at scale 0.85 and 1.15, the slow squeeze over all 72 Variants, perf rows with 0, 10, 30 and 100 Picked Plants (pass: at least 0.5x with 30) |
| M5e | Packaging: Manifest library paths independent of the working directory, install instructions for robot repositories, tag `v0.5.0` | In the `amiga-ros:jazzy` container, with no `amiga_ros2` change: clone tag `v0.5.0`, install it, build the Amiga example Field and the systems, launch `gazebo.launch.py gz_args:='-r <world.sdf>'`: the Amiga stands in the Field with the pull-out system loaded |

If the M5d perf check fails, the next chunk returns untouched, resting Picked Plants outside the Active Region to their static visual ("unpick").

Deferred: a pixelfield Docker image (ADR 0002), built when the first colleague or student needs to run a world without a robot; its check is that they run it from the image. With a robot, the robot repository's image installs pixelfield (ADR 0009). pixelfield itself needs no ROS: `ros-jazzy-ros-gz` belongs to the robot repositories.

| # | Content | Done when |
|---|---|---|
| M0 | Design spec, ADRs, glossary, repo structure | Spec agreed, open questions resolved or deferred |
| M1 | One carrot Pixel end to end: repo tooling (uv, ruff, pytest, CI), core (Field Spec, Pixel grid, Planting Pattern, Field Layout, Manifest), carrot Asset Generator and library, Gazebo Exporter (soil, sun, VCT GI, cameras), headless render check, fixing the local `gz` PATH conflict | `pixelfield build examples/carrot_pixel.yaml` creates a world, Gazebo opens it, camera images show a believable carrot Pixel, core tests pass |
| M2 | Multi-Pixel Fields, random mode, Path Gaps, performance measurement | A 10 x 10 random Field loads in Gazebo, frame rate and VRAM recorded |
| M3 | More Crops (carrot, beetroot, long red radish, head lettuce), iterate on looks | All four Crops render believably side by side |
| M4 | Pull-out physics for root crops: Variant physics export, articulated Plants, C++ gz-sim pull-out system with the Pull-out Curve, test gripper | A test pull by the tops detaches a Plant within its Pull-out Force range; a weak grip slips |
| M5 | Robot-ready Fields: robot interface, ground and Border, pick by id, Active Region, packaging for robot repositories | The Amiga from `amiga_ros2` stands in a pixelfield Field with the pull-out system loaded (M5e) |
| M6 | Blender Exporter and sim-to-real experiments | Detectors trained on each image source evaluated on real images |
| M7 | MuJoCo pull scene and policy training (item 8 of section 12) | Separate plan; M6 and M7 are independent, either can start first |

Real-field image collection (our own field, possibly WUR) is planned around M2 to M3, so camera parameters can be matched early.

## 12. Resolved questions and open items

Resolved:

1. **Pixel boundaries**: soil runs continuously between Pixels; Pixels are not visibly marked.
2. **Row direction**: a default per Crop, overridable by an optional Field-wide setting. Per-Pixel overrides only if real fields need them.
3. **Random mode rules**: weights, an exact `empty_fraction`, and an optional `no_same_neighbour: true` over edge neighbours (section 5).
4. **Path Gaps**: "every N columns, width W", off by default, columns only; they widen the Field instead of cutting into Pixels (section 5).
5. **Detection labels**: Gazebo semantic segmentation only (one label per Pixel model, ADR 0007); per-Plant boxes are projected from the Manifest when a consumer needs them, YOLO export first.
6. **Soil appearance**: one texture in M1; in M3 mild variation by blending two soils plus a moisture tint into a seamless 4 x 4 m atlas (section 8).
7. **Crops for M3**: carrot, beetroot, long red radish and head lettuce (Crop names `carrot`, `beetroot`, `radish`, `lettuce`; the variety goes in the Crop definition). Real plants are the target; shop props serve as visual reference for proportions and color only.
8. **Performance budget**: at least 0.5x real time on the development laptop with a 10 x 10 Pixel Field and an active camera; target 1.0x or better.
9. **License**: AGPL-3.0 is intended, so that commercial users contribute back. Relicensing later needs agreement of all copyright holders, which gets harder as outside contributions accumulate.
10. **Name**: package `pixelfield`, repository AgriSim. The simulation may later also cover row crops and conventional single-crop fields; the name can be revisited then.
11. **Crop placeholder values**: the carrot values in section 6 stand until measured in the real field. Carrots are only the first Crop; nothing in the core may be carrot-specific.

Open (deferred):

1. **Real camera** on the Amiga: an OAK-D Pro (RGB IMX378, HFOV 66 or 69 degrees depending on the focus version; stereo OV9282 pair, 1280 x 800, HFOV 80 degrees). Currently mounted at the Amiga front looking straight down; a mount pitched about 45 degrees down, looking along the rows, is planned. Still open: exact height, angle and focus version. The M3a perf check used an OAK-D-like rig and found triangle LOD unnecessary (see [perf.md](perf.md)).
2. **Real field values** for Planting Patterns and harvest sizes, per Crop.
3. **Row crops and single-crop fields**: out of scope now. The core should not assume Pixels are small, so a large "Pixel" with one Crop or a row layout stays possible later.
4. **Gazebo labels (M2b)**: a Label plugin per Pixel model plus a semantic segmentation camera. Deferred until a consumer needs it: camera-based harvesting in a robot repository, or M6 detectors trained on Gazebo renders. Oracle perception needs no labels: it reads the Manifest and the poses of Picked Plants, robot-side. Decided already: a stable label id per Crop, stored in the Crop definition so it is the same in every Field; soil and background are 0. Building it also checks the gz label behaviour noted in ADR 0007 by running it.
5. **Growth stages**: all Plants are harvest-ready for now. Farming games and CropCraft treat growth stage as a per-cell state with its own mesh; here it would be a Variant axis (Crop, stage, variation) chosen per Pixel or per Field. Variant names already carry a stage slot (ADR 0008), so adding a stage does not rename the library. See [prior-art.md](../research/prior-art.md).
6. **Soil mechanics**: a rigid soil plane with the default friction (mu 1). Contact friction takes the lower of the two surfaces (checked in M5b with dartsim, `tests/test_gazebo.py`: under tilted gravity a box of mu 0.3 slides on the soil at a slope of 0.5 and holds at 0.25, a box of mu 2 slides at 1.3 and holds at 0.8, a box of mu 1 holds at 0.95 and slides at 1.05), so a robot sets its traction on its own wheels, and wheel slip (the gz-sim `WheelSlip` system) belongs to the robot repository (ADR 0009). Pull-out uses loose soil only in M4 (item 7). Deformable terrain (Project Chrono SCM, as a separate Exporter) only if wheel sinkage or ruts become a research question; particle soil (DEM) is out of scope.
7. **Soil state and crown tear-off**: M4 models loose soil only. Soil state per Pixel (loosened or compact) would select the Pull-out Force range (carrot about 20 N loosened, 118 to 149 N undisturbed). With compact soil, tear-off of the tops (212 to 243 N for carrot) comes within reach and returns as a second force law on the crown ([ADR 0006](../adr/0006-pull-out-via-anchored-root-and-force-law.md)).
8. **Training engine (MuJoCo)**: a learned pull policy is the target. Training is expected to run in MuJoCo (GPU-parallel through MuJoCo Warp) on a small local pull scene, built by a new Exporter from the same Variant physics export and Pull-out Curve. Gazebo keeps the whole Field, the robot, cameras, ROS 2, and end-to-end tests of the trained policy. MuJoCo does not load glTF (only STL, OBJ, MSH) and collides every mesh as its convex hull, which the root hull of the physics export already fits (written out as OBJ by that Exporter); petiole capsules map to MuJoCo capsules with `fromto`. In MuJoCo Warp, flex is experimental and plugins are unsupported, so the foliage stays plain hinge joints with springs (two hinges per body in place of a universal joint). This is milestone M7, with its own ADR when it starts. Petiole links collide as capsules since M5d; a weak grip can still catch where the capsules meet at a joint, which a trained policy could exploit.

## 13. Publication angle

Existing work (CropCraft) generates row-based fields for Gazebo Classic and renders its datasets in Blender. Its authors list simulators beyond Gazebo, soil variation, vegetation deformation and richer labels as future work. This project can contribute:

1. Field generation for pixel cropping, which no existing tool supports.
2. Harvestable Plants: a per-Plant Pull-out Curve based on literature values, articulated foliage to grip, and a gz-sim uprooting system. No prior Gazebo work was found.
3. A simulator-agnostic design on current Gazebo (gz-sim), with a ground-truth Manifest.
4. A sim-to-real evaluation: detectors trained on Gazebo renders, Blender renders and real images, tested on real pixel field images.

Point 4 decides the strength of the paper: without real-world validation it is a tool paper (workshop, SoftwareX, JOSS), with it a stronger conference or journal paper. The design already supports it through seeded, reproducible runs, a versioned Asset Library and the Manifest.

## 14. Robot interface

pixelfield is a robot-free world provider ([ADR 0009](../adr/0009-robot-free-world-provider.md)): a robot repository launches a pixelfield world and spawns its robot into it, and everything pixelfield offers is gz-native. Interface version 1, recorded in the Manifest as `robot_interface` (from M5b); a breaking change raises it and is noted here.

- **World**: `out/<field>/world.sdf`, world name always `pixelfield`. Two worlds on one machine run in separate `GZ_PARTITION`s.
- **Frames**: SI units, z up, x east, y north, origin at the south-west corner of the Field at ground level (section 4). The ground is a plane at z = 0 reaching about 1 km in every direction (dartsim); textured soil covers the Field and its Border.
- **Manifest**: `out/<field>/manifest.json` (section 7), the ground truth: Plant ids, Crops, positions, scales, Pull-out Forces, Path Gap x ranges.
- **Systems**: built from `src/pixelfield/exporters/gazebo/systems/` and found through `GZ_SIM_SYSTEM_PLUGIN_PATH`; without them the world runs, but no Plant can be picked.
- **Pick service**: `/world/pixelfield/pixelfield/pick`, request `gz.msgs.StringMsg` with the Plant id, reply `gz.msgs.Boolean` (false for an id that is not a root crop Plant of the Field, one already picked, or any id before the first simulation update, while the system has not read its table yet). For example `gz service -s /world/pixelfield/pixelfield/pick --reqtype gz.msgs.StringMsg --reptype gz.msgs.Boolean --timeout 5000 --req 'data: "r0c0-017"'`. The system loads `out/<field>/plants/<id>.sdf`, written by `pixelfield build` for every root crop Plant, from the folder of the world file.
- **Active Region**: automatic from M5d, nothing to configure ([ADR 0010](../adr/0010-active-region.md)). A robot that sets its own collide bitmask must share a bit with the Plants and the soil (bit 0) to touch them.
- **Pull-out state**: `/world/pixelfield/pixelfield/pull_out` (`gz.msgs.Param`: plant, d, force, attached), on every physics step where a Picked Plant's d or force changed, plus one message per event: picked (the first step after the spawn), peak_passed and detached. Event messages also carry `event` with that name. A resting Picked Plant is silent, a part-pulled one held by the ratchet too. Poses of Picked Plants are on the standard `/world/pixelfield/dynamic_pose/info`.
- **Installing in a robot image**: clone a tagged release, install the Python package, build the systems against the image's gz-sim (instructions from M5e).

Robot-side, not part of pixelfield: the robot description and its Gazebo plugins, the ROS 2 control stack, the `ros_gz_bridge` configuration for the topics above, wheel and gripper friction, oracle or camera perception, and end-to-end harvest tests.
