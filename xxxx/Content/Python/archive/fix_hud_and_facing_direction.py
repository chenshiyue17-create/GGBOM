# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》UI 全量打包实装 & 角色 4/8 方向朝向保持彻底重构
1. 打包实装唯一统一 Master HUD (BP_GGBOM_MasterHUD)，放置在关卡最前层 (Z=0, Y=-60)，
   包含 Boss 战条、暂停按钮、右侧战术道具栏、底部玩家生命经验槽、4 张武器卡牌。
2. 重构 BP_Player_Medic 的 Event Graph:
   - 移动时播放对应方向奔跑动画 (Run_Up, Run_Down, Run_Left, Run_Right镜像)
   - 停下待机时精确保持移动后的朝向 (Idle_Up, Idle_Down, Idle_Left, Idle_Right镜像)
   - 杜绝停下时强制面对屏幕的错误
================================================================================
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import unreal

GEN = "/Game/GGBOM"
HUD_BP_PATH = f"{GEN}/Blueprints/BP_GGBOM_MasterHUD"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
MAP_PATH = f"{GEN}/Maps/MAP_GGBOM_Main"

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def log(msg: str):
    print(f"[HUD-FACING-FIX] {msg}")

def pin(node: unreal.K2Node, name: str, output: bool) -> unreal.BlueprintGraphPin:
    values = BPLIB.list_output_pins(node) if output else BPLIB.list_input_pins(node)
    wanted = name.lower()
    exact = [p for p in values if str(PINLIB.get_pin_name(p)).lower() == wanted]
    if len(exact) == 1:
        return exact[0]
    raise RuntimeError(f"Pin {name} not found; available={[str(PINLIB.get_pin_name(p)) for p in values]}")

def set_value(node: unreal.K2Node, name: str, value: Any) -> None:
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

def add_subobject(bp: unreal.Blueprint, parent_handle, name: str, cls: unreal.Class):
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", parent_handle)
    params.set_editor_property("new_class", cls)
    params.set_editor_property("blueprint_context", bp)
    handle, reason = SUBOBJECTS.add_new_subobject(params)
    if not unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(handle):
        raise RuntimeError(f"Component {name} failed: {reason}")
    SUBOBJECTS.rename_subobject(handle, unreal.Text(name))
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    return handle, unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)

