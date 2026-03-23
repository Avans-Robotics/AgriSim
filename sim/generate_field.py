"""
generate_field.py
=================
Creates a 20 × 20 m corn field in Isaac Sim 2026.

Scene hierarchy
---------------
  /World/
    SunLight              – distant light          (Replicator API)
    DomeLight             – sky ambient             (Replicator API)
    SoilPlane             – 20×20 m quad mesh       (Replicator API)
    CornField/            – UsdGeom.PointInstancer  ← single GPU upload
      Prototypes/
        CornStalk/        – 1 prototype, shared by all 50 instances
          Stalk           – UsdGeom.Cylinder  (green)
          Tassel          – UsdGeom.Cone      (yellow-gold)

VRAM budget
-----------
  Prototype geometry  ≈ 2 simple prims  → negligible
  50 instances        → position / orient / scale arrays ≈ 50 × (3+4+3) floats
  Total instancer overhead  << 1 MB  (well under the 1 GB target)

Run
---
  /path/to/python.sh sim/generate_field.py
  Output: assets/field_20x20.usd
"""

import argparse
import time
from isaacsim import SimulationApp

parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true", default=True,
                    help="Run without GUI (default: True; use --no-headless to open GUI)")
parser.add_argument("--no-headless", dest="headless", action="store_false",
                    help="Open the Isaac Sim GUI window")
args, _ = parser.parse_known_args()

# Use RayTracedLighting instead of PathTracing to reduce VRAM pressure on
# laptops. PathTracing can spike VRAM well beyond the 8 GB budget at startup.
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

# ── Field configuration ───────────────────────────────────────────────────────
FIELD_SIZE   = 20.0     # metres (square)
ROWS         = 5
COLS         = 10       # plants per row
ROW_SPACING  = FIELD_SIZE / ROWS    # 4 m between rows
COL_SPACING  = FIELD_SIZE / COLS    # 2 m between plants

STALK_HEIGHT = 2.5      # metres
STALK_RADIUS = 0.05     # metres
JITTER_M     = 0.15     # max positional jitter per plant (metres)
SCALE_VAR    = 0.10     # ±10 % height variation per plant

SEED = 42

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_USD = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "assets", "field_20x20.usd"))

# ── Stage setup ───────────────────────────────────────────────────────────────
stage = omni.usd.get_context().get_stage()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
stage.DefinePrim("/World", "Xform")

# ── 1. Lighting  (Replicator API) ─────────────────────────────────────────────
rep.create.light(
    light_type="distant",
    rotation=(315, 0, 0),       # 45° sun elevation from south
    intensity=5000,
    color=(1.0, 0.98, 0.92),
)
rep.create.light(
    light_type="Dome",
    intensity=500,
    color=(0.6, 0.8, 1.0),      # sky-blue ambient fill
)

# ── 2. Soil material  (Replicator API) ────────────────────────────────────────
soil_mat = rep.create.material_omnipbr(
    diffuse=(0.36, 0.25, 0.15),
    roughness=1.0,
    metallic=0.0,
)

# ── 3. Soil plane  (Replicator API) ───────────────────────────────────────────
# rep.create.plane produces a unit (1×1 m) plane; scale to 20×20 m.
rep.create.plane(
    scale=(FIELD_SIZE, FIELD_SIZE, 1),
    position=(0.0, 0.0, 0.0),
    material=soil_mat,
    semantics=[("class", "soil")],
)

# ── 4. Corn stalk prototype  (USD API — Replicator has no instancer primitive) ─
INSTANCER_PATH = "/World/CornField"
PROTO_PATH     = INSTANCER_PATH + "/Prototypes/CornStalk"

UsdGeom.Xform.Define(stage, PROTO_PATH)

# 4a. Stalk: green cylinder along Z, translated up by half its height
stalk = UsdGeom.Cylinder.Define(stage, PROTO_PATH + "/Stalk")
stalk.CreateHeightAttr(STALK_HEIGHT)
stalk.CreateRadiusAttr(STALK_RADIUS)
stalk.CreateAxisAttr(UsdGeom.Tokens.z)
stalk.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, STALK_HEIGHT / 2.0))
stalk.CreateDisplayColorAttr([Gf.Vec3f(0.18, 0.55, 0.14)])

