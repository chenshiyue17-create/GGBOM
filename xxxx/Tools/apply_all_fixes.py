# -*- coding: utf-8 -*-
"""
================================================================================
apply_all_fixes.py
一站式修复：
1. 玩家移动死锁、按键采样与 8 向动画 (BP_Player_Medic)
2. 自动开火射击循环与子弹生成 (BP_ProjectileBase)
3. 关卡 Boss 头顶血条 Z 轴高度拔高至头顶黄金区域 (Z: 115 -> 245)
4. 编译、关卡保存与实装数据同步回读
================================================================================
"""
from __future__ import annotations
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
import unreal

PROJECT_DIR = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
CONTENT_DIR = PROJECT_DIR / "Content"
DOCS_DIR = PROJECT_DIR.parent / "Docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
PLAYER = "/Game/Blueprints/Player/BP_Player_Medic"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
LEVEL_SUBSYS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUBSYS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def log(msg):
    print(f"[APPLY_ALL_FIXES] {msg}", flush=True)

def pin(node: unreal.K2Node, name: str, output: bool) -> unreal.BlueprintGraphPin:
    values = BPLIB.list_output_pins(node) if output else BPLIB.list_input_pins(node)
    found = [p for p in values if str(PINLIB.get_pin_name(p)).lower() == name.lower()]
    if len(found) != 1:
        available = [str(PINLIB.get_pin_name(p)) for p in values]
        raise RuntimeError(f"Pin {name} missing on {BPLIB.get_node_title(node)}; available={available}")
    return found[0]

def set_value(node: unreal.K2Node, name: str, value) -> None:
    target_pin = pin(node, name, False)
    if not PINLIB.set_pin_value(target_pin, str(value)):
        raise RuntimeError(f"Default rejected: {BPLIB.get_node_title(node)}.{name}={value}")

def connect(a: unreal.K2Node, a_name: str, b: unreal.K2Node, b_name: str) -> None:
    source, target = pin(a, a_name, True), pin(b, b_name, False)
    if not PINLIB.try_create_connection(source, target):
        raise RuntimeError(f"Connection rejected: {BPLIB.get_node_title(a)}.{a_name} -> {BPLIB.get_node_title(b)}.{b_name}")

def fn(editor: unreal.BlueprintGraphEditor, path: str, x: int, y: int) -> unreal.K2Node:
    node = editor.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"Cannot create function node: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

def place(node: unreal.K2Node, x: int, y: int) -> unreal.K2Node:
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

def event_editor(bp: unreal.Blueprint) -> unreal.BlueprintGraphEditor:
    return unreal.BlueprintGraphEditor.get_graph_editor(BPLIB.find_event_graph(bp))

def clean_graph(bp: unreal.Blueprint) -> int:
    editor = event_editor(bp)
    begin = editor.find_event_node("ReceiveBeginPlay")
    tick = editor.find_event_node("ReceiveTick")
    keep = set()
    if begin: keep.add(begin.get_path_name())
    if tick: keep.add(tick.get_path_name())
    all_nodes = editor.list_all_nodes()
    for n in all_nodes:
        if n.get_path_name() not in keep:
            for p in BPLIB.list_all_pins(n):
                try: PINLIB.break_pin_links(p)
                except Exception: pass
    if begin:
        for p in BPLIB.list_all_pins(begin):
            try: PINLIB.break_pin_links(p)
            except Exception: pass
    if tick:
        for p in BPLIB.list_all_pins(tick):
            try: PINLIB.break_pin_links(p)
            except Exception: pass
    stale = [node for node in all_nodes if node.get_path_name() not in keep]
    if stale:
        editor.remove_nodes(stale)
    return len(stale)

def reset_variables(bp: unreal.Blueprint, specs: list[tuple[str, unreal.EdGraphPinType, str]]) -> None:
    editor = event_editor(bp)
    existing = set(str(name) for name in BPLIB.list_member_variable_names(bp, False))
    for name, _pin_type, _default in specs:
        if name in existing:
            editor.remove_member_variable(name)
    BPLIB.compile_blueprint(bp)
    editor = event_editor(bp)
    for name, pin_type, default in specs:
        editor.add_member_variable(name, pin_type, default)
        BPLIB.set_blueprint_variable_category(bp, name, unreal.Text("Gameplay"))
    BPLIB.compile_blueprint(bp)

