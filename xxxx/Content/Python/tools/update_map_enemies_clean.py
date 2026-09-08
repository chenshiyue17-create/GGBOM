# -*- coding: utf-8 -*-
"""
更新关卡中的怪物为动态 Flipbook 敌人蓝图 (安全 load_level 方式)
"""
from __future__ import annotations
import unreal

GEN = "/Game/GGBOM"
MAP_PATH = f"{GEN}/Maps/MAP_GGBOM_Main"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def ensure(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def build_enemy_bp(name: str, fb_path: str, speed: float, scale: float):
    folder = f"{GEN}/Blueprints/Enemies"
    ensure(folder)
    path = f"{folder}/{name}"
    if ASSETS.does_asset_exist(path):
        bp = unreal.load_asset(path)
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(path, unreal.Actor.static_class())
        
    fb = unreal.load_asset(fb_path)
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if "Flipbook" in vname or isinstance(obj, unreal.PaperFlipbookComponent):
            if fb:
                obj.set_editor_property("source_flipbook", fb)
            obj.set_editor_property("relative_scale3d", unreal.Vector(scale, scale, scale))
            obj.set_editor_property("translucency_sort_priority", 300)
            obj.set_editor_property("visible", True)
            obj.set_editor_property("hidden_in_game", False)
            
    # 事件图
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick = ed.find_event_node("ReceiveTick")
    move_fn = ed.add_call_function_node("/Script/Engine.Actor.K2_AddActorWorldOffset")
    move_fn.set_node_pos(unreal.IntPoint(300, 0))
    
    pin_then = [p for p in BPLIB.list_output_pins(tick) if str(PINLIB.get_pin_name(p)).lower() == "then"][0]
    pin_exec = [p for p in BPLIB.list_input_pins(move_fn) if str(PINLIB.get_pin_name(p)).lower() == "execute"][0]
    PINLIB.try_create_connection(pin_then, pin_exec)
    
    pin_delta = [p for p in BPLIB.list_input_pins(move_fn) if str(PINLIB.get_pin_name(p)).lower() == "deltalocation"][0]
    # 固定向下速度 -speed * 0.033
    step_z = -float(speed) * 0.033
    PINLIB.set_pin_value(pin_delta, f"0,0,{step_z}")
    
    pin_sweep = [p for p in BPLIB.list_input_pins(move_fn) if str(PINLIB.get_pin_name(p)).lower() == "bsweep"][0]
    PINLIB.set_pin_value(pin_sweep, "false")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print(f"✅ 动态敌人蓝图构建成功: {name}")
    return bp

def main():
    print("🚀 正在构建动态敌人并更新 MAP_GGBOM_Main...")
    fb_zombie = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet"
    fb_hound = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet"
    fb_shambler = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet"
    fb_boss = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet"
    
    bp_zombie = build_enemy_bp("BP_Enemy_Zombie", fb_zombie, speed=65.0, scale=0.45)
    bp_hound = build_enemy_bp("BP_Enemy_Hound", fb_hound, speed=110.0, scale=0.48)
    bp_shambler = build_enemy_bp("BP_Enemy_Shambler", fb_shambler, speed=45.0, scale=0.58)
    bp_boss = build_enemy_bp("BP_Boss_Overlord", fb_boss, speed=30.0, scale=0.72)
    
    # 载入现有关卡
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 收集要删除的旧静态贴图
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for a in actors:
        lbl = a.get_actor_label()
        if any(lbl.startswith(k) for k in ("Zombie_", "Brute_", "VenomShooter_", "Hound_", "Boss_Overlord_Visual")):
            unreal.EditorLevelLibrary.destroy_actor(a)
            
    # 部署动态敌人
    enemies = [
        (bp_zombie, -180, 380, "Live_Zombie_01"),
        (bp_zombie, -60, 420, "Live_Zombie_02"),
        (bp_zombie, 140, 400, "Live_Zombie_03"),
        (bp_shambler, 0, 300, "Live_Shambler_Elite"),
        (bp_hound, -240, 160, "Live_Hound_01"),
        (bp_hound, 200, 220, "Live_Hound_02"),
        (bp_boss, 0, 600, "Live_Boss_Overlord"),
    ]
    for bp, x, z, lbl in enemies:
        cls = bp.generated_class()
        act = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, unreal.Vector(x, 0, z), unreal.Rotator())
        if act:
            act.set_actor_label(lbl)
            print(f"  + 部署动态敌人: {lbl}")
            
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    print("MAP_GGBOM_MAIN_UPDATED_SUCCESS")

if __name__ == "__main__":
    main()
