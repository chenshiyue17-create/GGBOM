"""Compatibility entry for numeric enemy-default import; never resets camera, art or graphs."""
from pathlib import Path
import runpy


def hot_reload_all():
    runpy.run_path(str(Path(__file__).resolve().parent / "apply_data_config.py"), run_name="__main__")


if __name__ == "__main__":
    hot_reload_all()
