# -*- coding: utf-8 -*-
"""Stable modular rebuild of the GGBOM Blueprint direction pipeline."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
BASE_FILE = ROOT / "Content" / "Python" / "rebuild_direction_state.py"
SPEC = importlib.util.spec_from_file_location("ggbom_direction_base", BASE_FILE)
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

OUT = ROOT / "output" / "direction_state_rebuild_status.json"
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

pin = base.pin
set_value = base.set_value
connect = base.connect
fn = base.fn
place = base.place
event_editor = base.event_editor
clean_graph = base.clean_graph
reset_variables = base.reset_variables
compile_save_report = base.compile_save_report


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
    # Standalone is locked to 30 FPS. A 7.5 uu fixed step produces roughly
    # 225 uu/s and avoids UE 5.8's crashing generated multiply nodes.
    # The portrait camera projects world -X toward screen-right, so the
    # horizontal input literals intentionally look reversed in world space.
    for key_name, value, y in (("A", 7.5, -240), ("D", -7.5, -150), ("W", 7.5, -60), ("S", -7.5, 30)):
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
    set_move = place(ed.add_set_member_variable_node("MoveInput"), 1100, -105)
    link_entry(ed, set_move)
    connect(vector, "ReturnValue", set_move, "MoveInput")


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


def build_apply_movement(bp, real_type):
    ed, _ = fresh_function(bp, "ApplyMovement")
    move = place(ed.add_get_member_variable_node("MoveInput"), 0, -140)
    split = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 220, -140)
    connect(move, "MoveInput", split, "InVec")
    speed = place(ed.add_get_member_variable_node("MoveSpeed"), 0, 20)
    delta_seconds = fn(ed, "/Script/Engine.GameplayStatics.GetWorldDeltaSeconds", 0, 100)
    frame_step = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 220, 40)
    connect(speed, "MoveSpeed", frame_step, "A"); connect(delta_seconds, "ReturnValue", frame_step, "B")
    delta_x = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 440, -100)
    connect(split, "X", delta_x, "A"); connect(frame_step, "ReturnValue", delta_x, "B")
    delta_z = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 440, 20)
    connect(split, "Z", delta_z, "A"); connect(frame_step, "ReturnValue", delta_z, "B")
    delta = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 660, -40)
    connect(delta_x, "ReturnValue", delta, "X"); set_value(delta, "Y", 0.0); connect(delta_z, "ReturnValue", delta, "Z")
    apply = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 880, -40)
    set_value(apply, "bSweep", "true")
    link_entry(ed, apply)
    connect(delta, "ReturnValue", apply, "DeltaLocation")


def build_update_scale(bp):
    ed, _ = fresh_function(bp, "UpdateFacingScale")
    facing = place(ed.add_get_member_variable_node("FacingDirection"), 0, -100)
    split = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 220, -100)
    connect(facing, "FacingDirection", split, "InVec")
    right = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 440, -100)
    connect(split, "X", right, "A"); set_value(right, "B", 0.0)
    scale_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 660, -100)
    # Facing -X is screen-right under this camera, and the source side
    # flipbook faces right at negative X scale.
    set_value(scale_x, "A", -0.45); set_value(scale_x, "B", 0.45); connect(right, "ReturnValue", scale_x, "bPickA")
    scale = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 880, -100)
    connect(scale_x, "ReturnValue", scale, "X"); set_value(scale, "Y", 0.45); set_value(scale, "Z", 0.45)
    visual = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 660, 40)
    set_value(visual, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    apply = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 1100, -80)
    link_entry(ed, apply)
    connect(visual, "ReturnValue", apply, "self"); connect(scale, "ReturnValue", apply, "NewScale3D")


def book_literal(book):
    return f"PaperFlipbook'{book.get_path_name()}'"


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
    bp = unreal.load_asset(base.PLAYER)
    if not bp:
        raise RuntimeError(f"Missing {base.PLAYER}")
    removed = clean_graph(bp)
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
    build_sample_move_input(bp)
    build_update_facing(bp)
    build_update_scale(bp)
    books = base.flipbooks()
    build_directional_animation(bp, "UpdateRunAnimation", True, {"side": books["run_side"], "up": books["run_up"], "down": books["run_down"]})
    build_directional_animation(bp, "UpdateIdleAnimation", False, {"side": books["idle_side"], "up": books["idle_up"], "down": books["idle_down"]})
    build_cooldown(bp, real_type)
    build_spawn_projectile(bp)
    if not BPLIB.compile_blueprint(bp):
        raise RuntimeError("Compile failed before building TryFireProjectile")
    build_try_fire(bp)
    if not BPLIB.compile_blueprint(bp):
        raise RuntimeError("Compile failed before wiring EventGraph")

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
    set_value(apply_move, "bSweep", "true"); connect(move_input, "MoveInput", apply_move, "DeltaLocation")

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
    report = compile_save_report(bp, removed)
    report["function_graphs"] = names + ["SpawnDirectionalProjectile"]
    return report


def main():
    status = {
        "DIRECTION_STATE_STATUS": "FAIL",
        "pure_blueprint": True,
        "model": {
            "MoveInput": "current 7.5 uu fixed-frame movement step; zero after release",
            "FacingDirection": "last non-zero MoveInput; never cleared on release",
            "ShotDirection": "snapshot of FacingDirection copied at fire time",
        },
    }
    try:
        vector_type = BPLIB.get_struct_type(unreal.Vector.static_struct())
        real_type = BPLIB.get_basic_type_by_name("real")
        status["projectile"] = base.rebuild_projectile(vector_type, real_type)
        status["player"] = rebuild_player(vector_type, real_type)
        gm = unreal.load_asset(base.GAME_MODE)
        if gm:
            gm_cdo = unreal.get_default_object(gm.generated_class())
            player_class = unreal.load_class(None, f"{base.PLAYER}.BP_Player_Medic_C")
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
        unreal.log_error(f"DIRECTION_STATE_V2_FAILED={exc!r}")
    OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    unreal.log(f"DIRECTION_STATE_STATUS={status['DIRECTION_STATE_STATUS']}")
    if status["DIRECTION_STATE_STATUS"] != "PASS":
        raise RuntimeError(status.get("error", "direction-state validation failed"))


if __name__ == "__main__":
    main()
