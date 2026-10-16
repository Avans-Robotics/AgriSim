"""Asset Generators by Crop name. Each takes a Variant count and an output folder.

Needs the `generate` extra (trimesh); import this package only when generating.
"""

from functools import partial

from pixelfield.generators import root_crop

GENERATORS = {crop: partial(root_crop.generate, crop) for crop in root_crop.CROPS}
