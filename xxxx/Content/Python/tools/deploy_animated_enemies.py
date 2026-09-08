"""Compatibility entry: apply enemy numeric defaults without recreating actors or graphs.

The previous hardcoded scene rebuild is retired. Visual data, weapons, waves and
live instances are outside this command's scope; see Docs/MULTI_DEVICE_DEVELOPMENT.md.
"""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "apply_data_config.py"), run_name="__main__")
