# Prior art and background research

Collected 2026-09-30 during the design phase. Items marked *unverified* come from search summaries and still need checking against the source.

## Pixel farming

- [pixelfarming.eu](https://pixelfarming.eu/what-is-pixelfarming/): land is divided into pixels, each tied to a crop, its care and its consumer. No dimensions given.
- [WUR Pixel cropping](https://www.wur.nl/en/project/Pixel-cropping.htm): Droevendaal trials use **50 x 50 cm pixels**, six crops placed randomly on a fixed grid in two 9 x 12 m plots. Landgoed Velhorst uses **1.5 x 1.5 m** pixels to fit machinery. *Unverified: page returned 404, taken from search snippet.*
- [Pixel Farming Robotics Robot One](https://pixelfarmingrobotics.com/robot-one/): straddles beds, track width 3.2 to 3.6 m or 5.8 to 6.2 m. Crops: spinach, onion, babyleaf, leek, chicory, herbs, tulips.
- No public source found on plant arrangement inside a pixel.

## Farm-ng Amiga

- Track width adjustable, about 40 to 80 in (1.0 to 2.0 m); payload 150 kg. Wheelbase adjustable, no default published. Ground clearance not published. [Mechanics docs](https://amiga.farm-ng.com/docs/hardware/mechanics/)
- No official Gazebo model. Community (UC Merced with farm-ng, unofficial, ROS 2 Humble): [jek97/BT_sim](https://github.com/jek97/BT_sim).
- Official SDK: [farm-ng/farm-ng-amiga](https://github.com/farm-ng/farm-ng-amiga).

## Intrinsic AI for Industry Challenge

- Repo: [intrinsic-dev/aic](https://github.com/intrinsic-dev/aic). Cable connector insertion, started 2026-02-11.
- ROS 2 Kilted, Gazebo built from source.
- World `aic_description/world/aic.sdf`: ogre2, VCT global illumination, zero ambient light, Bullet-featherstone physics.
- All visual meshes are `.glb` (glTF with PBR materials).
- Camera images come from Gazebo camera sensors bridged to ROS; RViz only displays them.

## Gazebo status (late 2026)

- [Releases](https://gazebosim.org/docs/latest/releases/): Jetty is the newest LTS (to 2031), Harmonic LTS to 2029, Ionic end of life Dec 2026.
- Recommended pairings: Jazzy with Harmonic, Lyrical with Jetty.
- [DetachableJoint system](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1DetachableJoint.html): detach and attach triggered by topic messages. No built-in force-threshold break.

## Field and world generators

| Project | What | License, activity | Gazebo | Relevance |
|---|---|---|---|---|
| [CropCraft](https://github.com/Romea/cropcraft) ([paper](https://arxiv.org/abs/2511.02417)) | Blender-based field generator from YAML: crops and weeds at growth stages, stones, curved rows, labelled RGB and mask rendering | Apache-2.0, active 2026 | Classic | Closest prior art. Source of Variants and design ideas, see ADR 0004. Dataset images are rendered in Blender, not Gazebo. |
| [virtual_maize_field](https://github.com/FieldRobotEvent/virtual_maize_field) | Python script placing randomised maize rows into an SDF world | GPL-3.0, 2025 | Classic (`main`), gz-sim (`ros2-gz` branch) | Ideas for row randomisation and SDF writing. Do not copy code (GPL). |
| [AutomaticRowCropGenerator](https://github.com/PIC4SeR/AutomaticRowCropGenerator) | Blender to Gazebo row crops | No license, 2022 | Classic | Ideas only |
| [clearpath_simulator](https://github.com/clearpathrobotics/clearpath_simulator) | Robot simulation with orchard world | BSD-3, active | gz-sim | Example of robot and world launching |
| [Fields2Cover](https://github.com/Fields2Cover/Fields2Cover) | Coverage path planning | BSD-3, active | n/a | Robot path planning later |
| [awesome-agriculture](https://github.com/rajithadesilva/awesome-agriculture) | Curated list | stale | n/a | Index |

## Procedural plant geometry

- [Helios](https://github.com/PlantSimulationLab/Helios) (LGPL-2.1) with [PyHelios](https://github.com/PlantSimulationLab/PyHelios) (MIT): plant architecture models. Carrot support not confirmed.
- [L-Py](https://github.com/openalea/lpy) and [PlantGL](https://github.com/openalea/plantgl) (OpenAlea): L-systems in Python, conda-only and heavy.
- Synthetic datasets from procedural plants: CropCraft's dataset, [AgriVerse](https://zenodo.org/records/21335445), [arXiv 2403.18351](https://arxiv.org/pdf/2403.18351).

## Carrot pull-out forces

- 25 N in loosened soil, 140 N in un-loosened sandy loam: [ICAR IJAgS 2019](https://epubs.icar.org.in/index.php/IJAgS/article/download/90825/36952/232936).
- 15.0 to 25.9 N for Nantes carrots with root length 10 to 25 cm: [PMC6189625](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6189625/). *Unverified.*
- Carrot damage at about 43 to 45 N, relevant as a grip limit: [doi:10.3390/agriculture11060471](https://doi.org/10.3390/agriculture11060471).
- Pull direction effects (alfalfa): [PMC7934573](https://pmc.ncbi.nlm.nih.gov/articles/PMC7934573/).
- No Gazebo uprooting plugin found.

## Free 3D models

- Gazebo Fuel: no carrot or lettuce; tomato and courgette under CC-BY-4.0.
- Poly Haven (CC0): `dandelion_01`, `weed_plant_02`, `nettle_plant`, grasses. Useful as weeds and distractors.
- Carrot models on Meshy, CGTrader, Tripo: mostly AI-generated with unclear licenses. Avoid.
