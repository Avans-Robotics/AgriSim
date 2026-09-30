"""Exporters by name. Each takes a Field Layout and an output folder."""

from pixelfield.exporters import svg

EXPORTERS = {"svg": svg.export}
