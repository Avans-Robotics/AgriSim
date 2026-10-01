"""Plant colors per Crop, shared so every Exporter's view of a Field matches."""

from pixelfield.core.layout import FieldLayout

PLANT_COLORS = ["#3c8d2f", "#c9d93a", "#2f7fbf", "#d9603a", "#9b4fc9"]  # cycled per Crop


def crop_colors(layout: FieldLayout) -> dict[str, str]:
    """Hex color per planted Crop, assigned in alphabetical order."""
    crops = sorted({p.crop for p in layout.plants})
    return {crop: PLANT_COLORS[i % len(PLANT_COLORS)] for i, crop in enumerate(crops)}
