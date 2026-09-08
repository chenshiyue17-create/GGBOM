# -*- coding: utf-8 -*-
"""
BP_Player_Medic 生产构建工具：
包含安全 Normal 向量归一化（步长恒定 7.5 uu/frame）、状态保持与完整 8 向动画绑定。
"""
from __future__ import annotations
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
PLAYER = "/Game/Blueprints/Player/BP_Player_Medic"
ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def log(msg):
    print(f"[REBUILD_MEDIC] {msg}", flush=True)

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
    keep = {begin.get_path_name(), tick.get_path_name()}
    stale = [node for node in editor.list_all_nodes() if node.get_path_name() not in keep]
    if stale:
        editor.remove_nodes(stale)
    return len(stale)

def reset_variables(bp: unreal.Blueprint, specs: list[tuple[str, unreal.EdGraphPinType, str]]) -> None:
    editor = event_editor(bp)
    existing = set(str(name) for name in BPLIB.list_member_variable_names(bp, False))
    for name, _pin_type, _default in specs:
        if name in existing:
            editor.remove_member_variable(name)
    if not BPLIB.compile_blueprint(bp):
        raise RuntimeError(f"Compile failed before variable rebuild: {bp.get_path_name()}")
    editor = event_editor(bp)
    for name, pin_type, default in specs:
        if not editor.add_member_variable(name, pin_type, default):
            raise RuntimeError(f"Cannot create {name} on {bp.get_path_name()}")
        BPLIB.set_blueprint_variable_category(bp, name, unreal.Text("Direction State"))
    if not BPLIB.compile_blueprint(bp):
        raise RuntimeError(f"Compile failed after variable rebuild: {bp.get_path_name()}")

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
        "attack_down": f"{root}/02_Attack_Hurt/Dir_01_Down/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_01_Down_Sheet",
        "attack_up": f"{root}/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet",
        "attack_side": f"{root}/02_Attack_Hurt/Dir_03_Right/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_03_Right_Sheet",
    }
    result = {name: unreal.load_asset(path) for name, path in paths.items()}
    missing = [name for name, asset in result.items() if not asset]
    if missing:
        raise RuntimeError(f"Missing Flipbooks: {missing}")
    return result

def book_literal(book):
    return f"PaperFlipbook'{book.get_path_name()}'"

def build_sample_move_input(bp):
    ed, _ = fresh_function(bp, "SampleMoveInput")
    pc = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, -100)
    set_value(pc, "PlayerIndex", 0)
    keys = {}
    for key_name, y in (("A", -240), ("D", -150), ("W", -60), ("S", 30)):
        key = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, y)
        set_value(key, "Key", key_name)
        connect(pc, "ReturnValue", key, "self")
        keys[key_name] = key
    values = {}
    for key_name, value, y in (("A", -7.5, -240), ("D", 7.5, -150), ("W", 7.5, -60), ("S", -7.5, 30)):
        select = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, y)
        set_value(select, "A", value); set_value(select, "B", 0.0)
        connect(keys[key_name], "ReturnValue", select, "bPickA")
        values[key_name] = select
    x_value = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -195)
    connect(values["A"], "ReturnValue", x_value, "A"); connect(values["D"], "ReturnValue", x_value, "B")
    z_value = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -15)
    connect(values["W"], "ReturnValue", z_value, "A"); connect(values["S"], "ReturnValue", z_value, "B")
    vector = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 880, -105)
    connect(x_value, "ReturnValue", vector, "X"); set_value(vector, "Y", 0.0); connect(z_value, "ReturnValue", vector, "Z")
    
    # 归一化移动输入向量并乘以 7.5 标量
    norm_vec = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 1100, -105)
    connect(vector, "ReturnValue", norm_vec, "A")
    scaled_vec = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1320, -105)
    connect(norm_vec, "ReturnValue", scaled_vec, "A")
    set_value(scaled_vec, "B", 7.5)

    is_zero = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_IsNearlyZero", 1320, 50)
    connect(vector, "ReturnValue", is_zero, "A")
    set_value(is_zero, "Tolerance", 0.001)

    zero_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1540, 50)
    set_value(zero_vec, "X", 0.0); set_value(zero_vec, "Y", 0.0); set_value(zero_vec, "Z", 0.0)

    safe_vec = fn(ed, "/Script/Engine.KismetMathLibrary.SelectVector", 1760, -105)
    connect(zero_vec, "ReturnValue", safe_vec, "A")
    connect(scaled_vec, "ReturnValue", safe_vec, "B")
    connect(is_zero, "ReturnValue", safe_vec, "bPickA")
    
    set_move = place(ed.add_set_member_variable_node("MoveInput"), 1980, -105)
    link_entry(ed, set_move)
    connect(safe_vec, "ReturnValue", set_move, "MoveInput")

