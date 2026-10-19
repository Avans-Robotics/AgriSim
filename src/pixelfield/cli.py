"""Command line interface: `pixelfield build <field spec>`, `pixelfield generate <crop>`,
`pixelfield render <world.sdf>`, `pixelfield settle <variant>...`."""

import argparse
import json
from pathlib import Path

from pixelfield.core.layout import build_layout, to_manifest
from pixelfield.core.spec import load_crop, load_field_spec
from pixelfield.exporters import EXPORTERS, gazebo
from pixelfield.exporters.gazebo import plant


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
    settle.add_argument("--scale", type=float, default=1.0, help="Plant scale")
    args = parser.parse_args(argv)
    if args.command == "settle":
        _settle(parser, args)
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
