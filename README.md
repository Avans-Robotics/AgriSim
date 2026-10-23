# pixelfield

Tools for generating pixel farming fields for robot simulation. A field is divided into square pixels, each holding one crop. Fields are described in a simple YAML file (hand-drawn or random), resolved into a simulator-independent layout, and exported to a simulator. Gazebo (Harmonic) is the first target; the end goal is harvesting with a simulated Farm-ng Amiga and manipulator.

**Status: v0.5.0 (milestone M5).** Gazebo Fields of carrot, beetroot, radish and lettuce Pixels with a ground-truth Manifest; root crop Plants can be pulled out by any robot through a gz-sim system. Robots live in their own repositories and load pixelfield worlds (see [Use in a robot repository](#use-in-a-robot-repository)).

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

## Use in a robot repository

pixelfield holds no robot ([ADR 0009](docs/adr/0009-robot-free-world-provider.md)): a robot repository installs it in its own image (ROS 2 Jazzy with `ros-jazzy-ros-gz`, which brings gz-sim 8), builds a Field and launches the world with its robot spawned into it. In the Dockerfile or by hand:

```bash
apt-get install -y python3-pip
git clone --branch v0.5.0 --depth 1 https://github.com/Avans-Robotics/AgriSim.git /opt/pixelfield
pip3 install --break-system-packages -e /opt/pixelfield   # editable: it finds its Asset Library in the clone
source /opt/ros/jazzy/setup.bash                          # puts the image's gz-sim on CMAKE_PREFIX_PATH
cmake -S /opt/pixelfield/src/pixelfield/exporters/gazebo/systems -B /opt/pixelfield/build/systems
cmake --build /opt/pixelfield/build/systems
export GZ_SIM_SYSTEM_PLUGIN_PATH=/opt/pixelfield/build/systems   # ENV in a Dockerfile
```

Then, from any folder:

```bash
pixelfield build /opt/pixelfield/examples/amiga_10x10.yaml -o ~/fields/amiga_10x10
ros2 launch amiga_arm_description gazebo.launch.py gz_args:="-r $HOME/fields/amiga_10x10/world.sdf"   # amiga_ros2
```

Spawn the robot in the Path Gaps or the Border, not on Plants: a robot spawned onto Plants crushes them and they stay picked (the unchanged amiga_ros2 launch spawns at the Field origin, the south-west corner, and runs at about 0.003x; spawned at x 2.024, y 1.5, heading north, the Amiga drives the gaps at 1.0x, see [perf.md](docs/design/perf.md)). The world is always named `pixelfield`. Its topics, the pick service and the frames are the robot interface ([spec section 14](docs/design/spec.md#14-robot-interface)). Without the systems on `GZ_SIM_SYSTEM_PLUGIN_PATH` the world still runs, but no Plant can be picked. `pixelfield pull` and `grip` (headless checks) need the gz Python bindings, which `source /opt/ros/jazzy/setup.bash` provides in a ROS image.

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
