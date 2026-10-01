# pixelfield

Tools for generating pixel farming fields for robot simulation. A field is divided into square pixels, each holding one crop. Fields are described in a simple YAML file (hand-drawn or random), resolved into a simulator-independent layout, and exported to a simulator. Gazebo (Harmonic) is the first target; the end goal is harvesting with a simulated Farm-ng Amiga and manipulator.

**Status: milestone M1a.** The core turns a Field Spec into a Field Layout and Manifest; the only Exporter so far is a top-down SVG view. Gazebo export follows in M1b.

## Quick start

Install [uv](https://docs.astral.sh/uv/) once:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, from the repository root:

```bash
uv sync                                               # install dependencies
uv run pixelfield build examples/carrot_pixel.yaml    # writes out/carrot_pixel/: manifest.json, field.svg, world.sdf
gz sim out/carrot_pixel/world.sdf                     # open the world in Gazebo
uv run pytest                                         # tests
uv run ruff check . && uv run ruff format --check .   # lint
```

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
