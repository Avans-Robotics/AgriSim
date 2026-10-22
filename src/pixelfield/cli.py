"""Command line interface: `pixelfield build <field spec>`, `pixelfield generate <crop>`,
`pixelfield render <world.sdf>`, `pixelfield settle <variant>...`,
`pixelfield pick <world folder> <plant id>`, `pixelfield pull <world folder> <plant id>`,
`pixelfield grip <world folder> <plant id>`, `pixelfield squeeze <variant>...`."""

import argparse
import json
from pathlib import Path

from pixelfield.core.layout import build_layout, to_manifest
from pixelfield.core.spec import load_crop, load_field_spec
from pixelfield.exporters import EXPORTERS, gazebo
from pixelfield.exporters.gazebo import gripper, plant


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="pixelfield")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="build a Field from a Field Spec")
    build.add_argument("spec", type=Path, help="Field Spec YAML")
    build.add_argument("-o", "--out", type=Path, help="output folder (default: out/<spec name>)")
    build.add_argument(
        "--crops", type=Path, default=Path("crops"), help="folder of Crop definitions"
    )
    build.add_argument(
        "--exporter", choices=sorted(EXPORTERS), help="run only this Exporter (default: all)"
    )
    generate = commands.add_parser("generate", help="regenerate a Crop's Variants")
    generate.add_argument("crop", help="Crop name, e.g. carrot")
    generate.add_argument(
        "--crops", type=Path, default=Path("crops"), help="folder of Crop definitions"
    )
    render = commands.add_parser("render", help="save camera images of a Gazebo world, headless")
    render.add_argument("world", type=Path, help="world.sdf written by build")
    render.add_argument("--iterations", type=int, default=5000, help="simulation steps to run")
    settle = commands.add_parser("settle", help="settle check of articulated Variants, headless")
    settle.add_argument("variants", nargs="+", type=Path,
                        help="library path without extension, e.g. "
                             "assets/library/carrot/carrot_harvest_v00")  # fmt: skip
    squeeze = commands.add_parser("squeeze", help="squeeze check of articulated Variants, "
                                                   "headless")  # fmt: skip
    for command in (settle, squeeze):
        command.add_argument("--scale", type=float, default=1.0, help="Plant scale")
    squeeze.add_argument("variants", nargs="+", type=Path,
                         help="library path without extension")  # fmt: skip
    pick = commands.add_parser("pick", help="pick a Plant in a running Field world")
    pull = commands.add_parser("pull", help="scripted pull of a Plant of a Field, headless")
    grip = commands.add_parser("grip", help="pull a Plant of a Field by its leaves with the "
                                             "test gripper, headless")  # fmt: skip
    for command in (pick, pull, grip):
        command.add_argument("world", type=Path, help="folder written by build")
        command.add_argument("plant", help="Plant id from the Manifest, e.g. r0c0-017")
    for command in (pull, grip):
        command.add_argument("--speed", type=float, default=plant.PULL_SPEED,
                             help="lift speed, m/s")  # fmt: skip
    for command in (grip, squeeze):
        command.add_argument("--force", type=float, default=gripper.GRIP_FORCE,
                             help="grip force per jaw, N")  # fmt: skip
    grip.add_argument("--lift", type=float,
                      help="lift this far, m (default: past the root depth)")  # fmt: skip
    grip.add_argument("--gui", action="store_true",
                      help="run in real time with a gz GUI attached, and keep it open "
                           f"{gripper.GUI_LINGER:g} s after the pull")  # fmt: skip
    pull.add_argument("--release", type=float,
                      help="let go at this lift, m (default: past the root depth)")  # fmt: skip
    args = parser.parse_args(argv)
    if args.command in ("pick", "pull"):
        _pick(parser, args)
        return
    if args.command == "settle":
        _settle(parser, args)
        return
    if args.command == "squeeze":
        _squeeze(parser, args)
        return
    if args.command == "grip":
        _grip(parser, args)
        return
    if args.command == "generate":
        _generate(parser, args)
        return
    if args.command == "render":
        for image in gazebo.render(args.world, args.iterations):
            print(image)
        return

    try:
        spec = load_field_spec(args.spec)
        names = {name for row in spec.grid for name in row if name}
        crops = {name: load_crop(args.crops / f"{name}.yaml") for name in names}
    except (OSError, ValueError, KeyError, TypeError) as e:
        parser.exit(1, f"error: {e}\n")

    layout = build_layout(spec, crops)
    out = args.out or Path("out") / args.spec.stem
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(to_manifest(layout), indent=2) + "\n")
    for name in [args.exporter] if args.exporter else sorted(EXPORTERS):
        EXPORTERS[name](layout, out)
    print(f"{len(layout.plants)} Plants in {spec.rows} x {spec.cols} Pixels, written to {out}")