# ==============================================================================
# 1. 构建统一 Master HUD
# ==============================================================================
def build_master_hud_blueprint():
    log("📦 1. 构建打包统一 Master HUD (BP_GGBOM_MasterHUD)...")
    if ASSETS.does_asset_exist(HUD_BP_PATH):
        hud_bp = unreal.load_asset(HUD_BP_PATH)
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Actor.static_class())
        hud_bp = TOOLS.create_asset("BP_GGBOM_MasterHUD", f"{GEN}/Blueprints", unreal.Blueprint, factory)
        
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(hud_bp)
    root_handle = handles[0]
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    
    existing_vars = {}
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        existing_vars[vname] = (h, unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, hud_bp))

    sprite_prefix = f"{GEN}/Art/Sprites"
    hud_components = [
        # (组件名, Sprite路径, 相对坐标(X, Y, Z), 缩放, 优先级)
        # 顶部 Boss
        ("Comp_BossBar_Bg", f"{sprite_prefix}/SP_HUD_BossBar_Bg", unreal.Vector(0.0, 0.0, 770.0), 0.55, 3000),
        ("Comp_BossBar_Fill", f"{sprite_prefix}/SP_HUD_BossBar_Fill", unreal.Vector(20.0, -1.0, 770.0), 0.55, 3010),
        ("Comp_Boss_Skull", f"{sprite_prefix}/SP_Boss_Skull", unreal.Vector(220.0, -2.0, 770.0), 0.55, 3020),
        ("Comp_Btn_Pause", f"{sprite_prefix}/SP_Btn_Pause", unreal.Vector(-410.0, -2.0, 770.0), 0.55, 3020),
        
        # 右侧战术栏 (X = -410)
        ("Comp_Tactical_Barricade", f"{sprite_prefix}/SP_Tactical_Barricade", unreal.Vector(-410.0, 0.0, 320.0), 0.45, 3010),
        ("Comp_Tactical_RedBarrel", f"{sprite_prefix}/SP_RedBarrel", unreal.Vector(-410.0, 0.0, 190.0), 0.45, 3010),
        ("Comp_Tactical_ToxicDrum", f"{sprite_prefix}/SP_ToxicDrum", unreal.Vector(-410.0, 0.0, 60.0), 0.45, 3010),
        ("Comp_Tactical_MedPod", f"{sprite_prefix}/SP_MedPod", unreal.Vector(-410.0, 0.0, -70.0), 0.45, 3010),
        
        # 底部玩家状态 (X = +290, Z = -710 ~ -775)
        ("Comp_Player_HP_Bg", f"{sprite_prefix}/SP_HUD_Player_HP_Bg", unreal.Vector(290.0, 0.0, -710.0), 0.55, 3000),
        ("Comp_Player_HP_Fill", f"{sprite_prefix}/SP_HUD_Player_HP_Fill", unreal.Vector(320.0, -1.0, -710.0), 0.55, 3010),
        ("Comp_Player_EXP_Bg", f"{sprite_prefix}/SP_HUD_Player_EXP_Bg", unreal.Vector(290.0, 0.0, -775.0), 0.55, 3000),
        ("Comp_Player_EXP_Fill", f"{sprite_prefix}/SP_HUD_Player_EXP_Fill", unreal.Vector(300.0, -1.0, -775.0), 0.55, 3010),
        
        # 底部 4 张武器卡牌 (Z = -745)
        ("Comp_Card_AutoRifle", f"{sprite_prefix}/SP_Card_AutoRifle", unreal.Vector(70.0, 0.0, -745.0), 0.48, 3010),
        ("Comp_Card_Shotgun", f"{sprite_prefix}/SP_Card_Shotgun", unreal.Vector(-70.0, 0.0, -745.0), 0.48, 3010),
        ("Comp_Card_Rocket", f"{sprite_prefix}/SP_Card_Rocket", unreal.Vector(-210.0, 0.0, -745.0), 0.48, 3010),
        ("Comp_Card_Tesla", f"{sprite_prefix}/SP_Card_Tesla", unreal.Vector(-350.0, 0.0, -745.0), 0.48, 3010),
    ]

    for comp_name, sp_path, loc, scale, sort_pri in hud_components:
        sp = unreal.load_asset(sp_path)
        if not sp:
            continue
        if comp_name not in existing_vars:
            h, comp = add_subobject(hud_bp, root_handle, comp_name, unreal.PaperFlipbookComponent.static_class() if "Flipbook" in sp_path else unreal.PaperSpriteComponent.static_class())
        else:
            comp = existing_vars[comp_name][1]
            
        comp.set_editor_property("source_sprite", sp)
        if mat:
            comp.set_material(0, mat)
        comp.set_editor_property("relative_location", loc)
        comp.set_editor_property("relative_scale3d", unreal.Vector(scale, scale, scale))
        comp.set_editor_property("translucency_sort_priority", sort_pri)
        comp.set_editor_property("visible", True)
        comp.set_editor_property("hidden_in_game", False)
        
    BPLIB.compile_blueprint(hud_bp)
    ASSETS.save_loaded_asset(hud_bp, only_if_is_dirty=False)
    log("✅ BP_GGBOM_MasterHUD 统一 UI 蓝图编译保存完成！")

