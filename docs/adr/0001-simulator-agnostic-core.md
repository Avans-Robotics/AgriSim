---
status: accepted
---

# Simulator-agnostic core with per-simulator Exporters

Gazebo is the first target, but Isaac Sim, MuJoCo or others may follow. The core (Field Spec parsing, Pixel grid, Planting Pattern, Field Layout) is pure Python with no simulator imports and is deterministic for a given seed. Everything simulator-specific lives in an Exporter that reads a Field Layout and writes files for one simulator. Meshes are stored as glTF (`.glb`), which all candidate simulators and renderers can load.

## Considered Options

- **Gazebo-only generator.** Faster to start, but every future simulator would mean a rewrite, and the Field Layout could not be reused for offline dataset rendering (see ADR 0005).

## Consequences

- Adding a simulator means adding one Exporter module; the core is untouched.
- Simulator-specific behavior (physics plugins, world files, lighting) must never leak into the core. Physical properties such as Pull-out Force are stored as plain data in the Field Layout and interpreted by each Exporter.