def link_entry(editor, node):
    start = editor.find_graph_entry_pin()
    target = pin(node, "execute", False)
    if not PINLIB.try_create_connection(start, target):
        raise RuntimeError(f"Cannot connect function entry to {BPLIB.get_node_title(node)}")

def fresh_function(bp, name, real_type=None):
    if name in [str(x) for x in BPLIB.list_graph_names(bp)]:
        BPLIB.remove_function_graph(bp, name)
    editor = unreal.BlueprintGraphEditor.create_and_edit_function_graph(bp, name)
    delta_pin = None
    if real_type is not None:
        delta_pin = editor.add_graph_input_parameter("DeltaSeconds", real_type, "0.0")
    return editor, delta_pin

def function_path(bp, name):
    return f"{bp.generated_class().get_path_name()}:{name}"

def flipbooks() -> dict[str, unreal.PaperFlipbook]:
    root = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    paths = {
        "idle_down": f"{root}/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet",
        "idle_up": f"{root}/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet",
        "idle_side": f"{root}/01_Idle_Run/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet",
        "run_down": f"{root}/01_Idle_Run/Dir_01_Down/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_01_Down_Sheet",
        "run_up": f"{root}/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet",
        "run_side": f"{root}/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet",
    }
    result = {name: unreal.load_asset(path) for name, path in paths.items()}
    return result

def book_literal(book):
    return f"PaperFlipbook'{book.get_path_name()}'"

