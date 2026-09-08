# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/test_var_defaults.txt"

bp = unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker")
BPLIB = unreal.BlueprintEditorLibrary

lines = []
methods = [m for m in dir(BPLIB) if "var" in m.lower()]
lines.append(f"BPLIB var methods: {methods}")

# 看看如何加 float 变量
pin_type = unreal.EdGraphPinType()
pin_type.pin_category = "real"
pin_type.pin_sub_category = "double"
try:
    var_desc = BPLIB.add_new_variable(bp, "CurrentHealth", pin_type)
    lines.append(f"add_new_variable returned: {var_desc}")
except Exception as e:
    lines.append(f"add_new_variable error: {e}")

# 看看 BPLIB 都有哪些设置默认值的方法
for m in dir(BPLIB):
    if any(k in m.lower() for k in ["default", "value", "variable"]):
        lines.append(f"  candidate: {m}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("DONE_VAR_DEFAULTS")
