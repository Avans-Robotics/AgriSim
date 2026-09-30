---
status: accepted
---

# Committed Asset Library with pluggable Asset Generators

Plants are not generated as unique meshes. Each Crop has a small library of Variants (24 by default) that are committed to git as `.glb` files. The field generator only picks a Variant per Plant and applies its own rotation, scale and color shift. Asset Generators (a procedural trimesh script, a Blender export, hand-made models) are optional tools that fill the library; users of the library never need to run them.

## Why

- **Performance.** A simulator loads each mesh once and reuses it. A few dozen Variants reused thousands of times fit the 8 GB VRAM budget; thousands of unique meshes do not.
- **Accessibility.** Students can use the models without installing Blender or running any generator.
- **Reviewability.** Visual changes to a Crop show up as a versioned change to the library.

## Considered Options

- **Generate meshes on demand into a gitignored cache.** Keeps the repo small, but makes every user depend on the generator toolchain. Estimated library size (about 5 MB per Crop) does not justify it.
- **Unique mesh per Plant.** More variety, but prohibitive memory use for fields of thousands of Plants.

## Consequences

- The default Asset Generator is a pure-Python trimesh script. Blender-based generators are allowed but must write into the same library format.
- If the library grows past about 100 MB, move it to Git LFS.
