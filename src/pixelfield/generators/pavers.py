"""Paver floor texture of a Venue: PERIOD x PERIOD grey concrete pavers in one seamless image.

The texture's edges fall on paver joints, so it repeats without seams. Each paver gets its own
brightness and a slight tint; a fine grain and a soft mottling, both periodic over the image,
break up the repetition. The Gazebo Exporter maps it once per PERIOD * PAVER meters.
"""

from pathlib import Path

import numpy as np
from PIL import Image

from pixelfield import ROOT

OUT_DIR = ROOT / "assets" / "library" / "textures" / "pavers"
PAVER = 0.6  # meters per paver side, the Avans greenhouse's 60 x 60 cm concrete pavers
PERIOD = 4  # pavers per texture side
SIZE = 1024  # pixels per texture side, about 2.3 mm per pixel
JOINT = 0.008  # meters of joint between two pavers
BASE = 0.55  # paver brightness
JOINT_COLOR = 0.22
SEED = 1


def generate(out_dir: Path = OUT_DIR) -> Path:
    """Write color.jpg to out_dir."""
    rng = np.random.default_rng(SEED)
    px = SIZE / (PERIOD * PAVER)  # pixels per meter
    coord = (np.arange(SIZE) + 0.5) / px  # meters across the texture
    in_paver = coord % PAVER
    # distance to the nearest joint centre, per axis; joints sit on the texture edges
    edge = np.minimum(in_paver, PAVER - in_paver)
    ex, ey = np.meshgrid(edge, edge)
    to_joint = np.minimum(ex, ey)

    paver = (coord // PAVER).astype(int)
    shade = BASE + rng.normal(0, 0.035, (PERIOD, PERIOD))
    tint = rng.normal(0, 0.004, (PERIOD, PERIOD, 3))
    color = shade[paver[:, None], paver[None, :], None] + tint[paver[:, None], paver[None, :]]

    grain = _periodic_blur(rng.normal(0, 1, (SIZE, SIZE)), 2)
    mottle = _periodic_blur(rng.normal(0, 1, (SIZE, SIZE)), 40)
    color = color + 0.03 * grain[..., None] / grain.std()
    color = color + 0.025 * mottle[..., None] / mottle.std()
    bevel = np.clip(to_joint / 0.006, 0, 1) ** 0.5  # rounded paver edges darken into the joint
    color = color * (0.8 + 0.2 * bevel[..., None])
    color = np.where((to_joint < JOINT / 2)[..., None], JOINT_COLOR, color)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "color.jpg"
    pixels = np.clip(np.round(color * 255), 0, 255).astype(np.uint8)
    Image.fromarray(pixels).save(path, quality=88)
    return path


def _periodic_blur(image: np.ndarray, radius: int) -> np.ndarray:
    """Box blur that wraps around the edges, so periodic noise stays periodic."""
    for axis in (0, 1):
        cumulative = np.zeros_like(image)
        for shift in range(-radius, radius + 1):
            cumulative += np.roll(image, shift, axis=axis)
        image = cumulative / (2 * radius + 1)
    return image


if __name__ == "__main__":
    print(f"paver texture written to {generate()}, {PERIOD * PAVER:g} m per repeat")