# -------------------------------------------------------------
# 1. 重建 BP_Player_Medic 移动与自动开火系统
# -------------------------------------------------------------
def build_player():
    log("================ 1. 重构并编译 BP_Player_Medic 核心系统 ================")
    bp = unreal.load_asset(PLAYER)
    if not bp:
        raise RuntimeError(f"未找到 {PLAYER}")

    v_type = BPLIB.get_struct_type(unreal.Vector.static_struct())
    r_type = BPLIB.get_basic_type_by_name("real")

    clean_graph(bp)
    for name in ("SampleMoveInput", "UpdateFacingDirection", "UpdateFacingScale", "UpdateRunAnimation", "UpdateIdleAnimation", "UpdateFireCooldown", "SpawnDirectionalProjectile", "TryFireProjectile"):
        if name in [str(x) for x in BPLIB.list_graph_names(bp)]:
            BPLIB.remove_function_graph(bp, name)

    reset_variables(bp, [
        ("MoveInput", v_type, "0,0,0"),
        ("FacingDirection", v_type, "0,0,1"),
        ("ShotDirection", v_type, "0,0,1"),
        ("MoveSpeed", r_type, "420.0"),
        ("ProjectileSpeed", r_type, "900.0"),
        ("FireCooldown", r_type, "0.18"),
        ("FireCooldownRemaining", r_type, "0.0"),
    ])

    # A. 构建输入采样 SampleMoveInput (WASD + 方向键双支持)
    ed, _ = fresh_function(bp, "SampleMoveInput")
    pc = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, -100)
    set_value(pc, "PlayerIndex", 0)

    key_configs = [
        ("A", "Left", -1.0, "X", 220, -320),
        ("D", "Right", 1.0, "X", 220, -120),
        ("W", "Up", 1.0, "Z", 220, 80),
        ("S", "Down", -1.0, "Z", 220, 280),
    ]
    x_nodes = []
    z_nodes = []
    for k1, k2, val, axis, bx, by in key_configs:
        nk1 = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", bx, by)
        set_value(nk1, "Key", k1)
        connect(pc, "ReturnValue", nk1, "self")
        nk2 = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", bx, by + 70)
        set_value(nk2, "Key", k2)
        connect(pc, "ReturnValue", nk2, "self")
        or_n = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", bx + 220, by + 35)
        connect(nk1, "ReturnValue", or_n, "A")
        connect(nk2, "ReturnValue", or_n, "B")
        sel = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", bx + 440, by + 35)
        set_value(sel, "A", val); set_value(sel, "B", 0.0)
        connect(or_n, "ReturnValue", sel, "bPickA")
        if axis == "X": x_nodes.append(sel)
        else: z_nodes.append(sel)

    add_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 880, -220)
    connect(x_nodes[0], "ReturnValue", add_x, "A"); connect(x_nodes[1], "ReturnValue", add_x, "B")
    add_z = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 880, 180)
    connect(z_nodes[0], "ReturnValue", add_z, "A"); connect(z_nodes[1], "ReturnValue", add_z, "B")

    vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1100, -100)
    connect(add_x, "ReturnValue", vec, "X"); set_value(vec, "Y", 0.0); connect(add_z, "ReturnValue", vec, "Z")

    norm_vec = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 1320, -100)
    connect(vec, "ReturnValue", norm_vec, "A")
    scaled = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1540, -100)
    connect(norm_vec, "ReturnValue", scaled, "A"); set_value(scaled, "B", 7.5)

    is_zero = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_IsNearlyZero", 1320, 60)
    connect(vec, "ReturnValue", is_zero, "A"); set_value(is_zero, "Tolerance", 0.001)

    zero_v = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1540, 60)
    set_value(zero_v, "X", 0.0); set_value(zero_v, "Y", 0.0); set_value(zero_v, "Z", 0.0)

    safe_v = fn(ed, "/Script/Engine.KismetMathLibrary.SelectVector", 1760, -100)
    connect(zero_v, "ReturnValue", safe_v, "A"); connect(scaled, "ReturnValue", safe_v, "B"); connect(is_zero, "ReturnValue", safe_v, "bPickA")

    set_move = place(ed.add_set_member_variable_node("MoveInput"), 1980, -100)
    link_entry(ed, set_move)
    connect(safe_v, "ReturnValue", set_move, "MoveInput")

    # B. 朝向更新 UpdateFacingDirection
    ed, _ = fresh_function(bp, "UpdateFacingDirection")
    move_g = place(ed.add_get_member_variable_node("MoveInput"), 0, -100)
    z_chk = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_IsNearlyZero", 220, -100)
    connect(move_g, "MoveInput", z_chk, "A"); set_value(z_chk, "Tolerance", 0.0001)
    is_mv = fn(ed, "/Script/Engine.KismetMathLibrary.Not_PreBool", 440, -100)
    connect(z_chk, "ReturnValue", is_mv, "A")
    face_g = place(ed.add_get_member_variable_node("FacingDirection"), 220, 20)
    ret_v = fn(ed, "/Script/Engine.KismetMathLibrary.SelectVector", 660, -60)
    connect(move_g, "MoveInput", ret_v, "A"); connect(face_g, "FacingDirection", ret_v, "B"); connect(is_mv, "ReturnValue", ret_v, "bPickA")
    set_face = place(ed.add_set_member_variable_node("FacingDirection"), 880, -60)
    link_entry(ed, set_face)
    connect(ret_v, "ReturnValue", set_face, "FacingDirection")

    # C. 朝向镜像 UpdateFacingScale
    ed, _ = fresh_function(bp, "UpdateFacingScale")
    face_g = place(ed.add_get_member_variable_node("FacingDirection"), 0, -100)
    split = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 220, -100)
    connect(face_g, "FacingDirection", split, "InVec")
    is_left = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 440, -100)
    connect(split, "X", is_left, "A"); set_value(is_left, "B", 0.0)
    sc_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 660, -100)
    set_value(sc_x, "A", -0.45); set_value(sc_x, "B", 0.45); connect(is_left, "ReturnValue", sc_x, "bPickA")
    mk_sc = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 880, -100)
    connect(sc_x, "ReturnValue", mk_sc, "X"); set_value(mk_sc, "Y", 0.45); set_value(mk_sc, "Z", 0.45)
    vis = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 660, 40)
    set_value(vis, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    set_rel_sc = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 1100, -80)
    link_entry(ed, set_rel_sc)
    connect(vis, "ReturnValue", set_rel_sc, "self"); connect(mk_sc, "ReturnValue", set_rel_sc, "NewScale3D")

    # D. 8向动画 UpdateRunAnimation & UpdateIdleAnimation
    books = flipbooks()
    for anim_name, is_run in [("UpdateRunAnimation", True), ("UpdateIdleAnimation", False)]:
        ed, _ = fresh_function(bp, anim_name)
        mv = place(ed.add_get_member_variable_node("MoveInput"), 0, -200)
        z_c = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_IsNearlyZero", 220, -200)
        connect(mv, "MoveInput", z_c, "A"); set_value(z_c, "Tolerance", 0.0001)
        cond = z_c
        if is_run:
            cond = fn(ed, "/Script/Engine.KismetMathLibrary.Not_PreBool", 440, -200)
            connect(z_c, "ReturnValue", cond, "A")
        br = place(ed.add_branch_node(), 660, -120)
        link_entry(ed, br)
        connect(cond, "ReturnValue", br, "Condition")

        fc = place(ed.add_get_member_variable_node("FacingDirection"), 0, -50)
        sp = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 220, -50)
        connect(fc, "FacingDirection", sp, "InVec")
        ax = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 440, -80); connect(sp, "X", ax, "A")
        az = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 440, 10); connect(sp, "Z", az, "A")
        is_side = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 660, -20)
        connect(ax, "ReturnValue", is_side, "A"); connect(az, "ReturnValue", is_side, "B")
        is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 660, 80)
        connect(sp, "Z", is_up, "A"); set_value(is_up, "B", 0.0)

        v_comp = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 660, 190)
        set_value(v_comp, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

        b_side = place(ed.add_branch_node(), 900, -100)
        connect(br, "then", b_side, "execute"); connect(is_side, "ReturnValue", b_side, "Condition")
        
        prefix = "run" if is_run else "idle"
        s_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 1140, -160)
        set_value(s_side, "NewFlipbook", book_literal(books[f"{prefix}_side"]))
        connect(b_side, "then", s_side, "execute"); connect(v_comp, "ReturnValue", s_side, "self")

        b_up = place(ed.add_branch_node(), 1140, 0)
        connect(b_side, "else", b_up, "execute"); connect(is_up, "ReturnValue", b_up, "Condition")
        s_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 1380, -20)
        set_value(s_up, "NewFlipbook", book_literal(books[f"{prefix}_up"]))
        connect(b_up, "then", s_up, "execute"); connect(v_comp, "ReturnValue", s_up, "self")

        s_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 1380, 100)
        set_value(s_down, "NewFlipbook", book_literal(books[f"{prefix}_down"]))
        connect(b_up, "else", s_down, "execute"); connect(v_comp, "ReturnValue", s_down, "self")

    # E. 射击冷却扣减 UpdateFireCooldown
    ed, _ = fresh_function(bp, "UpdateFireCooldown")
    rem = place(ed.add_get_member_variable_node("FireCooldownRemaining"), 0, -80)
    dt = fn(ed, "/Script/Engine.GameplayStatics.GetWorldDeltaSeconds", 0, 50)
    sub_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 220, -80)
    connect(rem, "FireCooldownRemaining", sub_dt, "A"); connect(dt, "ReturnValue", sub_dt, "B")
    is_pos = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 440, 20)
    connect(sub_dt, "ReturnValue", is_pos, "A"); set_value(is_pos, "B", 0.0)
    clamped = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 660, -60)
    connect(sub_dt, "ReturnValue", clamped, "A"); set_value(clamped, "B", 0.0); connect(is_pos, "ReturnValue", clamped, "bPickA")
    set_rem = place(ed.add_set_member_variable_node("FireCooldownRemaining"), 880, -60)
    link_entry(ed, set_rem)
    connect(clamped, "ReturnValue", set_rem, "FireCooldownRemaining")

    # F. 生成朝向子弹 SpawnDirectionalProjectile
    ed, _ = fresh_function(bp, "SpawnDirectionalProjectile")
    loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 0, -150)
    shot_d = place(ed.add_get_member_variable_node("ShotDirection"), 0, -30)
    scaled_shot = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 220, -30)
    connect(shot_d, "ShotDirection", scaled_shot, "A"); set_value(scaled_shot, "B", 40.0)

    muzzle = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 440, -90)
    connect(loc, "ReturnValue", muzzle, "A"); connect(scaled_shot, "ReturnValue", muzzle, "B")
    height = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 660, -90)
    connect(muzzle, "ReturnValue", height, "A"); set_value(height, "B", "0,-5,10")

    rot = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotFromX", 660, 40)
    connect(shot_d, "ShotDirection", rot, "X")
    tf = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 880, -80)
    connect(height, "ReturnValue", tf, "Location"); connect(rot, "ReturnValue", tf, "Rotation"); set_value(tf, "Scale", "1,1,1")

    spawn = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 1100, -80)
    set_value(spawn, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    link_entry(ed, spawn)
    connect(tf, "ReturnValue", spawn, "SpawnTransform")
    finish = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 1360, -80)
    connect(spawn, "then", finish, "execute"); connect(spawn, "ReturnValue", finish, "Actor"); connect(tf, "ReturnValue", finish, "SpawnTransform")

    BPLIB.compile_blueprint(bp)

    # G. 尝试开火判定 TryFireProjectile
    ed, _ = fresh_function(bp, "TryFireProjectile")
    rem_g = place(ed.add_get_member_variable_node("FireCooldownRemaining"), 0, 0)
    ready = fn(ed, "/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 220, 0)
    connect(rem_g, "FireCooldownRemaining", ready, "A"); set_value(ready, "B", 0.0)
    br_fire = place(ed.add_branch_node(), 440, -70)
    link_entry(ed, br_fire); connect(ready, "ReturnValue", br_fire, "Condition")

    cd_g = place(ed.add_get_member_variable_node("FireCooldown"), 440, 60)
    reset_cd = place(ed.add_set_member_variable_node("FireCooldownRemaining"), 660, -70)
    connect(br_fire, "then", reset_cd, "execute"); connect(cd_g, "FireCooldown", reset_cd, "FireCooldownRemaining")

    fc_g = place(ed.add_get_member_variable_node("FacingDirection"), 660, 60)
    set_shot = place(ed.add_set_member_variable_node("ShotDirection"), 880, -70)
    connect(reset_cd, "then", set_shot, "execute"); connect(fc_g, "FacingDirection", set_shot, "ShotDirection")

    spawn_call = fn(ed, function_path(bp, "SpawnDirectionalProjectile"), 1100, -70)
    connect(set_shot, "then", spawn_call, "execute")

    BPLIB.compile_blueprint(bp)

    # H. 装配主 EventGraph
    editor = event_editor(bp)
    begin = place(editor.find_event_node("ReceiveBeginPlay"), 0, -300)
    tick = place(editor.find_event_node("ReceiveTick"), 0, 0)

    # BeginPlay: 锁定正交摄像机视角
    pc_n = fn(editor, "/Script/Engine.GameplayStatics.GetPlayerController", 220, -360)
    set_value(pc_n, "PlayerIndex", 0)
    cam_n = fn(editor, "/Script/Engine.GameplayStatics.GetActorOfClass", 220, -240)
    set_value(cam_n, "ActorClass", "Class'/Script/Engine.CameraActor'")
    view_n = fn(editor, "/Script/Engine.PlayerController.SetViewTargetWithBlend", 460, -300)
    set_value(view_n, "BlendTime", 0.0)
    connect(begin, "then", cam_n, "execute"); connect(cam_n, "then", view_n, "execute")
    connect(pc_n, "ReturnValue", view_n, "self"); connect(cam_n, "ReturnValue", view_n, "NewViewTarget")

    # Tick: 位移应用 (bSweep=false 彻底杜绝卡死)
    move_in = place(editor.add_get_member_variable_node("MoveInput"), 470, 130)
    apply_m = fn(editor, "/Script/Engine.Actor.K2_AddActorWorldOffset", 700, 20)
    set_value(apply_m, "bSweep", "false"); connect(move_in, "MoveInput", apply_m, "DeltaLocation")

    chain_names = [
        "SampleMoveInput",
        "UpdateFacingDirection",
        "UpdateFacingScale",
        "UpdateFireCooldown",
        "UpdateRunAnimation",
        "UpdateIdleAnimation",
        "TryFireProjectile"
    ]
    calls = []
    for idx, cname in enumerate(chain_names):
        calls.append(fn(editor, function_path(bp, cname), 240 + idx * 230, 0))

    connect(tick, "then", calls[0], "execute")
    connect(calls[0], "then", calls[1], "execute")
    connect(calls[1], "then", apply_m, "execute")
    connect(apply_m, "then", calls[2], "execute")
    for prev, cur in zip(calls[2:], calls[3:]):
        connect(prev, "then", cur, "execute")

    # CDO 控制权设定
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        cdo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
        cdo.set_editor_property("auto_receive_input", unreal.AutoReceiveInput.PLAYER0)

    ok = BPLIB.compile_blueprint(bp)
    if not ok:
        raise RuntimeError("BP_Player_Medic 最终编译失败！")
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ [1/2] BP_Player_Medic 移动、动画与自动开火射击已全部编译落盘！")

# -------------------------------------------------------------
# 2. 精准校准关卡 MAP_GGBOM_Main 中 Boss 头顶血条
# -------------------------------------------------------------
def calibrate_boss_healthbar():
    log("================ 2. 校准关卡中 Boss 头顶血条 (Z 轴高度提升至头顶) ================")
    LEVEL_SUBSYS.load_level("/Game/GGBOM/Maps/MAP_GGBOM_Main")
    actors = ACTOR_SUBSYS.get_all_level_actors()

    boss = None
    for a in actors:
        if a.get_actor_label() == "Live_Boss_Overlord":
            boss = a
            break
    if not boss:
        log("⚠️ 未在关卡找到 Live_Boss_Overlord，尝试匹配任何 Boss...")
        for a in actors:
            if "Boss" in a.get_actor_label() and "Bar" not in a.get_actor_label():
                boss = a
                break

    if not boss:
        raise RuntimeError("关卡中未找到 Boss Actor！")

    # 黄金高度：将 Z 轴从腹部的 115 提升到头顶正上方 245
    TARGET_Z = 245.0
    configs = {
        "BossBar_Armor": {
            "rel_loc": unreal.Vector(0.0, -6.0, TARGET_Z),
            "scale": unreal.Vector(0.32, 1.0, 0.30)
        },
        "BossBar_Track": {
            "rel_loc": unreal.Vector(0.0, -10.0, TARGET_Z),
            "scale": unreal.Vector(0.30, 1.0, 0.30)
        },
        "BossBar_Fill": {
            "rel_loc": unreal.Vector(-32.0, -14.0, TARGET_Z),
            "scale": unreal.Vector(0.20, 1.0, 0.16)
        },
        "BossBar_Insignia": {
            "rel_loc": unreal.Vector(-62.0, -18.0, TARGET_Z),
            "scale": unreal.Vector(0.24, 1.0, 0.24)
        }
    }

    found_count = 0
    for a in actors:
        lbl = a.get_actor_label()
        if lbl in configs:
            cfg = configs[lbl]
            root = a.get_editor_property("root_component")
            root.set_mobility(unreal.ComponentMobility.MOVABLE)
            a.set_actor_enable_collision(False)
            a.attach_to_actor(boss, unreal.Name(), unreal.AttachmentRule.KEEP_RELATIVE,
                             unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_WORLD, False)
            root.set_editor_property("relative_location", cfg["rel_loc"])
            a.set_actor_scale3d(cfg["scale"])
            found_count += 1
            log(f"  ⭐ 已将 {lbl} 相对高度校准至头顶: Z={TARGET_Z} (RelLoc={cfg['rel_loc']})")

    log(f"共校准 {found_count} 个血条部件。")
    saved = LEVEL_SUBSYS.save_current_level()
    log(f"✅ [2/2] MAP_GGBOM_Main 关卡保存成功: {saved}")

def main():
    build_player()
    calibrate_boss_healthbar()
    log("🎉 所有实装缺陷修复完成，即将调用同步工具刷新 H5 蓝图审计数据...")

if __name__ == "__main__":
    main()