def build_update_facing(bp):
    ed, _ = fresh_function(bp, "UpdateFacingDirection")
    move = place(ed.add_get_member_variable_node("MoveInput"), 0, -100)
    zero = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_IsNearlyZero", 220, -100)
    connect(move, "MoveInput", zero, "A"); set_value(zero, "Tolerance", 0.0001)
    moving = fn(ed, "/Script/Engine.KismetMathLibrary.Not_PreBool", 440, -100)
    connect(zero, "ReturnValue", moving, "A")
    facing = place(ed.add_get_member_variable_node("FacingDirection"), 220, 20)
    retained = fn(ed, "/Script/Engine.KismetMathLibrary.SelectVector", 660, -60)
    connect(move, "MoveInput", retained, "A"); connect(facing, "FacingDirection", retained, "B"); connect(moving, "ReturnValue", retained, "bPickA")
    set_facing = place(ed.add_set_member_variable_node("FacingDirection"), 880, -60)
    link_entry(ed, set_facing)
    connect(retained, "ReturnValue", set_facing, "FacingDirection")

def build_update_scale(bp):
    ed, _ = fresh_function(bp, "UpdateFacingScale")
    facing = place(ed.add_get_member_variable_node("FacingDirection"), 0, -100)
    split = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 220, -100)
    connect(facing, "FacingDirection", split, "InVec")
    right = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 440, -100)
    connect(split, "X", right, "A"); set_value(right, "B", 0.0)
    scale_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 660, -100)
    set_value(scale_x, "A", -0.45); set_value(scale_x, "B", 0.45); connect(right, "ReturnValue", scale_x, "bPickA")
    scale = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 880, -100)
    connect(scale_x, "ReturnValue", scale, "X"); set_value(scale, "Y", 0.45); set_value(scale, "Z", 0.45)
    visual = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 660, 40)
    set_value(visual, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    apply = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 1100, -80)
    link_entry(ed, apply)
    connect(visual, "ReturnValue", apply, "self"); connect(scale, "ReturnValue", apply, "NewScale3D")

def build_directional_animation(bp, name, active_when_moving, books):
    ed, _ = fresh_function(bp, name)
    move = place(ed.add_get_member_variable_node("MoveInput"), 0, -210)
    zero = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_IsNearlyZero", 220, -210)
    connect(move, "MoveInput", zero, "A"); set_value(zero, "Tolerance", 0.0001)
    condition = zero
    if active_when_moving:
        condition = fn(ed, "/Script/Engine.KismetMathLibrary.Not_PreBool", 440, -210)
        connect(zero, "ReturnValue", condition, "A")
    active = place(ed.add_branch_node(), 660, -130)
    link_entry(ed, active)
    connect(condition, "ReturnValue", active, "Condition")

    facing = place(ed.add_get_member_variable_node("FacingDirection"), 0, -60)
    split = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 220, -60)
    connect(facing, "FacingDirection", split, "InVec")
    abs_x = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 440, -80); connect(split, "X", abs_x, "A")
    abs_z = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 440, 10); connect(split, "Z", abs_z, "A")
    side = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 660, -20)
    connect(abs_x, "ReturnValue", side, "A"); connect(abs_z, "ReturnValue", side, "B")
    up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 660, 80)
    connect(split, "Z", up, "A"); set_value(up, "B", 0.0)
    visual = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 660, 190)
    set_value(visual, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    side_branch = place(ed.add_branch_node(), 900, -100)
    connect(active, "then", side_branch, "execute"); connect(side, "ReturnValue", side_branch, "Condition")
    set_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 1140, -160)
    set_value(set_side, "NewFlipbook", book_literal(books["side"]))
    connect(side_branch, "then", set_side, "execute"); connect(visual, "ReturnValue", set_side, "self")
    up_branch = place(ed.add_branch_node(), 1140, 0)
    connect(side_branch, "else", up_branch, "execute"); connect(up, "ReturnValue", up_branch, "Condition")
    set_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 1380, -20)
    set_value(set_up, "NewFlipbook", book_literal(books["up"]))
    connect(up_branch, "then", set_up, "execute"); connect(visual, "ReturnValue", set_up, "self")
    set_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 1380, 100)
    set_value(set_down, "NewFlipbook", book_literal(books["down"]))
    connect(up_branch, "else", set_down, "execute"); connect(visual, "ReturnValue", set_down, "self")

