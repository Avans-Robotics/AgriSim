# exporters

One subpackage per simulator or renderer (`gazebo/` first; `blender/`, `isaac/`, `mujoco/` later). Each reads a Field Layout and writes into the output folder next to `manifest.json`. Registered by name in `EXPORTERS`; `pixelfield build` runs all of them unless `--exporter` picks one.

- `gazebo/`: `world.sdf` for Gazebo Harmonic: textured soil with a 0.5 m border, sun and sky, VCT global illumination for cameras, a top-down and an oblique camera, and one static model per Pixel (named `r<row>c<col>`) holding its Plants as visuals named by Plant id, each using its Variant mesh (ADR 0007). Meshes and textures are copied next to `world.sdf`, so the output folder is self-contained. Crops without Variants get colored cylinders sized from the Planting Pattern. `render()` (`pixelfield render`) runs the world headless and saves `renders/top.png` and `renders/oblique.png`.
- `svg.py`: a top-down view of Pixels and Plant positions, for checking a Field Layout by eye.
- `colors.py`: Plant color per Crop, shared so the SVG and the Gazebo world match.
