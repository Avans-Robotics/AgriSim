"""Pixel farming field generator for robot simulation."""

import os

# Asset Generators must give the same bytes on every machine (the committed Asset Library is
# checked against them). numpy's AVX512 kernels (SVML sin, cos, power, ...) differ from libm by
# a few ULP, which flips convex hulls and printed digits, so they are off before numpy loads.
os.environ.setdefault("NPY_DISABLE_CPU_FEATURES", "X86_V4 AVX512_ICL AVX512_SPR")