def build_cooldown(bp, real_type):
    ed, _ = fresh_function(bp, "UpdateFireCooldown")
    remaining = place(ed.add_get_member_variable_node("FireCooldownRemaining"), 0, -80)
    delta_seconds = fn(ed, "/Script/Engine.GameplayStatics.GetWorldDeltaSeconds", 0, 50)
    subtract = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 220, -80)
    connect(remaining, "FireCooldownRemaining", subtract, "A")
    connect(delta_seconds, "ReturnValue", subtract, "B")
    positive = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 440, 20)
    connect(subtract, "ReturnValue", positive, "A"); set_value(positive, "B", 0.0)
    clamp = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 660, -60)
    connect(subtract, "ReturnValue", clamp, "A"); set_value(clamp, "B", 0.0); connect(positive, "ReturnValue", clamp, "bPickA")
    set_remaining = place(ed.add_set_member_variable_node("FireCooldownRemaining"), 880, -60)
    link_entry(ed, set_remaining)
    connect(clamp, "ReturnValue", set_remaining, "FireCooldownRemaining")

def build_spawn_projectile(bp):
    ed, _ = fresh_function(bp, "SpawnDirectionalProjectile")
    location = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 0, -150)
    shot = place(ed.add_get_member_variable_node("ShotDirection"), 0, -30)
    muzzle = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 440, -90)
    connect(location, "ReturnValue", muzzle, "A"); connect(shot, "ShotDirection", muzzle, "B")
    height = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 660, -90)
    connect(muzzle, "ReturnValue", height, "A"); set_value(height, "B", "0,-5,55")
    rotation = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotFromX", 660, 40)
    connect(shot, "ShotDirection", rotation, "X")
    transform = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 880, -80)
    connect(height, "ReturnValue", transform, "Location"); connect(rotation, "ReturnValue", transform, "Rotation"); set_value(transform, "Scale", "1,1,1")
    spawn = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 1100, -80)
    set_value(spawn, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    link_entry(ed, spawn)
    connect(transform, "ReturnValue", spawn, "SpawnTransform")
    finish = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 1360, -80)
    connect(spawn, "then", finish, "execute"); connect(spawn, "ReturnValue", finish, "Actor"); connect(transform, "ReturnValue", finish, "SpawnTransform")

