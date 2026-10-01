# exporters

One subpackage per simulator or renderer (`gazebo/` first; `blender/`, `isaac/`, `mujoco/` later). Each reads a Field Layout and writes into the output folder next to `manifest.json`. Registered by name in `EXPORTERS`; `pixelfield build` runs all of them unless `--exporter` picks one.

- `gazebo/`: `world.sdf` for Gazebo Harmonic: flat soil with a 0.5 m border, a sun, and one static model per Plant (named by Plant id). Until Variants exist (M1d), Plants are colored cylinders sized from the Planting Pattern.
- `svg.py`: a top-down view of Pixels and Plant positions, for checking a Field Layout by eye.
- `colors.py`: Plant color per Crop, shared so the SVG and the Gazebo world match.
