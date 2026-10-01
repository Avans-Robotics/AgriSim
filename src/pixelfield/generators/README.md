# generators

Asset Generators that produce Crop Variants for `assets/library/`. Registered by Crop name in `GENERATORS`. The default carrot generator uses trimesh (ADR 0003), installed with the `generate` extra.

Run: `uv run pixelfield generate carrot`. It reads the Variant count and library folder from `crops/carrot.yaml`, replaces all `carrot_v*.glb` and `variants.json`, and writes a preview world to `out/carrot_variants/world.sdf`. Output is deterministic per Variant index.

Variant files are glTF binaries, y up as the glTF spec requires (z up is applied by whoever loads them). Origin: soil surface on the root axis.

`variants.json` holds per-Variant sizes in meters for collision shapes, in the z-up Field frame:

- `root.length`: crown top to tip; `root.radius`: shoulder radius; `root.top`: crown top above the soil.
- `foliage.height`: highest leaf point above the soil; `foliage.radius`: widest reach from the root axis.

Parts per Variant (glb nodes): `root`, `petioles`, `leaves`. Foliage materials are double-sided, so single-faced blades show from below too.
