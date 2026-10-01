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
