"""Top-down SVG of Pixels and Plant positions, for checking a Field Layout by eye."""

from pathlib import Path

from pixelfield.core.layout import FieldLayout

PX_PER_M = 1000
PLANT_COLORS = ["#3c8d2f", "#c9d93a", "#2f7fbf", "#d9603a", "#9b4fc9"]  # cycled per Crop
CROP_FILL, EMPTY_FILL = "#8b6b4a", "#c8b89a"
GRID_M = 0.1  # grid spacing, also the scale bar length
LINE_HEIGHT = 26
PAD = 20  # white border, so the frame at the origin corner is not clipped


def export(layout: FieldLayout, out_dir: Path) -> Path:
    spec = layout.spec
    size = spec.pixel_size * PX_PER_M
    width, height = spec.cols * size, spec.rows * size

    def svg_y(y: float) -> float:  # SVG y points down, Field y points north
        return height - y * PX_PER_M

    crops = sorted({p.crop for p in layout.plants})
    color = {crop: PLANT_COLORS[i % len(PLANT_COLORS)] for i, crop in enumerate(crops)}
    legend = _legend(layout, color, width, top=height)
    total_width = width + 2 * PAD
    total_height = height + LINE_HEIGHT * legend["lines"] + 2 * PAD

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width:.0f}" '
        f'height="{total_height:.0f}" viewBox="{-PAD} {-PAD} {total_width} {total_height}">',
        f'<rect x="{-PAD}" y="{-PAD}" width="100%" height="100%" fill="#fff"/>',
    ]
    for p in layout.pixels:
        fill = CROP_FILL if p.crop else EMPTY_FILL
        parts.append(
            f'<rect x="{p.origin[0] * PX_PER_M:.1f}" y="{svg_y(p.origin[1]) - size:.1f}" '
            f'width="{size:.1f}" height="{size:.1f}" fill="{fill}" stroke="#5a4632">'
            f"<title>r{p.row}c{p.col} {p.crop or 'empty'}</title></rect>"
        )
    parts.append(_grid(width, height, size))
    for p in layout.plants:
        parts.append(
            f'<circle cx="{p.x * PX_PER_M:.1f}" cy="{svg_y(p.y):.1f}" r="{8 * p.scale:.1f}" '
            f'fill="{color[p.crop]}"><title>{p.id} {p.variant}</title></circle>'
        )
    parts.append('<text x="6" y="18" font-size="16" fill="#fff">N &#8593;</text>')
    parts += _frame(height)
    parts += legend["parts"]
    parts.append("</svg>")

    path = Path(out_dir) / "field.svg"
    path.write_text("\n".join(parts) + "\n")
    return path


def _grid(width: float, height: float, pixel: float) -> str:
    """Light lines every GRID_M from the Field origin, skipping Pixel edges (already outlined)."""
    step = GRID_M * PX_PER_M
    lines = []
    for n, length, vertical in ((width, height, True), (height, width, False)):
        for i in range(1, round(n / step)):
            at = i * step
            if abs(at / pixel - round(at / pixel)) < 1e-6:
                continue
            lines.append(f"M{at:.1f} 0V{length:.1f}" if vertical else f"M0 {at:.1f}H{length:.1f}")
    return f'<path id="grid" d="{"".join(lines)}" stroke="#fff" stroke-opacity="0.25" fill="none"/>'


def _frame(height: float) -> list[str]:
    """x (east, red) and y (north, green) axes at the Field origin, the south-west corner."""
    k = GRID_M * PX_PER_M
    return [
        f'<g id="frame" stroke-width="3" font-size="14" font-weight="bold">'
        f'<path d="M0 {height}h{k - 10:.0f}" stroke="#e02020"/>'
        f'<path d="M{k:.0f} {height}l-12 -6v12z" fill="#e02020"/>'
        f'<path d="M0 {height}v{-(k - 10):.0f}" stroke="#20b020"/>'
        f'<path d="M0 {height - k:.0f}l-6 12h12z" fill="#20b020"/>'
        f'<text x="{k + 4:.0f}" y="{height - 4}" fill="#e02020">x</text>'
        f'<text x="-14" y="{height - k + 10:.0f}" fill="#20b020">y</text>'
        "</g>"
    ]


def _legend(layout: FieldLayout, color: dict[str, str], width: float, top: float) -> dict:
    """Legend below the Field: one entry per Crop with its Plant count, Empty Pixel, scale bar.

    Entries flow left to right and wrap to a new line when the Field is too narrow.
    """
    counts = {crop: sum(p.crop == crop for p in layout.plants) for crop in color}
    swatches = [
        (f'<circle cx="{{x}}" cy="{{y}}" r="7" fill="{color[c]}"/>', f"{c} ({n})")
        for c, n in counts.items()
    ]
    if any(p.crop is None for p in layout.pixels):
        swatches.append(
            (f'<rect x="{{x0}}" y="{{y0}}" width="14" height="14" fill="{EMPTY_FILL}" '
             f'stroke="#5a4632"/>', "empty Pixel")
        )  # fmt: skip
    bar = GRID_M * PX_PER_M
    swatches.append(
        (f'<path d="M{{x0}} {{y}}h{bar:.0f}m0 -5v10M{{x0}} {{y0}}v10" stroke="#000" fill="none"/>',
         f"{GRID_M * 100:.0f} cm (grid)")
    )  # fmt: skip

    # ponytail: text width estimated at 8 px per character, measure fonts only if labels clip.
    parts, x, line = [], 10.0, 0
    for i, (shape, label) in enumerate(swatches):
        shape_w = bar if i == len(swatches) - 1 else 14
        entry_w = shape_w + 8 + 8 * len(label) + 20
        if x > 10 and x + entry_w > width:
            x, line = 10.0, line + 1
        y = top + 20 + line * LINE_HEIGHT
        parts.append(shape.format(x=x + 7, y=y, x0=x, y0=y - 7))
        parts.append(
            f'<text x="{x + shape_w + 8:.1f}" y="{y + 5:.1f}" font-size="14" '
            f'font-family="sans-serif">{label}</text>'
        )
        x += entry_w
    return {"parts": parts, "lines": line + 1}
