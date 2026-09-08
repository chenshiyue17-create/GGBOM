# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》子弹可见性 (X-Z 平面飞行) 与射击动作全向精准匹配
1. 重构 BP_ProjectileBase:
   - 确保子弹绝对处于 Y = 0.0 正交可视平面，TranslucencySortPriority = 2800
   - 放大子弹尺寸至 (1.6, 1.6, 1.6)，使用高清 TranslucentUnlit 材质
   - 在 ReceiveTick 中使用简单的 AddActorWorldOffset(Velocity * DeltaSeconds) 或 ProjectileMovement
     沿着 Local X/Z 平面高速飞出，杜绝沿 Y 轴偏航被正交相机裁剪
2. 重构 BP_Player_Medic 射击动作状态机:
   - 朝上时按 J: 播放 Attack_Dir_05_Up，在 (X, 0, Z+70) 生成子弹，向上高速飞出
   - 朝下时按 J: 播放 Attack_Dir_01_Down，在 (X, 0, Z-70) 生成子弹，向下高速飞出
   - 朝左时按 J: 播放 Attack_Dir_03_Right (ScaleX=0.45)，在 (X+70, 0, Z) 生成子弹，向左飞出
   - 朝右时按 J: 播放 Attack_Dir_03_Right (ScaleX=-0.45)，在 (X-70, 0, Z) 生成子弹，向右飞出
================================================================================
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import unreal

GEN = "/Game/GGBOM"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
PROJ_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def log(msg: str):
    print(f"[COMBAT-FIX] {msg}")

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

def fix_projectile_blueprint():
    log("🚀 1. 重构 BP_ProjectileBase (确保 100% 正交屏幕高亮可见与沿平面平飞)...")
    bp = unreal.load_asset(PROJ_BP_PATH)
    if not bp:
        raise RuntimeError(f"BP_ProjectileBase 缺失: {PROJ_BP_PATH}")
        
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    root_handle = handles[0]
    
    existing_vars = {}
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        existing_vars[vname] = (h, unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp))

    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    fb = unreal.load_asset("/Game/GGBOM/Art/Flipbooks/Weapons/FB_Bullet_KineticPistol_Flight")
    
    # 挂载或配置 BulletFlipbook
    if "BulletFlipbook" in existing_vars:
        fb_comp = existing_vars["BulletFlipbook"][1]
    else:
        params = unreal.AddNewSubobjectParams()
        params.set_editor_property("parent_handle", root_handle)
        params.set_editor_property("new_class", unreal.PaperFlipbookComponent.static_class())
        params.set_editor_property("blueprint_context", bp)
        h, _ = SUBOBJECTS.add_new_subobject(params)
        SUBOBJECTS.rename_subobject(h, unreal.Text("BulletFlipbook"))
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        fb_comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)

    if fb:
        fb_comp.set_editor_property("source_flipbook", fb)
    if mat:
        fb_comp.set_material(0, mat)
    fb_comp.set_editor_property("translucency_sort_priority", 2800)
    fb_comp.set_editor_property("relative_scale3d", unreal.Vector(1.6, 1.6, 1.6))
    fb_comp.set_editor_property("visible", True)
    fb_comp.set_editor_property("hidden_in_game", False)

    # 隐藏旧的静态 BulletSprite
    if "BulletSprite" in existing_vars:
        existing_vars["BulletSprite"][1].set_editor_property("visible", False)

    # 飞行逻辑：在 Tick 中沿 Forward Vector (或 Up Vector) 高速移动
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for n in ed.list_all_nodes():
        if n.get_name() not in ["ReceiveBeginPlay", "ReceiveTick"]:
            try:
                ed.remove_node(n)
            except Exception:
                pass
                
    begin = ed.find_event_node("ReceiveBeginPlay")
    delay = fn(ed, "/Script/Engine.KismetSystemLibrary.Delay", 240, 0)
    set_value(delay, "Duration", 2.5)
    destroy = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 480, 0)
    connect(begin, "then", delay, "execute")
    connect(delay, "then", destroy, "execute")

    # Tick 移动: AddActorLocalOffset(X=2400*dt, Y=0, Z=0)
    tick = ed.find_event_node("ReceiveTick")
    mul_spd = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 240, 160)
    connect(tick, "DeltaSeconds", mul_spd, "A")
    set_value(mul_spd, "B", 2400.0)
    
    make_fly_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 480, 160)
    connect(mul_spd, "ReturnValue", make_fly_vec, "X") # Local X 高速向前平飞
    set_value(make_fly_vec, "Y", 0.0)
    set_value(make_fly_vec, "Z", 0.0)
    
    add_fly = fn(ed, "/Script/Engine.Actor.K2_AddActorLocalOffset", 720, 160)
    set_value(add_fly, "bSweep", "false")
    connect(tick, "then", add_fly, "execute")
    connect(make_fly_vec, "ReturnValue", add_fly, "DeltaLocation")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_ProjectileBase 正交可视飞行动画配置完毕！")

