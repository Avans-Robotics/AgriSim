"""Command line interface: `pixelfield build <field spec>`."""

import argparse
import json
from pathlib import Path

from pixelfield.core.layout import build_layout, to_manifest
from pixelfield.core.spec import load_crop, load_field_spec
from pixelfield.exporters import EXPORTERS


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
    args = parser.parse_args(argv)

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
