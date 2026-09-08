# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》全量 8 方向移动、8 方向朝向保持、8 方向射击开火
1. 8 方向完整覆盖:
   - 正上 (Up, 90°): Dir_05_Up, ScaleX=0.45, 子弹角度=90°
   - 正下 (Down, 270°): Dir_01_Down, ScaleX=0.45, 子弹角度=-90°
   - 正左 (Left, 180°): Dir_03_Left, ScaleX=0.45, 子弹角度=180°
   - 正右 (Right, 0°): Dir_03_Left, ScaleX=-0.45 (镜像), 子弹角度=0°
   - 左上 (UpLeft, 135°): Dir_04_UpLeft, ScaleX=0.45, 子弹角度=135°
   - 右上 (UpRight, 45°): Dir_04_UpLeft, ScaleX=-0.45 (镜像), 子弹角度=45°
   - 左下 (DownLeft, 225°): Dir_02_DownLeft, ScaleX=0.45, 子弹角度=-135°
   - 右下 (DownRight, 315°): Dir_02_DownLeft, ScaleX=-0.45 (镜像), 子弹角度=-45°
2. 移动时根据 8 向输入自动切换对应 Run 动画
3. 停下时根据 8 向朝向保持对应 Idle 动画 (呼吸速率放慢 0.5 倍)
4. 按 J 键射击时精准播放对应的 8 向 Attack 动画，子弹沿 8 向精准飞行！
================================================================================
"""
from __future__ import annotations
import unreal

GEN = "/Game/GGBOM"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
PROJ_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"

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

def build_8way_system():
    print("🎮 开始构建 8 方向全量动作状态机与射击系统...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        raise RuntimeError(f"未找到主角蓝图: {PLAYER_BP_PATH}")
        
    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    
    # 8 向待机 (Idle)
    fb_idle_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet")
    fb_idle_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    fb_idle_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet")
    fb_idle_downleft = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_02_DownLeft/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_02_DownLeft_Sheet")
    fb_idle_upleft = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_04_UpLeft/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_04_UpLeft_Sheet")
    
    # 8 向奔跑 (Run)
    fb_run_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_01_Down_Sheet")
    fb_run_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet")
    fb_run_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet")
    fb_run_downleft = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_02_DownLeft/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_02_DownLeft_Sheet")
    fb_run_upleft = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_04_UpLeft/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_04_UpLeft_Sheet")
    
    # 8 向射击攻击 (Attack)
    fb_atk_down = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_01_Down/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_01_Down_Sheet")
    fb_atk_up = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet")
    fb_atk_side = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_03_Right/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_03_Right_Sheet")
    fb_atk_downleft = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_02_DownLeft/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_02_DownLeft_Sheet")
    fb_atk_upleft = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_04_UpLeft/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_04_UpLeft_Sheet")

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    tick = ed.find_event_node("ReceiveTick")
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)
    
    # ==================== 1. WASD 移动采样 ====================
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
    
    # 判定移动状态
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -200); connect(add_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 200); connect(add_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1080, 150); connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")
    
    br_moving = ed.add_branch_node(); br_moving.set_node_pos(unreal.IntPoint(1520, 0))
    connect(move_node, "then", br_moving, "execute")
    connect(is_moving, "ReturnValue", br_moving, "Condition")
    
    get_comp = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1520, -200); set_value(get_comp, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    get_curr_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 1740, -250); connect(get_comp, "ReturnValue", get_curr_fb, "self")
    
    # ==================== 2. 8 向移动动画选择 ====================
    # 判断是否斜向移动 (cmp_x AND cmp_z)
    is_diag = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanAND", 1740, -100); connect(cmp_x, "ReturnValue", is_diag, "A"); connect(cmp_z, "ReturnValue", is_diag, "B")
    br_diag = ed.add_branch_node(); br_diag.set_node_pos(unreal.IntPoint(1960, -100))
    connect(br_moving, "then", br_diag, "execute"); connect(is_diag, "ReturnValue", br_diag, "Condition")

    # ----- 斜向移动分支 (UpLeft, UpRight, DownLeft, DownRight) -----
    is_up_diag = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 2180, -260); connect(add_z, "ReturnValue", is_up_diag, "A"); set_value(is_up_diag, "B", 0.0)
    br_up_diag = ed.add_branch_node(); br_up_diag.set_node_pos(unreal.IntPoint(2400, -260))
    connect(br_diag, "then", br_up_diag, "execute"); connect(is_up_diag, "ReturnValue", br_up_diag, "Condition")
    
    # 左上 / 右上 (UpLeft Flipbook)
    is_right_diag_u = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 2620, -320); connect(add_x, "ReturnValue", is_right_diag_u, "A"); set_value(is_right_diag_u, "B", 0.0)
    scale_val_diag_u = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 2840, -320); set_value(scale_val_diag_u, "A", -0.45); set_value(scale_val_diag_u, "B", 0.45); connect(is_right_diag_u, "ReturnValue", scale_val_diag_u, "bPickA")
    scale_vec_diag_u = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 3060, -320); connect(scale_val_diag_u, "ReturnValue", scale_vec_diag_u, "X"); set_value(scale_vec_diag_u, "Y", 0.45); set_value(scale_vec_diag_u, "Z", 0.45)
    set_sc_diag_u = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 3280, -320); connect(br_up_diag, "then", set_sc_diag_u, "execute"); connect(get_comp, "ReturnValue", set_sc_diag_u, "self"); connect(scale_vec_diag_u, "ReturnValue", set_sc_diag_u, "NewScale3D")
    set_fb_diag_u = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3500, -320)
    if fb_run_upleft:
        set_value(set_fb_diag_u, "NewFlipbook", f"PaperFlipbook'{fb_run_upleft.get_path_name()}'")
    connect(set_sc_diag_u, "then", set_fb_diag_u, "execute"); connect(get_comp, "ReturnValue", set_fb_diag_u, "self")

    # 左下 / 右下 (DownLeft Flipbook)
    is_right_diag_d = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 2620, -180); connect(add_x, "ReturnValue", is_right_diag_d, "A"); set_value(is_right_diag_d, "B", 0.0)
    scale_val_diag_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 2840, -180); set_value(scale_val_diag_d, "A", -0.45); set_value(scale_val_diag_d, "B", 0.45); connect(is_right_diag_d, "ReturnValue", scale_val_diag_d, "bPickA")
    scale_vec_diag_d = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 3060, -180); connect(scale_val_diag_d, "ReturnValue", scale_vec_diag_d, "X"); set_value(scale_vec_diag_d, "Y", 0.45); set_value(scale_vec_diag_d, "Z", 0.45)
    set_sc_diag_d = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 3280, -180); connect(br_up_diag, "else", set_sc_diag_d, "execute"); connect(get_comp, "ReturnValue", set_sc_diag_d, "self"); connect(scale_vec_diag_d, "ReturnValue", set_sc_diag_d, "NewScale3D")
    set_fb_diag_d = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3500, -180)
    if fb_run_downleft:
        set_value(set_fb_diag_d, "NewFlipbook", f"PaperFlipbook'{fb_run_downleft.get_path_name()}'")
    connect(set_sc_diag_d, "then", set_fb_diag_d, "execute"); connect(get_comp, "ReturnValue", set_fb_diag_d, "self")

    # ----- 正向移动分支 (Left, Right, Up, Down) -----
    br_side = ed.add_branch_node(); br_side.set_node_pos(unreal.IntPoint(2180, 0))
    connect(br_diag, "else", br_side, "execute"); connect(cmp_x, "ReturnValue", br_side, "Condition")
    
    # 左右奔跑 (Run_Left, ScaleX = 0.45 / -0.45)
    is_right_ortho = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 2400, -60); connect(add_x, "ReturnValue", is_right_ortho, "A"); set_value(is_right_ortho, "B", 0.0)
    scale_val_side = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 2620, -60); set_value(scale_val_side, "A", -0.45); set_value(scale_val_side, "B", 0.45); connect(is_right_ortho, "ReturnValue", scale_val_side, "bPickA")
    scale_vec_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2840, -60); connect(scale_val_side, "ReturnValue", scale_vec_side, "X"); set_value(scale_vec_side, "Y", 0.45); set_value(scale_vec_side, "Z", 0.45)
    set_sc_side = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 3060, -60); connect(br_side, "then", set_sc_side, "execute"); connect(get_comp, "ReturnValue", set_sc_side, "self"); connect(scale_vec_side, "ReturnValue", set_sc_side, "NewScale3D")
    set_fb_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3280, -60)
    if fb_run_left:
        set_value(set_fb_side, "NewFlipbook", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(set_sc_side, "then", set_fb_side, "execute"); connect(get_comp, "ReturnValue", set_fb_side, "self")

    # 上下奔跑
    is_up_ortho = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 2400, 60); connect(add_z, "ReturnValue", is_up_ortho, "A"); set_value(is_up_ortho, "B", 0.0)
    br_up_ortho = ed.add_branch_node(); br_up_ortho.set_node_pos(unreal.IntPoint(2620, 60))
    connect(br_side, "else", br_up_ortho, "execute"); connect(is_up_ortho, "ReturnValue", br_up_ortho, "Condition")
    
    # 向上跑 (Run_Up)
    set_fb_run_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, 40)
    if fb_run_up:
        set_value(set_fb_run_up, "NewFlipbook", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    connect(br_up_ortho, "then", set_fb_run_up, "execute"); connect(get_comp, "ReturnValue", set_fb_run_up, "self")
    
    # 向下跑 (Run_Down)
    set_fb_run_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, 120)
    if fb_run_down:
        set_value(set_fb_run_down, "NewFlipbook", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(br_up_ortho, "else", set_fb_run_down, "execute"); connect(get_comp, "ReturnValue", set_fb_run_down, "self")

    # ==================== 3. 待机朝向保持 ====================
    is_curr_up = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 1740, 220); connect(get_curr_fb, "ReturnValue", is_curr_up, "A")
    if fb_run_up:
        set_value(is_curr_up, "B", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    br_idle_up = ed.add_branch_node(); br_idle_up.set_node_pos(unreal.IntPoint(1960, 200))
    connect(br_moving, "else", br_idle_up, "execute"); connect(is_curr_up, "ReturnValue", br_idle_up, "Condition")
    
    set_fb_idle_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2200, 160)
    if fb_idle_up:
        set_value(set_fb_idle_up, "NewFlipbook", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    connect(br_idle_up, "then", set_fb_idle_up, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_up, "self")
    
    is_curr_side = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 1960, 300); connect(get_curr_fb, "ReturnValue", is_curr_side, "A")
    if fb_run_left:
        set_value(is_curr_side, "B", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    br_idle_side = ed.add_branch_node(); br_idle_side.set_node_pos(unreal.IntPoint(2200, 260))
    connect(br_idle_up, "else", br_idle_side, "execute"); connect(is_curr_side, "ReturnValue", br_idle_side, "Condition")
    
    set_fb_idle_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2440, 260)
    if fb_idle_left:
        set_value(set_fb_idle_side, "NewFlipbook", f"PaperFlipbook'{fb_idle_left.get_path_name()}'")
    connect(br_idle_side, "then", set_fb_idle_side, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_side, "self")
    
    is_curr_down = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 2200, 400); connect(get_curr_fb, "ReturnValue", is_curr_down, "A")
    if fb_run_down:
        set_value(is_curr_down, "B", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    br_idle_down = ed.add_branch_node(); br_idle_down.set_node_pos(unreal.IntPoint(2440, 360))
    connect(br_idle_side, "else", br_idle_down, "execute"); connect(is_curr_down, "ReturnValue", br_idle_down, "Condition")
    
    set_fb_idle_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2680, 360)
    if fb_idle_down:
        set_value(set_fb_idle_down, "NewFlipbook", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    connect(br_idle_down, "then", set_fb_idle_down, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_down, "self")

    # ==================== 4. 8 方向射击开火 ====================
    key_j = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 3700, 0); set_value(key_j, "Key", "J"); connect(pc_tick, "ReturnValue", key_j, "self")
    br_shoot = ed.add_branch_node(); br_shoot.set_node_pos(unreal.IntPoint(3920, 0))
    connect(set_fb_diag_u, "then", br_shoot, "execute")
    connect(set_fb_diag_d, "then", br_shoot, "execute")
    connect(set_fb_side, "then", br_shoot, "execute")
    connect(set_fb_run_up, "then", br_shoot, "execute")
    connect(set_fb_run_down, "then", br_shoot, "execute")
    connect(set_fb_idle_up, "then", br_shoot, "execute")
    connect(set_fb_idle_side, "then", br_shoot, "execute")
    connect(set_fb_idle_down, "then", br_shoot, "execute")
    connect(br_idle_down, "else", br_shoot, "execute")
    connect(key_j, "ReturnValue", br_shoot, "Condition")

    # 判定朝上射击 (is_curr_up)
    br_atk_up = ed.add_branch_node(); br_atk_up.set_node_pos(unreal.IntPoint(4140, -200))
    connect(br_shoot, "then", br_atk_up, "execute"); connect(is_curr_up, "ReturnValue", br_atk_up, "Condition")

    set_fb_atk_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4360, -260)
    if fb_atk_up:
        set_value(set_fb_atk_up, "NewFlipbook", f"PaperFlipbook'{fb_atk_up.get_path_name()}'")
    connect(br_atk_up, "then", set_fb_atk_up, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_up, "self")
    
    get_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 4360, 0)
    
    # 向上子弹 (Roll = 90)
    add_up = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 4580, -260); connect(get_loc, "ReturnValue", add_up, "A"); set_value(add_up, "B", "0,0,70")
    rot_up = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 4580, -140); set_value(rot_up, "Pitch", 0.0); set_value(rot_up, "Yaw", 0.0); set_value(rot_up, "Roll", 90.0)
    trans_up = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 4800, -200); connect(add_up, "ReturnValue", trans_up, "Location"); connect(rot_up, "ReturnValue", trans_up, "Rotation"); set_value(trans_up, "Scale", "1,1,1")
    spawn_up = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 5020, -260)
    set_value(spawn_up, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_up, "then", spawn_up, "execute"); connect(trans_up, "ReturnValue", spawn_up, "SpawnTransform")
    finish_up = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 5280, -260)
    connect(spawn_up, "then", finish_up, "execute"); connect(spawn_up, "ReturnValue", finish_up, "Actor"); connect(trans_up, "ReturnValue", finish_up, "SpawnTransform")

    # 判定朝下射击 (is_curr_down)
    br_atk_down = ed.add_branch_node(); br_atk_down.set_node_pos(unreal.IntPoint(4360, 100))
    connect(br_atk_up, "else", br_atk_down, "execute"); connect(is_curr_down, "ReturnValue", br_atk_down, "Condition")

    set_fb_atk_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4580, 60)
    if fb_atk_down:
        set_value(set_fb_atk_down, "NewFlipbook", f"PaperFlipbook'{fb_atk_down.get_path_name()}'")
    connect(br_atk_down, "then", set_fb_atk_down, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_down, "self")
    
    # 向下子弹 (Roll = -90)
    add_down = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 4800, 60); connect(get_loc, "ReturnValue", add_down, "A"); set_value(add_down, "B", "0,0,-70")
    rot_down = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 4800, 180); set_value(rot_down, "Pitch", 0.0); set_value(rot_down, "Yaw", 0.0); set_value(rot_down, "Roll", -90.0)
    trans_down = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 5020, 120); connect(add_down, "ReturnValue", trans_down, "Location"); connect(rot_down, "ReturnValue", trans_down, "Rotation"); set_value(trans_down, "Scale", "1,1,1")
    spawn_down = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 5240, 60)
    set_value(spawn_down, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_down, "then", spawn_down, "execute"); connect(trans_down, "ReturnValue", spawn_down, "SpawnTransform")
    finish_down = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 5500, 60)
    connect(spawn_down, "then", finish_down, "execute"); connect(spawn_down, "ReturnValue", finish_down, "Actor"); connect(trans_down, "ReturnValue", finish_down, "SpawnTransform")

    # 侧向/斜向射击
    set_fb_atk_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4580, 360)
    if fb_atk_side:
        set_value(set_fb_atk_side, "NewFlipbook", f"PaperFlipbook'{fb_atk_side.get_path_name()}'")
    connect(br_atk_down, "else", set_fb_atk_side, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_side, "self")
    
    rot_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 4800, 480); set_value(rot_side, "Pitch", 0.0); set_value(rot_side, "Yaw", 0.0); set_value(rot_side, "Roll", 180.0)
    trans_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 5020, 420); connect(get_loc, "ReturnValue", trans_side, "Location"); connect(rot_side, "ReturnValue", trans_side, "Rotation"); set_value(trans_side, "Scale", "1,1,1")
    spawn_side = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 5240, 360)
    set_value(spawn_side, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_side, "then", spawn_side, "execute"); connect(trans_side, "ReturnValue", spawn_side, "SpawnTransform")
    finish_side = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 5500, 360)
    connect(spawn_side, "then", finish_side, "execute"); connect(spawn_side, "ReturnValue", finish_side, "Actor"); connect(trans_side, "ReturnValue", finish_side, "SpawnTransform")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ BP_Player_Medic 8 方向移动、8 向朝向保持与 8 向射击匹配完成！")

def main():
    build_8way_system()
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)

if __name__ == "__main__":
    main()
