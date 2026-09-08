# -*- coding: utf-8 -*-
"""
UE5.8 2D 竖屏游戏 SOP 标准: 全动态怪物与高精关卡实装系统
1. 创建/更新 4 大动态敌人蓝图 (真实帧动画 Flipbook + 动态追踪 AI + 朝向翻转)
2. 重新组装主关卡 MAP_GGBOM_Main, 彻底替换所有静态怪物贴图为动态实体
"""
from __future__ import annotations
import math
from pathlib import Path
import unreal

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
ART_ROOT = ROOT / "Content" / "美术" / "Art"
GEN = "/Game/GGBOM"
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"

def log(msg: str):
    print(f"[LiveStage] {msg}")
    unreal.log(f"[LiveStage] {msg}")

def ensure(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def pin(node: unreal.K2Node, name: str, output: bool) -> unreal.BlueprintGraphPin:
    values = BPLIB.list_output_pins(node) if output else BPLIB.list_input_pins(node)
    wanted = name.lower()
    exact = [p for p in values if str(PINLIB.get_pin_name(p)).lower() == wanted]
    if len(exact) == 1:
        return exact[0]
    raise RuntimeError(f"Pin {name} not found; available={[str(PINLIB.get_pin_name(p)) for p in values]}")

def set_value(node: unreal.K2Node, name: str, value) -> None:
    target = pin(node, name, False)
    if not PINLIB.set_pin_value(target, str(value)):
        raise RuntimeError(f"Default rejected: {name}={value}")

def connect(a: unreal.K2Node, a_pin: str, b: unreal.K2Node, b_pin: str) -> None:
    source, target = pin(a, a_pin, True), pin(b, b_pin, False)
    if not PINLIB.try_create_connection(source, target):
        raise RuntimeError(f"Connection rejected: {a_pin} -> {b_pin}")

def fn(editor: unreal.BlueprintGraphEditor, path: str, x: int, y: int) -> unreal.K2Node:
    node = editor.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"Function node failed: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

def build_enemy_blueprint(bp_path: str, flipbook_path: str, move_speed: float, scale: float):
    log(f"🧟 正在构建动态敌人蓝图: {bp_path}...")
    ensure(str(Path(bp_path).parent))
    if ASSETS.does_asset_exist(bp_path):
        bp = unreal.load_asset(bp_path)
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(bp_path, unreal.Pawn.static_class())
        
    fb_asset = unreal.load_asset(flipbook_path)
    
    # 配置 Flipbook 组件
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if "Flipbook" in vname or isinstance(obj, unreal.PaperFlipbookComponent):
            if fb_asset:
                obj.set_editor_property("source_flipbook", fb_asset)
            obj.set_editor_property("relative_scale3d", unreal.Vector(scale, scale, scale))
            obj.set_editor_property("translucency_sort_priority", 300)
            obj.set_editor_property("visible", True)
            obj.set_editor_property("hidden_in_game", False)
            
    # 构建 AI 追踪 Tick 逻辑
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    tick = ed.find_event_node("ReceiveTick")
    get_player = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerPawn", 0, 0)
    set_value(get_player, "PlayerIndex", 0)
    
    is_valid_player = fn(ed, "/Script/Engine.KismetSystemLibrary.IsValid", 220, 0)
    connect(get_player, "ReturnValue", is_valid_player, "Object")
    
    br_valid = ed.add_branch_node(); br_valid.set_node_pos(unreal.IntPoint(420, 0))
    connect(tick, "then", br_valid, "execute")
    connect(is_valid_player, "ReturnValue", br_valid, "Condition")
    
    # 获取双方坐标
    p_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 620, -100); connect(get_player, "ReturnValue", p_loc, "self")
    my_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 620, 100)
    
    sub_vec = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 840, 0)
    connect(p_loc, "ReturnValue", sub_vec, "A"); connect(my_loc, "ReturnValue", sub_vec, "B")
    
    # 平面归一化
    norm_vec = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 1060, 0)
    connect(sub_vec, "ReturnValue", norm_vec, "A")
    
    mul_spd = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1280, 0)
    connect(norm_vec, "ReturnValue", mul_spd, "A"); set_value(mul_spd, "B", float(move_speed))
    
    mul_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1500, 0)
    connect(mul_spd, "ReturnValue", mul_dt, "A"); connect(tick, "DeltaSeconds", mul_dt, "B")
    
    # 移动节点
    move_node = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1720, 0)
    set_value(move_node, "bSweep", "false")
    connect(br_valid, "then", move_node, "execute")
    connect(mul_dt, "ReturnValue", move_node, "DeltaLocation")
    
    # 左右朝向翻转
    break_v = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 1060, 200); connect(sub_vec, "ReturnValue", break_v, "InVec")
    cmp_dir = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 1280, 200); connect(break_v, "X", cmp_dir, "A"); set_value(cmp_dir, "B", 0.0)
    
    sel_scale = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 1500, 200)
    set_value(sel_scale, "A", -scale); set_value(sel_scale, "B", scale); connect(cmp_dir, "ReturnValue", sel_scale, "bPickA")
    
    make_scale = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1720, 200)
    connect(sel_scale, "ReturnValue", make_scale, "X"); set_value(make_scale, "Y", scale); set_value(make_scale, "Z", scale)
    
    get_fb = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1720, 360); set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    set_sc = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 1940, 200)
    connect(move_node, "then", set_sc, "execute")
    connect(get_fb, "ReturnValue", set_sc, "self")
    connect(make_scale, "ReturnValue", set_sc, "NewScale3D")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ 动态敌人蓝图构建成功: {bp_path}")
    return bp

