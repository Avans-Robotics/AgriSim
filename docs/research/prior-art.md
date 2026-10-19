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
| AgriGen ([paper](https://arxiv.org/html/2609.25725v1), [site](https://baj31415.github.io/agrigen/)) | Isaac Sim field generator with ROS: row crops, orchards, vineyards; Perlin-noise terrain; domain randomization of terrain, assets, lighting and friction | Open-source assets, 2026 | n/a (Isaac Sim) | Possible Variant source (apple, lemon, cabbage, sugar beet, grapevine, 10 variations each; weeds Rumex and Chelidonium). Randomization list is a checklist for later. No growth stages. |
| Agri-Sim ([paper](https://arxiv.org/pdf/2608.29100)) | Unity tomato greenhouse with a dual-arm harvesting robot, RGB-D, LiDAR, ROS 2 | 2026 | n/a (Unity) | Different domain (greenhouse), low relevance |
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
- Nath et al. 2019 (Indian J. Agric. Sci., [abstract](https://epubs.icar.org.in/index.php/IJAgS/article/view/90825)): roots 19 to 23 cm long need 118 to 149 N in undisturbed beds and 20 to 22 N in loosened soil; detaching the tops from the root takes 212 to 243 N. The abstract gives no correlation with root size. Probably the same study as the first item.
- No Gazebo uprooting plugin found.

## Uprooting mechanics

Collected 2026-10-19 for the M4 design (ADR 0006).

- Curve shape: rice and barnyard grass pulls rise slowly to a peak, drop sharply, then level off at a residual force ([IJABE 1227](https://ijabe.org/index.php/ijabe/article/view/1227)). Oat and alfalfa seedlings start linear-elastic, then show sudden jumps with partial recovery ([EPFL 198677](https://infoscience.epfl.ch/record/198677), [PubMed 25109590](https://pubmed.ncbi.nlm.nih.gov/25109590/)).
- Ennos (1990), leek seedlings: a root passes tension into the soil by shear along its length; resistance rises with root length until the root itself snaps, at about 30 mm ([AGRIS](https://agris.fao.org/search/ru/records/65df787f0f3e94b9e5d8c08a)).
- Correlates: pull force rises with rooting depth, root diameter and the volume of soil moved, and falls as soil moisture rises ([eScholarship 2527v462](https://escholarship.org/uc/item/2527v462)). No study on pull speed found.
- DEM and MPM root pull-out simulations exist only as geotechnics studies, far too costly per step for robot training.
- Petiole stiffness: no carrot data found. Taro petiole epidermis about 500 MPa ([UoM 123/24338](https://dl.lib.uom.lk/handle/123/24338)).
- No published work on learned uprooting policies was found.

## Plant physics for manipulation

Collected 2026-10-02, extended 2026-10-19. The M4 choice is in ADR 0006.

| Work | Method | Engine | Evidence | Relevance |
|---|---|---|---|---|
| Gazebo Plants ([arXiv 2402.02570](https://arxiv.org/abs/2402.02570), ICRA 2024) | Branches as Cosserat rods solved with position-based dynamics; fruit detaches | Gazebo plugin | Arm fruit picking comparable to real experiments | Closest to our engine. Code MPL-2.0 only on request, not public. Classic or gz-sim *unverified*. |
| OrchardBench ([arXiv 2607.06337](https://arxiv.org/pdf/2607.06337)) | Branches as torsional spring-dampers (stiffness from Euler-Bernoulli beam theory, break at wood modulus of rupture); apples on stem tethers that detach at literature pull forces | Newton (GPU) | Every parameter tied to a published source; real-world validation unclear | Same pattern as ADR 0006 (tether plus literature force threshold) |
| Find the Fruit ([arXiv 2505.16547](https://arxiv.org/html/2505.16547)) | Full FEM plant, stems and leaves bend and twist under contact, plus randomization | Isaac Lab | Sim-only RL policy, up to 86.7% success on real plants | Most realistic, far too heavy for thousands of Plants |
| PCAP ([site](https://sites.google.com/view/pcap/home), CoRL 2024) | L-system branches with spring joints, stiffness and damping randomized | Isaac Gym | Zero-shot sim-to-real | Same pattern as our petiole chains |
| Discrete elastic rods ([arXiv 2310.00911](https://arxiv.org/abs/2310.00911)) | Rods with bend and twist stiffness identified from real tests | MuJoCo | 76.7% real success on wire flinging | Shows stiffness identification from simple tests |
| Blueberry canes ([arXiv 2609.13627](https://arxiv.org/html/2609.13627)) | Pseudo-rigid-body: rigid links with spring-damper joints | MuJoCo | Validated against real canes in the field | Cheap method with field evidence; maps to plain SDF revolute joints |
| Branch parameter estimation ([arXiv 2606.19314](https://arxiv.org/pdf/2606.19314)) | Spring-damper links, stiffness fitted by pushing real branches | n/a | Fitted to real data | Way to calibrate stiffness later |
| Leaf grasping ([arXiv 2505.03702](https://arxiv.org/html/2505.03702v1)) | Self-supervised geometric plus neural grasp point selection on deformable leaves | n/a | Real robot | Perception side, not physics |

- MuJoCo (checked 2026-10-19): no glTF import (STL, OBJ, MSH only), every mesh collides as its convex hull, hinge joints have stiffness, springref and damping, no breakable joint but a weld can be switched off at runtime (`eq_active`). The `cable` composite uses ball joints, with bend and twist from the `mujoco.elasticity.cable` plugin. MuJoCo Warp marks flex as experimental, does not support plugin actuators or sensors, and needs an NVIDIA GPU ([mujoco_warp](https://github.com/google-deepmind/mujoco_warp), [MJX docs](https://mujoco.readthedocs.io/en/latest/mjx.html)); whether the cable plugin runs there is *unverified*.
- No simulation of a root pulled out of soil was found in Gazebo, MuJoCo or Isaac. Uprooting appears only in weeding reviews and machine design ([robotic weeding review](https://pmc.ncbi.nlm.nih.gov/articles/PMC13210440/)).

## Soil and terrain

Collected 2026-10-02.

- Three roles: wheel contact (traction, slip, sinkage), root anchoring (pull-out), tool in soil (hoeing, digging).
- Project Chrono SCM (Soil Contact Model): semi-empirical deformable terrain, real time or close on a CPU, used for rovers and off-road vehicles, own ROS 2 bridge, not Gazebo. [Real-time vehicles on deformable terrain](https://www.researchgate.net/publication/359619160_Real-time_simulation_of_ground_vehicles_on_deformable_terrain), [Chrono terrain docs](https://api.projectchrono.org/development/terrain_synchronization.html), [rover use](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2024.1320261/full).
- DEM (particle soil, e.g. Chrono, EDEM): used for single tool design studies ([weeding knife](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11557383/)), far too heavy for a Field.
- gz-sim `WheelSlip` system: slip compliance for wheels on rigid ground. *Unverified, from memory.*
- No source yet for a soil friction coefficient or for root slip before detach.

## Farming games

Collected 2026-10-02. Ideas only: game engines and assets are proprietary and their licenses forbid reuse.

- Farming Simulator 25 (GIANTS): ground split into cells of about 0.5 m with bit-packed density maps: crop type and growth state (sown, visible stages, harvest-ready, withered), plus layers for ground state (plowed, cultivated, seeded, rolled, mulched), weeds (also growing), stones, lime and fertilizer. Plants are instanced foliage from that map with LOD and a wind-sway shader. Tools change cell state; no plant contact physics. [GDN foliage](https://gdn.giants-software.com/thread.php?categoryId=21&threadId=4603), [GDN density maps](https://gdn.giants-software.com/thread.php?categoryId=22&threadId=7935).
- Precision Farming 3.0 (FS25): per-cell soil type, pH, nitrogen, yield maps, variable-rate seeding and weed control, weed and crop sensors, an environmental score. Lookup tables, no physiology. [Wiki](https://farmingsimulator.wiki.gg/wiki/Precision_Farming/Farming_Simulator_25), [changelog](https://www.farming-simulator.com/changelogs/fs25-precisionFarming.php).
- Stardew Valley, Hay Day: tile grid with crop, growth stage and a watered flag per tile, a simpler Pixel.
- Ideas worth keeping: growth stage as a Variant axis; ground state per Pixel (loosened, compact, tracks); stones and residue as sparse scatter objects; wind sway for camera realism; per-Pixel agronomic values in the Manifest as ground truth for scouting tasks, only when a task needs them.

## Asset generation

Collected 2026-10-12.

- Artisan ([site](https://physicalvision.github.io/artisan/), [code](https://github.com/physicalvision/Artisan), [arXiv 2610.13947](https://arxiv.org/abs/2610.13947)): LLM agents (design, coding, review) build rigid articulated objects (furniture, kitchen, lab) from text or image, repaired with simulation feedback on collisions, stability, mass and joints. Apache-2.0, needs an OpenAI key, about $15 budget per object. No plants or deformables, not deterministic, export format not stated. Not a fit for Variants; the idea worth borrowing is the automated stability and collision check (the per-Variant stability check in ADR 0006).

## Free 3D models

- Gazebo Fuel: no carrot or lettuce; tomato and courgette under CC-BY-4.0.
- Poly Haven (CC0): `dandelion_01`, `weed_plant_02`, `nettle_plant`, grasses. Useful as weeds and distractors.
- Carrot models on Meshy, CGTrader, Tripo: mostly AI-generated with unclear licenses. Avoid.
