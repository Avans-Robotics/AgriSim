"""Pixel farming field generator for robot simulation."""

import os
from pathlib import Path

# The checkout this package runs from. Relative paths to the Asset Library and the Crop
# definitions (in Crop definitions and the Manifest) resolve against it, never against the
# working directory.
# ponytail: needs the package installed from its checkout (`pip install -e`, as robot images do,
# ADR 0009); ship assets/ and crops/ inside the package if a wheel install is ever needed.
ROOT = Path(__file__).resolve().parents[2]

# Asset Generators must give the same bytes on every machine (the committed Asset Library is
# checked against them). OpenBLAS picks its matrix kernels per CPU (AVX512 kernels on newer
# CPUs), which changes the last bits of numpy matrix products and with them convex hulls and
# printed digits, so one kernel is pinned before numpy loads OpenBLAS.
# ponytail: x86-64 only; an ARM machine ignores it and may regenerate a slightly different
# library.
os.environ.setdefault("OPENBLAS_CORETYPE", "Haswell")
