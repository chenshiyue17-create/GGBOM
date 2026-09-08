# -*- coding: utf-8 -*-
"""Canonical Blueprint-only direction-state rebuild for GGBOM.

MoveInput is transient movement input.
FacingDirection is the persistent character-facing direction.
ShotDirection is copied only when firing and owns projectile flight.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import unreal


ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = ROOT / "output" / "direction_state_rebuild_status.json"
PLAYER = "/Game/Blueprints/Player/BP_Player_Medic"
PROJECTILE = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
GAME_MODE = "/Game/GGBOM/Blueprints/BP_GGBOM_GameMode"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)


def pin(node: unreal.K2Node, name: str, output: bool) -> unreal.BlueprintGraphPin:
    values = BPLIB.list_output_pins(node) if output else BPLIB.list_input_pins(node)
    found = [p for p in values if str(PINLIB.get_pin_name(p)).lower() == name.lower()]
    if len(found) != 1:
        available = [str(PINLIB.get_pin_name(p)) for p in values]
        raise RuntimeError(f"Pin {name} missing on {BPLIB.get_node_title(node)}; available={available}")
    return found[0]


def set_value(node: unreal.K2Node, name: str, value: Any) -> None:
    if not PINLIB.set_pin_value(pin(node, name, False), str(value)):
        raise RuntimeError(f"Default rejected: {BPLIB.get_node_title(node)}.{name}={value}")


def connect(a: unreal.K2Node, a_name: str, b: unreal.K2Node, b_name: str) -> None:
    source, target = pin(a, a_name, True), pin(b, b_name, False)
    if not PINLIB.try_create_connection(source, target):
        raise RuntimeError(f"Connection rejected: {BPLIB.get_node_title(a)}.{a_name} -> {BPLIB.get_node_title(b)}.{b_name}")
    if not any(PINLIB.is_same_native_pin(p, target) for p in PINLIB.list_connected_pins(source)):
        raise RuntimeError(f"Connection read-back failed: {a_name} -> {b_name}")


def fn(editor: unreal.BlueprintGraphEditor, path: str, x: int, y: int) -> unreal.K2Node:
    unreal.log(f"[DirectionRebuild] add node {path} at {x},{y}")
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


def component_template(bp: unreal.Blueprint, class_name: str):
    for handle in SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if obj and obj.get_class().get_name() == class_name:
            return obj
    return None


def compile_save_report(bp: unreal.Blueprint, removed: int) -> dict:
    compiled = bool(BPLIB.compile_blueprint(bp))
    editor = event_editor(bp)
    errors = [BPLIB.get_node_title(node) for node in editor.list_nodes_with_errors()]
    saved = bool(ASSETS.save_loaded_asset(bp, only_if_is_dirty=False))
    return {
        "removed_stale_nodes": removed,
        "node_count": len(editor.list_all_nodes()),
        "variables": [str(name) for name in BPLIB.list_member_variable_names(bp, False)],
        "compiled": compiled,
        "compiler_errors": errors,
        "saved": saved,
    }


def rebuild_projectile(vector_type, real_type) -> dict:
    bp = unreal.load_asset(PROJECTILE)
    if not bp:
        raise RuntimeError(f"Missing {PROJECTILE}")
    removed = clean_graph(bp)
    reset_variables(bp, [
        ("ShotDirection", vector_type, "0,0,1"),
        ("ProjectileSpeed", real_type, "900.0"),
    ])
    for variable_name in ("ShotDirection", "ProjectileSpeed"):
        BPLIB.set_blueprint_variable_instance_editable(bp, variable_name, True)
        BPLIB.set_blueprint_variable_expose_on_spawn(bp, variable_name, True)
    if not BPLIB.compile_blueprint(bp):
        raise RuntimeError("Projectile expose-on-spawn compile failed")
    movement = component_template(bp, "ProjectileMovementComponent")
    if movement:
        movement.set_editor_property("auto_activate", False)
        movement.set_editor_property("velocity", unreal.Vector(0, 0, 0))
        movement.set_editor_property("initial_speed", 0.0)
        movement.set_editor_property("max_speed", 0.0)
        movement.set_editor_property("projectile_gravity_scale", 0.0)
    visual = component_template(bp, "PaperFlipbookComponent")
    if visual:
        visual.set_editor_property("relative_scale3d", unreal.Vector(0.03, 0.03, 0.03))
        visual.set_editor_property("translucency_sort_priority", 2800)
        visual.set_editor_property("visible", True)
        visual.set_editor_property("hidden_in_game", False)

    editor = event_editor(bp)
    begin = place(editor.find_event_node("ReceiveBeginPlay"), 0, -180)
    tick = place(editor.find_event_node("ReceiveTick"), 0, 80)
    forward = fn(editor, "/Script/Engine.Actor.GetActorForwardVector", 230, -300)
    set_direction = place(editor.add_set_member_variable_node("ShotDirection"), 450, -180)
    connect(begin, "then", set_direction, "execute")
    connect(forward, "ReturnValue", set_direction, "ShotDirection")
    lifespan = fn(editor, "/Script/Engine.Actor.SetLifeSpan", 680, -180)
    set_value(lifespan, "InLifespan", 3.0)
    connect(set_direction, "then", lifespan, "execute")

    get_direction = place(editor.add_get_member_variable_node("ShotDirection"), 210, 0)
    normalized = fn(editor, "/Script/Engine.KismetMathLibrary.Normal", 430, 0)
    connect(get_direction, "ShotDirection", normalized, "A")
    get_speed = place(editor.add_get_member_variable_node("ProjectileSpeed"), 430, 150)
    velocity = fn(editor, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 650, 40)
    connect(normalized, "ReturnValue", velocity, "A")
    connect(get_speed, "ProjectileSpeed", velocity, "B")
    delta = fn(editor, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 870, 40)
    connect(velocity, "ReturnValue", delta, "A")
    connect(tick, "DeltaSeconds", delta, "B")
    move = fn(editor, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1090, 80)
    set_value(move, "bSweep", "true")
    connect(tick, "then", move, "execute")
    connect(delta, "ReturnValue", move, "DeltaLocation")
    return compile_save_report(bp, removed)


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


def asset_literal(asset: unreal.Object) -> str:
    return f"PaperFlipbook'{asset.get_path_name()}'"


def select_asset(editor, asset_a, asset_b, condition, x, y):
    node = fn(editor, "/Script/Engine.KismetMathLibrary.SelectObject", x, y)
    set_value(node, "A", asset_literal(asset_a))
    set_value(node, "B", asset_literal(asset_b))
    connect(condition, "ReturnValue", node, "bPickA")
    return node


def rebuild_player(vector_type, real_type) -> dict:
    bp = unreal.load_asset(PLAYER)
    if not bp:
        raise RuntimeError(f"Missing {PLAYER}")
    removed = clean_graph(bp)
    reset_variables(bp, [
        ("MoveInput", vector_type, "0,0,0"),
        ("FacingDirection", vector_type, "0,0,1"),
        ("ShotDirection", vector_type, "0,0,1"),
        ("MoveSpeed", real_type, "420.0"),
        ("ProjectileSpeed", real_type, "900.0"),
        ("FireCooldown", real_type, "0.18"),
        ("FireCooldownRemaining", real_type, "0.0"),
    ])
    books = flipbooks()
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        cdo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
        cdo.set_editor_property("auto_receive_input", unreal.AutoReceiveInput.PLAYER0)

    editor = event_editor(bp)
    begin = place(editor.find_event_node("ReceiveBeginPlay"), 0, -620)
    tick = place(editor.find_event_node("ReceiveTick"), 0, 0)
    pc_begin = fn(editor, "/Script/Engine.GameplayStatics.GetPlayerController", 220, -680)
    set_value(pc_begin, "PlayerIndex", 0)
    camera = fn(editor, "/Script/Engine.GameplayStatics.GetActorOfClass", 220, -560)
    set_value(camera, "ActorClass", "Class'/Script/Engine.CameraActor'")
    view = fn(editor, "/Script/Engine.PlayerController.SetViewTargetWithBlend", 480, -620)
    set_value(view, "BlendTime", 0.0)
    connect(begin, "then", camera, "execute")
    connect(camera, "then", view, "execute")
    connect(pc_begin, "ReturnValue", view, "self")
    connect(camera, "ReturnValue", view, "NewViewTarget")

    pc = fn(editor, "/Script/Engine.GameplayStatics.GetPlayerController", 0, -260)
    set_value(pc, "PlayerIndex", 0)
    keys = {}
    for key_name, y in (("A", -320), ("D", -230), ("W", -140), ("S", -50), ("J", 40)):
        key = fn(editor, "/Script/Engine.PlayerController.IsInputKeyDown", 220, y)
        set_value(key, "Key", key_name)
        connect(pc, "ReturnValue", key, "self")
        keys[key_name] = key

    values = {}
    for key_name, value, x, y in (("A", 1.0, 450, -320), ("D", -1.0, 450, -230), ("W", 1.0, 450, -140), ("S", -1.0, 450, -50)):
        select = fn(editor, "/Script/Engine.KismetMathLibrary.SelectFloat", x, y)
        set_value(select, "A", value); set_value(select, "B", 0.0)
        connect(keys[key_name], "ReturnValue", select, "bPickA")
        values[key_name] = select
    raw_x = fn(editor, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 670, -275)
    connect(values["A"], "ReturnValue", raw_x, "A"); connect(values["D"], "ReturnValue", raw_x, "B")
    raw_z = fn(editor, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 670, -95)
    connect(values["W"], "ReturnValue", raw_z, "A"); connect(values["S"], "ReturnValue", raw_z, "B")
    raw = fn(editor, "/Script/Engine.KismetMathLibrary.MakeVector", 890, -185)
    connect(raw_x, "ReturnValue", raw, "X"); set_value(raw, "Y", 0.0); connect(raw_z, "ReturnValue", raw, "Z")
    normalized = fn(editor, "/Script/Engine.KismetMathLibrary.Normal", 1110, -185)
    connect(raw, "ReturnValue", normalized, "A")
    zero = fn(editor, "/Script/Engine.KismetMathLibrary.Vector_IsNearlyZero", 1110, -50)
    connect(raw, "ReturnValue", zero, "A"); set_value(zero, "Tolerance", 0.0001)
    moving = fn(editor, "/Script/Engine.KismetMathLibrary.Not_PreBool", 1330, -50)
    connect(zero, "ReturnValue", moving, "A")

    set_move = place(editor.add_set_member_variable_node("MoveInput"), 1330, -185)
    connect(tick, "then", set_move, "execute")
    connect(normalized, "ReturnValue", set_move, "MoveInput")
    old_facing = place(editor.add_get_member_variable_node("FacingDirection"), 1330, -320)
    retained = fn(editor, "/Script/Engine.KismetMathLibrary.SelectVector", 1550, -240)
    connect(normalized, "ReturnValue", retained, "A")
    connect(old_facing, "FacingDirection", retained, "B")
    connect(moving, "ReturnValue", retained, "bPickA")
    set_facing = place(editor.add_set_member_variable_node("FacingDirection"), 1770, -185)
    connect(set_move, "then", set_facing, "execute")
    connect(retained, "ReturnValue", set_facing, "FacingDirection")

    frame_speed = fn(editor, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1990, -60)
    connect(tick, "DeltaSeconds", frame_speed, "A"); set_value(frame_speed, "B", 420.0)
    delta = fn(editor, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 2210, -120)
    connect(set_move, "Output_Get", delta, "A"); connect(frame_speed, "ReturnValue", delta, "B")
    move = fn(editor, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2430, -185)
    set_value(move, "bSweep", "true")
    connect(set_facing, "then", move, "execute"); connect(delta, "ReturnValue", move, "DeltaLocation")

    facing = place(editor.add_get_member_variable_node("FacingDirection"), 1990, 100)
    split = fn(editor, "/Script/Engine.KismetMathLibrary.BreakVector", 2210, 100)
    connect(facing, "FacingDirection", split, "InVec")
    abs_x = fn(editor, "/Script/Engine.KismetMathLibrary.Abs", 2430, 40); connect(split, "X", abs_x, "A")
    abs_z = fn(editor, "/Script/Engine.KismetMathLibrary.Abs", 2430, 140); connect(split, "Z", abs_z, "A")
    side = fn(editor, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 2650, 80)
    connect(abs_x, "ReturnValue", side, "A"); connect(abs_z, "ReturnValue", side, "B")
    up = fn(editor, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 2650, 180)
    connect(split, "Z", up, "A"); set_value(up, "B", 0.0)
    right = fn(editor, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 2650, -20)
    connect(split, "X", right, "A"); set_value(right, "B", 0.0)
    scale_x = fn(editor, "/Script/Engine.KismetMathLibrary.SelectFloat", 2870, -20)
    set_value(scale_x, "A", -0.45); set_value(scale_x, "B", 0.45); connect(right, "ReturnValue", scale_x, "bPickA")
    scale = fn(editor, "/Script/Engine.KismetMathLibrary.MakeVector", 3090, -20)
    connect(scale_x, "ReturnValue", scale, "X"); set_value(scale, "Y", 0.45); set_value(scale, "Z", 0.45)
    visual = fn(editor, "/Script/Engine.Actor.GetComponentByClass", 2870, -160)
    set_value(visual, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    set_scale = fn(editor, "/Script/Engine.SceneComponent.SetRelativeScale3D", 3310, -185)
    connect(move, "then", set_scale, "execute"); connect(visual, "ReturnValue", set_scale, "self"); connect(scale, "ReturnValue", set_scale, "NewScale3D")

    idle_vertical = select_asset(editor, books["idle_up"], books["idle_down"], up, 2870, 270)
    idle = fn(editor, "/Script/Engine.KismetMathLibrary.SelectObject", 3090, 270)
    set_value(idle, "A", asset_literal(books["idle_side"])); connect(idle_vertical, "ReturnValue", idle, "B"); connect(side, "ReturnValue", idle, "bPickA")
    run_vertical = select_asset(editor, books["run_up"], books["run_down"], up, 2870, 370)
    run = fn(editor, "/Script/Engine.KismetMathLibrary.SelectObject", 3090, 370)
    set_value(run, "A", asset_literal(books["run_side"])); connect(run_vertical, "ReturnValue", run, "B"); connect(side, "ReturnValue", run, "bPickA")
    locomotion = fn(editor, "/Script/Engine.KismetMathLibrary.SelectObject", 3310, 320)
    connect(run, "ReturnValue", locomotion, "A"); connect(idle, "ReturnValue", locomotion, "B"); connect(moving, "ReturnValue", locomotion, "bPickA")
    attack_vertical = select_asset(editor, books["attack_up"], books["attack_down"], up, 3090, 480)
    attack = fn(editor, "/Script/Engine.KismetMathLibrary.SelectObject", 3310, 480)
    set_value(attack, "A", asset_literal(books["attack_side"])); connect(attack_vertical, "ReturnValue", attack, "B"); connect(side, "ReturnValue", attack, "bPickA")
    target = fn(editor, "/Script/Engine.KismetMathLibrary.SelectObject", 3530, 380)
    connect(attack, "ReturnValue", target, "A"); connect(locomotion, "ReturnValue", target, "B"); connect(keys["J"], "ReturnValue", target, "bPickA")
    set_book = fn(editor, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3750, -185)
    connect(set_scale, "then", set_book, "execute"); connect(visual, "ReturnValue", set_book, "self"); connect(target, "ReturnValue", set_book, "NewFlipbook")

    remaining = place(editor.add_get_member_variable_node("FireCooldownRemaining"), 3310, 620)
    subtract = fn(editor, "/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 3530, 620)
    connect(remaining, "FireCooldownRemaining", subtract, "A"); connect(tick, "DeltaSeconds", subtract, "B")
    positive = fn(editor, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 3750, 620)
    connect(subtract, "ReturnValue", positive, "A"); set_value(positive, "B", 0.0)
    clamp = fn(editor, "/Script/Engine.KismetMathLibrary.SelectFloat", 3970, 620)
    connect(subtract, "ReturnValue", clamp, "A"); set_value(clamp, "B", 0.0); connect(positive, "ReturnValue", clamp, "bPickA")
    set_remaining = place(editor.add_set_member_variable_node("FireCooldownRemaining"), 4190, -185)
    connect(set_book, "then", set_remaining, "execute"); connect(clamp, "ReturnValue", set_remaining, "FireCooldownRemaining")
    time_ready = fn(editor, "/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 4190, 80)
    connect(clamp, "ReturnValue", time_ready, "A"); set_value(time_ready, "B", 0.0)
    fire_ready = fn(editor, "/Script/Engine.KismetMathLibrary.BooleanAND", 4410, 40)
    connect(keys["J"], "ReturnValue", fire_ready, "A"); connect(time_ready, "ReturnValue", fire_ready, "B")
    branch = place(editor.add_branch_node(), 4630, -185)
    connect(set_remaining, "then", branch, "execute"); connect(fire_ready, "ReturnValue", branch, "Condition")
    cooldown = place(editor.add_get_member_variable_node("FireCooldown"), 4630, 20)
    reset = place(editor.add_set_member_variable_node("FireCooldownRemaining"), 4850, -185)
    connect(branch, "then", reset, "execute"); connect(cooldown, "FireCooldown", reset, "FireCooldownRemaining")
    facing_at_fire = place(editor.add_get_member_variable_node("FacingDirection"), 4850, 20)
    set_shot = place(editor.add_set_member_variable_node("ShotDirection"), 5070, -185)
    connect(reset, "then", set_shot, "execute"); connect(facing_at_fire, "FacingDirection", set_shot, "ShotDirection")

    actor_location = fn(editor, "/Script/Engine.Actor.K2_GetActorLocation", 5070, 90)
    offset = fn(editor, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 5290, 30)
    connect(set_shot, "Output_Get", offset, "A"); set_value(offset, "B", 40.0)
    muzzle = fn(editor, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 5510, 30)
    connect(actor_location, "ReturnValue", muzzle, "A"); connect(offset, "ReturnValue", muzzle, "B")
    muzzle_height = fn(editor, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 5730, 30)
    connect(muzzle, "ReturnValue", muzzle_height, "A"); set_value(muzzle_height, "B", "0,-5,10")
    rotation = fn(editor, "/Script/Engine.KismetMathLibrary.MakeRotator", 5510, 160)
    set_value(rotation, "Roll", 0.0); set_value(rotation, "Pitch", 0.0); set_value(rotation, "Yaw", 0.0)
    transform = fn(editor, "/Script/Engine.KismetMathLibrary.MakeTransform", 5950, 30)
    connect(muzzle_height, "ReturnValue", transform, "Location"); connect(rotation, "ReturnValue", transform, "Rotation"); set_value(transform, "Scale", "1,1,1")
    spawn = fn(editor, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 6170, -185)
    set_value(spawn, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_shot, "then", spawn, "execute"); connect(transform, "ReturnValue", spawn, "SpawnTransform")
    projectile_class = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C"
    projectile_direction = place(editor.add_set_member_variable_node("ShotDirection", projectile_class), 6410, -185)
    connect(spawn, "then", projectile_direction, "execute"); connect(spawn, "ReturnValue", projectile_direction, "self"); connect(set_shot, "Output_Get", projectile_direction, "ShotDirection")
    projectile_speed = place(editor.add_get_member_variable_node("ProjectileSpeed"), 6170, 70)
    set_projectile_speed = place(editor.add_set_member_variable_node("ProjectileSpeed", projectile_class), 6650, -185)
    connect(projectile_direction, "then", set_projectile_speed, "execute"); connect(spawn, "ReturnValue", set_projectile_speed, "self"); connect(projectile_speed, "ProjectileSpeed", set_projectile_speed, "ProjectileSpeed")
    finish = fn(editor, "/Script/Engine.GameplayStatics.FinishSpawningActor", 6890, -185)
    connect(set_projectile_speed, "then", finish, "execute"); connect(spawn, "ReturnValue", finish, "Actor"); connect(transform, "ReturnValue", finish, "SpawnTransform")
    return compile_save_report(bp, removed)


def main() -> None:
    status = {
        "DIRECTION_STATE_STATUS": "FAIL",
        "pure_blueprint": True,
        "model": {
            "MoveInput": "transient normalized movement input",
            "FacingDirection": "last non-zero input retained for character visuals",
            "ShotDirection": "fire-time snapshot copied into the projectile",
        },
    }
    try:
        vector_type = BPLIB.get_struct_type(unreal.Vector.static_struct())
        real_type = BPLIB.get_basic_type_by_name("real")
        status["projectile"] = rebuild_projectile(vector_type, real_type)
        status["player"] = rebuild_player(vector_type, real_type)
        gm = unreal.load_asset(GAME_MODE)
        if gm:
            gm_cdo = unreal.get_default_object(gm.generated_class())
            player_class = unreal.load_class(None, f"{PLAYER}.BP_Player_Medic_C")
            if gm_cdo and player_class:
                gm_cdo.set_editor_property("default_pawn_class", player_class)
            status["game_mode_compiled"] = bool(BPLIB.compile_blueprint(gm))
            status["game_mode_saved"] = bool(ASSETS.save_loaded_asset(gm, only_if_is_dirty=False))
        status["DIRECTION_STATE_STATUS"] = "PASS" if all((
            status["projectile"]["compiled"], status["projectile"]["saved"], not status["projectile"]["compiler_errors"],
            status["player"]["compiled"], status["player"]["saved"], not status["player"]["compiler_errors"],
        )) else "FAIL"
    except Exception as exc:
        status["error"] = repr(exc)
        unreal.log_error(f"DIRECTION_STATE_REBUILD_FAILED={exc!r}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    unreal.log(f"DIRECTION_STATE_STATUS={status['DIRECTION_STATE_STATUS']}")
    if status["DIRECTION_STATE_STATUS"] != "PASS":
        raise RuntimeError(status.get("error", "direction rebuild validation failed"))


if __name__ == "__main__":
    main()
