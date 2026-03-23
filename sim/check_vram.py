"""
check_vram.py - Report GPU VRAM usage after Isaac Sim context is loaded.
Usage: /path/to/python.sh sim/check_vram.py

Output is written to /tmp/vram_report.txt so it isn't lost in Isaac Sim's
log stream, and also printed via carb.log_warn so it appears in the kit log.
"""

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import subprocess
import sys
import carb

def query_vram():
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    rows = []
    for line in result.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        name = parts[0]
        total_mb = int(parts[1])
        used_mb = int(parts[2])
        free_mb = int(parts[3])
        rows.append((name, total_mb, used_mb, free_mb))
    return rows

def main():
    lines = ["\n=== VRAM Report (after SimulationApp init) ==="]
    for name, total, used, free in query_vram():
        pct_used = used / total * 100
        pct_free = free / total * 100
        lines.append(f"  GPU   : {name}")
        lines.append(f"  Total : {total:,} MB ({total / 1024:.2f} GB)")
        lines.append(f"  Used  : {used:,} MB ({pct_used:.1f}%)")
        lines.append(f"  Free  : {free:,} MB ({pct_free:.1f}%)")
        lines.append("")
    lines.append("==============================================\n")

    report = "\n".join(lines)

    # Write to file (not swallowed by kit log capture)
    out_path = "/tmp/vram_report.txt"
    with open(out_path, "w") as f:
        f.write(report)

    # Also surface through carb so it appears in the kit log
    carb.log_warn(report)

    sys.stderr.write(report + "\n")
    sys.stderr.flush()

main()
simulation_app.close()
