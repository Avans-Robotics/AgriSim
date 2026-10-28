"""Soil tiles: two CC0 soils blended into a seamless atlas of PERIOD x PERIOD tiles of 1 m.

The Gazebo Exporter lays the soil as 1 m tiles; tile (i, j) uses atlas tile (i % PERIOD,
j % PERIOD). Each atlas tile mixes the moist base soil with dry patches of a second soil by
a smooth mask, and darkens it slightly by a second mask. Both masks are sums of sines with
whole periods over the atlas, so neighbouring tiles join without seams and the pattern only
repeats every PERIOD meters. The two sources are seamless 1 m tiles themselves. Normals stay
the base soil's, shared by all tiles.
"""

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image

from pixelfield import ROOT

TEXTURES = ROOT / "assets" / "library" / "textures"
PERIOD = 4  # atlas tiles per side; the soil pattern repeats every PERIOD meters
DRY_COVER = 0.35  # fraction of the soil in dry patches
DRY_MIX = 0.45  # share of the dry soil inside a patch; mild, so the base soil still shows
DAMP = (0.88, 1.04)  # brightness range of the moisture mask
SEED = 1


def generate(out_dir: Path = TEXTURES / "soil_tiles") -> list[Path]:
    """Write tile_<i>_<j>_color.jpg and _roughness.jpg for every atlas tile to out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("tile_*.jpg"):
        old.unlink()
    base, dry = (_load(TEXTURES / name) for name in ("soil", "soil_dry"))
    rng = random.Random(SEED)
    dry_noise, damp_noise = _noise(rng, 4), _noise(rng, 3)
    # thresholds from a coarse sample of the whole atlas, so every tile uses the same ones
    coarse = np.linspace(0, PERIOD, 256, endpoint=False)
    cx, cy = np.meshgrid(coarse, coarse)
    dry_mean, dry_std = dry_noise(cx, cy).mean(), dry_noise(cx, cy).std()
    middle = np.quantile((dry_noise(cx, cy) - dry_mean) / dry_std, 1 - DRY_COVER)
    damp_range = (damp_noise(cx, cy).min(), damp_noise(cx, cy).max())
    size = base["color"].shape[0]
    # gz box top face: image rows run from east (+x) to west, columns from north (+y) to south
    rows, cols = np.mgrid[0:size, 0:size]
    local_x, local_y = 1 - (rows + 0.5) / size, 1 - (cols + 0.5) / size
    grain = dry["color"].mean(axis=2) - dry["color"].mean()  # ragged patch edges
    paths = []
    for i in range(PERIOD):
        for j in range(PERIOD):
            x, y = i + local_x, j + local_y
            dryness = (dry_noise(x, y) - dry_mean) / dry_std + 1.5 * grain
            mask = DRY_MIX * _smoothstep(middle - 0.4, middle + 0.4, dryness)  # soft, ragged
            low, high = damp_range
            damp = DAMP[0] + (damp_noise(x, y) - low) / (high - low) * (DAMP[1] - DAMP[0])
            color = base["color"] * (1 - mask[..., None]) + dry["color"] * mask[..., None]
            roughness = base["roughness"] * (1 - mask) + dry["roughness"] * mask
            for name, image in (("color", color * damp[..., None]), ("roughness", roughness)):
                path = out_dir / f"tile_{i}_{j}_{name}.jpg"
                pixels = np.clip(np.round(image * 255), 0, 255).astype(np.uint8)
                Image.fromarray(pixels).save(path, quality=88)
                paths.append(path)
    return paths


def _load(folder: Path) -> dict[str, np.ndarray]:
    return {
        "color": np.asarray(Image.open(folder / "color.jpg").convert("RGB")) / 255,
        "roughness": np.asarray(Image.open(folder / "roughness.jpg").convert("L")) / 255,
    }


def _noise(rng: random.Random, count: int):
    """Smooth noise from `count` sines per frequency band, periodic over the atlas."""
    waves = []
    for cycles, weight in ((1, 1.0), (2, 0.7), (3, 0.5), (5, 0.3), (8, 0.15)):
        for _ in range(count):
            angle = rng.uniform(0, 2 * math.pi)
            # whole cycles per atlas along x and y keep every wave periodic over PERIOD
            kx, ky = round(cycles * math.cos(angle)), round(cycles * math.sin(angle))
            if kx or ky:
                waves.append((kx, ky, rng.uniform(0, 2 * math.pi), weight))

    def noise(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        total = np.zeros_like(x, dtype=float)
        for kx, ky, phase, weight in waves:
            total += weight * np.sin(2 * math.pi * (kx * x + ky * y) / PERIOD + phase)
        return total

    return noise


def _smoothstep(low: float, high: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - low) / (high - low), 0.0, 1.0)
    return t * t * (3 - 2 * t)


if __name__ == "__main__":
    print(f"{len(generate())} soil tile textures written to {TEXTURES / 'soil_tiles'}")
