# -*- coding: utf-8 -*-
"""
test_set_root.py
测试将 BoxComponent 设为 RootComponent
"""
import unreal

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
bp = ASSETS.load_asset(bp_path)

handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
box_handle = None
render_handle = None

for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)).lower()
    if "enemycollision" in vname or ("box" in vname and "render" not in vname):
        box_handle = h
    elif "render" in vname:
        render_handle = h

print(f"box_handle: {box_handle}, render_handle: {render_handle}")

if box_handle:
    try:
        ok = subsys.set_root_subobject_data(bp, box_handle)
        print(f"subsys.set_root_subobject_data result: {ok}")
    except Exception as e:
        print(f"set_root failed: {e}")

BPLIB.compile_blueprint(bp)
ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
