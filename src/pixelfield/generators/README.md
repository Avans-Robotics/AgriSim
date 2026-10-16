# generators

Asset Generators that produce Crop Variants for `assets/library/`. Registered by Crop name in `GENERATORS`. Root crops share `root_crop.py`, one entry per Crop in its `CROPS` table; romaine lettuce has `lettuce.py`, which reuses the root crop palette and file writing. Both use trimesh and Pillow (ADR 0003), installed with the `generate` extra.

Run: `uv run pixelfield generate carrot`. It reads the Variant count and library folder from `crops/carrot.yaml`, replaces all `carrot_*.glb` and `variants.json`, and writes a preview world to `out/carrot_variants/world.sdf`. Output is deterministic per Variant index.

Variant files are named `<crop>_<stage>_v<NN>.glb` (ADR 0008) and are glTF binaries, y up as the glTF spec requires (z up is applied by whoever loads them). Origin: soil surface on the root axis.

`variants.json` holds per-Variant sizes in meters, in the z-up Field frame (lettuce has `foliage` only, its root stays hidden):

- `root.length`: crown top to tip; `root.radius`: shoulder radius; `root.top`: crown top above the soil.
- `foliage.height`: highest leaf point above the soil; `foliage.radius`: widest reach from the root axis.

Root crop shapes are picked per Crop in `CROPS`: root profile `taper` (carrot), `globe` (beetroot) or `spindle` (radish); leaf `divided`, `simple` or `lobed`. An optional `tip_color` fades the root to a second color towards the tip (radish).

Each `.glb` holds one mesh with one double-sided material (single-faced blades show from below too). The parts (root crops: root, petioles, leaves; lettuce: outer, inner, rib) each sample their own column of a small sRGB palette texture; a fading root samples a vertical gradient in its column by height. `variant()` still returns the parts separately.
