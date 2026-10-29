## 2026-09-30 Reset main and start fresh branch
### Goal & outcome
Clean local main and start the project from scratch. Local main now matches origin/main (LICENSE only); new branch feat/fresh-start created from it.
### Decisions & why
- Old local main (bb04a4c) had unrelated history to origin/main and only a toy corn field prototype; discarded via hard reset.
- No archive tag: bb04a4c is the parent of fix/field-freeze-makefile, which still preserves the old work locally and on origin.
- Uncommitted CLAUDE.md edits dropped; CLAUDE.md to be rewritten during new project design.
### Lessons / gotchas
- Old CLAUDE.md referenced 'omni.physx.graph.nodes.PPointInstancer', which does not look like a real API; UsdGeom.PointInstancer is the real instancing prim.
- Old .gitignore listed sim/*.py files that were committed anyway, so the ignore had no effect.
### State
Branch feat/fresh-start at ce39370, clean tree. Validated via git status/log. Not pushed (user pushes).
### Open items
- Decide whether to delete fix/field-freeze-makefile (local + remote).
- Design new project structure and CLAUDE.md.

## 2026-09-30 Design phase M0: spec, ADRs, glossary, repo structure
### Goal & outcome
Capture the agreed design for the pixel farming field generator as docs before any code. Written: docs/design/spec.md, CONTEXT.md, ADRs 0001-0006, docs/research/prior-art.md, README.md, new CLAUDE.md, folder skeleton with a README per folder.
### Decisions & why
- Simulator-agnostic core plus per-simulator Exporters; Gazebo Harmonic + Jazzy target, Docker for distribution (installed, recommended pairing).
- Committed Asset Library of Variants reused per Plant: VRAM budget and students need no generator toolchain.
- CropCraft used as asset source only: row-based, Blender runtime, Gazebo Classic, no carrots or physics.
- Dataset rendering separated from closed-loop sim: Gazebo cannot reach path-traced quality; Blender Exporter later.
- Pull-out via custom force-threshold system + DetachableJoint (ADR 0006 proposed, settled in M4).
### Lessons / gotchas
- CropCraft paper images are Blender renders, not Gazebo; do not expect that look in Gazebo.
- Repo LICENSE is AGPL-3.0; Apache-2.0 CropCraft assets may be included. License choice listed as open question.
- `gz sim` broken locally: ROS-vendored gz shadows system gz on PATH.
### State
Branch feat/fresh-start. Docs only, no code; links checked. Uncommitted except this log.
### Open items
- Resolve the 13 open questions in spec section 12 (camera model, carrot planting defaults, license, name, ...).
- Then start M1 on IMPLEMENT.

## 2026-09-30 M1a: core Field Spec to Manifest, SVG view
### Goal & outcome
M1a chunk: repo tooling (uv, ruff, pytest, GitHub Actions CI) and core. `pixelfield build examples/carrot_pixel.yaml` writes manifest.json and field.svg (32 of 33 carrot positions planted, 3 east-west rows). 12 tests pass, ruff clean.
### Decisions & why
- SVG writer is an Exporter (`EXPORTERS["svg"]`): exercises the extension point now, keeps rendering out of core.
- One RNG per Pixel seeded with "seed:row:col": editing one Pixel leaves all other Plants identical.
- All random draws happen for every nominal position, missing or not: ids (position index) and values stay stable.
- Rows are centred in the Pixel and clipped to the margin-inset square; jittered positions are clamped to it (ponytail note in layout.py).
- Random mode and path_gap raise a clear "planned for M2" error instead of being silently ignored.
- Only runtime dependency: pyyaml; stdlib random, argparse.
### Lessons / gotchas
- ROS Jazzy puts /opt/ros/jazzy site-packages on PYTHONPATH; their pytest11 plugins (launch_testing etc.) break collection. Fixed with `addopts = "--disable-plugin-autoload"` in pyproject.
- uv was not installed; user installed it via the official script (~/.local/bin).
### State
Branch m1a-core, commit 1e0c73a, not pushed. Validated: tests, lint, CLI run, SVG rendered and inspected (single Pixel and a rotated 2x2 grid). CI workflow UNVERIFIED until pushed to GitHub.
### Open items
- Push m1a-core and check the CI run; user reviews and merges.
- Next chunk M1b: fix local gz PATH, Gazebo Exporter with soil plane and primitive Plants.

## 2026-10-01 M1a: second Crop (lettuce) to prove crop-generic core
### Goal & outcome
Check that adding a Crop needs no code change. Added crops/lettuce.yaml (placeholder values), examples/mixed.yaml (2x3 grid, carrot, lettuce, empty) and a two-Crop test. Only code change: SVG colors Plants per Crop. 13 tests pass; mixed build gives 76 Plants and the SVG matches the grid.
### Decisions & why
- Lettuce added on m1a-core (not yet merged) because it validates M1a's crop-generic claim; values are guesses, marked provisional in the file.
- Lettuce: 0.25 m spacing, 0.125 m margin, 4 heads per 0.5 m Pixel.
### Lessons / gotchas
- Per-Pixel seeding visibly works: Pixel r0c0 in mixed.yaml is identical to carrot_pixel.yaml (same seed).
### State
Branch m1a-core, validated (tests, lint, CLI, rendered SVG inspected). Not pushed; CI UNVERIFIED.
### Open items
- Replace lettuce values with measured ones (spec section 12, open item 2).
- Push, CI check, review and merge; then M1b.

## 2026-10-01 M1a: legend in the SVG view
### Goal & outcome
field.svg now has a legend strip below the Field: one entry per Crop with its Plant count, an Empty Pixel swatch (only when present) and a scale bar. Rendered for carrot_pixel and mixed; 13 tests pass.
### Decisions & why
- Legend below the Field (user choice), so no Plants are covered.
- Scale bar 10 cm instead of the proposed 0.5 m: 0.5 m equals the full width of a one-Pixel image.
- Entries wrap to a new line on narrow Fields; text width estimated at 8 px per character (ponytail note).
### Lessons / gotchas
- Legend circles are self-closing, Plant circles have a <title> child: tests count "</circle>" to count Plants only.
### State
Branch m1a-core, validated (tests, lint, both SVGs rendered and inspected). Not pushed; CI UNVERIFIED.
### Open items
- Push, CI check, review and merge; then M1b.

## 2026-10-01 M1a: coordinate frame and 10 cm grid in the SVG view
### Goal & outcome
field.svg now shows the Field frame at the origin (x east red, y north green, 10 cm arrows) and a light grid every 10 cm from the origin. Legend label reads "10 cm (grid)". Rendered for carrot_pixel and mixed; 13 tests pass.
### Decisions & why
- No axis tick labels (user choice): frame plus grid is enough to count positions.
- Grid spacing and scale bar share one constant (GRID_M) so they cannot drift apart.
- Grid lines on Pixel edges are skipped so the darker Pixel outlines stay visible.
- 20 px white border via a negative viewBox origin: field coordinates in the SVG are unchanged.
### Lessons / gotchas
- A frame drawn exactly on the image edge is half clipped; the first render showed only half of the y axis. Always render and look.
- Green label on brown soil is unreadable; axis labels sit in the white border or use the axis color on a contrasting area.
### State
Branch m1a-core, validated (tests, lint, both SVGs rendered and inspected). Not pushed; CI UNVERIFIED.
### Open items
- Push, CI check, review and merge; then M1b.

## 2026-10-01 M1b: fix local gz (GZ_CONFIG_PATH, not PATH)
### Goal & outcome
Make `gz sim` work locally. Root cause: sourcing ROS Jazzy sets GZ_CONFIG_PATH to /opt/ros/jazzy/opt/sdformat_vendor/share/gz only, so gz sees just `sdf`. Fixed by appending /usr/share/gz in ~/.bashrc (backup at ~/.bashrc.bak-gzconfig). CLAUDE.md known issue rewritten.
### Decisions & why
- Fix lives in ~/.bashrc, not the repo: machine issue; Docker (M1e) covers other users.
- Keep gz-transport15/msgs12 (user-installed 2026-02-01 via python3-gz-transport15, may serve another project); workaround `--force-version 13` documented.
- ros-jazzy-ros-gz deferred until a chunk needs ROS topics.
### Lessons / gotchas
- The PATH theory was wrong: vendor gz and /usr/bin/gz behave identically; the gz tools discover commands via *.yaml in GZ_CONFIG_PATH.
- `gz topic --versions` lists 15.1.0 and 13.5.0; default may pick 15, incompatible with Harmonic.
### State
Branch m1b-gazebo. Validated in fresh `bash -i`: gz sim 8.14.0, gz sdf 14.9.0, `gz sdf -k` on stock shapes.sdf Valid. GUI open of shapes.sdf UNVERIFIED (user checks by eye).
### Open items
- User: run `gz sim shapes.sdf` in a new terminal, confirm GUI.
- Next: Gazebo Exporter with soil plane and primitive Plants (grill first).

## 2026-10-01 M1b: silence gz protobuf errors and EGL warnings
### Goal & outcome
`gz sim shapes.sdf` worked but printed hundreds of `libprotobuf ERROR ... File already exists` lines plus libEGL dri2 warnings. Protobuf errors fixed by removing the gz-msgs12/transport15 stack (user ran apt). EGL: `__EGL_VENDOR_LIBRARY_FILENAMES` set to NVIDIA only in ~/.bashrc. CLAUDE.md known issues updated.
### Decisions & why
- Removed the stack instead of dpkg-diverting the desc file: its only user (DroneBalloonProto, PX4 camera scripts, last touched 2026-02-01) is obsolete per user.
- Explicit `apt remove libgz-msgs12 libgz-utils4 libzenohc`, no `apt autoremove`: autoremove would also drop the unrelated ros-jazzy-hpp-fcl.
### Lessons / gotchas
- gz-msgs loads every *.gz_desc in /usr/share/gz/protos; two major versions there means duplicate descriptors in every gz process.
- GZ_DESCRIPTOR_PATH is additive: pointing it at a msgs10-only dir doubled the errors (220 to 432).
### State
Branch m1b-gazebo. Validated in fresh `bash -i`: 0 protobuf errors in headless `gz sim -s` and `gz topic -l` (was 220 and 440), gz sim 8.14.0, only transport 13.5.0 left. EGL fix validated: user opened the GUI, shapes render, no warnings.
### Open items
None for the gz setup.
- Next: grill the Gazebo Exporter (soil plane, primitive Plants).

## 2026-10-01 M1b: Gazebo Exporter with soil and stand-in Plants
### Goal & outcome
`pixelfield build` now also writes world.sdf: flat brown soil (Field plus 0.5 m border, 2 cm box, top at z=0, with collision), a directional sun, Physics/UserCommands/SceneBroadcaster systems, and one static cylinder model per Plant named by Plant id. 17 tests pass; both examples pass `gz sdf -k` and load headless without warnings.
### Decisions & why
- One world.sdf with inline Plant models, no per-Crop model.sdf + include: `<include>` cannot scale, and every Plant has its own scale. Modularity lives in the shared Variant .glb files (M1d).
- Stand-in size derived, no YAML field: radius 0.4 x min(row_spacing, in_row_spacing), height 0.1 m, both times Plant scale. Thrown away in M1d.
- Visual only on Plants; collision comes with Variants.
- FieldLayout gained `crops` (deviation, reported): Exporters need the Planting Pattern and only receive the Layout.
- Plant colors moved to exporters/colors.py so SVG and Gazebo match.
- build runs all Exporters by default; `--exporter` picks one.
- SDF written with stdlib ElementTree (escaping, ET.indent, tests parse with the same module).
### Lessons / gotchas
- The gz sdf test is skipped only when gz is absent; with gz present but GZ_CONFIG_PATH unfixed it fails (intended, it flags the broken setup).
### State
Branch m1b-gazebo, commit 2c5b0ec. Validated: pytest (17), ruff, build + `gz sdf -k` on carrot_pixel and mixed, headless `gz sim -s` load clean, user checked both worlds in the GUI (stand-in sizes differ from the SVG dots, accepted: both are throwaway).
### Open items
- Push m1b-gazebo, CI check, review and merge. Then M1c (carrot Asset Generator).

## 2026-10-01 M1c checkpoint 1: carrot root Variants
### Goal & outcome
`pixelfield generate carrot` writes 24 root-only carrot Variants (glb, about 16 KB each, 760 triangles), `variants.json` with root sizes, and a Gazebo preview world (`out/carrot_variants/world.sdf`). 21 tests pass.
### Decisions & why
- Grilled: harvest stage only; real mesh leaflets (checkpoint 2); one PBR material per part, no textures; trimesh as optional `generate` extra plus dev group; collision sizes in variants.json now (only the generator knows them); at most 3k triangles per Variant; Variant files are spec-correct y-up, any Gazebo rotation goes in the Exporter (M1d).
- Variant count and library path come from the Crop YAML (Crop gained `library`).
- Preview world lives in exporters/gazebo (`preview`), keeping simulator code out of generators.
- Root = solid of revolution (flat crown, rounded edge, Nantes-like taper) with a small sideways bend.
### Lessons / gotchas
- trimesh `fix_normals` needs scipy; instead the revolve profile runs tip to crown so the volume is positive (normals outward). A test asserts it.
- trimesh names glb meshes `geometry_0` unless `geom_name` is passed.
- The agent shell lacks ~/.bashrc; gz commands need `bash -ic`.
- Headless `gz sim -s` does not load visual meshes, so it does not prove the glb renders.
### State
Branch m1c-carrot. Validated: pytest (21), ruff, determinism (same md5 across runs), `gz sdf -k` on the preview world, build still works without trimesh. GUI look in gz UNVERIFIED (user checks, including whether gz shows the y-up glb standing or lying).
### Open items
- User: `gz sim out/carrot_variants/world.sdf`, judge shape and orientation.
- Checkpoint 2: foliage.

## 2026-10-01 M1c: y-up Variants stood up in Gazebo
### Goal & outcome
User saw the preview carrots lying on their side: Gazebo loads glTF without converting y up to z up (confirms the Q10 expectation). The Gazebo code now puts a roll of +90 degrees on each Variant visual (`GLTF_TO_Z_UP`), so the preview stands them up; M1d reuses it.
### Decisions & why
- Roll on the visual pose, not the model pose: the model frame stays z up with yaw only, so M1d Plant poses need no change.
- Moved forward from M1d (user approved) so foliage can be judged upright at checkpoint 2.
### Lessons / gotchas
None.
### State
Branch m1c-carrot. Validated: pytest (21), ruff, `gz sdf -k`. Upright look in the GUI UNVERIFIED (user checks). User judged the root shape fine.
### Open items
- Checkpoint 2: foliage.

## 2026-10-01 M1c checkpoint 2: carrot foliage
### Goal & outcome
Carrot Variants now have 6-10 leaves: a tapered 3-sided petiole tube along a quadratic Bezier (up, out, slight droop) and 4-6 leaflet pairs plus a tip leaflet, each a fan of 3-5 diamond blades. At most about 2,000 triangles per Variant, library 1.2 MB. `variants.json` gained `foliage.height` and `foliage.radius`, measured from the mesh.
### Decisions & why
- Double-sided glTF material on foliage instead of duplicated back faces: halves the triangles, and gz-common reads assimp's `$mat.twosided` (found in libgz-common5-graphics).
- Blades are flipped to face up so the single faces light correctly from above.
- Foliage sizes measured from the vertices, not from the sampled parameters, so collision shapes match the mesh.
### Lessons / gotchas
- `uv run --with matplotlib` gives a quick off-repo render to look at meshes before asking the user, with no project dependency change.
### State
Branch m1c-carrot. Validated: pytest (21), ruff, `gz sdf -k`, matplotlib render of three Variants looked like carrots. User checked the leaves in the gz GUI and approved them ("perfect for now").
### Open items
- Push m1c-carrot, PR, CI, review and merge. Then M1d.

## 2026-10-01 M1d checkpoint 1: Plants use carrot Variants
### Goal & outcome
Grilled M1d into 4 checkpoints (Variants, lighting, soil texture, cameras + `pixelfield render`). Checkpoint 1 done: the Gazebo Exporter gives each Plant its Variant glb (relative URI `meshes/<variant>.glb`, glTF roll, uniform Plant scale, yaw), copying the used glbs into `out/<name>/meshes/`. Crops without Variants (lettuce) keep the cylinder stand-in.
### Decisions & why
- Self-contained out dir with relative mesh URIs: relocatable and Docker-friendly (M1e); gz resolves relative mesh URIs against the world file (tested).
- Visual only, no collision: Plants are static until M4.
- hue_shift ignored in Gazebo (ponytail note): glb materials cannot be tinted per Plant without replacing them.
- Rest of M1d agreed: one world.sdf holding cameras (top-down + 45 deg oblique, 1920x1080, hfov 60 deg), VCT GI in the Sensors plugin (32^3), sun about 40 deg elevation from SE plus sky, one approved ambientCG 1K soil set, `pixelfield render` running from the out dir.
### Lessons / gotchas
- VCT GI is not SDF scene syntax: it is a `<global_illumination type="vct">` block inside the Sensors system plugin and only affects camera sensors (GUI needs the separate GlobalIlluminationVct plugin). Example: /usr/share/gz/gz-sim8/worlds/global_illumination.sdf.
- A gz camera sensor saves no images unless something subscribes to its topic (`gz topic -e -t /camera` alongside works).
- A relative camera `<save><path>` resolves against the cwd, not the world file.
- Headless runs need a few thousand iterations; at 200 the run ends before the render thread produces a frame.
### State
Branch m1d-variants, uncommitted code. Validated: pytest (21), ruff, `gz sdf -k` on carrot_pixel and mixed, headless camera snapshot shows 32 upright carrots with shoulders above the soil. GUI look UNVERIFIED (user checks).
### Open items
- User: `gz sim out/carrot_pixel/world.sdf`. Then checkpoint 2 (lighting).

## 2026-10-01 M1d checkpoint 2: lighting
### Goal & outcome
world.sdf now has the Sensors system (ogre2) with VCT global illumination (32^3, 6 bounces, other values from gz-sim's example world), a `<scene>` with sky, ambient 0.4 and no grid, and the sun at 40 degrees elevation from the south-east (constants `SUN_ELEVATION`, `SUN_AZIMUTH`, `GI_RESOLUTION`, `GI_BOUNCES`).
### Decisions & why
- GI lives in world.sdf (Sensors plugin), not a separate render world: cameras (checkpoint 4) pick it up, and the GUI ignores it.
- No custom `<gui>` block for the GUI GI plugin: it would replace gz's default GUI layout.
### Lessons / gotchas
- At 32^3 GI on one Pixel the effect is subtle (lighter canopy interior and stems); compare against a no-GI render to see it.
### State
Branch m1d-variants, uncommitted code. Validated: pytest (22), ruff, `gz sdf -k`, headless GI and no-GI renders with 0 errors. GUI sky look UNVERIFIED (user checks).
### Open items
- Tune ambient/sun intensity by eye once the soil texture and real cameras are in.
- Next: checkpoint 3 (soil texture, user approves the ambientCG set).

## 2026-10-01 M1d checkpoint 3: soil texture
### Goal & outcome
Soil uses ambientCG Ground048 (CC0, 1K JPG color, NormalGL, roughness; about 5 MB) from `assets/library/textures/soil/`, copied into `out/<name>/textures/` and referenced relatively in a PBR material. Commit f3ebcdd.
### Decisions & why
- User picked Ground048 (dark crumbly soil, like a loosened bed) from six ambientCG candidates; swapping later is a one-folder change.
- NormalGL, not NormalDX: OGRE uses the OpenGL normal convention.
- Soil visual = grid of 1 m box tiles (`SOIL_TILE`) over one collision box: SDF boxes map the texture once per face, so one big box would stretch it.
### Lessons / gotchas
- Relative PBR map paths also resolve against the world file (render run from /tmp worked).
### State
Branch m1d-variants. Validated: pytest (23), ruff, `gz sdf -k`, headless oblique and top-down renders show textured soil without visible tile seams.
### Open items
- Next: checkpoint 4 (cameras + `pixelfield render`).

## 2026-10-01 M1d checkpoint 4: cameras and pixelfield render
### Goal & outcome
world.sdf has two static placeholder cameras, 1.0 m from the Field centre, looking north: top-down and 45 degree oblique (1920x1080, hfov 60 deg, 2 Hz, save path `renders/<name>`, topic `camera/<name>`). `pixelfield render <world.sdf>` runs gz headless from the out dir with one `gz topic -e` per camera, keeps the last frame as `renders/top.png` / `renders/oblique.png`, about 12 s. Commit f117e22.
### Decisions & why
- Render code in exporters/gazebo (`render()`), CLI only wires it: simulator code stays in the Exporter.
- gz run with cwd = out dir: camera save paths are cwd-relative, this keeps world.sdf relocatable.
- Fails loudly if a camera saved no frames (hint: more iterations).
### Lessons / gotchas
- Opening the world interactively from the repo root and subscribing to a camera (e.g. Image Display) would save PNGs into ./renders/; harmless, only happens when subscribed.
- Top-down at 1.0 m sees about 1.15 x 0.65 m: the canopy (foliage radius about 0.2 m) fills most of it and spills over the Pixel edge.
### State
Branch m1d-variants. Validated: pytest (25, including a real headless render), ruff, `pixelfield render` on carrot_pixel produced both images. Realism judgment UNVERIFIED (user compares with a real carrot photo).
### Open items
- User: judge renders vs real photos (M1d check). Known look gaps: flat maple-like leaflets vs feathery real carrot leaves, no hue variation, GI barely visible.
- Then push, PR, review, merge; next M1e (Docker).

## 2026-10-01 M1d: look tuning after first renders
### Goal & outcome
User judged the first renders: leaves too big and coarse, no color variation, GI invisible, top-down view all canopy. Changed: leaflets now divided again (3-4 narrow segment pairs on a midrib, leaflets 40% shorter), one sampled shade per Variant mixing root/petiole/leaf colors between two ends, ambient 0.4 to 0.1, top camera at 1.7 m (oblique stays 1.0 m). Variants regenerated (max 3,334 triangles, library 2.0 MB).
### Decisions & why
- Finer geometry over alpha-textured leaf cards: only the generator changes; cards are the fallback if M2 performance fails.
- Color variation baked per Variant, not per Plant in Gazebo: 24 shades with no Exporter change; Manifest `hue_shift` stays unused in Gazebo.
- `MAX_TRIANGLES` 3000 to 8000 (M1c limit) so the finer leaves fit with headroom.
### Lessons / gotchas
- With ambient 0.4 the flat fill hid VCT GI; at 0.1 the canopy interior and shadows gain depth (A/B renders).
### State
Branch m1d-variants. Validated: pytest (25), ruff, regenerated library, A/B renders. User verdict on the new look UNVERIFIED.
### Open items
- User: judge the A/B and new renders; keep or drop GI.
- Then push, PR, review, merge; next M1e.

## 2026-10-01 M1d: GI kept
### Goal & outcome
User judged the A/B: low ambient plus VCT GI is clearly better, GI stays.
### Decisions & why
None beyond keeping GI.
### Lessons / gotchas
- `out/<name>/meshes/` is only refreshed by `pixelfield build`; after `pixelfield generate`, rebuild before opening the world, or Gazebo shows the old Variants.
- The GUI ignores the Sensors-plugin GI, so with ambient 0.1 its shadows look darker than in the renders.
### State
Branch m1d-variants, validated as before; user re-checks the rebuilt world in the GUI.
### Open items
- Push, PR, review, merge; next M1e.

## 2026-10-01 M2 preview: 10x10 smoke test
### Goal & outcome
Before Docker, checked whether the finer leaves hold up at M2 scale. A 10x10 carrot Field (3,058 Plants, spec in gitignored `out/carrot_10x10.yaml`) builds in 0.16 s and renders headless in about 37 s at about 550 MB VRAM. In the GUI, Play seemed ignored and the RTF was 0.3. Cause: the Physics system with 3,058 separate models (even static, no collision). Grouping Plants as visuals in one model per Pixel (100 models) gives RTF 1.0 with Physics, Sensors and GI kept; user confirmed 99.97% RTF in the GUI at about 960 MiB VRAM.
### Decisions & why
- No code change now: grouping makes a Plant no longer its own model, which affects M4 pull-out and per-Plant labels, so it is a design decision. It is the first grill topic of M2, ahead of Docker (M1e).
- Leaf geometry (fine segments, about 3k triangles) stays: rendering and VRAM are not the bottleneck.
### Lessons / gotchas
- Hybrid laptop (Intel Arrow Lake + NVIDIA, PRIME on-demand): the gz GUI renders on Intel by default (nvidia-smi shows about 100 MiB). Run it on NVIDIA with `__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia gz sim ...`. Headless rendering already uses NVIDIA through the EGL vendor setting.
- Measured RTF (10x10, server only): as built 0.3 after a 20 s stall; without Sensors/GI 0.3-0.5; without Physics 1.0; grouped per Pixel 1.0 after 4 s.
- `pkill -f "gz sim"` inside a `bash -ic '...gz sim...'` kills that shell itself; use a script file.
### State
Branch m1d-variants, PR #5 open (unchanged by the smoke test). Test worlds (`world_grouped.sdf` and variants) only in gitignored `out/carrot_10x10/`.
### Open items
- User: review and merge PR #5.
- M2 grill, first topic: Plant grouping per Pixel vs per-Plant models (M4 pull-out, labels). Then Docker (M1e).
- Decide whether the PRIME offload env goes into CLAUDE.md known issues and ~/.bashrc.

## 2026-10-01 NVIDIA as default for the gz GUI
### Goal & outcome
`~/.bashrc` now wraps `gz` in a function that sets PRIME render offload (`__NV_PRIME_RENDER_OFFLOAD=1`, `__GLX_VENDOR_LIBRARY_NAME=nvidia`), so only Gazebo runs on NVIDIA. CLAUDE.md known issues documents it (in PR #5).
### Decisions & why
- gz-only function instead of exporting the variables globally: other OpenGL apps stay on the Intel iGPU.
### Lessons / gotchas
- `pixelfield render` calls gz via subprocess and does not see the shell function; it already uses NVIDIA through EGL.
- Backup of the previous ~/.bashrc in the session scratchpad only.
### State
Branch m1d-variants. Validated: new interactive shell resolves `gz` to the function, `gz sim --versions` works, the offload env gives an NVIDIA OpenGL renderer. GUI on NVIDIA through the function UNVERIFIED (user checks nvidia-smi with gz open).
### Open items
- Review and merge PR #5; then M2 grill (Plant grouping first).

## 2026-10-01 M2a: Plants grouped per Pixel in Gazebo
### Goal & outcome
M2 grill, first topic settled and built. The Gazebo Exporter now writes one static model per Pixel (`r<row>c<col>`, at the Pixel's south-west corner) with its Plants as visuals named by Plant id. 10x10 carrot Field: 103 models instead of 3,061, headless server RTF 1.00 with Sensors and GI, 514 MiB VRAM. carrot_pixel renders are pixel-identical to main. ADR 0007 added; spec §10 and §12.5, ADR 0006 and exporters README updated. Commits 9e316e7, edfe82b.
### Decisions & why
- Group per Pixel, not per row or Field: Pixel is the domain unit and the M4 swap unit. Per-Plant path deleted, no switch (no current user).
- Gazebo labels: semantic segmentation only, one Label plugin per Pixel model (M2b). Per-Plant boxes from the Manifest only when a consumer needs them; datasets from Blender later (ADR 0005).
- M4 pull-out: spawn a Plant model near the gripper and remove its grouped visual from the custom C++ system (ADR 0006).
- Order: M2a, then M1e (Docker), then random mode, Path Gaps and perf record (own grill round).
### Lessons / gotchas
- From gz source (not yet run): segmentation instance ids and bounding boxes are per top-level model, labels on visuals do not split them. `visual_config` ignores `visible`; `/world/<w>/remove` only takes models and lights. Label values 0-255.
- SDF pose rpy applies roll before yaw, so one visual pose (roll pi/2 for glTF y-up, then Plant yaw) replaces the old model-yaw plus visual-roll pair.
- Renders in `out/carrot_pixel/renders/` can be stale (older Variants and camera); compare against a fresh render of main in a git worktree.
- Non-interactive shells miss the `~/.bashrc` gz env; the render test fails there unless `GZ_CONFIG_PATH` and the EGL vendor are exported.
### State
Branch m2a-grouping. Validated: pytest (25), ruff, `gz sdf -k` on carrot_pixel and 10x10, headless RTF and VRAM, pixel-identical renders. GUI RTF on 10x10 with the new Exporter UNVERIFIED (smoke test hand-made world gave 99.97%).
### Open items
- User: open `out/carrot_10x10/world.sdf` in the GUI, check RTF about 1.0; then push, PR, review, merge.
- Next: M2b (Label plugin per Pixel model plus semantic segmentation camera, proves the gz label facts by running).

## 2026-10-01 Docker image deferred
### Goal & outcome
M1e (Docker) removed from the M1 chunk table and the M1 row; the spec now defers it until the first colleague or student needs to run the world. Commit b91b060 on m2a-grouping.
### Decisions & why
- Nobody waits on the image, development is native and Field generation needs no Docker (ADR 0002); an image built now would drift while the M2 stack still changes.
### Lessons / gotchas
None.
### State
Branch m2a-grouping, doc-only change, not pushed (the user pushed the earlier commits).
### Open items
- The M1 row still lists installing `ros-jazzy-ros-gz`, which CLAUDE.md defers until a chunk needs ROS topics; decide whether to move it out too.
- Order now: M2a merge, M2b labels, then the grill for random mode, Path Gaps and perf record.

## 2026-10-01 ros-gz deferred, PR #6 opened
### Goal & outcome
Spec M1 row no longer lists installing `ros-jazzy-ros-gz`; the deferred note covers it (until a chunk needs ROS topics). M1 is now complete per the spec. Branch pushed, PR #6 opened for M2a plus both deferrals.
### Decisions & why
- Matches CLAUDE.md, which already deferred ros-gz; the spec row was the only place still requiring it.
### Lessons / gotchas
None.
### State
Branch m2a-grouping, PR #6 open. Validated as in the M2a entry; GUI RTF on 10x10 UNVERIFIED (review check).
### Open items
- User: GUI RTF check, review and merge PR #6.
- Next: M2b labels (Label plugin per Pixel model plus semantic segmentation camera).

## 2026-10-02 M2b labels deferred
### Goal & outcome
M2b (Label plugin per Pixel model plus a semantic segmentation camera) is deferred, not built. Spec §12 "Open (deferred)" item 4 records it with the decision already made.
### Decisions & why
- Deferred: no consumer yet. The M2 check does not need labels, ADR 0005 puts labelled datasets in Blender, and the robot stack (M5) is far off. Build it when M5 oracle perception or M6 Gazebo training data needs it.
- Label id per Crop is stable and stored in the Crop definition (not per Field alphabetical), so datasets from different Fields agree. Soil and background are 0.
### Lessons / gotchas
- If the M2 perf record should include a segmentation camera, M2b has to come first; currently it does not.
### State
Branch m2-defer-labels, doc-only change, committed, not pushed.
### Open items
- User: push and merge if happy.
- Next: grill round for random mode, Path Gaps and the M2 perf record.

## 2026-10-02 M2c-e: random mode, Path Gaps, perf record
### Goal & outcome
Grill settled random mode, Path Gaps and the perf record; all three built as stacked branches m2c-random (9335191), m2d-path-gap (639fa54), m2e-perf (3d06471). Random Specs resolve to the same grid as hand-drawn ones; Path Gaps widen the Field; `docs/design/perf.md` holds the record. The 10x10 random Field (2,760 Plants, 93 models) runs at 1.00x headless as built. At 30 Hz cameras VCT GI drops it to 0.05x (single Pixel keeps 1.00x, no GI keeps 1.00x).
### Decisions & why
- `empty_fraction` exact count, not per-Pixel chance: predictable for tests and perf comparisons.
- `no_same_neighbour` over edge neighbours only, Empty Pixels exempt, solved by backtracking (fails with an error, never silently empties a Pixel). Skews the weights: with two Crops the Field is near a checkerboard; documented, not corrected.
- Grid draws use their own stream `"{seed}:grid"`, so a hand-drawn copy of a random grid gives identical Plants.
- Path Gaps shift columns east (Field widens, Pixels stay whole), columns only, none at the edges; `every_n_cols >= cols` means no gap. Geometry lives on `FieldSpec.column_x/width/depth`.
- Manifest field gains `width`, `depth`, `path_gap` (additive, format_version stays 1).
- Perf measured manually with documented commands, no `pixelfield perf` command yet.
- Extra perf rows at 30 Hz added (not in the plan) because the world's 2 Hz placeholder cameras make "active camera" meaningless.
### Lessons / gotchas
- Cameras without a subscriber may not render; subscribe with `gz topic -e` when measuring.
- At 30 Hz, PNG saving costs another ~20x; GI cost grows with Plant count.
- Unexplained: GI at 30 Hz shows 16.8 camera frames per wall second at RTF 0.05; re-check before relying on it.
- `pkill -f "gz sim"` in a Bash tool command kills the tool's own shell (exit 1, no output); keep it in a script file.
### State
Branches m2c-random, m2d-path-gap (on m2c), m2e-perf (on m2d), not pushed. Validated: pytest (53), ruff, `gz sdf -k` and headless render of `examples/random.yaml`, headless perf runs. GUI row in perf.md UNVERIFIED (user runs it). Hand check of `out/random/field.svg` by the user pending.
### Open items
- User: view `out/random/field.svg` and `out/random/renders/`, run the GUI row, push and PR (stacked or squashed into one, user's call).
- Discussion: the budget passes only at 2 Hz. Decide what "active camera" means (rate) and whether GI stays on for robot cameras on large Fields (GI off, GI only in `render`, or accept).

## 2026-10-02 M2e: perf record corrected, CiVCT ruled out
### Goal & outcome
User asked whether GI could cover only what the camera sees. CiVCT does exactly that, but Harmonic's Sensors system rejects it (`GI CI VCT is not supported`, run confirmed). While testing VCT settings, single `/stats` RTF readings proved unreliable (0.04 to 1.0 in one run). Averaged over 20 s: 10x10 at 30 Hz is 0.60x with GI, 0.66x without, 0.07x with PNG saving; single Pixel 0.97x. perf.md rewritten (a68964c). The earlier "GI drops 10x10 to 0.05x" conclusion was wrong.
### Decisions & why
- Perf record uses averaged RTF (sim time over a wall window) only.
- GI stays: it costs about 10%; the bottleneck is rendering two full-HD cameras of 2,760 detailed Plants at 30 Hz.
### Lessons / gotchas
- When sensors block the simulation, `real_time_factor` in `/stats` is an instantaneous value that swings wildly; never quote single readings. Camera rate ≈ update rate x RTF is a consistency check.
- In `gz topic -e` text output, match `$1=="sec:"`, not `/sec:/` (also hits `nsec:`).
### State
Branch m2e-perf (stacked on m2d, m2c), not pushed. Validated: averaged headless runs. GUI row UNVERIFIED.
### Open items
- Discuss: 0.6x at 30 Hz passes the 0.5x budget but misses the 1.0x target. Levers: one robot camera instead of two render cameras, lower resolution, lower rate, simpler Plants far from the camera (LOD). Decide when the real camera is known (spec open item 1).
- User: GUI row, SVG check, push and PR.

## 2026-10-12 Prior art: plant physics, soil, games, asset generation
### Goal & outcome
Side research recorded so later design chats see it: `docs/research/prior-art.md` gained sections on plant physics for manipulation, soil and terrain, farming games and asset generation, plus AgriGen and Agri-Sim rows. ADR 0006 (still proposed) lists M4 candidates; spec §12 deferred items 5 (growth stages) and 6 (soil mechanics). Commit 51ab8b8.
### Decisions & why
- Nothing decided, only recorded: ADR 0006 stays `proposed`, no new ADR, CONTEXT.md untouched (no new terms fixed).
- Leading M4 candidate: leaves as a pseudo-rigid-body spring chain in plain SDF (field-validated, cheap), root kept as the force-threshold detach (OrchardBench uses the same tether pattern).
- Soil stays a rigid plane; deformable terrain (Chrono SCM) only as a separate Exporter if sinkage becomes a research question.
### Lessons / gotchas
- No uprooting simulation exists in any simulator found; supports publication point 2.
- Games (Farming Simulator 25) offer ideas only: proprietary engine and assets, no plant contact physics.
- Artisan (LLM articulated asset generator) does not fit Variants (no plants, not deterministic); borrow only its simulation stability check.
- Unverified: gz-sim `WheelSlip` details, whether Gazebo Plants targets gz-sim.
### State
Branch docs-prior-art-physics (from origin/main), doc-only, committed, not pushed. Branch m2e-perf left untouched.
### Open items
- User: review, push and merge.
- Missing sources: soil friction coefficient, root slip distance before detach.

## 2026-10-16 M3a: OAK-D camera perf check, LOD ruled out
### Goal & outcome
M3 started (Crops: carrot, beetroot, long red radish, head lettuce; decofoodshop.nl props as visual reference only). First chunk measured an OAK-D-like rig (RGB 1920 x 1080 HFOV 66, depth 640 x 400 HFOV 80, both 30 Hz, 1.0 m) on `random_10x10`. Result: 0.50x in every pose (45 degrees along rows at Field edge or centre, nadir), 0.83x on a single Pixel. Triangle LOD is not part of M3. perf.md, spec open item 1 and CLAUDE.md (driver gotcha) updated, commit 4c527c9.
### Decisions & why
- No LOD: GPU at about 16% while one gz server thread is pegged at 100%, so rendering is CPU-bound on render items (3 meshes per carrot Variant, about 8,300 items), not triangles.
- Pose A (45 degrees down, along rows) is the planned mount; nadir is the current real mount. Both measured; they give the same RTF.
- Rig measured as hand-edited worlds (M2e method), no Exporter change until the real mount height and angle are known.
### Lessons / gotchas
- The 0.60x row from 2026-10-02 re-measures at 0.37x today, after the NVIDIA 595.84 to 595.99 and kernel -34 to -38 upgrades. Cause not isolated; compare only rows from the same system.
- The cost scales with all Plants in the Field, not those in view: sun shadows draw every Plant (shadows off 0.62x).
- `pkill -f "gz sim"` also matches any tool command line that merely contains that text, including a heredoc that writes a script. Write the script in one call, run it in another. Piping a measure script into `head` kills it before cleanup and leaves a server running that skews the next run.
- Driver/library mismatch confirmed in the journal at the 11:18 upgrade (`Failed to initialize NVML`).
### State
Branch m3a-camera-perf, doc-only, committed, not pushed. Validated: averaged headless runs (numbers in perf.md). Rig worlds and scripts only in gitignored `out/` and the session scratchpad.
### Open items
- Cheap CPU levers for later: one mesh and material per Variant (fold into the shared root generator design), shorter shadow distance, merged render mesh per Pixel.
- Optional: isolate the driver vs kernel regression.
- `renders/` untracked on main: delete or gitignore (user's call).
- Spec §12 item 7 still lists lettuce, onion, bean; update during the naming grill.
- Next: grill on Variant naming with a growth stage slot and a shared root crop generator.

## 2026-10-16 M3 grill and m3b: root_crop generator, stage slot, one mesh per Variant
### Goal & outcome
Grill settled Variant naming and the root crop generator design; m3b built it (stacked on m3a). `carrot.py` became `root_crop.py` with per-Crop ranges in `CROPS`; Variants are `<crop>_harvest_v<NN>`; each `.glb` is one mesh with one material sampling an sRGB palette texture. 10x10 OAK-D rig: 0.50x to 0.61x (nadir), 0.51x to 0.59x (edge). ADR 0008; spec M3 row, items 1, 5, 7 and §8 updated. Commits fd8c8ea (refactor, byte-identical Variants), 00d851f (merge plus docs).
### Decisions & why
- Name `<crop>_<stage>_v<NN>`, flat folder, stage as a plain word, optional `assets.stage` (default `harvest`); Manifest keeps only `variant`. Rename done now so later stages never rename the library.
- Crop names `carrot`, `beetroot`, `radish`, `lettuce`; variety in the Crop definition. Lettuce gets its own generator (m3e).
- One generator module for root crops; leaf shapes as named builders come with beetroot (m3c), not before.
- Palette texture over vertex colors: gz-common `SubMesh` has no color channel. Parts keep separate inside `variant()`, merge only on write, so M4 can export articulated foliage for the spawned Plant.
- User rejected capsule plus cylinder collision as unrealistic for grasping. Unused `collision:` keys removed from Crop YAMLs and spec; M4 direction recorded: convex low-poly root from the real profile, per-leaf spring petiole chains. Where the gripper grasps (leaf bunch or shoulder) is the first M4 question.
- Chunk order: m3c beetroot, m3d radish, m3e head lettuce, m3f soil blend plus a four-Crop example Field. User supplies real photo links per Crop for the look check; nothing committed.
- Pillow added to the `generate` extra and dev group only (trimesh needs it for textures).
### Lessons / gotchas
- glTF `baseColorFactor` is linear, texture texels are sRGB: writing the factor values straight into the palette made Plants clearly darker. Encoded, renders match main within 0.1/255 mean.
- One UV per part gives a zero UV gradient, so sampling stays at mip 0 and part colors do not bleed at distance.
- `pkill -f "gz sim"` also matches a tool command whose heredoc only writes a script containing that text. Write scripts and run them in separate calls.
- 3x fewer render items gave about 20% more RTF, not 3x: shadows and per-frame overhead remain.
### State
Branch m3b-root-crop (on m3a-camera-perf), committed, not pushed. Validated: pytest (53), ruff, `gz sdf -k`, render comparison against main, averaged headless perf runs. Look of the merged Variants in the GUI UNVERIFIED (renders identical, GUI not opened).
### Open items
- User: review m3a and m3b, push and PR (stacked).
- `renders/` untracked in the repo root (from running `render` there): delete or gitignore.
- Next: m3c beetroot; needs real beetroot photo links from the user.

## 2026-10-16 Perf: gz upgrade fixes the 10x10 camera cost; active region parked
### Goal & outcome
User wanted a real fix instead of tweaks ("render only what the camera sees"). Research (gz source) found per-visual CPU fixes in gz-rendering 8.3.0 and gz-sim 8.15.0, already in apt. After the user upgraded: 10x10 with the OAK-D rig 0.96x nadir, 0.92x edge (was 0.61/0.59), old two-camera baseline 0.95x (was 0.37), single Pixel 1.01x. perf.md and CLAUDE.md (minimum versions) updated, commit on m3b-root-crop. The OAK-D rig worlds in `out/` now show a body box and yellow field-of-view lines in the GUI, hidden from the rig's own sensors.
### Decisions & why
- Active region (Field Manager gz-sim system: merged far Pixels, detailed near the robot, dynamic only for the grasped Plant) agreed as the right design if needed, as its own milestone merged with M4. Not needed for a 10x10 Field now; grill Q1-Q5 (performers plus radius, Pixel as swap unit, free-running camera, plugin in exporters/gazebo/systems/, opt-in fallback) left unanswered.
- No event-driven Gazebo fork: lockstep sensor sync and repeatability are worth keeping.
### Lessons / gotchas
- Check upstream changelogs and apt candidates before designing around a performance problem: the "real solution" was a package upgrade.
- From gz source: in-memory meshes (`name://`) are invisible to the separate GUI process; triggered cameras (`<triggered>`) stop blocking the sim between triggers; sensors without subscribers are skipped; gz-sim never marks visuals static and sets every pose every frame; gz-rendering 8 hardcodes 500 m shadow range and 3 PSSM splits.
- SDF `<visibility_flags>` on visuals plus `<visibility_mask>` on sensors hides GUI-only markers from robot cameras (verified: 0 marker pixels). A plain OBJ with an SDF material rendered flat white and opaque; primitives work.
- Heavy gz runs slow the user's laptop: ask for a slot before running them (memory saved).
### State
Branch m3b-root-crop, committed, not pushed. Validated: averaged headless runs after the upgrade. perf_event_paranoid still 4, no CPU profile taken (no longer needed).
### Open items
- User: review and push m3a and m3b.
- Next: m3c beetroot (photo links from the user).
- Active region grill when Fields grow beyond 10x10 or at M4.

## 2026-10-16 m3c: beetroot Variants
### Goal & outcome
Beetroot added through the root crop generator: `globe` root profile (top-shaped, thin taproot, a third to half above soil), `simple` leaf builder (ovate blade, blunt tip, wavy margin, slight cup; the red stalk tube runs on as the midrib), per-Crop leaf curve so stalks fan out in a V. 24 Variants (2.1k to 3.2k triangles, 1.6 MB), `crops/beetroot.yaml`, `examples/beetroot_pixel.yaml` (12 Plants), spec §8 bullet. Commit a9f8fc1 on m3c-beetroot (from m3b).
### Decisions & why
- Grill: midrib only (no vein texture, side veins are a few pixels at 1 m), round red table beet at harvest, 2 rows 0.25 m apart at 0.08 m in-row, pull-out 30 to 60 N guessed, user photos stay out of the repo.
- Margin 0.05 instead of the discussed 0.125: with 0.125 the layout fits only 4 Plants per row (8 per Pixel), not the intended 12.
- Of the 7 user photos, 1 to 4 are the reference; 5 and 6 look AI-generated (layout only); 7 is Swiss chard.
- Beet colors are written as linear factors with their sRGB targets in comments, since the palette encodes linear to sRGB.
### Lessons / gotchas
- A quick flat-shaded PIL sketch of `variant()` parts (scratchpad `sketch.py`) catches shape errors in seconds without Gazebo: it showed the first beet as an umbrella (blades flat on top) because the carrot curve droops; per-Crop `leaf_arch`, `leaf_reach`, `leaf_tip` fixed it.
- Keeping carrot rng call order unchanged keeps its Variants byte-identical; checked after each generator change.
### State
Branch m3c-beetroot, committed, not pushed. Validated: pytest (54), ruff, `gz sdf -k` on beetroot_pixel and beetroot_variants, carrot bytes unchanged, PIL sketches. Gazebo render and look vs photos UNVERIFIED (render needs a slot from the user).
### Open items
- Headless render of `out/beetroot_pixel/world.sdf` (about 15 s) when the user allows, then compare with photos 1 to 4.
- Known look gaps: no side veins, no rough crown, one roughness for the whole Plant (beet leaves are glossier).
- Next: m3d radish.

## 2026-10-16 M3 build-out: radish, lettuce, soil atlas, four-Crop example
### Goal & outcome
User asked to implement the rest of M3 in one go. Built as stacked branches: m3d-radish (48c1f0b: `spindle` root, `lobed` lyrate leaves, root color fade to a white tip), m3e-lettuce (0afc641: romaine generator `lettuce.py`, reusing root_crop helpers), m3f-soil (da58678: two CC0 soils blended into a seamless 4 x 4 atlas of 1 m tiles, Exporter picks tile (i % 4, j % 4); `examples/m3_crops.yaml` with all four Crops, seed 8 for 7 to 9 Pixels each). Also on m3c: 0d4186e regenerates the beetroot library, which had been committed from the first draft.
### Decisions & why
- Reference photos: radish 9 and 10 (8 color only, 11 is AI-looking round radish); lettuce 13 and 14 are romaine, so "head lettuce" became romaine (12 is loose-leaf, frill only).
- Root fade: a palette column holds a vertical gradient and v follows height, keeping one mesh and one material per Variant.
- Soil: bake offline into the library (ADR 0003 style) instead of per-Field at build time, so the Exporter needs no Pillow at runtime. Masks are sums of sines with whole periods over 4 m, so tiles are seamless; the pattern repeats every 4 m, beyond the camera's view. Dry patches capped at 45% mix ("mild" per spec). Normals stay the base soil's (gap: dry patches have the base relief). Ground104 and Ground036 rejected (yellow sand, grey debris).
- Lettuce `variants.json` holds foliage only; no root mesh.
### Lessons / gotchas
- Generating a library, then changing the generator and committing without regenerating, shipped stale beet Variants. New tests regenerate v00 per Crop and compare bytes with the committed file.
- trimesh flips v on glTF export (bottom-left vs top-left origin): constant v = 0.5 hides it, a gradient exposes it.
- gz-common `CreateBox` top face: u runs north to south along y, v east to west along x; the soil atlas is baked in that orientation (from source, render check pending).
- Writing a file twice from one original string in a Python edit script silently drops the first edit.
### State
Branches m3d-radish, m3e-lettuce, m3f-soil (stacked on m3c, m3b, m3a), committed, not pushed. Validated: pytest (63), ruff, `gz sdf -k` for all examples, PIL sketches, atlas seam test. Gazebo renders of the new Crops, the soil and the four-Crop Field UNVERIFIED (need a slot from the user; script ready in the session scratchpad). Validator agent running.
### Open items
- User: render slot for the M3 look check (about 70 s), then compare with photos.
- Look gaps: no side veins on beet, no rough crown, one roughness per Plant, shared soil normals, lettuce crinkle only geometric.
- Review and merge the six stacked branches (m3a to m3f).

## 2026-10-16 M3 validation fixes
### Goal & outcome
Validator agent found no blocking bugs (all 96 Variants fresh and deterministic, no NaN, UVs inside their palette columns, radish fade correct, CreateBox mapping confirmed by a compiled probe against libgz-common5). Fixed its confirmed findings in 26eda5e on m3f-soil: freshness tests over every Variant, ValueError for leaves running straight up (was NaN), stronger soil seam test, atlas size tied to the Exporter, stale tiles removed on rebake, only the shared normal map copied into builds, README parts list.
### Decisions & why
- All fixes on the top branch m3f-soil; the stack merges in order, so m3d and m3e do not carry them on their own.
### Lessons / gotchas
- Seam tests on full-resolution textures drown in texture grain; low-pass to the scale of the mask first (32 px per m), then wrong mappings score 3.9+ against 1.36.
### State
Branch m3f-soil, committed, not pushed. Validated: pytest (65), ruff, `gz sdf -k` for all 9 examples. Gazebo look of radish, lettuce, soil and the four-Crop Field UNVERIFIED (render slot).
### Open items
- Suspicions not confirmed: mip bleed on the fading radish root at distance, irregular radish lobe notches at 4 pairs, lettuce lighting from below (no `_face_up`), rotated rows can leave lettuce Pixels empty (core, older).
- Render slot, then the look check; review and merge m3a to m3f.

## 2026-10-16 M3 render check against photos
### Goal & outcome
Headless renders (top, oblique) of beetroot_pixel, radish_pixel, lettuce_pixel and m3_crops compared with the user's photos. Beetroot matches best (crimson globes a third above soil, red stalks fanning out, red midribs). Radish reads as radish (red shoulders, pale stalks) but its leaves look like smooth round paddles, lobes barely show. Romaine reads as an upright head with a pale heart and white midribs, but faceted and too dark, no visible crinkle or frill. Soil: mild lighter and darker patches, no tile seams visible in any render.
### Decisions & why
None; gaps recorded for a look-iteration chunk.
### Lessons / gotchas
- At 1 m camera distance, flat single-color blades look plastic; venation and color variation across a leaf matter more than more geometry for beet and radish.
- Geometric crinkle of 2.5 mm on 12 stations is invisible; lettuce needs finer mesh or a normal/detail texture.
### State
Branch m3f-soil, PR #10. Renders in gitignored out/<world>/renders/. Look judged by the agent only; user verdict pending.
### Open items
- Look iteration (proposed m3g): lettuce lighter yellow-green, more stations and stronger frill; radish deeper lobes with more stations; leaf textures with veins and color variation per Crop (palette design change, needs discussion).

## 2026-10-19 M4 design settled (m4a)
### Goal & outcome
Grilled the M4 pull-out design (28 questions) and wrote it down: ADR 0006 rewritten and accepted (renamed to match its new title), spec sections 2, 3, 6, 8, 10, 11 (M4 chunk table m4a to m4e) and 12 (deferred items 7 soil state and tear-off, 8 MuJoCo training engine) updated, `docs/research/measurement-protocol.md` added, uprooting and MuJoCo research added to prior-art.md, Pull-out Curve added to CONTEXT.md.
### Decisions & why
- Target is a learned pull policy on low-dimensional state, so realism goes into the force on the gripper over the pull and the leaf bunch bending, both as cheap lumped models with measurable parameters. No particle soil (geotechnics cost, unmeasurable parameters).
- Pull-out Curve (rise to the Pull-out Force at 5 mm, drop to 0.3 of it, linear decay to 0 over the root length, then detach) on an anchor link with a vertical prismatic joint, root welded by a DetachableJoint our system creates. Reason: Gazebo has no break-at-force joint and DetachableJoint has no force readout.
- Petioles: 3 links per leaf on universal joints, because dartsim ignores springs on ball joints and revolute bends in one plane only.
- Engine-agnostic Variant physics export (JSON plus convex OBJ hulls) so a later MuJoCo Exporter and Gazebo share one Plant model.
- Crown tear-off dropped for M4: tops take 212 to 243 N against 20 to 22 N pull-out in loose soil.
- Pull-out Curve gets a damping term `c * v` (`pull_out_damping`, default 0), agreed after the grill: a guessed `c` would invent a speed penalty, so it stays off until the protocol's second pull speed measures it. A speed-dependent peak, if measured, needs a curve change, not just `c`.
- Added during writing, not explicitly grilled: once past the peak the curve does not climb back if the root is pushed down (soil bond broken), and the prismatic range is 0 to root length.
### Lessons / gotchas
- dartsim freezes a body welded to a static model (`setMobile(!Static())`): anchor in a non-static model.
- MuJoCo has no glTF import and collides meshes as convex hulls, so the physics export uses OBJ hulls.
### State
Branch m4a-design, commit 601b2a5, not pushed. Docs only. Validated: relative links resolve, no em-dashes, ruff, pytest (65). Design itself UNVERIFIED until m4c and m4d run.
### Open items
- Maintainer reads the docs (m4a check), then m4b-physics-export.
- Measurement protocol pull speed (about 5 cm/s) is a suggestion, not a decision.

## 2026-10-19 M4b physics export
### Goal & outcome
The root crop generator writes, per Variant, `<variant>.physics.json` (links with pose, mass, center of mass, inertia and a convex hull in link frame; universal petiole joints with stiffness and damping; root length and depth) and `<variant>.articulated.glb` (one visual mesh per link). Library regenerated for carrot, beetroot and radish; static `.glb` files and `variants.json` stayed byte-identical. ADR 0006, spec and library README updated to match.
### Decisions & why
- Agreed in discussion: hulls inside the JSON (about 30 per Variant, 2,000 files otherwise); an articulated glb per Variant for link visuals (`<submesh>` in Gazebo); generation-time material constants in the generator's CROPS table, runtime Pull-out Curve knobs in the Crop YAML; petiole damping as a damping ratio, so damping scales by s^4.
- Physics constants drawn from their own stream (`Random(f"physics-{index}")`) so visuals never shift.
- Pull-out Curve ends at `root_depth` (length below the soil), not the full root length: the root is out once its buried part has travelled. ADR wording fixed.
- Petiole mass from a round rod, not the 3- or 5-sided tube; inertia from point samples plus a short-cylinder term so the axial inertia never vanishes.
- JSON written compact (half the size of indented); scipy added to the generate extra and dev group for trimesh's convex hull.
### Lessons / gotchas
- trimesh `convex_hull` silently needs scipy (lazy import); now imported up front.
- Library globs counting Variants must use `*_v??.glb`, since `*.glb` now also matches the articulated files.
- Validator caught that mass bounds tested only v00 to v02 and failed on 5 committed Variants; physics tests now read every committed Variant.
### State
Branch m4b-physics-export (stacked on m4a-design), commits 1312b95 and a fix, not pushed. Validated: pytest (69), ruff, validator agent (frames to 1 µm, masses, inertias, joint continuity, determinism), PIL hull sketch. Behaviour in Gazebo UNVERIFIED (m4c).
### Open items
- Smallest link inertia about 8.5e-10 kg m2 and carrot crown stiffness about 0.009 N m/rad: watch solver stability and leaf droop in m4c.
- Carrot tops 14 g for v00 look light (thin visual petioles); calibration later.
- Beetroot root hull is a cone (1.3 to 2.4x root volume); drooping carrot tips give small sail-shaped hulls; whole blade rides on the last link.
- Root crop library 6.8 MB to 14.9 MB.

## 2026-10-19 M4c articulated SDF and settle check (first part)
### Goal & outcome
`exporters/gazebo/plant.py` builds the scaled SDF of one Plant from its Variant physics export (OBJ hulls as collisions, articulated glb submeshes as visuals, universal joints with springs and damping) and a settle world (root welded to the world, soil plane, 1 ms step). `settle_check.py` runs it headless in the system Python through the gz-sim bindings. `pixelfield settle <variant>...` and a slow test over all 72 root crop Variants (`PIXELFIELD_SLOW=1`). Result: carrot v00 does NOT settle by 2 s (19.7 mm/s, leaves travel up to 102 mm, below 1 mm/s only after about 4.5 s); radish v00 settles (0.42 mm/s, 15 mm travel).
### Decisions & why
- Settle check through the gz-sim Python bindings (TestFixture, link velocities from the ECM) instead of parsing topics: in process, tied to the physics step, about 4 s per Variant.
- The script rewrites the world with real_time_factor 0 for the run, so the written world still plays at real time when opened in the GUI.
### Lessons / gotchas
- dartsim silently drops a collision mesh without normals (CustomMeshShape error, submesh ignored): hull OBJs need `vn` lines.
- gz.sim8 bindings return entity ids from `model_by_name`, wrap in `Model(...)`; `world_pose` returns Pose3d only after `import gz.math7`, otherwise a pybind11 abort.
- Carrot leaves stand nearly upright on soft springs (crown about 0.008 N m/rad), an inverted pendulum that leans several cm under gravity with spring_reference 0. A scratch preload (spring_reference = minus gravity torque over stiffness at the generated pose, at most 0.12 rad) kept carrot v00 within 0.1 mm and settled at once.
### State
Branch m4c-articulated-sdf (stacked on m4b-physics-export), commit 87e4c16, not pushed. Validated: pytest (71 passed, 72 slow skipped), ruff, `gz sdf -k`, settle runs of carrot v00 and radish v00. Link visuals in the GUI UNVERIFIED (submesh names not yet seen loaded). Slow test over 72 Variants not run yet (needs a slot).
### Open items
- Decide: gravity-preloaded spring references (generated pose is the equilibrium) versus spring_reference 0 as in ADR 0006.
- Run the 72-Variant slow test, then the GUI hand check.

## 2026-10-19 M4c spring preload
### Goal & outcome
Petiole joints now carry a spring reference that holds the generated shape against gravity, computed by the generator at scale 1 and scaled by s in the SDF. Library physics exports regenerated (glb files unchanged). Settle check: carrot, beetroot and radish v00 all settle (at most 0.03 mm/s after 2 s, 0.1 mm travel).
### Decisions & why
- The generated shape is the shape under gravity (agreed): a spawned Plant must look like its static Variant, and a reference of 0 made carrot leaves lean up to 10 cm. ADR 0006 and spec updated.
- Gravity 9.81 in the generator against Gazebo's default 9.8: the 0.1% mismatch leaves sub-millimetre sag, not worth an engine-specific value.
### Lessons / gotchas
- A spring reference scales with s (gravity torque s^4 over stiffness s^3).
- `gz sim world.sdf` opens paused; a preloaded Plant does not visibly move on play, by design.
### State
Branch m4c-articulated-sdf, commits 87e4c16 and the preload commit, not pushed. Validated: pytest (71 passed, 72 slow skipped), ruff, settle runs of three Variants. 72-Variant slow test not run (needs a slot). Link visuals in the GUI UNVERIFIED.
### Open items
- GUI hand check of link visuals; scale extremes (0.85, 1.15) not checked.

## 2026-10-19 M4c slow settle test
### Goal & outcome
`PIXELFIELD_SLOW=1 uv run pytest -k settles`: all 72 root crop Variants settle at scale 1 (72 passed, 5 min 14 s). User checked the carrot settle world in the GUI: link visuals look right.
### Decisions & why
None
### Lessons / gotchas
- Leaf blades have no visual thickness by design; their mass comes from `blade_mass_per_area`, so thickness would add triangles, not mass.
### State
Branch m4c-articulated-sdf, commits 87e4c16 and 2839af8, not pushed. Validated: slow test over 72 Variants, GUI visual check by the user. m4c done.
### Open items
- Scale extremes (0.85, 1.15) not checked.
- Next chunk m4d-pullout-system (C++), needs IMPLEMENT.

## 2026-10-19 M4d pull-out system
### Goal & outcome
C++ gz-sim system `PixelfieldPullOut` (`exporters/gazebo/systems/`, plain CMake into `build/systems/`, loaded through `GZ_SIM_SYSTEM_PLUGIN_PATH`) and always listed in Field worlds. On a pick it removes the Plant's grouped visual, spawns the articulated Plant, anchors the root on a vertical prismatic joint with a DetachableJoint weld, applies the Pull-out Curve as the joint force each step, detaches at the root depth and publishes the state. Python `pixelfield pick` (running world, via `gz service`) and `pixelfield pull` (headless scripted pull, CSV log). Scripted pulls: force matches an independent curve evaluation to 1 mN, detach within 0.1 mm of the root depth, peak within 1% of the Plant's Pull-out Force, for carrot, beetroot and radish, scale extremes and 0.01 to 0.2 m/s.
### Decisions & why
- Agreed: CMake build plus GZ_SIM_SYSTEM_PLUGIN_PATH (portable worlds); pick request is a standard `gz.msgs.EntityFactory` with the curve in the Plant SDF as `<pixelfield:pull_out>` (one file describes a pick, no JSON library in C++).
- Decided without asking (user delegated): state topic `gz.msgs.Param` (plant, d, force, attached) every step; Crop YAML curve knobs copied to a new Manifest `crops` section (with the library path) so pick reads only the Manifest; Manifest scale now 4 decimals so the spawned Plant matches its visual; one pick at a time, each Plant id once; scripted pull is a PD lift of the root (5000 N/m, 30 N s/m) on the real Field world without its Sensors system.
- Root collision leaves out the soil's collide bit: the buried root starts inside the soil box and contacts would add to the force law. A dropped detached root falls through the soil.
### Lessons / gotchas
- Removing the weld and the anchor model in the same step freezes the root: dartsim keeps the root in the anchor's skeleton until the weld is gone. Anchor removed one step later.
- Joint position at rest reads about -1e-14: with d_peak 0 the curve divides 0 by 0, so the system validates the curve on request.
- gz-transport delivers the state topic to the in-process subscriber asynchronously: the log matches messages to steps by their sim-time stamp. d is read at the start of a step, lift at its end.
- ElementTree resolves the `pixelfield:` prefix to its namespace URI on parse; look the element up by `{uri}pull_out`.
### State
Branch m4d-pullout-system. Validated: pytest (74 passed, 72 slow skipped; the pull test runs when the system is built), ruff, validator agent (scale extremes, speeds, error paths, pause, reset, re-pick after detach, spawn pose against the static visual), live `pixelfield pick` against `gz sim -s`. Grouped visual removal in the GUI UNVERIFIED (removed from the ECM, seen headless). Non-zero pull_out_damping UNVERIFIED.
### Open items
- GUI check: visual gone and the Plant in its place after `pixelfield pick`.
- A picked Plant that is never fully pulled blocks later picks: release or timeout to decide in m4e.
- The scripted pull lifts with a vertical force only; a detached Plant tips over after a while (test ends 0.6 s after detach).
- Library paths in the Manifest are relative to the repo root, so pick and pull run from there.
- Next: m4e test gripper.

## 2026-10-19 M4d detached root lands on the soil
### Goal & outcome
User test in the GUI: a detached carrot dropped back through the soil to its old spot, because the root never collided with the soil. The system now sets `CollideBitmaskCmd` 0xFFFF on the root's collisions at detach (gz-sim 8.15 changes the bitmask at runtime), so a dropped Plant lands. The scripted pull now lets go past the root depth and logs one more second; carrot, beetroot and radish roots end with their lowest hull point at the soil (about 0 mm, was about minus the root depth).
### Decisions & why
- Fix on the open PR without a new plan: it is m4d's own "Plant moves freely after detach".
### Lessons / gotchas
- The GUI Apply Force Torque button applies the wrench for one step only: an impulse, so it takes hundreds of newtons to pull a carrot out with it. Use the scripted pull or a persistent wrench for a realistic pull.
- A link's world axis-aligned box is the world box of its rotated local box: on a lying beetroot it overshoots the real hull by about 2 cm. Use hull vertices for contact checks.
### State
Branch m4d-pullout-system. Validated: pytest (74 passed, 72 skipped), ruff, scripted pull with drop for three Crops. GUI removal of the grouped visual still UNVERIFIED: the server's scene info still lists the static visual after a pick.
### Open items
- GUI check of the grouped visual (does a static copy stay behind after pulling the picked Plant away?).

## 2026-10-19 M4d several picks and post-peak ratchet
### Goal & outcome
Agreed with the user after a GUI session: any number of Plants can be picked at once (each Plant id once per running world), and after the peak the anchor's lower limit follows the highest point reached (`JointPositionLimitsCmd`), so a part-pulled root that is let go stays where it is. `pixelfield pull --release <m>` lets go early. Validated: a carrot released at 49 mm stays at 49.06 mm for 1 s, still attached; three concurrent picks against `gz sim -s`, each publishing its state, re-pick refused.
### Decisions & why
- Ratchet instead of the residual force pushing a loosened root back down: a real loosened carrot is held by friction. Explicit regularized friction was ruled out: stable only with a slip speed of about 0.1 m/s, which would distort the curve at a 5 cm/s pull. The joint limit is implicit, so stable.
- ADR 0006 and spec updated (no longer one picked Plant at a time).
### Lessons / gotchas
- The user's "broken simulator" was an orphaned `gz sim server` (GUI gone, reparented to systemd, 82% CPU) holding the world name, plus new shells without GZ_SIM_SYSTEM_PLUGIN_PATH: a new `gz sim` then has a twin and picks reach the orphan.
- While the ratchet holds a root, the state topic's force is the commanded residual force, taken up by the joint limit.
- A heredoc ends a `&&` chain: commands on the following lines run even when the lint before it failed.
### State
Branch m4d-pullout-system, pushed (PR #14). Validated: pytest (75 passed, 72 skipped), ruff, partial pull, live concurrent picks. GUI removal of the grouped visual still UNVERIFIED.
### Open items
- GUI check of the grouped visual.

## 2026-10-19 M4d done
### Goal & outcome
User checked in the GUI: after a pick and pulling the Plant away, no static copy stays behind, so the grouped visual removal reaches the GUI. All M4d checks of the spec are met: logged F(d) follows the Pull-out Curve, detach with a peak inside the Pull-out Force range, the visual is gone in the GUI. ADR 0006 and 0007 notes updated.
### Decisions & why
None
### Lessons / gotchas
- `/world/<w>/scene/info` keeps listing a visual removed with RequestRemoveEntity, while the GUI drops it: do not use scene info to check removals.
### State
Branch m4d-pullout-system, pushed (PR #14). Validated: pytest (75 passed, 72 skipped), ruff, scripted pulls, live picks, GUI check by the user. m4d done.
### Open items
- Non-zero pull_out_damping never run.
- Scale extremes (0.85, 1.15) not settle-checked (pulls at those scales passed).
- Next: m4e test gripper, needs IMPLEMENT.

## 2026-10-19 M4e test gripper
### Goal & outcome
Test gripper (`exporters/gazebo/gripper.py`, run by `grip_check.py` in the system Python): a carriage on a vertical prismatic lift, a palm behind a wrist force-torque sensor, two box jaws on prismatic joints closing 3 cm above the crown. `pixelfield grip <world> <plant>` picks a Plant and pulls it by the leaf bunch, logging gripper lift, jaw gap, wrist force and the pull-out state per step to `picks/<id>/grip.csv`. `pixelfield squeeze <variant>` runs the ADR 0006 squeeze check (root welded, jaws hold 1 s). Spec checks met on carrot: a 20 N per jaw grip detaches at the root depth with peak wrist force minus weight within 1% of the Plant's Pull-out Force; a 5 N grip slips (wrist force about 2 mu F = 10 N while sliding, d below d_peak).
### Decisions & why
- User skipped the grill and accepted the recommendations: separate non-static gripper model only in a headless test copy of the world; tests: carrot strong pull, weak slip and carrot v00 squeeze in the default suite, squeeze over all 72 Variants as a slow test.
- Jaws and lift are joint velocity commands, which dartsim runs as servos capped by the SDF effort limit: jaws close at 5 cm/s and squeeze with exactly the effort limit, so a weak grip is a defined force. Not JointPositionController (spec deviation, spec row updated): its target comes over gz-transport, out of step with the physics.
- Wrist force from a gz ForceTorque sensor on a fixed carriage-palm joint, tared before the jaws close; jaw friction mu 1 (guess).
- Each pull or grip run gets its own GZ_PARTITION: Field worlds share the name `pixelfield`, and concurrent runs read each other's state topic (validator found a 120% wrong peak).
### Lessons / gotchas
- gz.sim8 Python `Joint.transmitted_wrench` aborts (no converter for gz::msgs::Wrench); use a ForceTorque sensor topic.
- The ForceTorque system refuses a sensor on a joint whose parent is `world`: hence the carriage link.
- Model `self_collide` is off, so squeezed petioles pass through each other and the jaws stall on the fattest hulls (gap 6 to 9 mm carrot, up to 33 mm beetroot).
- The convex hull of a curved petiole segment is a wedge, and hulls step at link joints: jaws sliding up the bunch can catch and hold more than friction. A 5 N grip pulled two carrots out of the bond (one within 6 cm of lift, one after 11 cm at the link1 joint).
- A one-step lift stop gave -21 to -36 N wrist spikes; the lift now ramps down.
### State
Branch m4e-test-gripper, commits 10f3aa2 and f08dc97, not pushed. Validated: pytest (79 passed, 144 skipped), ruff, validator agent (strong pulls on 4 carrots, 3 radish, 3 beetroot, speeds 0.01 and 0.2 m/s, tare and weight to 0.01 N, squeeze on 10 Variants at scales 0.85 and 1.15, synthetic and physical escape negatives, error paths, no orphans), concurrent grips now match a solo run. Slow squeeze over 72 Variants NOT run (needs a slot, about 4 minutes).
### Open items
- Weak grip slips only where the hulls do not wedge (tested on plant 0); decide: thinner or split petiole hulls in the generator, or accept as a model limit.
- 20 N per jaw does not detach the strongest beetroot (60 N, slips 50 mm): grip force per Crop, or lift until detach.
- Real petiole tunnelling out of the jaws never provoked, so the escape check is only verified on synthetic and geometric negatives.
- Still open from earlier: non-zero pull_out_damping never run; settle check at scales 0.85 and 1.15.

## 2026-10-19 M4e decisions after review
### Goal & outcome
User decided the open items: hull wedging accepted as a known limit (noted in ADR 0006 Consequences); a test added that the strongest beetroot in m3_crops (59.91 N) does not come out at 20 N per jaw and does at 1.5 x (Pull-out Force + weight) / (2 mu) = 47.8 N per jaw, detaching at the root depth with wrist force minus weight within 1% of its Pull-out Force. Separately, CODEOWNERS (`* @aandrien`) on its own branch `codeowners` from main, PR #15.
### Decisions & why
- No per-Crop grip force: slipping when friction cannot hold is correct physics; grip strength and pad friction are robot design choices for M5, and the friction value waits for the measurement protocol.
### Lessons / gotchas
- At 20 N per jaw the strongest beetroot still peaks at 63.6 N wrist force (friction allows 40 N): the jaws wedge on the hulls, break the bond, then slip 50 mm. The test checks "no detach", not "friction-limited".
- CODEOWNERS done in a git worktree so the uncommitted AGENT_LOG.md stayed on m4e.
### State
Branch m4e-test-gripper, commit with the beetroot test on top of f08dc97, not pushed. Validated: tests/test_gripper.py 5 passed (beetroot test 17 s), ruff. PR #15 open, diff is the one CODEOWNERS line. Slow squeeze over 72 Variants still NOT run (needs a slot).
### Open items
- Slow squeeze run, then push m4e and open its PR.
- Finer petiole hulls as a later chunk.

## 2026-10-20 M5 design settled (m5a)
### Goal & outcome
Grilled the M5 plan (18 questions plus one redo) and wrote it down: ADR 0009 (pixelfield is a robot-free world provider), ADR 0010 (Active Region), spec sections 2, 5, 7, 10, 11 (M5 chunk table m5a to m5e, M5 row rewritten, new M7 row) and 12 (items 4, 6, 8), a new section 14 "Robot interface", ADR 0002 and 0006 amendments, glossary terms Picked Plant, Active Region and Border.
### Decisions & why
- Robots stay out of this repo: `amiga_ros2` (Amiga from `amiga_description`, Lite 6 + Gripper Lite from xarm_ros2, gz DiffDrive, gz_ros2_control, Docker) loads pixelfield worlds via `gz_args`. Common practice (ur_simulation_gz, Clearpath sim take a world argument); one robot description for real and sim. pixelfield has no ROS; the contract is gz-native with a fixed world name `pixelfield` and a `robot_interface` version in the Manifest.
- Robot-side questions (gripper force, control stack, MoveIt, bridge, WheelSlip, oracle perception) dropped from this repo's plan at the user's request; this repo plans only the world provider.
- Active Region: every link of every non-Field model triggers it (AABB plus 0.05 m padding against a 3D Plant footprint cylinder), zero config, no unpick unless the perf check fails. Plant SDFs pre-written at build (measured 3.3 ms, 34 KB per carrot Plant: about 10 s, 100 MB for 10 x 10), so the C++ system needs no Python and the scaling rules exist once.
- State topic publishes only while a Plant is pulled plus events: 100 Picked Plants at 1 kHz would be 100k messages per second.
- Plant-Plant contact on, measured first in an M5d spike; per-Pixel model with self_collide off is the fallback.
- Ground: soil collision becomes an infinite plane, Field Spec `border`, Manifest `field.path_gaps`, example Field for the Amiga's 1.524 m wheel track (every_n_cols 2, width 0.524). Soil friction stays default; traction is robot-side.
- Packaging: robot image clones a tagged release; library paths must stop depending on the cwd. MuJoCo pull scene becomes M7 with finer petiole hulls. M4 loose ends: damping test in m5c, settle at 0.85/1.15 and slow squeeze in the m5d slot.
### Lessons / gotchas
- Collide bitmasks cannot switch Plant-Plant contact off with zero-config robots: two shapes collide when masks share a bit and robots default to 0xFFFF, so each overlapping neighbour needs its own bit. The validator measured foliage reach (carrot 0.12 to 0.20 m, beetroot up to 0.27 m): 30 to 56 overlapping neighbours, far beyond 15 bits. Q7 was redone.
- A 2D footprint would let a chassis passing over a bed pick every Plant; wheels in Path Gaps still pick edge Plants.
- The Gripper Lite in xarm_ros2 has 8.9 mm stroke per finger and a 5 N effort limit: at mu 1 friction holds 10 N, below a carrot's 15 to 26 N. Note for amiga_ros2: measure the real grip force.
- No official farm-ng Amiga description exists; `Avans-Robotics/amiga_description` is the model.
### State
Branch m5a-design, commit 88cb7f6, not pushed. Docs only. Validated: relative links resolve, no em-dashes, ruff; validator agent checked decisions, arithmetic and stale text (its 13 findings fixed or turned into the Q7 redo). Design UNVERIFIED until m5b to m5e run: bitmask and friction semantics, DART penetration recovery, perf with many Picked Plants.
### Open items
- Maintainer reads the docs (m5a check), then m5b-ground, needs IMPLEMENT.
- For amiga_ros2's own plan: real Gripper Lite force, gripper control in sim, wheel friction.

## 2026-10-20 M5b ground for robots
### Goal & outcome
Soil collision is a plane at z = 0 on SOIL_BITMASK; textured tiles cover the Field plus the Border. Field Spec `border` (default 0.5, finite and at least 0) replaces SOIL_BORDER. Manifest: `field.path_gaps` ([] when off), `field.border`, top-level `robot_interface: 1`, format_version still 1. SVG draws Path Gaps (class `path-gap`, title with the x range). `examples/amiga_10x10.yaml`: random_10x10's Pixels with every_n_cols 2, width 0.524, border 2.0; gap centres 1.524 m apart. Spec item 12.6 checked: friction is the lower of the two mu.
### Decisions & why
- User skipped the grill and took all recommendations: Amiga example is carrot-only (same Pixels as the perf Field), friction check is a permanent test, SVG draws the gaps, `path_gaps` is [] when off, no border cap, old examples keep their 0.3 m gaps (perf rows) with only the comment changed.
- Ground tests reuse settle_check.py on a tiny world (the Field's soil model plus a box, physics only), so no new headless script.
- Friction rule found by tilting gravity instead of pushing the box: pure SDF, no force injection.
### Lessons / gotchas
- dartsim's `<plane>` is not infinite: a box lands at x = 1040 m and falls at 1060 m (validator). Spec says about 2 km wide; harmless for a Field.
- A box resting on the plane reads just under 1 mm/s in DART every step, so a 1e-3 speed threshold is flaky; tests use 0.01.
- Measured friction thresholds: mu 0.3 holds at slope 0.25 and slides at 0.5; mu 1 vs default soil holds at 0.95 and slides at 1.05 (soil mu is 1); mu 2 holds at 0.8 and slides at 1.3.
- PyYAML reads `1e3` as a string, so `border: 1e3` is rejected; `1.0e+3` works.
### State
Branch m5b-ground, commit 4024520, not pushed. Validated: pytest 86 passed, 144 skipped (slow) before the validator fixes, test_gazebo.py 16 passed after them; ruff; `gz sdf -k` on the Amiga example; validator agent (path_gaps over 8 col/gap cases, pull detaches at the root depth and the root lands at about 0 mm, strong and weak grip, old soil box makes the drop test fail).
### Open items
- Hand check: open `out/amiga_10x10/field.svg` and hover the gaps.
- Large borders cost tiles quadratically (border 50 on 3 x 5 Pixels: about 10k tile visuals, 7 MB world.sdf); cap only if someone needs it.
- Next: m5c pick by id, needs IMPLEMENT.

## 2026-10-20 M5b Amiga drive test and row direction
### Goal & outcome
The user drove the Amiga (`amiga_description`, gz DiffDrive, gz GUI Teleop plugin on `/cmd_vel`) in `out/amiga_10x10`; the ground works. Plant rows in the Amiga example now run north-south (`row_direction: 1.5707963`), along the Path Gaps, since the carrot default (0, east-west) had the robot driving across the rows.
### Decisions & why
- Field-wide override in the example only; the carrot default stays, so the other examples and the perf rows do not shift.
### Lessons / gotchas
- `amiga_description` is not in a colcon workspace, so `xacro` fails on `$(find amiga_description)`. Workaround: substitute the absolute path in a copy of `amiga.urdf.xacro` and pass `gazebo:=true` (without it there is no drive plugin). Meshes need `GZ_SIM_RESOURCE_PATH=~/git_repos/SustainableAgriculture` for `package://`.
- Spawn heading north at x = 2.024 puts the wheels in the centres of the first two Path Gaps.
- No ROS teleop or ros_gz_bridge installed; gz-gui's Teleop plugin needs neither.
- The Amiga passes through Plants: static Plants have no collision until M5d (Active Region).
### State
Branch m5b-ground, commit 17c5f15 on top of 4024520, not pushed. Validated: test_core 43 passed (the new row check fails without the example change), ruff, `gz sdf -k`. Drive test done by the user in the GUI.
### Open items
- Push and PR when the user says so. Proper Amiga launch belongs in amiga_ros2 (colcon build of amiga_description).
- Next: m5c pick by id, needs IMPLEMENT.

## 2026-10-20 M5c pick by id
### Goal & outcome
`pixelfield build` writes `plants/<id>.sdf` for every root crop Plant (model named by id at its Field pose, Pull-out Curve element, hulls and articulated glb shared per Variant in `plants/meshes/`) and `plants/plants.tsv` (id, x, y, z, footprint radius and height, scaled). The C++ system reads the table and loads the file on a pick; the pick service takes a `gz.msgs.StringMsg` id; Python `pick`, `pull` and `grip` send only the id. The state topic publishes only when d or the force changed, plus events. Damped pull (c = 50 N s/m) checked: force minus curve equals c * v per step within 0.01 N, median 2.5 N at 5 cm/s. Build of the 10 x 10 carrot Field: 4.7 s, 165 MB `out/` (142 MB of Plant SDFs, 46 KB per Plant); Amiga example 4.3 s, 152 MB (perf.md).
### Decisions & why
- User skipped discussion and delegated all choices.
- Pick message `gz.msgs.StringMsg` with reply `gz.msgs.Boolean`: standard, works from `gz service` and ros_gz without a custom message.
- Events are ordinary state messages with an extra `event` param (picked, peak_passed, detached): one message type for consumers. "Being pulled" means d or force changed by more than 1e-9 m or 1e-6 N since the last message, so a root held still by a robot or by the ratchet is silent too (both repeat to the last bit at rest). The picked event goes out on the first step with joint data, which keeps a full `pull.csv` byte-identical to main.
- The model pose lives in the Plant SDF, so the file alone describes the Plant; Plant SDFs come from `to_manifest(layout)` so scale and pose match the Manifest's rounding.
- `build` deletes `plants/` first: no stale SDFs from an earlier spec.
- Fixed a pre-existing crash found by the validator: at 20 m/s the ratchet set the slide's lower limit above its upper one on the detach step and dartsim aborted (confirmed on main). The ratchet now skips the detach step; test added.
### Lessons / gotchas
- gz-sim 8 hands a system its plugin element without a file path (`FilePath()` empty, no parent, no WorldSdf component). The world file's absolute path is on the `soil` model (`Model::SourceFilePath`), but models do not exist yet in Configure, so the table is read on the first PreUpdate; a pick before that is refused with "still loading". The first live check passed only because the server's cwd was the world folder.
- `gz service` prints nothing for a `data: false` reply (protobuf text omits defaults).
- The validator saw 23 silent steps mid-pull on a beetroot: after the peak the root rests on the ratchet while the scripted pull's target catches up. That is a resting root, so silence is by design.
- Global rule: no Co-Authored-By trailer in commits, it overrides the harness reminder.
### State
Branch m5c-pick-by-id from main, commit 87376e9, not pushed. Validated: pytest 94 passed, 144 skipped (slow); ruff; `pull.csv` of r0c0-000 byte-identical to main, part-pulled r0c0-001 identical except the silenced resting rows after release; headless `gz sim -s` with `pixelfield pick`: one `picked` message per Plant then silence for 10 s, re-pick and unknown ids refused, worlds loaded from another cwd, relative and absolute; validator agent (footprint against trimesh over 398 Plants at scales 0.85 to 1.15, 8 concurrent picks of one id give one spawn, lettuce Field refuses cleanly, moved world works, grip slip). GUI pick UNVERIFIED (user's slot).
### Open items
- User: `pixelfield pick` in a running GUI world, and `gz topic -e -t /world/pixelfield/pixelfield/pull_out` silent for the resting Plant.
- Spec M5c check says "pull.csv unchanged": true for a full pull; a part-pulled log now has blank state rows while the root rests.
- `plants/` is 142 MB for 10 x 10, 1.4x the ADR 0010 estimate; the ADR's ceiling (one scale-1 SDF per Variant) applies if Fields grow.
- `pull` and `grip` still need the repo root as cwd (library paths in the Manifest): m5e.
- If one step crosses both d_peak and the root depth, only `detached` is sent (not seen even at 50 m/s).

## 2026-10-22 M5d spike: full carrot Pixel picked at once fails
### Goal & outcome
Spike of ADR 0010 before building the Active Region: pick every Plant of `carrot_pixel` (32) by id in a headless, unthrottled world without Sensors, and measure leaf drift, NaN and physics-only RTF. FAILED: the full Pixel with contact runs below 0.02x with the mesh hulls (10 s of sim time did not finish in 10 min), and the leaves of neighbours picked together are shoved apart violently. Stopped before building the region, as agreed. Physics only, 1 ms step (the Field world has no `<physics>` element, so dartsim defaults), throttle removed:

| Plants | Petiole collision | RTF | Leaf tip drift |
|---|---|---|---|
| 1 | mesh hulls (as built) | at least 1.0 | 0.1 mm |
| 4 | mesh hulls, FCL (default) | 0.17 | 34 mm in 0.5 s, up to 83 mm/s |
| 4 | mesh hulls, bullet detector | 0.20 | 0.9 mm in 0.5 s |
| 4 | capsules fitted to the hulls | 1.48 | 1.1 mm in 0.5 s |
| 4 | hulls, no Plant-Plant contact (bitmask 0) | 1.8 | 0.07 mm |
| 32 | capsules | 0.036 (PGS solver: 0.035) | max 10 mm, median 1 mm over 3 s, slowing |
| 32 | hulls, no Plant-Plant contact | 0.13 to 0.15 | none |
| 32 | no petiole collisions | 0.19 | none |
| 32 | no petiole collisions, all joints fixed | 0.34 | none |

### Decisions & why
- Spike verdict FAIL, region not built: ADR 0010's per-Pixel fallback (no contact inside a Pixel) is the "no Plant-Plant contact" row, 0.15x for one full Pixel before cameras, so it fails the 0.5x-with-30 budget too.
- User delegated the M5d choices (box from `Link::ComputeAxisAlignedBox` cached per link, brute force over the table, `<padding>` in the plugin element, inline SDF parse, grip tests run with the region, probe-box tests, slot runs without new code); they wait for the direction after the spike.
### Lessons / gotchas
- ADR 0010's "DART corrects penetration with a capped velocity of about 1 mm/s" is wrong for mesh hulls under FCL: interpenetrating hulls are pushed out at up to 8 cm/s. Bullet or capsules separate them at about 1 to 4 mm/s.
- Contact between mesh hulls is the dominant cost (4 Plants: 0.17x vs 1.8x without contact). Capsules remove most of it at 4 Plants, but 32 overlapping Plants form one contact island and run at 0.036x.
- A Picked Plant costs about 0.15 ms per step without any contact; about half remains with every joint fixed, so per-link bookkeeping (gz-sim or DART bodies) matters as much as articulation.
- `<dart><collision_detector>dart</collision_detector>` does not support mesh shapes; `ode` gave the same numbers as the default.
- Field worlds have no `<physics>` element, so the `real_time_factor` regex in `pull_check.py` and `grip_world` replaces nothing: scripted pulls and grips run throttled at 1.0x.
- `pkill -f <pattern>` typed into a shell kills that shell too, since its command line has the pattern; kill by pid. Profiling with gdb or perf is blocked here (ptrace refused, perf_event_paranoid 4).
- Spike script (scratchpad, not committed): TestFixture, pick by id through the service, link positions every 10 ms; capsule copies fitted by PCA (axis = longest extent, radius = median distance from it).
### State
Branch m5d-active-region from main (8ce2350), no code changes. Spike numbers measured and observed; the capsule rows use rough fitted capsules, not a generator change.
### Open items
- Direction after the failed spike (user decision): capsule petioles, fewer links per Picked Plant, a smaller trigger footprint, unpick, or a revised budget.
- `real_time_factor` regex no-op in the pull and grip worlds (harmless, they only need correctness, but they run slower than they could).

## 2026-10-22 M5d capsules and Active Region (grip tests open)
### Goal & outcome
User took the three post-spike recommendations: petiole collisions as capsules, a crown footprint for the Active Region, and a scenario perf budget with unpick as the next chunk. Branch m5d-capsules (commit 50d2372): each petiole link collides as 2 capsules along chords of its curve (`CAPSULES_PER_LINK`, `"capsules"` list in physics.json, MuJoCo fromto style), root keeps its hull, library regenerated (only physics.json changed), ADR 0006 and spec amended; suite green (94 passed). Branch m5d-active-region (stacked on it, uncommitted): the pull-out system picks Plants whose crown cylinder meets any non-Field link's box plus `<padding>` every 10 ms; `plants.tsv` gains a crown column; `<padding>` and `<footprint>` (crown or foliage) in the world's plugin element; new tests/test_region.py with tests/region_check.py; ADR 0010 and spec rewritten with the spike table and decisions.
### Decisions & why
- 2 capsules per link, not 1: one chord misses a carrot petiole's bend by up to 12.8 mm (median 5.4), two by 3.7 mm; cost 1.74x to 1.0x at 4 Plants. Three would give 1.6 mm.
- Link boxes computed by the system: each collision's geometry box (sdformat `Geometry::AxisAlignedBox`, gz-sim `meshAxisAlignedBox` for meshes, mesh `<scale>` honoured) moved through its 8 corners by the collision pose, merged per link, cached per link entity, then moved by the link's world pose per check. No components, no Physics work.
- Brute force over the whole table per link (ponytail note), SDF parse inline in PreUpdate (ponytail note), a broken Plant file is marked picked so it errors once.
- grip_check reports `requested` true when the Plant is a model at the end: the region can pick it before the request.
### Lessons / gotchas
- Capsules fixed the M4e wedge: a 5 N grip over the full 0.2 m lift slipped on 4 of 4 carrots with the bond intact (d below 3 mm); with one capsule per link one carrot still broke the bond at a joint. The weak grip test now lifts the full height.
- grip_check and pull_check filed every state message by its time stamp, whatever Plant sent it; with neighbours picked the rows mixed Plants. Both now filter on `plant`.
- With the region, the 10 cm wide test gripper jaws close on an in-row neighbour 3.9 cm away too: pulling r0c0-000 dragged r0c0-001 up 108 mm, wrist at the 40 N friction limit, no detach. Three grip tests fail for that reason.
- gz-sim 8's `Link::ComputeAxisAlignedBox` moves only the min and max corners of each collision's box (validator): a cube turned 45 degrees about z in its link comes out with zero width in x (checked: x 0, y +-0.0566 for a 0.08 cube). That is the M5c "narrower than the hull" sighting. A test probe approaches a Plant from the side gz gets wrong; the mutation back to gz's box fails it.
- An empty or inverted geometry box would span everything once its corners are moved; the system skips it.
- Mutation check: region off fails the pick test, no Field exclusion fails the Field test.
- The M5c system reads only the first row of a 7-column plants.tsv (it misparses the rest): worlds must be rebuilt with the systems of the same commit.
### State
m5d-capsules: commits 50d2372 and 4b241f9 (review fixes: physics export format_version 2, ADR figures over the whole library, CLAUDE.md weak grip without --lift), validated: pytest 94 passed, ruff, validator agent (capsules match the glb tubes in all 72 Variants within 0.5 um and in gz at scales 0.85 to 1.15, library deterministic, footprint vs sampled capsule surfaces, 6 settles and 6 squeezes, 6 of 6 weak grips slip with the bond intact). m5d-active-region: stacked on 4b241f9, uncommitted; region tests 3 passed (mutation-checked three ways), pull.csv byte-identical to the capsule commit's system; 3 gripper tests FAIL (neighbours gripped), waiting for the user's decision.
### Open items
- Grip tests with neighbours: user decision.
- Slot runs (settle 0.85/1.15, slow squeeze, perf scenario rows) and the GUI check.
- Unpick chunk after M5d.

## 2026-10-22 M5d slot runs and the overlapping roots
### Goal & outcome
User approved the sparse-Field grip tests and the slot. Grip tests now use crops copied with one root crop Plant per Pixel (margin 0.2, spacing 0.5, no missing Plants, neighbours at least 0.48 m apart); a new test grips in the dense carrot Pixel and checks a neighbour is picked and moved; grip_check reports every Picked Plant heard with its largest d. Commit 2977ae1 (region) and the perf commit on m5d-active-region. Slot: settle at scale 0.85 and 1.15 all 144 settled (worst carrot v19 at 1.15: 0.57 mm/s, 2.3 mm travel); slow squeeze 72 of 72 held (4 min); rig re-run 0.96x (matches); gripper scenario 0.21x, FAIL.
### Decisions & why
- Perf scenario world: fresh `random_10x10` build, camera models replaced by the old `oakd` rig model (visuals only, so it never triggers the region), test gripper as a static model at its grasp pose. A non-static gripper without its control script would fall.
### Lessons / gotchas
- The scenario's cost is physics: two picked carrots 2.3 cm apart have overlapping roots (crown radii about 2 cm). Both roots are welded to anchors, so the contact never resolves; a leaf keeps moving at up to 15 cm/s and the pair alone runs at 0.31x (2.6x with the two root collisions off). 1,231 of 2,760 Plants in random_10x10 are in such a pair.
- With all root collisions off: scenario 0.64x (pass), 32-Plant spike 0.089x (was 0.036x).
- Collide bitmasks cannot switch off root-root contact while roots still touch robots: equal masks always collide.
- The old rig worlds in out/random_10x10 (world_nadir.sdf and others) predate the pull-out system; perf_rig.sdf and perf_grip.sdf are the M5d ones (out/ only, rebuilt by the scratch script).
- One full pytest run out of four had one failing test that could not be identified (no -rf) or reproduced in 13 targeted and 2 full reruns. UNVERIFIED flake.
### State
Branch m5d-active-region: 2977ae1 plus the perf commit, stacked on m5d-capsules (50d2372, 4b241f9). Validated: pytest 98 passed (3 of 4 runs), ruff, region tests mutation-checked, slot runs above. Perf check FAILS until the root contact is decided. GUI check by the user not done.
### Open items
- Root-root contact of Picked Plants: user decision (root collision off while attached, a minimum Plant distance in the Planting Pattern, or accept).
- GUI check: the M4e gripper pulling one carrot pushes its neighbours.
- The unidentified flaky test.
- Unpick chunk after M5d.

## 2026-10-22 M5d rethink after the failed scenario, timestep sweep
### Goal & outcome
User questioned the approach (why so hard, other engines, GPU, MuJoCo in Gazebo). Agreed after discussion: keep Gazebo (ROS 2, known by students and colleagues), keep full-fidelity neighbours (no cheaper models, no Plant-Plant contact switched off, no roots switched off), keep the Active Region (no collisions far from the robot), target at least 1.0x for a live Amiga showcase (0.8x floor while tuning), measure a larger physics step, then non-overlapping roots, re-measure, then unpick. Commit 57d35fc: one physics step constant (`gazebo.PHYSICS_STEP`) written into every Field world, the pull and grip scripts take the step from it or from gz. Timestep sweep (13 settles, 12 squeezes, pulls of carrot, beetroot and radish, strong and weak grip on a sparse Field, the gripper perf scenario):

| Step | Settle worst | Squeeze | Scripted pull | Grip (strong, weak) | Scenario RTF |
|---|---|---|---|---|---|
| 1 ms | 0.57 mm/s | 12/12 | 3 detach, peaks within 0.5% | detach, -0.5%; slips, d 2.8 mm | 0.23 |
| 2 ms | 0.57 mm/s | 12/12 | 3 detach, peaks within 0.5% | detach, -1.0%; slips | 0.42 |
| 4 ms | 0.56 mm/s | 12/12 | carrot and radish do not detach | detach, -0.1%; slips | 0.72 |
| 5 ms | 0.56 mm/s | 12/12 | crash (ODE AABB assertion) | not run | not run |

### Decisions & why
- Within Gazebo Harmonic, DART is the only engine that runs the Plant model: bullet-featherstone replaces universal joints by fixed ones, ignores joint springs and creates no joints at runtime but fixed-to-world (gz-physics 7 source). No maintained MuJoCo plugin (gz-physics issue #299 abandoned). GPU physics helps many parallel worlds (M7), not one live world.
### Lessons / gotchas
- gz-sim's default collision detector for dartsim is ODE, not FCL (corrected in the ADRs): the spike's unset and ode runs were identical.
- The Pull-out Curve holds at every step (force matches the curve exactly); the scripted pull fails from 4 ms because its harness (a 5000 N/m, 30 N s/m force on the root) is an explicit damper with c dt / m = 1.7 for a 70 g carrot: it overshoots, and at 5 ms flings a body far enough to trip ODE's AABB assertion. The gripper path is unaffected.
- Q2 premise was wrong: carrot crown radii (1.2 to 2.2 cm) against 4 cm in-row spacing make big neighbours touch even at nominal positions, which is realistic. Touching roots in random_10x10 have at most 2 neighbours, so 2 collide bits (roots coloured so touching roots never share a bit, robots keep all bits) separate them without a minimum distance.
- The first sweep run died once in a squeeze at 1 ms (grip_check, exit code unknown); 12 squeezes alone and the rerun passed. Possibly the earlier unexplained pytest failure.
### State
Branch m5d-active-region at the ADR fix commit on top of 57d35fc. Validated: pytest 98 passed at 1 ms, pull.csv byte-identical, sweep above. Step still 1 ms.
### Open items
- User decisions: step 4 ms with the harness gains scaled by the step; roots coloured with collide bits instead of a minimum distance.
- Then re-measure the scenario, then unpick.

## 2026-10-22 M5d root colours fail, grasp friction drifts with the step
### Goal & outcome
User approved root collide-bit colours and a 4 ms step. Implemented (uncommitted): `_root_bits` in plant.write_plants (greedy, 5 mm margin, 3 bits used in random_10x10), PHYSICS_STEP 0.004, scripted pull gains divided by the step in ms, tests for one bit per root and touching roots on different bits (mutation-checked). Results argue against both as they stand: gripper scenario with colours 0.46x at 2 ms, 0.88x at 4 ms (0.42x, 0.72x without), and at 1 ms the gz server aborts on ODE's AABB assertion. At 4 ms four tests fail: three scripted pull tests (lower harness gains change the log) and the strongest beetroot no longer detaching.
### Decisions & why
None yet: back to the user.
### Lessons / gotchas
- Overlapping roots are unphysical, not just costly: with root-root contact off, a carrot's leaves start inside its neighbour's root and that contact cannot resolve either (both anchored); at 1 ms a body is flung far enough to abort ODE. Touching crowns are realistic, overlapping ones are not, so the layout must keep crowns apart (a minimum distance of the sum of crown radii, touch allowed).
- Grasp friction drifts with the step on the strongest beetroot (58.4 N): a 20 N per jaw grip peaks at 42 N wrist force at 1 ms (friction allows 40), 60 N at 2 and 4 ms; the 45.8 N grip detaches at 1 and 2 ms but slips at d = 80 mm at 4 ms. Carrot grips (strong and weak) stay right at 4 ms. Cause unknown (deeper jaw penetration per step raising the normal force above the effort limit is a guess).
- When the gz server aborts, `gz topic -e -n 1` waits forever: perf_run.sh hangs (scratch script; needs a timeout on the stats read).
- The ODE AABB abort is a candidate for the unexplained intermittent squeeze and pytest failures.
### State
Branch m5d-active-region at 7029336 plus uncommitted root colours, 4 ms step and harness gains. Tests at 4 ms: 4 failures (above). Not committed on purpose.
### Open items
- User: drop the colours for a non-overlapping layout; step size given the grasp drift; scripted pull harness at a fixed 1 ms instead of scaled gains.

## 2026-10-22 M5d scenario at the camera ceiling: no overlapping roots, 2 ms step
### Goal & outcome
User approved: drop root colours, keep crowns apart in the layout, scripted pull at its own 1 ms, choose the step after the layout fix and the grasp drift. Commits 857951b (Planting Pattern redraws jitter so no two roots overlap, touching allowed, radii from variants.json, Plant left out after 20 tries; scripted pull pinned to plant.PULL_STEP) and 8d5b614 (PHYSICS_STEP 2 ms; settle, pull and grip scripts raise with their stderr; CLI catches that). Gripper scenario on the new layout: 0.58x at 1 ms, 0.97x at 2 ms, 1.00x at 4 ms; rig alone 0.97x. Pass bar (as fast as the cameras allow, at least 0.8x) met at 2 ms.
### Decisions & why
- 2 ms, not 4: 2 ms already reaches the camera ceiling; 4 ms lost the strongest beetroot's 45.8 N grip. Grasp friction is not step-dependent in a systematic way: 12 sparse 20 N grips peak within 1 to 3 N at 1 and 2 ms except one wedging beetroot (40.6 vs 60.1 N); wedging past friction occurs at 1 ms too (46.9 N on another beetroot).
- Overlap check only within a Pixel: margins (4 to 5 cm) keep crowns of neighbouring Pixels apart for all current Crops (beetroot crown radius up to 4.5 cm).
### Lessons / gotchas
- In random_10x10 the layout rule moves 845 of 2,760 Plants by a few mm and leaves out 47; no overlapping pair remains in any example.
- The weak 20 N grip limit "friction allows 2 mu F" holds for parallel petioles only: jaws sliding up a bunch that spreads outward meet geometric resistance too (gap closes from 16 to 5 mm over a 0.12 m lift).
- The intermittent check-script crash struck again once in the slow squeeze at 2 ms (carrot v03, fine in 8 reruns). Its stderr will now be in the error.
### State
Branch m5d-active-region at 8d5b614 (stacked on m5d-capsules), not pushed. Validated at 2 ms: pytest 99 passed; slow settle 72/72; slow squeeze 71/72 (v03 intermittent, then 5/5); perf rows in perf.md.
### Open items
- GUI check of the gripper pushing neighbours (needs a GUI path for the test gripper).
- Unpick (next chunk, design to discuss).
- The intermittent crash: wait for its stderr.
- Settle at 0.85 and 1.15 not re-run at 2 ms.

## 2026-10-22 M5d unpick and grip --gui
### Goal & outcome
User approved unpick (U1 to U3) and a GUI path for the grip (Q8). Commit 9cdfb44: in the Active Region check, a Plant the region picked turns back into its static visual once its bond is intact (not broken, d under 0.1 mm), every link moved under 1 mm/s for 2 s, no robot box meets it, and every link is within 1 cm of where it settled after the spawn. Weld removed first, models a step later; the visual is rebuilt from the Pixel model's `ModelSdf` with SdfEntityCreator; an `unpicked` event goes out; the Plant can be picked again. `pixelfield grip --gui` runs the grip in real time with `gz sim -g` on the run's own partition (waits 8 s, lingers 30 s). In the carrot Pixel a probe that leaves at 0.2 s gets its 4 Plants unpicked at 2.3 to 5.0 s, all 31 static visuals back.
### Decisions & why
- Decided without asking, flagged to the user: a Plant picked through the pick service is never unpicked (someone asked for it; it keeps `pixelfield pick` plus a manual GUI pull and the resting-silence check working).
- Rest is judged from link positions every 10 ms (no velocity components enabled), the settled pose taken at the first region check after the spawn.
### Lessons / gotchas
- A test of a restored visual must look before the robot returns: at the end the re-pick removes it again, so a final-state check passed with the restore switched off (mutation caught only after adding a snapshot step).
- `Model.set_world_pose_cmd` moves a static probe model in a TestFixture run.
- Region tests and the check scripts now fail with the script's stderr (run_check), to catch the intermittent crash; one region test run failed once right after a rebuild, 8 reruns passed.
### State
Branch m5d-active-region at 9cdfb44, not pushed. Validated: pytest 100 passed; region tests mutation-checked (never unpick, unpick by id, no visual restore each fail a test); grip --gui path checked headless with a stubbed viewer (real-time pacing, 500 linger rows at 2 ms). GUI itself UNVERIFIED (user's slot). Validator agent running.
### Open items
- User GUI check: `uv run pixelfield grip out/carrot_pixel <id> --gui` shows the gripper pushing neighbours, and unpicked Plants turning static.
- The bent-leaf tolerance (1 cm) has no automated test.

## 2026-10-22 M5d validator findings fixed
### Goal & outcome
Validator agent on 857951b..9cdfb44: nothing blocking. Unpick held under mass unpick (30 of 31 Plants, restored visuals byte-identical in all 8 ECM components), broken bonds never unpicked, re-pick after unpick runs a full pull, 225 pause cycles change nothing, layout has no root overlap in any example or rotated variant (exact 3D hull test), the pinned pull is byte-identical between 1 and 2 ms worlds. Seven smaller findings fixed in one commit: loud failures for worlds that do not load, layout refuses root crops without root sizes, grip --gui waits with the world running and starts the viewer inside the cleanup, a Pick owns its parsed SDF (freed on unpick), docs corrected.
### Decisions & why
- Refuse instead of warn when a root crop has no root sizes: the same Field Spec and seed must not give a different Manifest depending on the working directory.
### Lessons / gotchas
- A gz-sim server stopped between TestFixture runs answers no scene requests: a GUI attaching during a sleep sees nothing until the world runs.
- The layout rule moves Plants 2 cm median (90th percentile 3.4 cm, max 5.8 cm), not "a few mm" as the previous entry said.
- A TestFixture script on a broken world prints the XML error and still exits 0: scripts must check that steps ran.
- Radish v15's root hull is 1.56x its listed radius; the margins still keep Pixels apart.
### State
Branch m5d-active-region, latest commit the review fixes, not pushed. Validated: pytest 100 passed plus the new layout test (core 45 passed); broken world fails pull and grip with the XML error; build from another directory refuses cleanly; grip --gui path checked headless. GUI itself UNVERIFIED.
### Open items
- User GUI check.
- The dense-Pixel grip does not pull a carrot out with the 10 cm test jaws (neighbours grabbed): fine for the showcase test gripper? The real Amiga gripper will differ.

## 2026-10-23 M5d test gripper across the row, jaws sized per Plant
### Goal & outcome
User GUI check: the jaws looked like they missed the target and lifted another carrot. Measured: gripping r0c0-015 lifted its in-row neighbour r0c0-016 by 21.9 mm (bond broken) while the target rose 0.1 mm. Cause: jaws closed along the row (east-west) from 6 cm out and were 10 cm wide, so they swept through and clamped the in-row neighbours' bunches 4 to 5 cm away. User approved G1. Uncommitted: the Manifest's Crops gain `row_direction` (resolved Field override or Crop default); the gripper turns to close across the rows; jaw width = the gripped Plant's leaf bunch diameter at grip height plus 1 cm (`jaw_width`, carrot about 3.5, radish 4.1, beetroot 5.9 cm). In the dense carrot Pixel three targets now detach at their root depth and neighbours only get pushed (d 1.6 to 3.9 mm, bond intact). Slow squeeze 72/72 with the sized jaws (a fixed 4 cm let 22 beetroot and other Variants escape: beetroot bunches are 4.9 to 5.3 cm at grip height).
### Decisions & why
- Jaw width per Plant instead of one width: in-row spacing (4, 6, 8 cm) and bunch width differ per Crop; no single width clears carrot neighbours and holds a beetroot bunch.
### Lessons / gotchas
- Wedging of the leaf bunch between the jaws depends on the angle between the jaws and the Plant's random yaw: weak 5 N grips broke the bond on 1 to 2 of 4 sparse carrots in every jaw orientation and width tried, the old configuration included (48.7 mm on one). The M4e weak-grip and strongest-beetroot tests passed because of their particular angle, not because wedging was gone.
- The strongest beetroot's wrist force over its Pull-out Force: 0.98 along x, 1.11 to 1.29 across the rows (wedging and stick-slip peaks on the wrist).
### State
Branch m5d-active-region at fd5ec43 plus the uncommitted gripper change. Tests: 2 failures (weak grip bond holds; strongest beetroot within 5%), both angle-dependent wedging; squeeze 72/72; dense grip test passes.
### Open items
- User decision on what the weak-grip and strong-grip tests should assert.

## 2026-10-23 Session wrap-up: M5d state
### Goal & outcome
User checked the new gripper in the GUI: the target comes out, but the gripper and carrot shake once the carrot is fully out. Committed the gripper change with the two angle-dependent test failures noted in the message. Session wrapped up at the user's request.
### Decisions & why
None
### Lessons / gotchas
- Shaking after the carrot is out is unexplained: likely the jaw servos (velocity commands capped by the effort limit) chattering on thin capsules at the 2 ms step, or stick-slip of the held bunch; not measured.
### State
Branches, none pushed, none merged: m5d-capsules (50d2372, 4b241f9; green) and m5d-active-region stacked on it (latest the gripper commit). On m5d-active-region: pytest 2 known failures (weak grip bond, strongest beetroot wrist within 5%), everything else passes; slow settle 72/72 and squeeze 72/72 at 2 ms; perf scenario 0.97x (camera ceiling).
### Open items
- G2: what the weak and strong grip tests assert (proposal: friction-limited sliding and no detach; soil force within 1% and wrist at least 95%), and correct ADR 0006's claim that capsules removed wedging.
- Shaking of the gripper with a pulled-out carrot.
- The intermittent check-script crash (stderr now captured).
- Settle at 0.85 and 1.15 at 2 ms not re-run; bent-leaf unpick tolerance untested.
- Then M5e packaging; merge order m5d-capsules, then m5d-active-region.

## 2026-10-23 M5d finished: grip tests, wedging, linked jaws
### Goal & outcome
User asked to finish fast. G2 done (e846fd7): grip tests check what holds at any jaw angle (weak grip: no detach, friction-limited sliding; strong grips: detach at the root depth, soil force within 3% of the Pull-out Force, which is one 2 ms step of a 5 cm/s pull, wrist carrying at least 95%); grip report gains peak_force; ADR 0006 no longer claims capsules removed the wedging. The shaking the user saw (a61dd3d): the held carrot swung 7 mm at the root because two force-capped jaw servos leave the jaw pair free to slide as a unit; each jaw now backs off when ahead of the other (JAW_LINK 200 1/s), root motion under 0.2 mm. Settle at 0.85 and 1.15 at 2 ms: 72/72 each.
### Decisions & why
- Linked jaws in the controller, not one fixed jaw: a parallel gripper's fingers are mechanically mirrored, and a single moving jaw would push the bunch sideways.
### Lessons / gotchas
- The 1% soil-force tolerance held at 1 ms but the peak is sampled once per step: at 2 ms the last sample before the peak can be 2% low.
- With linked jaws, r0c0-020 in the dense carrot Pixel no longer comes out: its close in-row neighbour's bunch ends up between the jaws too (neighbour lifted 49.6 mm, wrist 39.2 N at the 40 N friction limit). r0c0-015 and r0c0-005 come out.
### State
m5d-capsules (50d2372, 4b241f9) and m5d-active-region stacked on it (latest a61dd3d), not pushed. Validated: pytest 101 passed, 144 skipped; slow settle 72/72 at scales 0.85, 1.0, 1.15 and squeeze 72/72 at 2 ms; perf scenario 0.97x (camera ceiling); GUI check of the grip by the user (before the linked jaws).
### Open items
- User: GUI check that the shaking is gone (`uv run pixelfield grip out/carrot_pixel r0c0-015 --gui`).
- The intermittent check-script crash (stderr now captured); the 1 cm bent-leaf unpick tolerance has no automated test.
- Merge m5d-capsules, then m5d-active-region; then M5e packaging.

## 2026-10-23 M5e packaging and the Amiga in the Field
### Goal & outcome
User asked how far amiga_ros2 is from driving the Amiga in a Field, then said to finish M5e. Done: library paths independent of the cwd, install instructions for robot repositories (README, CLAUDE.md, spec 14), version 0.5.0 and a local tag `v0.5.0`, plus an Active Region fix found while answering. Container check in `amiga-ros:jazzy` with amiga_ros2 unchanged: clone of the tag, `pip3 install --break-system-packages -e`, systems built against the vendored gz-sim 8.15.0, Field built from another folder, launch: the Amiga stands in the Field with the pull-out system loaded. With the spawn pose in the gaps (temp copy of the launch, `-x 2.024 -y 1.5 -Y 1.5707963`) it stands and drives 10 m north at 1.0x, 3 edge Plants picked and all unpicked (perf.md, M5e section).
### Decisions & why
- Active Region tests one box per collision, not one per link (ADR 0010 amended): the Amiga's base_link holds the low wheel forks and the high cross tubes, so its single box picked 144 carrots under the chassis at about 0.01x. Found by reading the URDF before any run.
- Relative library paths resolve against `pixelfield.ROOT` (the checkout), the Manifest keeps `assets/library/<crop>`: same Manifest on every machine, no format change. Needs an editable install from the clone, which ADR 0009 already prescribes; `build` refuses a non-editable install and a missing library folder loudly.
- `SYSTEM_PYTHON` stays `/usr/bin/python3`: in a ROS image `source /opt/ros/jazzy/setup.bash` puts the vendored gz bindings (gz.sim8, gz.msgs10) on PYTHONPATH.
- Tag kept local and moved with each commit: it must point at main after the merge, so the user tags the merge commit (or pushes this one).
### Lessons / gotchas
- `timeout` around `docker exec` kills only the client; processes inside the container keep running. Leftover servers in the same ROS domain (two controller managers) made later runs look hung. Clean container: no hang. Kill inside the container (a script file, so `pkill -f` does not match its own `bash -c`).
- A stale .pyc after `git stash pop`: same mtime second and same byte size as the old source, so Python kept the old bytecode. Clear `__pycache__` after stash games.
- The unchanged amiga_ros2 launch spawns at the Field origin, one wheel and fork on the carrots of r8c0/r8c1: 27 crushed Picked Plants that never unpick, 0.003x. A robot must spawn in the gaps or the Border (README, spec 14).
- `amiga-ros:jazzy` has no pip and gz-rendering 8.2.3 (below the 8.3.0 floor; matters once it has a camera). EGL fails on the NVIDIA node with `/dev/dri`; headless sensors still ran.
- In every launch, the empty world too, the `joint_state_broadcaster` spawner times out; only `lite6_traj_controller` activates. amiga_ros2 issue, driving is unaffected (gz DiffDrive).
### State
Branch m5e-packaging from main, commits a2c6a96, 95c50b3, 35f9e36, 9af4e39, local tag v0.5.0 on 9af4e39, not pushed. Validated: pytest 103 passed, 144 skipped (slow); ruff; region test fails against main's per-link system and passes now; cwd test fails without the path change; build, pull and grip from a scratch folder; container check and drive runs (on 95c50b3 code, later commits are docs, comments and the CLI refusals, tested on the host); validator agent (mesh, visual-only, nested and empty links; unpick with two-collision links; Manifest without machine paths).
### Open items
- User: push the branch, PR, merge, then tag `v0.5.0` on the merge commit and push the tag (the README clone command needs it on GitHub).
- amiga_ros2 (their repo): spawn pose launch args (x, y, yaw), the joint_state_broadcaster timeout, gz-rendering 8.3.0 in the image, the pick service and pull_out bridges for harvesting.
- `test_a_grip_in_a_full_pixel_pulls_the_target_past_its_neighbours` failed once in 4 full-suite runs, passed in 4 isolated runs; no traceback kept. Probably the M5d intermittent check-script failure.
- Camera `<save>` paths in world.sdf (`renders/top`) are relative to the server's cwd: under `ros2 launch` any camera subscriber writes PNGs into the launch folder (the untracked `renders/` in the repo root). Pre-existing.
- The 1 cm bent-leaf unpick tolerance still has no automated test.

## 2026-10-26 Soil-only collide bit (robot interface 2)
### Goal & outcome
The user drove the Amiga into the carrots: RTF fell to 0.5%, carrots flew and the Amiga vanished. Spike with a 37 kg wheel rig over a carrot row (one Pixel, physics only) found the cost: a heavy wheel pressing gram-light leaves into the soil (0.03x); a wheel touching only the soil runs fast. Built fix (a): bit 0 belongs to the soil alone (soil 0x3, leaves 0xFFFE, roots 0xFFFC), the Active Region skips collisions that share no bit with the Plants, `robot_interface` 2. A wheel with `collide_bitmask` 0x1 picks nothing and runs at 2.1x on the rig; the default wheel is unchanged (0.09x, 10 picks).
### Decisions & why
- Soil gets a second bit (1) shared with leaves instead of dropping leaf-soil contact: leaves keep resting on the soil, so settle, squeeze and unpick behaviour stay as validated. Roots skip both soil bits.
- Opt-out is robot-side (wheels and chassis set 0x1), zero config stays the default: a robot that keeps 0xFFFF behaves as in interface 1, except that 0x1 no longer touches leaves (hence the version bump).
- Runaway guard (fix b) not built: the explosion was not reproduced in 2 to 4 s of rig sim; build it after a reproduction (suspect the Amiga's wheel-fork boxes bulldozing leaves).
### Lessons / gotchas
- Spike numbers (interface 1 bits): wheel on leaves+roots 0.03x, rides 2.3 cm up; leaves off the soil 0.07 to 0.1x; wheel on soil+leaves without roots 0.03x (roots are not the cost); soil-only wheel with 10 Picked Plants whose leaves rest on the soil 0.23x, leaves off the soil about 1x. Picked Plants cost on their own, so skipping the pick matters as much as skipping the contact.
- A new region probe first sat at the same spot as an existing probe, so the old system passed too; a test probe must reach a Plant no other probe reaches, checked by running the old .so.
- NVIDIA in the container: the toolkit is installed; `--gpus all -e NVIDIA_DRIVER_CAPABILITIES=all` injects the 595.99 EGL/GLX libs into amiga-ros:jazzy (checked), plus the PRIME and EGL vendor env vars. GUI on NVIDIA in the container UNVERIFIED.
- gz.sim8 Python: `Link.world_pose` needs `import gz.math7` first, or pybind cannot convert the Pose3d.
### State
Branch m5e-soil-bit stacked on m5e-packaging, commit f626a43, not pushed. Local tag v0.5.0 still on m5e-packaging (9af4e39). Validated: pytest 104 passed, 144 skipped; ruff; region test fails against m5e-packaging's system and passes now; spike rerun on the new build (soil-only wheel 0 picks 2.1x, default wheel unchanged). Slow settle and squeeze not rerun (leaf-soil, leaf-leaf and root contacts unchanged by the bit choice). Amiga with 0x1 wheels UNVERIFIED (needs the amiga_description change).
### Open items
- amiga_description: `collide_bitmask` 0x1 on wheels and base collisions (URDF `<gazebo reference>` collision surface block; check the conversion with `gz sdf -p`). Then the user drives into the beds again.
- Tag: merge m5e-packaging and m5e-soil-bit, then tag v0.5.0 on the merge so the release carries interface 2.
- Fix (b) runaway guard after reproducing the explosion (fork box rig, about 2 to 3 min on one Pixel).
- From M5e: amiga_ros2 spawn pose args, joint_state_broadcaster timeout, gz-rendering 8.3.0; camera save path relative to the cwd; the flaky full-Pixel grip test.

## 2026-10-26 Amiga chassis and wheels on the soil-only bit
### Goal & outcome
In amiga_description (branch feat/soil-only-collisions, 67c9ae1, not pushed): `collide_bitmask` 0x01 on base_link and the four wheels. Container drive test (pixelfield m5e-soil-bit, local amiga_description mounted over the image's v0.5.1): the Amiga spawned in a gap heading 0.8 rad drove 0.3 m/s diagonally across the beds for about 15 m at 0.95 to 1.0x, 3 Plants picked (arm and arm platform keep the default bits), z stays on the soil. Row added to perf.md.
### Decisions & why
- Opt-out lives in the robot description, not in pixelfield: other worlds are unaffected (ground planes and obstacles use 0xFFFF, which shares bit 0), the real robot ignores `<gazebo>` tags, Amiga_ws has its own amiga_description copy, and amiga_ros2's image pins v0.5.1 until someone bumps it.
### Lessons / gotchas
- sdformat URDF conversion: a second `<gazebo reference>` block with a `<collision><surface>` blob for a link replaces the friction set by `mu1`/`mu2`/`fdir1` in an earlier block (the wheels came out with an empty `<friction/>`). The blob must sit in the same block as the friction tags; checked by diffing `gz sdf -p` output against main (only the 13 bitmask lines and empty default surface elements on the 9 base boxes are added, wheel mu kept, prefix works).
- Collisions lumped from base_link into base_footprint keep the extension's bitmask; collisions lumped from child links (amiga_ros2's arm platform) do not.
- The scratchpad was emptied between sessions; keep container scripts reproducible from the log, not from scratch files.
### State
pixelfield m5e-soil-bit (f626a43 plus this log and the perf row), amiga_description feat/soil-only-collisions 67c9ae1, both not pushed. Validated: `gz sdf -p` diff of the Amiga model; container drive test above. Explosion while driving into beds with the default bits not reproduced; with the new bits it cannot happen through wheel or chassis contact.
### Open items
- User: drive into the beds in the GUI with the local amiga_description (mount it over /ros2_ws/src/amiga_description and `colcon build --packages-select amiga_description`).
- amiga_description: PR, tag (v0.6.0?), then amiga_ros2 bumps its pin. Merge pixelfield m5e-packaging and m5e-soil-bit, tag v0.5.0 on the merge.
- The arm platform lumped into base_footprint by amiga_ros2 keeps the default bits; set 0x1 there too if it ever reaches into the foliage.

## 2026-10-26 GUI crash on unpick: 1 s re-pick delay
### Goal & outcome
The user's GUI run (Amiga with soil-only chassis and wheels) crashed: `Another item already exists with name: r7c2::link::r7c2-012`, then a segfault in `SceneManager::CreateVisual`. Cause: an unpick rebuilt the Plant's static visual and a quick re-pick (the arm or arm platform, default bits, at the bed edge) removed it within one GUI frame; gz-sim's `RenderUtil::Update` applies removals before creations and checks timestamps only for models, so the visual stayed as a ghost and the next unpick duplicated its name. Fix on m5e-unpick-cooldown (e73f076): an unpicked Plant cannot be picked again for 1 s of sim time (region skips it, the pick service refuses it). ADR 0010 and spec 14 amended.
### Decisions & why
- Cooldown over unique visual names: unique names would avoid the crash but leave ghost Plants in the GUI.
- 1 s of sim time spans many GUI frames even at 10x real time; the cost is a robot passing through that one Plant's static visual during that second.
### Lessons / gotchas
- Headless servers did not show it: the Sensors system's render update runs every step, so creation and removal never share a batch. GUI-only races need a GUI run or reading gz-sim's RenderUtil (gz-sim8 `src/rendering/RenderUtil.cc`).
- In the region test, Plants of one group unpick at very different times (2.3 s, 4.8 s, 6.8 s after the probe left), so a test on re-pick timing must use the latest unpick and expect earlier ones at the return.
- The null dereference after a failed `CreateVisual` is a gz-sim bug worth reporting upstream.
### State
Branch m5e-unpick-cooldown stacked on m5e-soil-bit, commit e73f076, not pushed. Validated: pytest 105 passed, 144 skipped; ruff; the new test fails against m5e-soil-bit's system (re-picked 0.11 s after the unpick) and passes now. GUI rerun by the user UNVERIFIED.
### Open items
- User: rerun the GUI drive with branch m5e-unpick-cooldown.
- Report the CreateVisual null dereference to gz-sim.
- amiga_ros2 arm platform: bitmask 0x1 so it stops picking edge Plants.
- Merge order: m5e-packaging, m5e-soil-bit, m5e-unpick-cooldown; tag v0.5.0 on the last merge.

## 2026-10-26 GUI crash at the first unpick: rebuilt visuals get new names
### Goal & outcome
The cooldown (e73f076) did not stop the user's GUI crash: it always hit r7c2-012 at its first unpick, after the Amiga spawned next to it (0.25 m from the arm platform) and the user drove off without touching any Plant. Started with `-s` and the GUI attached after the spawn, the same drive did not crash, so the GUI missed the pick's removal of the static visual during its startup. Fix (this commit): an unpick rebuilds the static visual as `<id>~<n>` and the pull-out system tracks the current name. Region tests check `~1` and `~2` names and one visual per Plant; both checks fail on e73f076.
### Decisions & why
- New names over trying to detect the GUI: the race lives in gz-sim's GUI and depends on GPU and load timing; a unique name makes a duplicate impossible whatever the timing. Cost: a GUI that missed a removal shows a stale copy, visible only once that Plant is pulled out.
- The 1 s re-pick delay stays: it covers the create-and-remove-in-one-frame ghost.
### Lessons / gotchas
- Four Xvfb (llvmpipe) GUI reproductions did not crash (picks during GUI load, flapping, 10 x 10 Field); the race needs the real GPU's timing. The user's `-s` plus later `gz sim -g` run was the discriminating test.
- gz.sim8 Python has no Visual class or name accessor; tests probe the predictable names with `Link.visual_by_name`.
- My handoff once said "everything as before" without the `docker run`; the user ran the in-container block on the host, which added `safe.directory '*'` to the global git config and colcon dirs to the repo (cleanup given). Every command block now names where it runs (memory: full-commands).
### State
Branch m5e-unpick-cooldown, not pushed. Validated: pytest 105 passed, 144 skipped; ruff; region name checks fail on e73f076 and pass now. GUI with the normal launch (GUI started with the server) UNVERIFIED until the user reruns it.
### Open items
- User: rerun with the normal launch (GUI together with the server).
- Report the gz-sim GUI issues upstream: missed removal at startup, removals applied before creations without a visual timestamp check, null dereference after a failed CreateVisual.
- Amiga does not push Plants when driving over beds (soil-only wheels, by design); a "trampled" visual only if a demo needs it.

## 2026-10-28 Venue: Avans greenhouse around a Field (M5f)
### Goal & outcome
Optional Field Spec `venue` (size, center, wall) adds a glasshouse around the Field, for looks only: 0.6 m paver floor around the soil, glass walls and gable roof, steel frame, low stone wall. Example `examples/avans_kas.yaml`: the agrobot competition bed, 3 x 8 Pixels of 0.9 m, Path Gaps every column of 0.624 m (Amiga wheel track 1.524 m straddling one column), border 0.03 so the soil is about 4.0 x 7.26 m, random mix of all four Crops, 1420 Plants. Manifest gets a top-level `venue` key (null without one). Commit 5c2974d on m5f-venue.
### Decisions & why
- Bed layout (a) 3 x 8 with Path Gaps, and the other eight discussion recommendations, accepted by the user's IMPLEMENT without separate answers. The real bed's paths (or wheels on the soil) are still to be confirmed by the user.
- Floor, glass and frame are each one OBJ mesh written at build time (floor UVs repeat per 4 x 4 pavers, joints aligned to the soil's south-west corner): four visuals for the whole greenhouse instead of hundreds of boxes, since a box maps its texture once per face.
- Paver texture baked procedurally (`generators/pavers.py`), no external asset. Exporter keeps its own copy of PAVER and PERIOD (like SOIL_ATLAS) so `build` never imports PIL; a test checks they match.
- No collisions on the greenhouse; robots drive through glass, frame and wall. The floor is the existing soil plane.
- Soil tiles scaled to whole counts (`round`, tiles about 0.67 to 1.5 m) so they end exactly at the Border; otherwise the overhang would z-fight with the pavers. Changes every world's soil visuals slightly, not physics.
- The footprint must leave at least 0.5 m of pavers around the soil (core `VENUE_MIN_FLOOR`): one rule keeps the stone wall off the soil and avoids an empty floor mesh.
- Manifest `venue` is an added key: format_version 1 and robot_interface 2 unchanged.
### Lessons / gotchas
- gz ogre2 honours an SDF PBR material on an OBJ visual and wraps UVs beyond 0..1 (checked by render), so one mesh can tile a texture over any area.
- Glass with `cast_shadows` false lets the sun through; the frame still casts shadows on the floor.
- A coplanar face (stone wall ends against the gable glass) z-fights; the wall is 2 cm shorter.
### State
Branch m5f-venue, commit 5c2974d, not pushed. Validated: pytest 113 passed, 144 skipped (slow); ruff; `gz sdf -k` on the kas world; two wide-camera renders (pavers, joints at the bed edge, see-through glass, frame shadows; done before the tile `round` change and the 2 cm wall trim); perf rows: kas world with a 30 Hz full-HD camera 1.00x with and without the Venue, +23 MiB VRAM; validator agent (odd inputs, OBJ winding and indices, soil-tile test fails on the old overhang code, other worlds' Manifest only gains `venue: null`, build works with pyyaml only). GUI look UNVERIFIED.
### Open items
- User: confirm the real bed layout (3 x 8 with paths, or 4 x 8 with wheels on the soil) and the greenhouse size and bed position; adjust `examples/avans_kas.yaml`.
- User: push m5f-venue, PR, merge; amiga_ros2 then pins the merge commit (or 5c2974d) and adds kas spawn support (pavers from Manifest `venue.bounds`).
- `venue: null` in a spec raises like `border: null`; make it mean "no Venue" if anyone writes that.

## 2026-10-28 Avans greenhouse: 4 pavers each side
### Goal & outcome
The user asked for a narrower floor: 4 pavers west and east of the bed. Option (a) chosen by the user: the whole greenhouse narrows to 8.808 m (4.008 m soil plus 2 x 2.4 m), length stays 25 m; only `examples/avans_kas.yaml` changed, plus docs and a test on the venue bounds.
### Decisions & why
- Narrower greenhouse over a 12 m greenhouse with a second floor type beyond the pavers: matches "about 4 tiles on each side" of the real kas with no code change. The ridge drops to about 6.05 m (pitch fixed).
### Lessons / gotchas
- The stone wall stands on the outer 0.25 m of the 4th west paver (inside the footprint by design).
### State
Branch m5f-venue, commit after 5c2974d (see git log), not pushed. Validated: fast tests (core, gazebo, pavers) 71 passed; ruff; `gz sdf -k`; overhead render shows 4 pavers east of the bed. The perf row was measured at 12 x 25 m (same 4 visuals, not re-measured).
### Open items
- User: confirm the real bed layout and the greenhouse length; push, PR, merge; amiga_ros2 pins the merge commit.

## 2026-10-28 Crop overrides: build --set (M5g)
### Goal & outcome
amiga_ros2 needs carrots 10 cm apart in the row (the gripper's 3 cm pads grab neighbours' stalks at 4 cm) on the multi-Crop `avans_kas.yaml`, without copying crop files. Built `pixelfield build <spec> --set <crop>.<key path>=<value>` (repeatable), Manifest `crop_overrides` (only when used), more crop checks, and a margin check across Pixels. avans_kas with carrots at 0.10: 961 Plants (341 carrots instead of 800, other Crops identical). Commit 0856a94 on m5g-crop-overrides.
### Decisions & why
- CLI `--set` over a `--crops` overlay or spec includes: no file at all, and `--crops` keeps its meaning (an overlay would silently fill keys a full custom file left out on purpose).
- Overrides replace the YAML values before parsing, so crop file checks apply unchanged; an override must keep the file value's kind (finite number, list of the same length, same type). That one rule also keeps the Manifest valid JSON.
- Refused: Crops not in the Field, keys missing from the file, `name`, keys a build ignores (`hue_shift`, `generator`: they would claim a change in the Manifest), the same key twice.
- `crop_overrides` is absent without overrides (sorted keys when present): builds without `--set` stay byte-identical, checked against main for all 11 examples (validator) and again for 3 after the fixes.
- New check for crop files too: root crop margin >= widest root radius x largest scale. The spec only claimed it before; the shipped Crops pass (carrot 0.023 < 0.04, beetroot 0.045 < 0.05, radish 0.025 < 0.05).
### Lessons / gotchas
- YAML 1.1 reads `1e-1` as a string (needs `1.0e-1`), and `0x10` as 16. Documented in spec section 6.
- Crop files had almost no checks (planting values went straight into `PlantingPattern(**...)`); bad values gave tracebacks deep in layout. Planting, scale, pull_out_force and variants are now checked.
### State
Branch m5g-crop-overrides from main 01def74, commit 0856a94. Validated: pytest 116 passed, 144 skipped (slow); ruff; byte-identical builds; validator agent (root overlap within and across Pixels at 0.10 and at the margin boundary, override reaches plants/<id>.sdf, plant_info reads such a Manifest, works from a foreign cwd). pick/pull/grip on an overridden world UNVERIFIED (unchanged code paths; they read only Plant entries).
### Open items
- `variants` above the Variants the library holds is not checked (pre-existing for crop files).
- The Manifest does not record which `--crops` folder was used (pre-existing).
- User: PR, merge; amiga_ros2 pins the merge commit and drops its carrot.yaml copy.

## 2026-10-29 No leaf contact between Plants (M5h)
### Goal & outcome
amiga_ros2's xArm 6 lifting r6c1-041 in avans_kas (carrots at 0.10) pulled its in-row neighbours out through leaf-to-leaf contact. Now each Picked Plant's leaves get one collide bit of 2 to 7 from the pull-out system, so leaves of different Plants do not touch. Commit e4d6330 on m5h-plant-contact (stacked on m5g-crop-overrides, same content as main c37045b).
### Decisions & why
- Per-pick collide bits over low leaf friction (dartsim takes the lower friction of two surfaces, so pads would slip too) and over a force cap (dartsim has none). Choice: a free bit, else the one whose nearest Picked Plant is farthest. ADR 0010 amended (it had rejected collide bits for all overlapping neighbours; only Picked Plants need them).
- Bits: soil 0xFD, buried root 0x2, leaves 0xFC in files, one bit once picked. robot_interface stays 2; spec now says only default, 0xFF, 0xFFFF and 0x1 are part of the interface.
### Lessons / gotchas
- A collision without collide_bitmask acts as 0xFF, not 0xFFFF: leaves on bit 8 or higher are not touched by a default robot collision. Only 6 leaf bits.
- gz-physics dartsim reads collide_bitmask from the SDF element, not from sdf::Surface: setting it through the DOM (Collision::SetSurface) had no effect.
- The pixelfield-only repros (pairs, kas with the test gripper, an xArm-like hand with body box and descent) never showed the bug (neighbour d at most 0.7 mm); the dense carrot Pixel did (r0c0-020 stuck at d 64 mm, r0c0-021 up 20 mm), and the real amiga pick did. An A/B in amiga's own container settled the cause before any code was written.
- A root whose bits overlap the soil's is pushed up by the soil (seen at 130 mm in a bisect); keep root and soil bits disjoint.
- Killing all ros2 processes between launches in one container also kills the ROS daemon; the next launch's controller spawners fail. One container per run.
### State
Branch m5h-plant-contact, commit e4d6330, not pushed. Validated: pytest 117 passed, 144 skipped; slow settle and squeeze of the v00 Variants; ruff; new dense test fails on the old system binary and passes now; amiga_ros2 xArm 6 pick of r6c1-041 in avans_kas, headless, 3/3 pulled out with r6c1-040 at 0.1 mm and r6c1-042 at 0 (as-is: 195 and 160 mm, detached). Perf row not measured (fewer contacts only).
### Open items
- r6c1-039 rises 4.5 to 5.6 mm past its d_peak in every amiga run, with or without leaf contact: robot contact (arm links), for amiga_ros2.
- Jaws no longer held apart by the target's bunch close further on a neighbour petiole lying between them (dense Pixel r0c0-004: neighbour about 20 mm).
- More than 6 Picked Plants close together share bits and touch again; a pulled-out Plant keeps its bit after it leaves the table.
- User: push m5h-plant-contact, PR, merge; amiga_ros2 pins the commit.