def _generate(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    try:
        from pixelfield.generators import GENERATORS
    except ImportError as e:
        parser.exit(1, f"error: {e}; install the generate extra: uv sync --extra generate\n")
    try:
        crop = load_crop(args.crops / f"{args.crop}.yaml")
        generator = GENERATORS[crop.name]
    except (OSError, ValueError, KeyError, TypeError) as e:
        parser.exit(1, f"error: no Crop or Asset Generator: {e}\n")

    paths = generator(crop.variants, Path(crop.library))
    world = gazebo.preview(paths, Path("out") / f"{crop.name}_variants")
    print(f"{len(paths)} Variants written to {crop.library}, preview: gz sim {world}")


def _settle(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    failed = 0
    for variant in args.variants:
        world = plant.settle_world(variant, Path("out") / f"settle_{variant.name}", args.scale)
        r = plant.settle(world)
        failed += not r["settled"]
        print(f"{variant.name}: {'settled' if r['settled'] else 'NOT settled'}, "
              f"max speed after {plant.SETTLE_AFTER:g} s {r['max_speed_after'] * 1000:.2f} mm/s "
              f"({r['fastest_link']}), max travel {r['max_travel'] * 1000:.1f} mm, "
              f"view: gz sim {world}")  # fmt: skip
    if failed:
        parser.exit(1, f"{failed} of {len(args.variants)} Variants did not settle\n")


def _squeeze(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    failed = 0
    for variant in args.variants:
        out = Path("out") / f"squeeze_{variant.name}"
        try:
            r = gripper.squeeze(variant, out, args.scale, args.force)
        except RuntimeError as e:
            parser.exit(1, f"error: the squeeze check failed:\n{e}\n")
        except (OSError, ValueError, StopIteration) as e:
            parser.exit(1, f"error: {variant} is not an articulated Variant: {e!r}\n")
        failed += not r["held"]
        print(f"{variant.name}: {'held' if r['held'] else 'NOT held'}, "
              f"gap {r['gap'] * 1000:.1f} mm, {len(r['escaped'])} of {r['leaves']} leaves "
              f"outside the jaws {r['escaped']}{', NaN' if r['nan'] else ''}")  # fmt: skip
    if failed:
        parser.exit(1, f"{failed} of {len(args.variants)} Variants were not held\n")


def _grip(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    try:
        r = gripper.grip(args.world, args.plant, args.force, args.speed, args.lift, args.gui)
    except RuntimeError as e:
        parser.exit(1, f"error: the grip check failed:\n{e}\n")
    except (OSError, ValueError) as e:
        parser.exit(1, f"error: {e}\n")
    if not r["requested"]:
        parser.exit(1, "error: the pull-out system refused the pick or is not loaded; build it "
                       "(see CLAUDE.md)\n")  # fmt: skip
    if r["detach_d"]:
        result = f"detached at d = {r['detach_d'] * 1000:.1f} mm"
    else:
        result = (
            f"NOT detached, slipped {r['slip'] * 1000:.1f} mm, d up to {r['max_d'] * 1000:.1f} mm"
        )
    print(f"{args.plant}: {result} (root depth {r['depth'] * 1000:.1f} mm), "
          f"grip {args.force:g} N per jaw, peak wrist force {r['peak_wrist']:.2f} N "
          f"(Pull-out Force {r['pull_out_force']:.2f} N plus weight {r['weight']:.2f} N), "
          f"log: {r['log']}")  # fmt: skip


def _pick(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    try:
        if args.command == "pick":
            if not plant.pick(args.world, args.plant):
                parser.exit(1, "error: pick refused or no reply: the Plant was already picked "
                               "(see the gz log), or no world is running with the pull-out "
                               "system on GZ_SIM_SYSTEM_PLUGIN_PATH\n")  # fmt: skip
            print(f"picked {args.plant}")
            return
        r = plant.pull(args.world, args.plant, args.speed, args.release)
    except RuntimeError as e:
        parser.exit(1, f"error: the pull check failed:\n{e}\n")
    except (OSError, ValueError) as e:
        parser.exit(1, f"error: {e}\n")
    if not r["requested"]:
        parser.exit(1, "error: the pull-out system refused the pick or is not loaded; build it "
                       "(see CLAUDE.md)\n")  # fmt: skip
    detach = f"detached at d = {r['detach_d'] * 1000:.1f} mm" if r["detach_d"] else "NOT detached"
    print(f"{args.plant}: {detach} (root depth {r['depth'] * 1000:.1f} mm), "
          f"peak soil force {r['peak_force']:.2f} N (Pull-out Force {r['pull_out_force']:.2f} N), "
          f"peak pull {r['peak_pull']:.2f} N with weight {r['weight']:.2f} N, "
          f"grouped visual removed: {r['visual_before'] and not r['visual_after']}, "
          f"root bottom after the drop {r['landed_bottom'] * 1000:.1f} mm, "
          f"log: {r['log']}")  # fmt: skip
    if not r["detach_d"] and args.release is None:
        parser.exit(1, "error: the Plant did not detach\n")
