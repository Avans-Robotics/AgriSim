# pixelfield

Tools for generating pixel farming fields for robot simulation. A field is divided into square pixels, each holding one crop. Fields are described in a simple YAML file (hand-drawn or random), resolved into a simulator-independent layout, and exported to a simulator. Gazebo (Harmonic) is the first target; the end goal is harvesting with a simulated Farm-ng Amiga and manipulator.

**Status: design phase.** No code yet. Start with the design documents below.

## Documentation

- [Design spec](docs/design/spec.md): goals, architecture, formats, milestones and open questions.
- [Glossary](CONTEXT.md): the terms used throughout the project.
- [Architecture decisions](docs/adr/): why the project is built the way it is.
- [Prior art](docs/research/prior-art.md): related tools, data and sources.

## Repository layout

| Path | Contents |
|---|---|
| `src/pixelfield/core/` | Field Spec, Pixel grid, Planting Pattern, Field Layout. No simulator code. |
| `src/pixelfield/generators/` | Asset Generators that produce Crop Variants |
| `src/pixelfield/exporters/` | One Exporter per simulator or renderer |
| `crops/` | Crop definitions (YAML) |
| `assets/library/` | Committed Asset Library (`.glb` Variants, textures) |
| `examples/` | Example Field Specs |
| `tools/` | One-off scripts (asset imports, render checks) |
| `docker/` | Container image for running the simulation |
| `tests/` | Automated tests |
| `docs/` | Design spec, ADRs, research |

## Extending

- **New Crop**: add `crops/<crop>.yaml` and Variants in `assets/library/<crop>/`, either from a generator in `src/pixelfield/generators/` or dropped in by hand.
- **New simulator**: add an Exporter in `src/pixelfield/exporters/`. The core does not change.

## Credits

Some Crop Variants will be imported from [CropCraft](https://github.com/Romea/cropcraft) (Apache-2.0, INRAE). See the attribution file in each affected `assets/library/<crop>/` folder.

## License

AGPL-3.0, see [LICENSE](LICENSE).
