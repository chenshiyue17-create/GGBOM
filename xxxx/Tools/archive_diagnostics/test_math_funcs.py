# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

OUT = Path(unreal.Paths.project_dir()).resolve() / "output/math_funcs.txt"
lines = []

kml = unreal.KismetMathLibrary
for name in ["sign_op_double", "sign_op_float", "sign", "select_vector", "select_float"]:
    lines.append(f"{name}: {hasattr(kml, name)}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("Saved math funcs test")
