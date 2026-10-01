"""Asset Generators by Crop name. Each takes a Variant count and an output folder.

Needs the `generate` extra (trimesh); import this package only when generating.
"""

from pixelfield.generators import carrot

GENERATORS = {"carrot": carrot.generate}
