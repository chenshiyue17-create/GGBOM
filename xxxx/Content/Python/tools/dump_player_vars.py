# -*- coding: utf-8 -*-
import unreal

bp = unreal.load_asset("/Game/Blueprints/Player/BP_Player_Medic")
out = []
if bp:
    # 列出所有变量
    vars = unreal.BlueprintEditorLibrary.find_variables(bp)
    out.append(f"Variables count: {len(vars)}")
    for v in vars:
        v_name = v.get_name()
        out.append(f"Var: {v_name}")

with open("/Users/cc/Desktop/GGBOM/player_vars.txt", "w") as f:
    f.write("\n".join(out))
print("DONE_PLAYER_VARS")