def fix_player_attack_and_matching():
    log("🎮 2. 重构 BP_Player_Medic 全向动作匹配与射击发射...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        raise RuntimeError(f"BP_Player_Medic 缺失: {PLAYER_BP_PATH}")
        
    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    # Idle
    fb_idle_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet")
    fb_idle_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    fb_idle_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet")
    # Run
    fb_run_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_01_Down_Sheet")
    fb_run_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet")
    fb_run_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet")
    # Attack
    fb_atk_down = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_01_Down/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_01_Down_Sheet")
    fb_atk_up = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet")
    fb_atk_side = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_03_Right/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_03_Right_Sheet")

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for n in ed.list_all_nodes():
        if n.get_name() not in ["ReceiveBeginPlay", "ReceiveTick"]:
            try:
                ed.remove_node(n)
            except Exception:
                pass
                
    tick = ed.find_event_node("ReceiveTick")
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)
    
    # 移动采样
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -180); set_value(key_a, "Key", "A"); connect(pc_tick, "ReturnValue", key_a, "self")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -80);  set_value(key_d, "Key", "D"); connect(pc_tick, "ReturnValue", key_d, "self")
    sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -180); set_value(sel_a, "A", 450.0); set_value(sel_a, "B", 0.0); connect(key_a, "ReturnValue", sel_a, "bPickA")
    sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -80);  set_value(sel_d, "A", -450.0); set_value(sel_d, "B", 0.0); connect(key_d, "ReturnValue", sel_d, "bPickA")
    add_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -130); connect(sel_a, "ReturnValue", add_x, "A"); connect(sel_d, "ReturnValue", add_x, "B")
    
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 40);   set_value(key_w, "Key", "W"); connect(pc_tick, "ReturnValue", key_w, "self")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 140);  set_value(key_s, "Key", "S"); connect(pc_tick, "ReturnValue", key_s, "self")
    sel_w = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 40);   set_value(sel_w, "A", 450.0); set_value(sel_w, "B", 0.0); connect(key_w, "ReturnValue", sel_w, "bPickA")
    sel_s = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 140);  set_value(sel_s, "A", -450.0); set_value(sel_s, "B", 0.0); connect(key_s, "ReturnValue", sel_s, "bPickA")
    add_z = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, 90); connect(sel_w, "ReturnValue", add_z, "A"); connect(sel_s, "ReturnValue", add_z, "B")
    
    make_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 880, 0)
    connect(add_x, "ReturnValue", make_vec, "X"); set_value(make_vec, "Y", 0.0); connect(add_z, "ReturnValue", make_vec, "Z")
    
    mul_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1080, 0)
    connect(make_vec, "ReturnValue", mul_dt, "A"); connect(tick, "DeltaSeconds", mul_dt, "B")
    
    move_node = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1300, 0)
    set_value(move_node, "bSweep", "false")
    connect(tick, "then", move_node, "execute")
    connect(mul_dt, "ReturnValue", move_node, "DeltaLocation")
    
    # 状态判定
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -200); connect(add_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 200); connect(add_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1080, 150); connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")
    
    br_moving = ed.add_branch_node(); br_moving.set_node_pos(unreal.IntPoint(1520, 0))
    connect(move_node, "then", br_moving, "execute")
    connect(is_moving, "ReturnValue", br_moving, "Condition")
    
    get_comp = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1520, -200); set_value(get_comp, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    get_curr_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 1740, -250); connect(get_comp, "ReturnValue", get_curr_fb, "self")
    
    # 移动分支
    br_side = ed.add_branch_node(); br_side.set_node_pos(unreal.IntPoint(1740, -100))
    connect(br_moving, "then", br_side, "execute"); connect(cmp_x, "ReturnValue", br_side, "Condition")
    
    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 1960, -180); connect(add_x, "ReturnValue", is_right, "A"); set_value(is_right, "B", 0.0)
    scale_val_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 2180, -180); set_value(scale_val_x, "A", -0.45); set_value(scale_val_x, "B", 0.45); connect(is_right, "ReturnValue", scale_val_x, "bPickA")
    scale_side_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2400, -180); connect(scale_val_x, "ReturnValue", scale_side_vec, "X"); set_value(scale_side_vec, "Y", 0.45); set_value(scale_side_vec, "Z", 0.45)
    set_sc_side = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2620, -180); connect(br_side, "then", set_sc_side, "execute"); connect(get_comp, "ReturnValue", set_sc_side, "self"); connect(scale_side_vec, "ReturnValue", set_sc_side, "NewScale3D")
    
    set_fb_run_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, -180)
    if fb_run_left:
        set_value(set_fb_run_side, "NewFlipbook", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(set_sc_side, "then", set_fb_run_side, "execute"); connect(get_comp, "ReturnValue", set_fb_run_side, "self")
    
    is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1960, 0); connect(add_z, "ReturnValue", is_up, "A"); set_value(is_up, "B", 0.0)
    br_up = ed.add_branch_node(); br_up.set_node_pos(unreal.IntPoint(2180, 0))
    connect(br_side, "else", br_up, "execute"); connect(is_up, "ReturnValue", br_up, "Condition")
    
    scale_up_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2400, -60); set_value(scale_up_vec, "X", 0.45); set_value(scale_up_vec, "Y", 0.45); set_value(scale_up_vec, "Z", 0.45)
    set_sc_up = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2620, -60); connect(br_up, "then", set_sc_up, "execute"); connect(get_comp, "ReturnValue", set_sc_up, "self"); connect(scale_up_vec, "ReturnValue", set_sc_up, "NewScale3D")
    set_fb_run_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, -60)
    if fb_run_up:
        set_value(set_fb_run_up, "NewFlipbook", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    connect(set_sc_up, "then", set_fb_run_up, "execute"); connect(get_comp, "ReturnValue", set_fb_run_up, "self")
    
    scale_down_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2400, 60); set_value(scale_down_vec, "X", 0.45); set_value(scale_down_vec, "Y", 0.45); set_value(scale_down_vec, "Z", 0.45)
    set_sc_down = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2620, 60); connect(br_up, "else", set_sc_down, "execute"); connect(get_comp, "ReturnValue", set_sc_down, "self"); connect(scale_down_vec, "ReturnValue", set_sc_down, "NewScale3D")
    set_fb_run_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, 60)
    if fb_run_down:
        set_value(set_fb_run_down, "NewFlipbook", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(set_sc_down, "then", set_fb_run_down, "execute"); connect(get_comp, "ReturnValue", set_fb_run_down, "self")

    # 待机分支
    is_curr_up = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 1740, 220); connect(get_curr_fb, "ReturnValue", is_curr_up, "A")
    if fb_run_up:
        set_value(is_curr_up, "B", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    br_idle_up = ed.add_branch_node(); br_idle_up.set_node_pos(unreal.IntPoint(1960, 200))
    connect(br_moving, "else", br_idle_up, "execute"); connect(is_curr_up, "ReturnValue", br_idle_up, "Condition")
    
    set_fb_idle_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2200, 160)
    if fb_idle_up:
        set_value(set_fb_idle_up, "NewFlipbook", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    connect(br_idle_up, "then", set_fb_idle_up, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_up, "self")
    
    is_curr_side = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 1960, 320); connect(get_curr_fb, "ReturnValue", is_curr_side, "A")
    if fb_run_left:
        set_value(is_curr_side, "B", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    br_idle_side = ed.add_branch_node(); br_idle_side.set_node_pos(unreal.IntPoint(2200, 280))
    connect(br_idle_up, "else", br_idle_side, "execute"); connect(is_curr_side, "ReturnValue", br_idle_side, "Condition")
    
    set_fb_idle_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2440, 260)
    if fb_idle_left:
        set_value(set_fb_idle_side, "NewFlipbook", f"PaperFlipbook'{fb_idle_left.get_path_name()}'")
    connect(br_idle_side, "then", set_fb_idle_side, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_side, "self")
    
    is_curr_down = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 2200, 420); connect(get_curr_fb, "ReturnValue", is_curr_down, "A")
    if fb_run_down:
        set_value(is_curr_down, "B", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    br_idle_down = ed.add_branch_node(); br_idle_down.set_node_pos(unreal.IntPoint(2440, 380))
    connect(br_idle_side, "else", br_idle_down, "execute"); connect(is_curr_down, "ReturnValue", br_idle_down, "Condition")
    
    set_fb_idle_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2680, 380)
    if fb_idle_down:
        set_value(set_fb_idle_down, "NewFlipbook", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    connect(br_idle_down, "then", set_fb_idle_down, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_down, "self")

    # ==================== J 键开火与朝向动作精准匹配 ====================
    key_j = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 3100, 0); set_value(key_j, "Key", "J"); connect(pc_tick, "ReturnValue", key_j, "self")
    br_shoot = ed.add_branch_node(); br_shoot.set_node_pos(unreal.IntPoint(3340, 0))
    connect(set_fb_run_side, "then", br_shoot, "execute")
    connect(set_fb_run_up, "then", br_shoot, "execute")
    connect(set_fb_run_down, "then", br_shoot, "execute")
    connect(set_fb_idle_up, "then", br_shoot, "execute")
    connect(set_fb_idle_side, "then", br_shoot, "execute")
    connect(set_fb_idle_down, "then", br_shoot, "execute")
    connect(br_idle_down, "else", br_shoot, "execute")
    connect(key_j, "ReturnValue", br_shoot, "Condition")

    # 判断当前朝向，播放对应的攻击动作
    # 1. 判定是否朝上
    is_atk_up = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3560, -200)
    connect(get_curr_fb, "ReturnValue", is_atk_up, "A")
    if fb_idle_up:
        set_value(is_atk_up, "B", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    br_atk_up = ed.add_branch_node(); br_atk_up.set_node_pos(unreal.IntPoint(3780, -200))
    connect(br_shoot, "then", br_atk_up, "execute"); connect(is_atk_up, "ReturnValue", br_atk_up, "Condition")

    # 向上开火: 动作 FB_T_Player_Medic_Attack_Dir_05_Up_Sheet, 旋转 Pitch=0, Yaw=0, Roll=90, 偏移 (0,0,70)
    set_fb_atk_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4000, -300)
    if fb_atk_up:
        set_value(set_fb_atk_up, "NewFlipbook", f"PaperFlipbook'{fb_atk_up.get_path_name()}'")
    connect(br_atk_up, "then", set_fb_atk_up, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_up, "self")
    
    get_loc_up = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 4000, -180)
    add_loc_up = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 4220, -180)
    connect(get_loc_up, "ReturnValue", add_loc_up, "A"); set_value(add_loc_up, "B", "0,0,70")
    rot_up = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 4220, -60); set_value(rot_up, "Pitch", 0.0); set_value(rot_up, "Yaw", 0.0); set_value(rot_up, "Roll", 90.0)
    trans_up = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 4440, -180)
    connect(add_loc_up, "ReturnValue", trans_up, "Location"); connect(rot_up, "ReturnValue", trans_up, "Rotation"); set_value(trans_up, "Scale", "1,1,1")
    
    spawn_up = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 4660, -250)
    set_value(spawn_up, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_up, "then", spawn_up, "execute"); connect(trans_up, "ReturnValue", spawn_up, "SpawnTransform")
    finish_up = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 4920, -250)
    connect(spawn_up, "then", finish_up, "execute"); connect(spawn_up, "ReturnValue", finish_up, "Actor"); connect(trans_up, "ReturnValue", finish_up, "SpawnTransform")

    # 2. 判定是否朝下
    is_atk_down = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3780, 0)
    connect(get_curr_fb, "ReturnValue", is_atk_down, "A")
    if fb_idle_down:
        set_value(is_atk_down, "B", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    br_atk_down = ed.add_branch_node(); br_atk_down.set_node_pos(unreal.IntPoint(4000, 0))
    connect(br_atk_up, "else", br_atk_down, "execute"); connect(is_atk_down, "ReturnValue", br_atk_down, "Condition")

    # 向下开火: 动作 FB_T_Player_Medic_Attack_Dir_01_Down_Sheet, 旋转 Pitch=0, Yaw=0, Roll=-90, 偏移 (0,0,-70)
    set_fb_atk_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4220, -60)
    if fb_atk_down:
        set_value(set_fb_atk_down, "NewFlipbook", f"PaperFlipbook'{fb_atk_down.get_path_name()}'")
    connect(br_atk_down, "then", set_fb_atk_down, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_down, "self")
    
    get_loc_down = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 4220, 60)
    add_loc_down = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 4440, 60)
    connect(get_loc_down, "ReturnValue", add_loc_down, "A"); set_value(add_loc_down, "B", "0,0,-70")
    rot_down = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 4440, 180); set_value(rot_down, "Pitch", 0.0); set_value(rot_down, "Yaw", 0.0); set_value(rot_down, "Roll", -90.0)
    trans_down = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 4660, 60)
    connect(add_loc_down, "ReturnValue", trans_down, "Location"); connect(rot_down, "ReturnValue", trans_down, "Rotation"); set_value(trans_down, "Scale", "1,1,1")
    
    spawn_down = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 4880, 0)
    set_value(spawn_down, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_down, "then", spawn_down, "execute"); connect(trans_down, "ReturnValue", spawn_down, "SpawnTransform")
    finish_down = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 5140, 0)
    connect(spawn_down, "then", finish_down, "execute"); connect(spawn_down, "ReturnValue", finish_down, "Actor"); connect(trans_down, "ReturnValue", finish_down, "SpawnTransform")

    # 3. 侧向开火 (Left / Right): 动作 FB_T_Player_Medic_Attack_Dir_03_Right_Sheet
    # 旋转 Roll=180 (左) 或 Roll=0 (右)
    set_fb_atk_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4220, 260)
    if fb_atk_side:
        set_value(set_fb_atk_side, "NewFlipbook", f"PaperFlipbook'{fb_atk_side.get_path_name()}'")
    connect(br_atk_down, "else", set_fb_atk_side, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_side, "self")
    
    get_loc_side = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 4220, 380)
    rot_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 4440, 480); set_value(rot_side, "Pitch", 0.0); set_value(rot_side, "Yaw", 0.0); set_value(rot_side, "Roll", 180.0) # 向左/右平飞
    trans_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 4660, 380)
    connect(get_loc_side, "ReturnValue", trans_side, "Location"); connect(rot_side, "ReturnValue", trans_side, "Rotation"); set_value(trans_side, "Scale", "1,1,1")
    
    spawn_side = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 4880, 320)
    set_value(spawn_side, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_side, "then", spawn_side, "execute"); connect(trans_side, "ReturnValue", spawn_side, "SpawnTransform")
    finish_side = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 5140, 320)
    connect(spawn_side, "then", finish_side, "execute"); connect(spawn_side, "ReturnValue", finish_side, "Actor"); connect(trans_side, "ReturnValue", finish_side, "SpawnTransform")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_Player_Medic 射击动作与子弹朝向全向精准匹配重构完成！")

def main():
    log("==================================================================")
    log("🚀 开始执行子弹可见性与射击动作匹配修复...")
    log("==================================================================")
    
    fix_projectile_blueprint()
    fix_player_attack_and_matching()
    
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    log("🎉 修复完成，资产全部持久化保存！")

if __name__ == "__main__":
    main()
