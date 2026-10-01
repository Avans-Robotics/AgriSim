"""Top-down SVG of Pixels and Plant positions, for checking a Field Layout by eye."""

from pathlib import Path

from pixelfield.core.layout import FieldLayout

PX_PER_M = 1000
PLANT_COLORS = ["#3c8d2f", "#c9d93a", "#2f7fbf", "#d9603a", "#9b4fc9"]  # cycled per Crop


def export(layout: FieldLayout, out_dir: Path) -> Path:
    spec = layout.spec
    size = spec.pixel_size * PX_PER_M
    width, height = spec.cols * size, spec.rows * size

    def svg_y(y: float) -> float:  # SVG y points down, Field y points north
        return height - y * PX_PER_M

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.1f} {height:.1f}">'
    ]
    for p in layout.pixels:
        fill = "#8b6b4a" if p.crop else "#c8b89a"
        parts.append(
            f'<rect x="{p.origin[0] * PX_PER_M:.1f}" y="{svg_y(p.origin[1]) - size:.1f}" '
            f'width="{size:.1f}" height="{size:.1f}" fill="{fill}" stroke="#5a4632">'
            f"<title>r{p.row}c{p.col} {p.crop or 'empty'}</title></rect>"
        )
    crops = sorted({p.crop for p in layout.plants})
    color = {crop: PLANT_COLORS[i % len(PLANT_COLORS)] for i, crop in enumerate(crops)}
    for p in layout.plants:
        parts.append(
            f'<circle cx="{p.x * PX_PER_M:.1f}" cy="{svg_y(p.y):.1f}" r="{8 * p.scale:.1f}" '
            f'fill="{color[p.crop]}"><title>{p.id} {p.variant}</title></circle>'
        )
    parts.append('<text x="6" y="18" font-size="16" fill="#fff">N &#8593;</text>')
    parts.append("</svg>")

    path = Path(out_dir) / "field.svg"
    path.write_text("\n".join(parts) + "\n")
    return path