# ==============================================================================
# 2. 重构主角 BP_Player_Medic 方向保持动画状态机
# ==============================================================================
def configure_player_facing_and_animation():
    log("🎮 2. 重构 BP_Player_Medic 移动与朝向保持状态机...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        raise RuntimeError(f"Player Blueprint 缺失: {PLAYER_BP_PATH}")
        
    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    fb_idle_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet")
    fb_run_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_01_Down_Sheet")
    fb_idle_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    fb_run_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet")
    fb_idle_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet")
    fb_run_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet")

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    # 清理非标准事件节点
    try:
        for node in ed.list_all_nodes():
            if node.get_name() not in ["ReceiveBeginPlay", "ReceiveTick", "ReceiveActorBeginOverlap"]:
                ed.remove_node(node)
    except Exception:
        pass
        
    tick = ed.find_event_node("ReceiveTick")
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)
    
    # A/D
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -180); set_value(key_a, "Key", "A"); connect(pc_tick, "ReturnValue", key_a, "self")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -80);  set_value(key_d, "Key", "D"); connect(pc_tick, "ReturnValue", key_d, "self")
    sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -180); set_value(sel_a, "A", 450.0); set_value(sel_a, "B", 0.0); connect(key_a, "ReturnValue", sel_a, "bPickA")
    sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -80);  set_value(sel_d, "A", -450.0); set_value(sel_d, "B", 0.0); connect(key_d, "ReturnValue", sel_d, "bPickA")
    add_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -130); connect(sel_a, "ReturnValue", add_x, "A"); connect(sel_d, "ReturnValue", add_x, "B")
    
    # W/S
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 40);   set_value(key_w, "Key", "W"); connect(pc_tick, "ReturnValue", key_w, "self")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 140);  set_value(key_s, "Key", "S"); connect(pc_tick, "ReturnValue", key_s, "self")
    sel_w = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 40);   set_value(sel_w, "A", 450.0); set_value(sel_w, "B", 0.0); connect(key_w, "ReturnValue", sel_w, "bPickA")
    sel_s = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 140);  set_value(sel_s, "A", -450.0); set_value(sel_s, "B", 0.0); connect(key_s, "ReturnValue", sel_s, "bPickA")
    add_z = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, 90); connect(sel_w, "ReturnValue", add_z, "A"); connect(sel_s, "ReturnValue", add_z, "B")
    
    # Move Vector & Apply
    make_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 880, 0)
    connect(add_x, "ReturnValue", make_vec, "X"); set_value(make_vec, "Y", 0.0); connect(add_z, "ReturnValue", make_vec, "Z")
    
    mul_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1080, 0)
    connect(make_vec, "ReturnValue", mul_dt, "A"); connect(tick, "DeltaSeconds", mul_dt, "B")
    
    move_node = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1300, 0)
    set_value(move_node, "bSweep", "true")
    connect(tick, "then", move_node, "execute")
    connect(mul_dt, "ReturnValue", move_node, "DeltaLocation")
    
    # 状态判定: is_moving
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -200); connect(add_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 200); connect(add_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1080, 150); connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")
    
    br_moving = ed.add_branch_node(); br_moving.set_node_pos(unreal.IntPoint(1520, 0))
    connect(move_node, "then", br_moving, "execute")
    connect(is_moving, "ReturnValue", br_moving, "Condition")
    
    get_comp = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1520, -200); set_value(get_comp, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    get_curr_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 1740, -250); connect(get_comp, "ReturnValue", get_curr_fb, "self")
    
    # ==================== 移动分支 (is_moving = True) ====================
    # 左右奔跑优先判定
    br_side = ed.add_branch_node(); br_side.set_node_pos(unreal.IntPoint(1740, -100))
    connect(br_moving, "then", br_side, "execute")
    connect(cmp_x, "ReturnValue", br_side, "Condition")
    
    # 左右奔跑设置 ScaleX (向右: -0.45 镜像, 向左: 0.45)
    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 1960, -180); connect(add_x, "ReturnValue", is_right, "A"); set_value(is_right, "B", 0.0)
    scale_val_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 2180, -180); set_value(scale_val_x, "A", -0.45); set_value(scale_val_x, "B", 0.45); connect(is_right, "ReturnValue", scale_val_x, "bPickA")
    scale_side_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2400, -180); connect(scale_val_x, "ReturnValue", scale_side_vec, "X"); set_value(scale_side_vec, "Y", 0.45); set_value(scale_side_vec, "Z", 0.45)
    set_sc_side = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2620, -180); connect(br_side, "then", set_sc_side, "execute"); connect(get_comp, "ReturnValue", set_sc_side, "self"); connect(scale_side_vec, "ReturnValue", set_sc_side, "NewScale3D")
    
    # 切换为 Run_Left
    set_fb_run_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, -180)
    if fb_run_left:
        set_value(set_fb_run_side, "NewFlipbook", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(set_sc_side, "then", set_fb_run_side, "execute"); connect(get_comp, "ReturnValue", set_fb_run_side, "self")
    
    # 上下奔跑分支
    is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1960, 0); connect(add_z, "ReturnValue", is_up, "A"); set_value(is_up, "B", 0.0)
    br_up = ed.add_branch_node(); br_up.set_node_pos(unreal.IntPoint(2180, 0))
    connect(br_side, "else", br_up, "execute")
    connect(is_up, "ReturnValue", br_up, "Condition")
    
    # 向上跑 (Run_Up, ScaleX = 0.45)
    scale_up_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2400, -60); set_value(scale_up_vec, "X", 0.45); set_value(scale_up_vec, "Y", 0.45); set_value(scale_up_vec, "Z", 0.45)
    set_sc_up = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2620, -60); connect(br_up, "then", set_sc_up, "execute"); connect(get_comp, "ReturnValue", set_sc_up, "self"); connect(scale_up_vec, "ReturnValue", set_sc_up, "NewScale3D")
    set_fb_run_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, -60)
    if fb_run_up:
        set_value(set_fb_run_up, "NewFlipbook", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    connect(set_sc_up, "then", set_fb_run_up, "execute"); connect(get_comp, "ReturnValue", set_fb_run_up, "self")
    
    # 向下跑 (Run_Down, ScaleX = 0.45)
    scale_down_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2400, 60); set_value(scale_down_vec, "X", 0.45); set_value(scale_down_vec, "Y", 0.45); set_value(scale_down_vec, "Z", 0.45)
    set_sc_down = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2620, 60); connect(br_up, "else", set_sc_down, "execute"); connect(get_comp, "ReturnValue", set_sc_down, "self"); connect(scale_down_vec, "ReturnValue", set_sc_down, "NewScale3D")
    set_fb_run_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, 60)
    if fb_run_down:
        set_value(set_fb_run_down, "NewFlipbook", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(set_sc_down, "then", set_fb_run_down, "execute"); connect(get_comp, "ReturnValue", set_fb_run_down, "self")

    # ==================== 待机分支 (is_moving = False) - 朝向保持 ====================
    # 判定当前是否是 Run_Up 或 Idle_Up
    is_curr_up = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 1740, 220)
    connect(get_curr_fb, "ReturnValue", is_curr_up, "A")
    if fb_run_up:
        set_value(is_curr_up, "B", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
        
    br_idle_up = ed.add_branch_node(); br_idle_up.set_node_pos(unreal.IntPoint(1960, 200))
    connect(br_moving, "else", br_idle_up, "execute")
    connect(is_curr_up, "ReturnValue", br_idle_up, "Condition")
    
    # 待机保持向上 (Idle_Up)
    set_fb_idle_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2200, 160)
    if fb_idle_up:
        set_value(set_fb_idle_up, "NewFlipbook", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    connect(br_idle_up, "then", set_fb_idle_up, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_up, "self")
    
    # 判定当前是否是 Run_Left 或 Idle_Left
    is_curr_side = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 1960, 320)
    connect(get_curr_fb, "ReturnValue", is_curr_side, "A")
    if fb_run_left:
        set_value(is_curr_side, "B", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
        
    br_idle_side = ed.add_branch_node(); br_idle_side.set_node_pos(unreal.IntPoint(2200, 280))
    connect(br_idle_up, "else", br_idle_side, "execute")
    connect(is_curr_side, "ReturnValue", br_idle_side, "Condition")
    
    # 待机保持侧向 (Idle_Left, 此时保持原有的 ScaleX 正负号，左边为正，右边为负，不重置 ScaleX！)
    set_fb_idle_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2440, 260)
    if fb_idle_left:
        set_value(set_fb_idle_side, "NewFlipbook", f"PaperFlipbook'{fb_idle_left.get_path_name()}'")
    connect(br_idle_side, "then", set_fb_idle_side, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_side, "self")
    
    # 判定当前是否是 Run_Down
    is_curr_down = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 2200, 420)
    connect(get_curr_fb, "ReturnValue", is_curr_down, "A")
    if fb_run_down:
        set_value(is_curr_down, "B", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
        
    br_idle_down = ed.add_branch_node(); br_idle_down.set_node_pos(unreal.IntPoint(2440, 380))
    connect(br_idle_side, "else", br_idle_down, "execute")
    connect(is_curr_down, "ReturnValue", br_idle_down, "Condition")
    
    # 待机保持向下 (Idle_Down)
    set_fb_idle_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2680, 380)
    if fb_idle_down:
        set_value(set_fb_idle_down, "NewFlipbook", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    connect(br_idle_down, "then", set_fb_idle_down, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_down, "self")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_Player_Medic 朝向保持状态机构建编译完成！")

# ==============================================================================
# 3. 关卡装配与清理
# ==============================================================================
def assemble_level_and_place_hud():
    log("🗺️ 3. 关卡清理与唯一 Master_Combat_HUD 装配...")
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    removed = 0
    for a in actors:
        lbl = a.get_actor_label() if hasattr(a, "get_actor_label") else a.get_name()
        if (lbl.startswith("HUD_") or lbl.startswith("UI_") or lbl.startswith("UI-") or 
            lbl == "Master_Combat_HUD" or "MasterHUD" in lbl):
            unreal.EditorLevelLibrary.destroy_actor(a)
            removed += 1
            
    log(f"🗑️ 已清除关卡中 {removed} 个散落旧 HUD 实体")

    # 放置唯一的 MasterHUD Actor，固定在 (0, -60, 0)
    master_cls = unreal.load_class(None, f"{HUD_BP_PATH}.BP_GGBOM_MasterHUD_C")
    master_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        master_cls, unreal.Vector(0.0, -60.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0)
    )
    if master_actor:
        master_actor.set_actor_label("Master_Combat_HUD")
        log("✅ 唯一统一 Master_Combat_HUD 实体已放置在关卡最前层 (0, -60, 0)！")

    # 保存关卡
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    log("🎉 关卡与全量资产已持久化保存！")

def main():
    build_master_hud_blueprint()
    configure_player_facing_and_animation()
    assemble_level_and_place_hud()

if __name__ == "__main__":
    main()