def build_try_fire(bp):
    ed, _ = fresh_function(bp, "TryFireProjectile")
    remaining = place(ed.add_get_member_variable_node("FireCooldownRemaining"), 0, 0)
    ready = fn(ed, "/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 220, 0)
    connect(remaining, "FireCooldownRemaining", ready, "A"); set_value(ready, "B", 0.0)
    branch = place(ed.add_branch_node(), 440, -70)
    link_entry(ed, branch); connect(ready, "ReturnValue", branch, "Condition")
    cooldown = place(ed.add_get_member_variable_node("FireCooldown"), 440, 60)
    reset = place(ed.add_set_member_variable_node("FireCooldownRemaining"), 660, -70)
    connect(branch, "then", reset, "execute"); connect(cooldown, "FireCooldown", reset, "FireCooldownRemaining")
    facing = place(ed.add_get_member_variable_node("FacingDirection"), 660, 60)
    shot = place(ed.add_set_member_variable_node("ShotDirection"), 880, -70)
    connect(reset, "then", shot, "execute"); connect(facing, "FacingDirection", shot, "ShotDirection")
    spawn = fn(ed, function_path(bp, "SpawnDirectionalProjectile"), 1100, -70)
    connect(shot, "then", spawn, "execute")

def rebuild_player(vector_type, real_type):
    bp = unreal.load_asset(PLAYER)
    if not bp:
        raise RuntimeError(f"Missing {PLAYER}")
    log("1. 清理并重置变量...")
    clean_graph(bp)
    for name in ("SampleMoveInput", "UpdateFacingDirection", "ApplyMovement", "UpdateFacingScale", "UpdateRunAnimation", "UpdateIdleAnimation", "UpdateFireCooldown", "SpawnDirectionalProjectile", "TryFireProjectile"):
        if name in [str(x) for x in BPLIB.list_graph_names(bp)]:
            BPLIB.remove_function_graph(bp, name)
    reset_variables(bp, [
        ("MoveInput", vector_type, "0,0,0"),
        ("FacingDirection", vector_type, "0,0,1"),
        ("ShotDirection", vector_type, "0,0,1"),
        ("MoveSpeed", real_type, "420.0"),
        ("ProjectileSpeed", real_type, "900.0"),
        ("FireCooldown", real_type, "0.18"),
        ("FireCooldownRemaining", real_type, "0.0"),
    ])
    log("2. 构建函数图表...")
    build_sample_move_input(bp)
    build_update_facing(bp)
    build_update_scale(bp)
    books = flipbooks()
    build_directional_animation(bp, "UpdateRunAnimation", True, {"side": books["run_side"], "up": books["run_up"], "down": books["run_down"]})
    build_directional_animation(bp, "UpdateIdleAnimation", False, {"side": books["idle_side"], "up": books["idle_up"], "down": books["idle_down"]})
    build_cooldown(bp, real_type)
    build_spawn_projectile(bp)
    if not BPLIB.compile_blueprint(bp):
        raise RuntimeError("Compile failed before TryFireProjectile")
    build_try_fire(bp)
    if not BPLIB.compile_blueprint(bp):
        raise RuntimeError("Compile failed before EventGraph")

    log("3. 装配 EventGraph...")
    editor = event_editor(bp)
    begin = place(editor.find_event_node("ReceiveBeginPlay"), 0, -300)
    tick = place(editor.find_event_node("ReceiveTick"), 0, 0)
    pc = fn(editor, "/Script/Engine.GameplayStatics.GetPlayerController", 220, -360)
    set_value(pc, "PlayerIndex", 0)
    camera = fn(editor, "/Script/Engine.GameplayStatics.GetActorOfClass", 220, -240)
    set_value(camera, "ActorClass", "Class'/Script/Engine.CameraActor'")
    view = fn(editor, "/Script/Engine.PlayerController.SetViewTargetWithBlend", 460, -300)
    set_value(view, "BlendTime", 0.0)
    connect(begin, "then", camera, "execute"); connect(camera, "then", view, "execute")
    connect(pc, "ReturnValue", view, "self"); connect(camera, "ReturnValue", view, "NewViewTarget")

    move_input = place(editor.add_get_member_variable_node("MoveInput"), 470, 130)
    apply_move = fn(editor, "/Script/Engine.Actor.K2_AddActorWorldOffset", 700, 20)
    set_value(apply_move, "bSweep", "false"); connect(move_input, "MoveInput", apply_move, "DeltaLocation")

    names = ["SampleMoveInput", "UpdateFacingDirection", "UpdateFacingScale", "UpdateFireCooldown", "UpdateRunAnimation", "UpdateIdleAnimation", "TryFireProjectile"]
    calls = []
    for index, name in enumerate(names):
        calls.append(fn(editor, function_path(bp, name), 240 + index * 230, 0))
    connect(tick, "then", calls[0], "execute")
    connect(calls[0], "then", calls[1], "execute")
    connect(calls[1], "then", apply_move, "execute")
    connect(apply_move, "then", calls[2], "execute")
    for previous, current in zip(calls[2:], calls[3:]):
        connect(previous, "then", current, "execute")

    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        cdo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
        cdo.set_editor_property("auto_receive_input", unreal.AutoReceiveInput.PLAYER0)

    log("4. 编译并保存...")
    compile_ok = BPLIB.compile_blueprint(bp)
    if not compile_ok:
        raise RuntimeError("Final compilation failed on BP_Player_Medic")
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    ASSETS.save_directory("/Game/Blueprints/Player", only_if_is_dirty=False, recursive=True)
    log("✅ BP_Player_Medic 编译并落盘完成！")
    return True

if __name__ == "__main__":
    v_type = BPLIB.get_struct_type(unreal.Vector.static_struct())
    r_type = BPLIB.get_basic_type_by_name("real")
    rebuild_player(v_type, r_type)
