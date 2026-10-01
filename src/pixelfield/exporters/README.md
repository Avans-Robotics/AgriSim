# exporters

One subpackage per simulator or renderer (`gazebo/` first; `blender/`, `isaac/`, `mujoco/` later). Each reads a Field Layout and writes a world folder plus `manifest.json`. Registered by name in `EXPORTERS`.

`svg.py` is a top-down view of Pixels and Plant positions, for checking a Field Layout by eye.
