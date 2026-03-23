# Agri-Factory Project: Isaac Sim 2026

## Environment
- **Simulator Path:** /home/alex/git_repos/isaacsim/_build/linux-x86_64/release
- **Python Executable:** /home/alex/git_repos/isaacsim/_build/linux-x86_64/release/python.sh
- **Hardware:** NVIDIA RTX PRO 1000 Blackwell (8GB VRAM)

## Commands
- **Run Sim:** `[Python Executable] [script_path]`
- **Test:** `[Python Executable] -m pytest tests/`

## Coding Rules
- **VRAM Constraint:** Always use "Instancing" for large crop fields to save memory.
- **Headless Mode:** For testing logic without the GUI, add `--headless` flag.
- **Async:** Use the Isaac Sim Action Graph or Python Snippets for real-time control.

## Project Structure
- `sim/`: Logic for the agriculture environment.
- `assets/`: Custom 3D USD files.
