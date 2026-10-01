"""Exporters by name. Each takes a Field Layout and an output folder."""

from pixelfield.exporters import gazebo, svg

EXPORTERS = {"gazebo": gazebo.export, "svg": svg.export}
