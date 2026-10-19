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
