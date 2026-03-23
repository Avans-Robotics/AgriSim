"""
farm_manager.py
===============
Modular FarmManager class for creating crop fields in Isaac Sim 2026.

Supports two layout modes:
  - "row"   : Traditional row-based crop planting with configurable spacing.
  - "pixel" : Pixel-cropping / intensive grid layout for intercropped fields.

Uses UsdGeom.PointInstancer (GPU instancing) for all vegetation to keep VRAM
well under 1 GB even with thousands of plants on an 8 GB RTX PRO 1000.

Quick start (or use ./run_sim.sh)
----------------------------------
  Row crops (5 rows × 10 cols, all three plants):
    python.sh sim/farm_manager.py --mode row

  Row crops, custom layout:
    python.sh sim/farm_manager.py --mode row --rows 8 --cols 15 --plants broccoli,lettuce

  Pixel-cropping (30 cm grid):
    python.sh sim/farm_manager.py --mode pixel --spacing 0.30

  Dense pixel-cropping, carrots only, 30 m field:
    python.sh sim/farm_manager.py --mode pixel --spacing 0.20 --plants carrot --field-size 30

  Headless 100-frame validation:
    python.sh sim/farm_manager.py --test
"""

import argparse
import sys
import time

# ── Argument parsing must happen before SimulationApp import ────────────────
parser = argparse.ArgumentParser(description="FarmManager — row and pixel-cropping field generator")
parser.add_argument("--mode", choices=["row", "pixel"], default="row",
                    help="Layout mode: 'row' (traditional) or 'pixel' (intensive grid)")
parser.add_argument("--headless", action="store_true", default=True,
                    help="Run without GUI (default: True)")
parser.add_argument("--no-headless", dest="headless", action="store_false",
                    help="Open the Isaac Sim GUI window")
parser.add_argument("--test", action="store_true",
                    help="Run 100 frames headless then exit (validation mode)")
parser.add_argument("--field-size", type=float, default=20.0,
                    help="Square field side length in metres (default: 20)")
parser.add_argument("--seed", type=int, default=42,
                    help="Random seed for layout jitter")

# ── Row-mode parameters ──────────────────────────────────────────────────────
parser.add_argument("--rows", type=int, default=5,
                    help="Number of crop rows (row mode, default: 5)")
parser.add_argument("--cols", type=int, default=10,
                    help="Plants per row (row mode, default: 10)")
parser.add_argument("--jitter", type=float, default=0.15,
                    help="Position jitter radius in metres (row mode, default: 0.15)")
parser.add_argument("--scale-var", type=float, default=0.10,
                    help="Scale variation ±fraction, e.g. 0.10 = ±10%% (default: 0.10)")

# ── Pixel-mode parameters ────────────────────────────────────────────────────
parser.add_argument("--spacing", type=float, default=0.30,
                    help="Grid spacing in metres (pixel mode, default: 0.30)")

# ── Plant selection ──────────────────────────────────────────────────────────
parser.add_argument("--plants", type=str, default="broccoli,carrot,lettuce",
                    help="Comma-separated plant types to include "
                         "(any of: broccoli, carrot, lettuce). Default: all three.")

args, _ = parser.parse_known_args()

# --test implies headless
if args.test:
    args.headless = True

from isaacsim import SimulationApp

simulation_app = SimulationApp({
    "headless": args.headless,
    "renderer": "RayTracedLighting",
})

import os
import numpy as np
import carb
import omni.usd
import omni.replicator.core as rep
from pxr import Gf, Sdf, UsdGeom


# ── Default plant assets (placeholders until Botanist provides real paths) ──
DEFAULT_PLANT_ASSETS = {
    "broccoli": "/home/alex/git_repos/SustainableAgriculture/agri-sim/assets/plants/broccoli.usda",
    "carrot":   "/home/alex/git_repos/SustainableAgriculture/agri-sim/assets/plants/carrot.usda",
    "lettuce":  "/home/alex/git_repos/SustainableAgriculture/agri-sim/assets/plants/lettuce.usda",
}