def spawn_sprite_actor(sprite_path: str, loc: unreal.Vector, scale: float, priority: int = 0, label: str = "") -> unreal.PaperSpriteActor:
    sprite = unreal.load_asset(sprite_path)
    if not sprite:
        return None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, loc, unreal.Rotator())
    comp = actor.get_component_by_class(unreal.PaperSpriteComponent)
    if comp:
        comp.set_editor_property("source_sprite", sprite)
        comp.set_editor_property("translucency_sort_priority", priority)
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    if label:
        actor.set_actor_label(label)
    return actor

def assemble_live_stage():
    log("==================================================================")
    log("🚀 正在构建全动态怪物 + 1:1 概念图主关卡 MAP_GGBOM_Main...")
    log("==================================================================")
    
    # 1. 编译 4 大动态敌人蓝图
    zombie_bp = build_enemy_blueprint(
        "/Game/Blueprints/Combat/BP_ENE_ZombieWalker",
        "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet",
        move_speed=80.0, scale=0.45
    )
    
    hound_bp = build_enemy_blueprint(
        "/Game/Blueprints/Combat/BP_ENE_Hound",
        "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet",
        move_speed=130.0, scale=0.48
    )
    
    shambler_bp = build_enemy_blueprint(
        "/Game/Blueprints/Combat/BP_ENE_Shambler",
        "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet",
        move_speed=55.0, scale=0.58
    )
    
    boss_bp = build_enemy_blueprint(
        "/Game/Blueprints/Combat/BP_BOSS_Overlord",
        "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet",
        move_speed=40.0, scale=0.72
    )

    # 2. 创建并组装全新主关卡 MAP_GGBOM_Main
    ensure(f"{GEN}/Maps")
    unreal.EditorLevelLibrary.new_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 绑定 GameMode
    gm_path = f"{GEN}/Blueprints/BP_GGBOM_GameMode"
    gm_cls = unreal.load_class(None, f"{gm_path}.BP_GGBOM_GameMode_C")
    if gm_cls:
        world.get_world_settings().set_editor_property("default_game_mode", gm_cls)
        
    # 3. 9:16 正交摄像机
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(0, -500, 0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    cam_comp.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    cam_comp.set_editor_property("ortho_width", 1080.0)
    cam_comp.set_editor_property("aspect_ratio", 0.5625)
    cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    cam.set_actor_label("PortraitCamera_9x16")
    
    # 4. 背景地面与战术掩体
    spawn_sprite_actor(f"{GEN}/Art/Sprites/SP_Ground", unreal.Vector(0, 80, 0), 1.15, -100, "Ground_Stage00")
    
    barricade_sp = f"{GEN}/Art/Sprites/SP_Barricade"
    spawn_sprite_actor(barricade_sp, unreal.Vector(-180, 15, 480), 0.55, 6, "Barricade_Top_L")
    spawn_sprite_actor(barricade_sp, unreal.Vector(180, 15, 480), 0.55, 6, "Barricade_Top_R")
    spawn_sprite_actor(barricade_sp, unreal.Vector(-240, 15, 0), 0.58, 6, "DefenseLine_L")
    spawn_sprite_actor(barricade_sp, unreal.Vector(240, 15, 0), 0.58, 6, "DefenseLine_R")
    
    # 5. 部署【动态敌人蓝图 Actor】（绝非静态贴图！）
    enemies_to_spawn = [
        # 行尸群
        (zombie_bp, unreal.Vector(-180, 0, 380), "Live_Zombie_01"),
        (zombie_bp, unreal.Vector(-60, 0, 420), "Live_Zombie_02"),
        (zombie_bp, unreal.Vector(140, 0, 400), "Live_Zombie_03"),
        # 重型蛮兽
        (shambler_bp, unreal.Vector(0, 0, 300), "Live_Shambler_Elite"),
        # 变异快犬
        (hound_bp, unreal.Vector(-240, 0, 160), "Live_Hound_01"),
        (hound_bp, unreal.Vector(200, 0, 220), "Live_Hound_02"),
        # 深渊领主 Boss
        (boss_bp, unreal.Vector(0, 0, 600), "Live_Boss_Overlord"),
    ]
    
    for bp, loc, label in enemies_to_spawn:
        cls = bp.generated_class()
        act = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, loc, unreal.Rotator())
        if act:
            act.set_actor_label(label)
            log(f"  + 部署动态敌人: {label} @ {loc}")
            
    # 6. 玩家出生点
    unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -10, -520), unreal.Rotator())
    
    # 7. HUD 美术部件
    spawn_sprite_actor(f"{GEN}/Art/Sprites/SP_Boss_Bar_Bg", unreal.Vector(0, -60, 880), 0.85, 90, "UI_BossBar_Bg")
    spawn_sprite_actor(f"{GEN}/Art/Sprites/SP_Boss_Bar_Fill", unreal.Vector(0, -60, 880), 0.82, 95, "UI_BossBar_Fill")
    spawn_sprite_actor(f"{GEN}/Art/Sprites/SP_Boss_Skull", unreal.Vector(-240, -60, 880), 0.65, 100, "UI_Boss_SkullIcon")
    spawn_sprite_actor(f"{GEN}/Art/Sprites/SP_Btn_Pause", unreal.Vector(450, -60, 880), 0.28, 100, "UI_Btn_Pause")
    
    spawn_sprite_actor(f"{GEN}/Art/Sprites/SP_HUD_HP_Bg", unreal.Vector(-360, -60, -750), 0.65, 90, "UI_Player_HP_Bg")
    spawn_sprite_actor(f"{GEN}/Art/Sprites/SP_HUD_HP_Fill", unreal.Vector(-360, -60, -750), 0.63, 95, "UI_Player_HP_Fill")
    spawn_sprite_actor(f"{GEN}/Art/Sprites/SP_HUD_Exp_Fill", unreal.Vector(-360, -60, -810), 0.55, 95, "UI_Player_EXP_Fill")

    # 8. 保存关卡与资产
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    log("🎉 全动态主关卡构建成功！MAP_GGBOM_Main SAVED!")

def main():
    assemble_live_stage()

if __name__ == "__main__":
    main()
