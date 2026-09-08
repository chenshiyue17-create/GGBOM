# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/hud_components.txt"

bp_path = "/Game/GGBOM/Blueprints/BP_GGBOM_MasterHUD"
bp = unreal.EditorAssetLibrary.load_asset(bp_path)
handles = unreal.SubobjectDataBlueprintFunctionLibrary.k2_gather_subobject_data_for_blueprint(bp)

lines = []
for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    cls_name = obj.get_class().get_name() if obj else "None"
    lines.append(f"Handle: {vname} | Class: {cls_name}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("INSPECT_HUD_COMPONENTS_DONE")
