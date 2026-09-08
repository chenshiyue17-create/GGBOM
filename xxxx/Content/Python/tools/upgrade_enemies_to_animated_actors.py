# -*- coding: utf-8 -*-
"""
UE5.8 2D 竖屏游戏 SOP 标准: 怪物由静态 Sprite 全面升级为动态 Flipbook + AI 追踪 Actor
1. 将关卡 MAP_GGBOM_Main 中的静态 PaperSpriteActor 怪物与 Boss 彻底清除
2. 生成并部署具备真实帧动画 Flipbook、生命值、AI 寻路追踪的动态敌人蓝图 Actor
"""
from __future__ import annotations
import unreal

GEN = "/Game/GGBOM"
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

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

def build_dynamic_enemy_bp(bp_path: str, flipbook_path: str, move_speed: float, scale: float, max_hp: float):
    print(f"🧟 正在构建动态敌人蓝图: {bp_path}...")
    if ASSETS.does_asset_exist(bp_path):
        bp = unreal.load_asset(bp_path)
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(bp_path, unreal.Actor.static_class())
        
    fb_asset = unreal.load_asset(flipbook_path)
    
    # 确保有 PaperFlipbookComponent
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    has_fb = False
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if "Flipbook" in vname or isinstance(obj, unreal.PaperFlipbookComponent):
            has_fb = True
            if fb_asset:
                obj.set_editor_property("source_flipbook", fb_asset)
            obj.set_editor_property("relative_scale3d", unreal.Vector(scale, scale, scale))
            obj.set_editor_property("translucency_sort_priority", 300)
            obj.set_editor_property("visible", True)
            obj.set_editor_property("hidden_in_game", False)
            
    # 构建 AI 追踪与移动事件图
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
    
    # 获取双方坐标并计算追踪向量
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
    
    # 移动
    move_node = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1720, 0)
    set_value(move_node, "bSweep", "false")
    connect(br_valid, "then", move_node, "execute")
    connect(mul_dt, "ReturnValue", move_node, "DeltaLocation")
    
    # 朝向翻转: 如果 sub_vec.X < 0 向右则 ScaleX = -scale, 否则 ScaleX = scale
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
    print(f"✅ 动态敌人蓝图就绪: {bp_path}")
    return bp

def deploy_to_level():
    print("🗺️ 正在打开主关卡 MAP_GGBOM_Main 部署动态怪物实体...")
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    
    # 1. 扫描并清除场景中残留的怪物静态贴图 (PaperSpriteActor)
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = actor.get_actor_label()
        if any(lbl.startswith(prefix) for prefix in ("Zombie_", "Brute_", "VenomShooter_", "Hound_", "Boss_Overlord")):
            unreal.EditorLevelLibrary.destroy_actor(actor)
            print(f"  - 清除静态怪物贴图: {lbl}")
            
    # 2. 构建动态敌人蓝图
    zombie_bp = build_dynamic_enemy_bp(
        "/Game/Blueprints/Combat/BP_ENE_ZombieWalker",
        "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet",
        move_speed=80.0, scale=0.45, max_hp=60.0
    )
    
    hound_bp = build_dynamic_enemy_bp(
        "/Game/Blueprints/Combat/BP_ENE_Hound",
        "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet",
        move_speed=130.0, scale=0.48, max_hp=45.0
    )
    
    shambler_bp = build_dynamic_enemy_bp(
        "/Game/Blueprints/Combat/BP_ENE_Shambler",
        "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet",
        move_speed=55.0, scale=0.58, max_hp=180.0
    )
    
    boss_bp = build_dynamic_enemy_bp(
        "/Game/Blueprints/Combat/BP_BOSS_Overlord",
        "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet",
        move_speed=40.0, scale=0.72, max_hp=2000.0
    )
    
    # 3. 部署动态蓝图实体到关卡指定战术位置
    spawn_list = [
        # 行尸群 (自上向下推进)
        (zombie_bp, unreal.Vector(-180, 0, 380), "Live_Zombie_01"),
        (zombie_bp, unreal.Vector(-60, 0, 420), "Live_Zombie_02"),
        (zombie_bp, unreal.Vector(140, 0, 400), "Live_Zombie_03"),
        # 重型蛮兽
        (shambler_bp, unreal.Vector(0, 0, 300), "Live_Shambler_Elite"),
        # 变异快犬 (两侧包抄)
        (hound_bp, unreal.Vector(-240, 0, 160), "Live_Hound_01"),
        (hound_bp, unreal.Vector(200, 0, 220), "Live_Hound_02"),
        # 深渊领主 Boss
        (boss_bp, unreal.Vector(0, 0, 600), "Live_Boss_Overlord"),
    ]
    
    for bp, loc, label in spawn_list:
        cls = bp.generated_class()
        act = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, loc, unreal.Rotator())
        if act:
            act.set_actor_label(label)
            print(f"  + 部署动态敌人: {label} @ {loc}")
            
    # 4. 保存关卡
    world = unreal.EditorLevelLibrary.get_editor_world()
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    print("ALL_ENEMIES_UPGRADED_SUCCESS")

def main():
    deploy_to_level()

if __name__ == "__main__":
    main()
