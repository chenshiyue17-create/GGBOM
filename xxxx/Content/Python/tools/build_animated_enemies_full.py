# -*- coding: utf-8 -*-
"""
UE5.8 2D 竖屏游戏: 怪物动画与动态推进蓝图全套实装
1. 构建带真实 Flipbook 帧动画与向下推进速度的怪物蓝图 (Zombie, Hound, Boss)
2. 在主关卡 MAP_GGBOM_Main 中生成动态怪物蓝图实体
"""
from __future__ import annotations
from pathlib import Path
import unreal

GEN = "/Game/GGBOM"
MAP_PATH = f"{GEN}/Maps/MAP_GGBOM_Main"

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def ensure(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def build_flipbook_enemy(name: str, fb_path: str, speed: float, scale: float) -> unreal.Blueprint:
    print(f"🧟 正在构建动态怪物蓝图: {name} (Flipbook: {fb_path}, Speed: {speed})...")
    folder = f"{GEN}/Blueprints/Enemies"
    ensure(folder)
    path = f"{folder}/{name}"
    
    if ASSETS.does_asset_exist(path):
        bp = unreal.load_asset(path)
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(path, unreal.Actor.static_class())
        
    fb_asset = unreal.load_asset(fb_path)
    
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    
    # 查找或配置 Flipbook 和 ProjectileMovement
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if "Flipbook" in vname or isinstance(obj, unreal.PaperFlipbookComponent):
            if fb_asset:
                obj.set_editor_property("source_flipbook", fb_asset)
            obj.set_editor_property("relative_scale3d", unreal.Vector(scale, scale, scale))
            obj.set_editor_property("translucency_sort_priority", 200)
            obj.set_editor_property("visible", True)
            obj.set_editor_property("hidden_in_game", False)
        elif "Movement" in vname or isinstance(obj, unreal.ProjectileMovementComponent):
            obj.set_editor_property("initial_speed", float(speed))
            obj.set_editor_property("max_speed", float(speed))
            obj.set_editor_property("velocity", unreal.Vector(0.0, 0.0, -float(speed)))
            obj.set_editor_property("projectile_gravity_scale", 0.0)

    # 编写 Tick 自推进位移（双保险保证平滑向下行走）
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick = ed.find_event_node("ReceiveTick")
    
    move_fn = ed.add_call_function_node("/Script/Engine.Actor.K2_AddActorWorldOffset")
    move_fn.set_node_pos(unreal.IntPoint(300, 0))
    pin_then = [p for p in BPLIB.list_output_pins(tick) if str(PINLIB.get_pin_name(p)).lower() == "then"][0]
    pin_exec = [p for p in BPLIB.list_input_pins(move_fn) if str(PINLIB.get_pin_name(p)).lower() == "execute"][0]
    PINLIB.try_create_connection(pin_then, pin_exec)
    
    # 每秒向下位移 -speed
    pin_delta = [p for p in BPLIB.list_input_pins(move_fn) if str(PINLIB.get_pin_name(p)).lower() == "deltalocation"][0]
    # 固定每帧向 -Z 移动 speed * 0.033
    step_z = -float(speed) * 0.033
    PINLIB.set_pin_value(pin_delta, f"0,0,{step_z}")
    
    pin_sweep = [p for p in BPLIB.list_input_pins(move_fn) if str(PINLIB.get_pin_name(p)).lower() == "bsweep"][0]
    PINLIB.set_pin_value(pin_sweep, "false")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print(f"✅ {name} 蓝图构建并保存完毕！")
    return bp

def rebuild_visual_stage():
    print("🗺️ 正在重构主关卡 MAP_GGBOM_Main 部署动态动画怪物...")
    
    fb_zombie = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet"
    fb_hound = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet"
    fb_shambler = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet"
    fb_boss = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet"
    
    bp_zombie = build_flipbook_enemy("BP_Enemy_Zombie", fb_zombie, speed=65.0, scale=0.45)
    bp_hound = build_flipbook_enemy("BP_Enemy_Hound", fb_hound, speed=110.0, scale=0.48)
    bp_shambler = build_flipbook_enemy("BP_Enemy_Shambler", fb_shambler, speed=45.0, scale=0.58)
    bp_boss = build_flipbook_enemy("BP_Boss_Overlord", fb_boss, speed=30.0, scale=0.72)
    
    # 重新组装主关卡
    if ASSETS.does_asset_exist(MAP_PATH):
        ASSETS.delete_asset(MAP_PATH)
    unreal.EditorLevelLibrary.new_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 绑定 GameMode
    gm_path = f"{GEN}/Blueprints/BP_GGBOM_GameMode"
    gm_cls = unreal.load_class(None, f"{gm_path}.BP_GGBOM_GameMode_C")
    if gm_cls:
        world.get_world_settings().set_editor_property("default_game_mode", gm_cls)
        
    # 相机
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(0, -500, 0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    cam_comp.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    cam_comp.set_editor_property("ortho_width", 1080.0)
    cam_comp.set_editor_property("aspect_ratio", 0.5625)
    cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    cam.set_actor_label("PortraitCamera_9x16")
    
    # 地面与掩体
    sp_ground = unreal.load_asset(f"{GEN}/Art/Sprites/SP_Ground")
    if sp_ground:
        g_act = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, unreal.Vector(0, 80, 0), unreal.Rotator())
        g_act.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("source_sprite", sp_ground)
        g_act.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("translucency_sort_priority", -100)
        g_act.set_actor_scale3d(unreal.Vector(1.15, 1.15, 1.15))
        g_act.set_actor_label("Ground_Stage00")
        
    sp_barricade = unreal.load_asset(f"{GEN}/Art/Sprites/SP_Barricade")
    if sp_barricade:
        for x, z, lbl in ((-180, 480, "Barricade_Top_L"), (180, 480, "Barricade_Top_R"), (-240, 0, "DefenseLine_L"), (240, 0, "DefenseLine_R")):
            b_act = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, unreal.Vector(x, 15, z), unreal.Rotator())
            b_act.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("source_sprite", sp_barricade)
            b_act.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("translucency_sort_priority", 6)
            b_act.set_actor_scale3d(unreal.Vector(0.58, 0.58, 0.58))
            b_act.set_actor_label(lbl)

    # 部署动态敌人蓝图 (动态 Flipbook 行走动画 + 自向下推进)
    enemies = [
        (bp_zombie, -180, 380, "Live_Zombie_01"),
        (bp_zombie, -60, 420, "Live_Zombie_02"),
        (bp_zombie, 140, 400, "Live_Zombie_03"),
        (bp_shambler, 0, 300, "Live_Shambler_Elite"),
        (bp_hound, -240, 160, "Live_Hound_01"),
        (bp_hound, 200, 220, "Live_Hound_02"),
        (bp_boss, 0, 600, "Live_Boss_Overlord"),
    ]
    for bp, x, z, label in enemies:
        cls = bp.generated_class()
        act = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, unreal.Vector(x, 0, z), unreal.Rotator())
        if act:
            act.set_actor_label(label)
            print(f"  + 部署动态怪物蓝图实体: {label} @ ({x}, 0, {z})")

    # 玩家出生点
    unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -10, -520), unreal.Rotator())

    # HUD 部件
    hud_items = [
        (f"{GEN}/Art/Sprites/SP_Boss_Bar_Bg", unreal.Vector(0, -60, 880), 0.85, 90, "UI_BossBar_Bg"),
        (f"{GEN}/Art/Sprites/SP_Boss_Bar_Fill", unreal.Vector(0, -60, 880), 0.82, 95, "UI_BossBar_Fill"),
        (f"{GEN}/Art/Sprites/SP_Boss_Skull", unreal.Vector(-240, -60, 880), 0.65, 100, "UI_Boss_SkullIcon"),
        (f"{GEN}/Art/Sprites/SP_Btn_Pause", unreal.Vector(450, -60, 880), 0.28, 100, "UI_Btn_Pause"),
        (f"{GEN}/Art/Sprites/SP_HUD_HP_Bg", unreal.Vector(-360, -60, -750), 0.65, 90, "UI_Player_HP_Bg"),
        (f"{GEN}/Art/Sprites/SP_HUD_HP_Fill", unreal.Vector(-360, -60, -750), 0.63, 95, "UI_Player_HP_Fill"),
        (f"{GEN}/Art/Sprites/SP_HUD_Exp_Fill", unreal.Vector(-360, -60, -810), 0.55, 95, "UI_Player_EXP_Fill"),
    ]
    for sp_p, loc, sc, prio, lbl in hud_items:
        sp = unreal.load_asset(sp_p)
        if sp:
            act = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, loc, unreal.Rotator())
            act.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("source_sprite", sp)
            act.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("translucency_sort_priority", prio)
            act.set_actor_scale3d(unreal.Vector(sc, sc, sc))
            act.set_actor_label(lbl)

    # 保存
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    print("🎉 全动态怪物主关卡构建成功！MAP_GGBOM_Main SAVED!")

def main():
    rebuild_visual_stage()

if __name__ == "__main__":
    main()