# 4b. Tassel: golden cone sitting on top of the stalk
tassel = UsdGeom.Cone.Define(stage, PROTO_PATH + "/Tassel")
tassel.CreateHeightAttr(0.6)
tassel.CreateRadiusAttr(0.18)
tassel.CreateAxisAttr(UsdGeom.Tokens.z)
tassel.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, STALK_HEIGHT + 0.3))
tassel.CreateDisplayColorAttr([Gf.Vec3f(0.88, 0.78, 0.30)])

# ── 5. PointInstancer: 5 rows × 10 cols = 50 instances ───────────────────────
# The prototype geometry is uploaded to VRAM exactly once.
# Each of the 50 instances is represented by a position/orientation/scale
# tuple — a few hundred bytes total — so VRAM stays well under 1 GB.
instancer = UsdGeom.PointInstancer.Define(stage, INSTANCER_PATH)
instancer.CreatePrototypesRel().SetTargets([Sdf.Path(PROTO_PATH)])

rng = np.random.default_rng(SEED)
hw  = FIELD_SIZE / 2.0

positions    = []
orientations = []
scales       = []

for row in range(ROWS):
    # Row centres at Y = -8, -4, 0, +4, +8 m
    y = -hw + ROW_SPACING / 2.0 + row * ROW_SPACING
    for col in range(COLS):
        # Plant centres at X = -9, -7, …, +9 m
        x = -hw + COL_SPACING / 2.0 + col * COL_SPACING

        # Small natural jitter so rows don't look machine-perfect
        jx, jy = rng.uniform(-JITTER_M, JITTER_M, size=2)
        positions.append(Gf.Vec3f(float(x + jx), float(y + jy), 0.0))

        # Random yaw rotation around Z so plants face different directions.
        # USD PointInstancer stores orientations as half-precision quaternions
        # (Gf.Quath).  For a Z-axis rotation by angle θ:
        #   q = (cos θ/2,  0,  0,  sin θ/2)
        yaw_half = float(rng.uniform(0.0, np.pi))
        orientations.append(
            Gf.Quath(
                float(np.cos(yaw_half)),
                Gf.Vec3h(0.0, 0.0, float(np.sin(yaw_half))),
            )
        )

        # Per-plant height variation (uniform scale keeps aspect ratio)
        s = float(rng.uniform(1.0 - SCALE_VAR, 1.0 + SCALE_VAR))
        scales.append(Gf.Vec3f(s, s, s))

instancer.CreatePositionsAttr().Set(positions)
instancer.CreateOrientationsAttr().Set(orientations)
instancer.CreateScalesAttr().Set(scales)
instancer.CreateProtoIndicesAttr().Set([0] * len(positions))

# ── 6. Export USD ─────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_USD), exist_ok=True)
stage.GetRootLayer().Export(OUTPUT_USD)

n = len(positions)
carb.log_warn(f"[generate_field] Saved     → {OUTPUT_USD}")
carb.log_warn(f"[generate_field] Field     → {FIELD_SIZE}×{FIELD_SIZE} m soil plane")
carb.log_warn(f"[generate_field] Instances → {n}  ({ROWS} rows × {COLS} plants/row)")
carb.log_warn(f"[generate_field] Prototype → 1 mesh  (Stalk + Tassel)")
carb.log_warn(f"[generate_field] VRAM      → 1× prototype geometry + tiny transform arrays  ≪ 1 GB")

# In GUI mode keep rendering until the window is closed.
# In headless mode exit immediately after export.
if args.headless:
    simulation_app.close()
else:
    print("[generate_field] GUI open — close the Isaac Sim window to exit.")
    _target_dt = 1.0 / 60.0     # cap at 60 fps to avoid pegging CPU/GPU
    while simulation_app.is_running():
        _t0 = time.monotonic()
        simulation_app.update()
        _elapsed = time.monotonic() - _t0
        if _elapsed < _target_dt:
            time.sleep(_target_dt - _elapsed)
    simulation_app.close()