class FarmManager:
    """Manages crop field generation and simulation using GPU-instanced vegetation.

    Parameters
    ----------
    mode : str
        Layout mode — "row" or "pixel".
    field_size : float
        Side length of the square field in metres.
    plant_assets : dict
        Mapping of plant name to USD asset path (None → procedural fallback).
    seed : int
        Random seed for reproducible jitter.
    rows : int
        Number of crop rows (row mode).
    cols : int
        Plants per row (row mode).
    jitter : float
        Position jitter radius in metres (row mode).
    scale_var : float
        Scale variation ±fraction (row mode and pixel mode).
    spacing : float
        Grid spacing in metres (pixel mode).
    """

    # ── Prototype fallback geometry (used when no USD asset is supplied) ──────
    STALK_HEIGHT = 0.40
    STALK_RADIUS = 0.04

    def __init__(self, mode="row", field_size=20.0, plant_assets=None, seed=42,
                 rows=5, cols=10, jitter=0.15, scale_var=0.10, spacing=0.30):
        self.mode = mode
        self.field_size = field_size
        self.plant_assets = plant_assets or DEFAULT_PLANT_ASSETS
        self.seed = seed
        self.rng = np.random.default_rng(seed)

        # Layout parameters (instance-level so they can be set per-run)
        self.row_rows = rows
        self.row_cols = cols
        self.row_jitter = jitter
        self.row_scale_var = scale_var
        self.pixel_spacing = spacing

        self.stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(self.stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(self.stage, 1.0)
        self.stage.DefinePrim("/World", "Xform")

        self._positions = []
        self._orientations = []
        self._scales = []
        self._proto_indices = []
        self._proto_paths = []
        self._instancer = None
        self._running = False

    # ── Public API ───────────────────────────────────────────────────────────

    def generate_layout(self):
        """Compute plant positions, orientations, and scales for the chosen mode."""
        self._positions.clear()
        self._orientations.clear()
        self._scales.clear()
        self._proto_indices.clear()

        if self.mode == "row":
            self._generate_row_layout()
        else:
            self._generate_pixel_layout()

        carb.log_warn(
            f"[FarmManager] Layout '{self.mode}' generated — "
            f"{len(self._positions)} plant instances"
        )

    def instantiate_plants(self):
        """Build USD scene: lighting, soil plane, prototypes, and PointInstancer."""
        self._create_environment()
        self._create_prototypes()
        self._create_instancer()

        carb.log_warn(
            f"[FarmManager] Instancer created at /World/Farm — "
            f"{len(self._positions)} instances, "
            f"{len(self._proto_paths)} prototype(s)"
        )

    def run_update_loop(self, max_frames=0):
        """Run the simulation loop.

        Parameters
        ----------
        max_frames : int
            If > 0, exit after this many frames (used by --test).
            If 0, run until the window is closed (GUI mode).
        """
        self._running = True
        frame = 0
        target_dt = 1.0 / 60.0

        carb.log_warn(
            f"[FarmManager] Starting update loop "
            f"({'infinite' if max_frames == 0 else f'{max_frames} frames'})"
        )

        try:
            while self._running and simulation_app.is_running():
                t0 = time.monotonic()
                simulation_app.update()
                frame += 1

                if 0 < max_frames <= frame:
                    carb.log_warn(f"[FarmManager] Reached {frame} frames — exiting.")
                    break

                elapsed = time.monotonic() - t0
                if elapsed < target_dt:
                    time.sleep(target_dt - elapsed)
        except KeyboardInterrupt:
            carb.log_warn("[FarmManager] Interrupted by user.")
        finally:
            self.shutdown()

    def shutdown(self):
        """Gracefully close the simulation."""
        self._running = False
        carb.log_warn("[FarmManager] Shutting down.")
        simulation_app.close()

    # ── Layout generators ────────────────────────────────────────────────────

    def _generate_row_layout(self):
        """Traditional row crop layout — evenly spaced rows with position jitter."""
        hw = self.field_size / 2.0
        row_spacing = self.field_size / self.row_rows
        col_spacing = self.field_size / self.row_cols
        plant_names = list(self.plant_assets.keys())

        for row in range(self.row_rows):
            y = -hw + row_spacing / 2.0 + row * row_spacing
            # Each row uses a single plant type, cycling through selected plants
            proto_idx = row % len(plant_names)

            for col in range(self.row_cols):
                x = -hw + col_spacing / 2.0 + col * col_spacing
                jx, jy = self.rng.uniform(-self.row_jitter, self.row_jitter, size=2)
                self._positions.append(Gf.Vec3f(float(x + jx), float(y + jy), 0.0))
                self._orientations.append(self._random_yaw())
                s = float(self.rng.uniform(1.0 - self.row_scale_var,
                                           1.0 + self.row_scale_var))
                self._scales.append(Gf.Vec3f(s, s, s))
                self._proto_indices.append(proto_idx)

    def _generate_pixel_layout(self):
        """Pixel-cropping / intensive grid — plants on a uniform tight grid."""
        hw = self.field_size / 2.0
        spacing = self.pixel_spacing
        plant_names = list(self.plant_assets.keys())
        num_types = len(plant_names)

        n = int(self.field_size / spacing)
        for row in range(n):
            y = -hw + spacing / 2.0 + row * spacing
            for col in range(n):
                x = -hw + spacing / 2.0 + col * spacing
                self._positions.append(Gf.Vec3f(float(x), float(y), 0.0))
                self._orientations.append(self._random_yaw())
                s = float(self.rng.uniform(1.0 - self.row_scale_var,
                                           1.0 + self.row_scale_var))
                self._scales.append(Gf.Vec3f(s, s, s))
                # Checkerboard-style intercropping cycles through plant types
                self._proto_indices.append((row + col) % num_types)

    # ── Scene construction ───────────────────────────────────────────────────

    def _create_environment(self):
        """Set up lighting and soil plane via Replicator API."""
        rep.create.light(
            light_type="distant",
            rotation=(315, 0, 0),
            intensity=5000,
            color=(1.0, 0.98, 0.92),
        )
        rep.create.light(
            light_type="Dome",
            intensity=500,
            color=(0.6, 0.8, 1.0),
        )
        soil_mat = rep.create.material_omnipbr(
            diffuse=(0.36, 0.25, 0.15),
            roughness=1.0,
            metallic=0.0,
        )
        rep.create.plane(
            scale=(self.field_size, self.field_size, 1),
            position=(0.0, 0.0, 0.0),
            material=soil_mat,
            semantics=[("class", "soil")],
        )

    def _create_prototypes(self):
        """Build one USD prototype per plant type under /World/Farm/Prototypes.

        If a USD asset path is provided for a plant, it is loaded via a USD
        reference. Otherwise, a simple coloured cylinder is used as a fallback.
        """
        base = "/World/Farm/Prototypes"
        self.stage.DefinePrim(base, "Xform")

        fallback_colours = [
            Gf.Vec3f(0.18, 0.55, 0.14),   # green  (broccoli)
            Gf.Vec3f(0.90, 0.45, 0.10),   # orange (carrot)
            Gf.Vec3f(0.30, 0.75, 0.25),   # light green (lettuce)
        ]

        for i, name in enumerate(self.plant_assets):
            proto_path = f"{base}/{name}"
            asset_path = self.plant_assets[name]

            if asset_path is not None and os.path.isfile(asset_path):
                prim = self.stage.DefinePrim(proto_path, "Xform")
                prim.GetReferences().AddReference(asset_path)
            else:
                UsdGeom.Xform.Define(self.stage, proto_path)
                stalk = UsdGeom.Cylinder.Define(self.stage, f"{proto_path}/Stalk")
                stalk.CreateHeightAttr(self.STALK_HEIGHT)
                stalk.CreateRadiusAttr(self.STALK_RADIUS)
                stalk.CreateAxisAttr(UsdGeom.Tokens.z)
                stalk.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, self.STALK_HEIGHT / 2.0))
                colour = fallback_colours[i % len(fallback_colours)]
                stalk.CreateDisplayColorAttr([colour])

            self._proto_paths.append(Sdf.Path(proto_path))

    def _create_instancer(self):
        """Create a UsdGeom.PointInstancer with all computed transforms.

        This is the key VRAM optimisation: prototype geometry is uploaded to
        the GPU exactly once, and each instance is just a lightweight
        position/orientation/scale tuple.
        """
        instancer_path = "/World/Farm"
        self._instancer = UsdGeom.PointInstancer.Define(self.stage, instancer_path)
        self._instancer.CreatePrototypesRel().SetTargets(self._proto_paths)
        self._instancer.CreatePositionsAttr().Set(self._positions)
        self._instancer.CreateOrientationsAttr().Set(self._orientations)
        self._instancer.CreateScalesAttr().Set(self._scales)
        self._instancer.CreateProtoIndicesAttr().Set(self._proto_indices)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _random_yaw(self):
        """Return a random Z-axis rotation as a half-precision quaternion."""
        yaw_half = float(self.rng.uniform(0.0, np.pi))
        return Gf.Quath(
            float(np.cos(yaw_half)),
            Gf.Vec3h(0.0, 0.0, float(np.sin(yaw_half))),
        )


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    # Build plant_assets filtered by --plants selection
    selected = [p.strip().lower() for p in args.plants.split(",")]
    plant_assets = {k: v for k, v in DEFAULT_PLANT_ASSETS.items() if k in selected}
    if not plant_assets:
        carb.log_error(f"[FarmManager] No valid plants in --plants '{args.plants}'. "
                       f"Choose from: {', '.join(DEFAULT_PLANT_ASSETS)}")
        simulation_app.close()
        return

    farm = FarmManager(
        mode=args.mode,
        field_size=args.field_size,
        plant_assets=plant_assets,
        seed=args.seed,
        rows=args.rows,
        cols=args.cols,
        jitter=args.jitter,
        scale_var=args.scale_var,
        spacing=args.spacing,
    )
    farm.generate_layout()
    farm.instantiate_plants()

    if args.test:
        farm.run_update_loop(max_frames=100)
    elif args.headless:
        carb.log_warn("[FarmManager] Headless mode — no update loop. Exiting.")
        farm.shutdown()
    else:
        farm.run_update_loop()


if __name__ == "__main__":
    main()
