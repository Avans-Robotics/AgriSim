---
status: accepted
---

# Variant naming with a growth stage slot

Variants are named `<crop>_<stage>_v<NN>` (for example `carrot_harvest_v07`) and live flat in `assets/library/<crop>/`. The stage is a plain lowercase word per Crop; only `harvest` exists so far. A Crop definition picks its stage with the optional `assets.stage` key (default `harvest`), and the Manifest keeps only the Variant name, which already contains the stage. Crop names are short (`carrot`, `beetroot`, `radish`, `lettuce`); the variety goes in the Crop definition.

Each Variant `.glb` is one mesh with one material: its parts sample their own block of a small palette texture. This file is for the static Field only.

## Why

Growth stages are a likely next axis (spec section 12, deferred item 5), and adding one later must not rename a library that four Crops already use. The slot costs nothing now: renaming the 24 carrot Variants once gave byte-identical files.

One mesh per Variant: rendering the 10 x 10 Field with an OAK-D-like camera is CPU-bound on render items, not triangles (docs/design/perf.md). Merging the three parts (root, petioles, leaves) cut items by 3x and raised the averaged RTF from 0.50 to 0.61 (nadir) with no visible change in the renders.

## Considered Options

- **Subfolder per stage** (`carrot/harvest/carrot_v07.glb`). Changes the library path logic for no gain over a name slot.
- **No slot until a second stage exists.** Renames the whole library later, which the spec ruled out.
- **BBCH codes as the stage** (`bbch49`). Precise, but cryptic in file names and different per crop family. A BBCH mapping can go in a Crop definition comment when a second stage arrives.
- **Vertex colors instead of a palette texture.** gz-common's `SubMesh` has no vertex color channel, so Gazebo would drop them.

## Consequences

- The palette texture is sRGB while the part colors are linear PBR factors, so the generator encodes them; skipping that makes Plants visibly darker.
- Generators keep the parts separate internally and merge only when writing the `.glb`. Articulated foliage for M4 (per-leaf pieces on spring-jointed links) can then be written as a second export of the same Variant, used only for the Plant spawned at the gripper.
- The Asset Generator extra needs Pillow for the texture.
