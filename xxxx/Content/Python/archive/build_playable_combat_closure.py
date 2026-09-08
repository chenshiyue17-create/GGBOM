"""Build the real combat loop after the direction-state rebuild.

This script intentionally owns only combat actors and the map's dynamic wave
placements.  Player movement/aim/fire stays exclusively in
rebuild_direction_state_v2.py.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output" / "playable_combat_closure.json"
B = unreal.BlueprintEditorLibrary
P = unreal.BlueprintGraphPinLibrary
A = unreal.EditorAssetLibrary

PLAYER = "/Game/Blueprints/Player/BP_Player_Medic"
PROJECTILE = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
ZOMBIE = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
HOUND = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
BOSS = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
MAP = "/Game/GGBOM/Maps/MAP_GGBOM_Main"


def pin(node, name, output):
    pins = B.list_output_pins(node) if output else B.list_input_pins(node)
    for item in pins:
        if str(P.get_pin_name(item)).lower() == name.lower():
            return item
    raise RuntimeError(f"missing pin {name} on {B.get_node_title(node)}")


def connect(a, a_name, b, b_name):
    if not P.try_create_connection(pin(a, a_name, True), pin(b, b_name, False)):
        raise RuntimeError(f"connection failed {B.get_node_title(a)}.{a_name} -> {B.get_node_title(b)}.{b_name}")


def value(node, name, literal):
    if not P.set_pin_value(pin(node, name, False), str(literal)):
        raise RuntimeError(f"literal rejected {B.get_node_title(node)}.{name}={literal}")


def call(ed, path, x, y):
    node = ed.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"cannot create {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node


def clean(bp, wanted_events):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(B.find_event_graph(bp))
    kept = []
    for event in wanted_events:
        node = ed.find_event_node(event)
        if not node:
            node = B.add_event_override(bp, event, unreal.IntPoint(0, 0))
        node.set_node_pos(unreal.IntPoint(0, 0 if event == "ReceiveTick" else -220))
        kept.append(node)
    keep_paths = {node.get_path_name() for node in kept}
    for node in ed.list_all_nodes():
        if node.get_path_name() not in keep_paths:
            for graph_pin in B.list_all_pins(node):
                try:
                    P.break_pin_links(graph_pin)
                except Exception:
                    pass
    stale = [node for node in ed.list_all_nodes() if node.get_path_name() not in keep_paths]
    if stale:
        ed.remove_nodes(stale)
    return ed, {str(B.get_node_title(n)): n for n in kept}


def variable(bp, name, type_, default):
    names = {str(n) for n in B.list_member_variable_names(bp, False)}
    if name not in names:
        ed = unreal.BlueprintGraphEditor.get_graph_editor(B.find_event_graph(bp))
        if not ed.add_member_variable(name, type_, str(default)):
            raise RuntimeError(f"cannot add {name}")


def visual(bp, scale, priority):
    cdo = unreal.get_default_object(bp.generated_class())
    comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
    if not comp:
        comp = cdo.get_component_by_class(unreal.PaperSpriteComponent)
    if comp:
        comp.set_collision_profile_name("OverlapAllDynamic")
        comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
        comp.set_editor_property("generate_overlap_events", True)
        comp.set_editor_property("relative_scale3d", unreal.Vector(scale, scale, scale))
        comp.set_editor_property("translucency_sort_priority", priority)


def build_projectile():
    bp = unreal.load_asset(PROJECTILE)
    visual(bp, 0.12, 2800)
    # Direction script already supplies flight.  Add only overlap hit handling.
    ed, events = clean(bp, ("ReceiveBeginPlay", "ReceiveTick"))
    begin, tick = events["事件BeginPlay"], events["事件Tick"]
    life = call(ed, "/Script/Engine.Actor.SetLifeSpan", 240, -220)
    value(life, "InLifespan", 2.0); connect(begin, "then", life, "execute")
    overlaps = call(ed, "/Script/Engine.Actor.GetOverlappingActors", 220, 80)
    # Any combat enemy inherits no common class; use Actor then allow the
    # target-side health graph to filter projectiles instead.
    count = call(ed, "/Script/Engine.KismetArrayLibrary.Array_Length", 440, 80)
    connect(overlaps, "OverlappingActors", count, "TargetArray")
    has = call(ed, "/Script/Engine.KismetMathLibrary.Greater_IntInt", 650, 80)
    connect(count, "ReturnValue", has, "A"); value(has, "B", 0)
    branch = ed.add_branch_node(); branch.set_node_pos(unreal.IntPoint(860, 0))
    connect(tick, "then", branch, "execute"); connect(has, "ReturnValue", branch, "Condition")
    destroy = call(ed, "/Script/Engine.Actor.K2_DestroyActor", 1080, 0)
    connect(branch, "then", destroy, "execute")
    # Recreate self-owned flight after the hit check, preserving shot snapshot.
    direction = ed.add_get_member_variable_node("ShotDirection"); direction.set_node_pos(unreal.IntPoint(220, 250))
    norm = call(ed, "/Script/Engine.KismetMathLibrary.Normal", 440, 250); connect(direction, "ShotDirection", norm, "A")
    speed = ed.add_get_member_variable_node("ProjectileSpeed"); speed.set_node_pos(unreal.IntPoint(440, 360))
    velocity = call(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 650, 250)
    connect(norm, "ReturnValue", velocity, "A"); connect(speed, "ProjectileSpeed", velocity, "B")
    delta = call(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 860, 250)
    connect(velocity, "ReturnValue", delta, "A"); connect(tick, "DeltaSeconds", delta, "B")
    move = call(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1080, 250)
    value(move, "bSweep", "false"); connect(branch, "else", move, "execute"); connect(delta, "ReturnValue", move, "DeltaLocation")
    if not B.compile_blueprint(bp): raise RuntimeError("projectile compile failed")
    A.save_loaded_asset(bp, only_if_is_dirty=False)


def build_enemy(path, hp, step, scale, priority):
    bp = unreal.load_asset(path)
    real = B.get_basic_type_by_name("real")
    variable(bp, "CurrentHealth", real, hp)
    visual(bp, scale, priority)
    ed, events = clean(bp, ("ReceiveTick",))
    tick = events["事件Tick"]
    move = call(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 240, 0)
    value(move, "DeltaLocation", f"0,0,{-step}"); value(move, "bSweep", "false")
    connect(tick, "then", move, "execute")
    overlap = call(ed, "/Script/Engine.Actor.GetOverlappingActors", 460, 120)
    value(overlap, "ClassFilter", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    length = call(ed, "/Script/Engine.KismetArrayLibrary.Array_Length", 680, 120); connect(overlap, "OverlappingActors", length, "TargetArray")
    has = call(ed, "/Script/Engine.KismetMathLibrary.Greater_IntInt", 880, 120); connect(length, "ReturnValue", has, "A"); value(has, "B", 0)
    hit = ed.add_branch_node(); hit.set_node_pos(unreal.IntPoint(1080, 0)); connect(move, "then", hit, "execute"); connect(has, "ReturnValue", hit, "Condition")
    current = ed.add_get_member_variable_node("CurrentHealth"); current.set_node_pos(unreal.IntPoint(1080, 230))
    damage = call(ed, "/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 1300, 200); connect(current, "CurrentHealth", damage, "A"); value(damage, "B", 30.0)
    set_hp = ed.add_set_member_variable_node("CurrentHealth"); set_hp.set_node_pos(unreal.IntPoint(1520, 0)); connect(hit, "then", set_hp, "execute"); connect(damage, "ReturnValue", set_hp, "CurrentHealth")
    dead = call(ed, "/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 1520, 200); connect(damage, "ReturnValue", dead, "A"); value(dead, "B", 0.0)
    death = ed.add_branch_node(); death.set_node_pos(unreal.IntPoint(1740, 0)); connect(set_hp, "then", death, "execute"); connect(dead, "ReturnValue", death, "Condition")
    destroy = call(ed, "/Script/Engine.Actor.K2_DestroyActor", 1960, 0); connect(death, "then", destroy, "execute")
    if not B.compile_blueprint(bp): raise RuntimeError(f"enemy compile failed {path}")
    A.save_loaded_asset(bp, only_if_is_dirty=False)


def deploy_stage():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if label.startswith("CombatWave_") or label.startswith("Enemy_") or label == "Boss_Overlord_Live":
            unreal.EditorLevelLibrary.destroy_actor(actor)
    layout = [
        (ZOMBIE, "CombatWave_Zombie_01", unreal.Vector(0, 0, 140)),
        (ZOMBIE, "CombatWave_Zombie_02", unreal.Vector(-110, 0, 260)),
        (ZOMBIE, "CombatWave_Zombie_03", unreal.Vector(110, 0, 340)),
        (HOUND, "CombatWave_Hound_01", unreal.Vector(-170, 0, 440)),
        (BOSS, "CombatWave_Boss", unreal.Vector(0, 0, 610)),
    ]
    for path, label, location in layout:
        cls = unreal.load_asset(path).generated_class()
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, location)
        actor.set_actor_label(label)
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)
    return [label for _, label, _ in layout]


def main():
    report = {"PLAYABLE_COMBAT_STATUS":"FAIL", "pure_blueprint":True}
    try:
        build_projectile()
        build_enemy(ZOMBIE, 60.0, 0.55, 0.45, 350)
        build_enemy(HOUND, 90.0, 0.8, 0.50, 360)
        build_enemy(BOSS, 300.0, 0.25, 0.75, 2000)
        report["stage_actors"] = deploy_stage()
        report["PLAYABLE_COMBAT_STATUS"] = "PASS"
    except Exception as exc:
        report["error"] = repr(exc)
        unreal.log_error(f"PLAYABLE_COMBAT_FAILURE={exc!r}")
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    unreal.log(f"PLAYABLE_COMBAT_STATUS={report['PLAYABLE_COMBAT_STATUS']}")
    if report["PLAYABLE_COMBAT_STATUS"] != "PASS": raise RuntimeError(report["error"])


if __name__ == "__main__": main()
