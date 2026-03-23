#!/usr/bin/env bash
# run_sim.sh — easy launcher for the agri-sim FarmManager
#
# Usage:
#   ./run_sim.sh [options]
#
# Layout modes:
#   --mode row              Traditional row crops (default)
#   --mode pixel            Intensive pixel-cropping grid
#
# Row-mode options:
#   --rows N                Number of rows            (default: 5)
#   --cols N                Plants per row             (default: 10)
#   --jitter M              Position jitter, metres    (default: 0.15)
#   --scale-var F           Scale variation ±fraction  (default: 0.10)
#
# Pixel-mode options:
#   --spacing M             Grid spacing, metres       (default: 0.30)
#
# Plant selection:
#   --plants a,b,c          Comma-separated subset of: broccoli, carrot, lettuce
#                           (default: all three)
#
# Field / display:
#   --field-size M          Square field side, metres  (default: 20)
#   --no-headless           Open the Isaac Sim GUI window
#   --seed N                Random seed                (default: 42)
#
# Validation:
#   --test                  Run 100 frames headless and exit
#
# Examples:
#   ./run_sim.sh                                        # row, all plants, headless
#   ./run_sim.sh --mode pixel --spacing 0.25            # dense pixel grid
#   ./run_sim.sh --mode row --rows 8 --cols 20          # bigger row field
#   ./run_sim.sh --plants broccoli,lettuce --no-headless  # GUI, two plant types
#   ./run_sim.sh --mode pixel --plants carrot --field-size 30 --spacing 0.20
#   ./run_sim.sh --test                                 # 100-frame validation

PYTHON="/home/alex/git_repos/isaacsim/_build/linux-x86_64/release/python.sh"
SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/sim/farm_manager.py"

exec "$PYTHON" "$SCRIPT" "$@"
