---
status: accepted
---

# CropCraft as a source of Variants, not as a dependency

[CropCraft](https://github.com/Romea/cropcraft) (Apache-2.0, INRAE) already generates crop fields for Gazebo from YAML, with a Blender asset library of bean, maize, vine and weeds at several growth stages. It is not used as the field generator: it is organised around crop rows rather than Pixels, it has no carrots and no harvesting physics, it requires Blender at run time, it is a standalone script rather than a library, and it exports to Gazebo Classic. Instead, a one-time Blender script exports selected CropCraft plants to `.glb` Variants in our Asset Library (see ADR 0003). Its YAML schema, weed mixing and labelled image output are used as design inspiration.

## Consequences

- Blender is only needed by whoever refreshes the imported Variants, never by users of the library.
- Imported assets keep CropCraft's Apache-2.0 attribution in `assets/library/<crop>/ATTRIBUTION.md`. Apache-2.0 material may be included in this AGPL-3.0 project.
- CropCraft is cited in any publication built on this work.
