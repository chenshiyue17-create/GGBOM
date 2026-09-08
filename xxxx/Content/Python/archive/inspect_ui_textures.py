import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
UI_DIR = ROOT / "Content" / "美术" / "Art" / "07_UI"

for p in sorted(UI_DIR.rglob("*.png")):
    rel = p.relative_to(UI_DIR)
    # Check image size using python
    try:
        from PIL import Image
        with Image.open(p) as img:
            unreal.log(f"[UI-Art] {rel}: {img.size} mode={img.mode}")
    except Exception as e:
        unreal.log(f"[UI-Art] {rel}: {e}")
