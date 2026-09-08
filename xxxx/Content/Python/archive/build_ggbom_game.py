"""Build the playable GGBOM 2D game using editor Python and runtime Blueprints only.

Runtime contains no Python or C++; this script only authors/imports .uasset files.
All source art is intentionally restricted to Content/美术/Art.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import unreal


ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
ART_ROOT = ROOT / "Content" / "美术" / "Art"
OUT = ROOT / "output"
GEN = "/Game/GGBOM"
ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
PINLIB = unreal.BlueprintGraphPinLibrary
BPLIB = unreal.BlueprintEditorLibrary

SOURCES = {
    "T_Ground": ART_ROOT / "08_Maps/Stage00_Start/T_Map_Stage00_Start_Ground.png",
    "T_Player": ART_ROOT / "01_Player/01_Idle_Run/Dir_05_Up/Idle/T_Player_Medic_Idle_Dir_05_Up_01.png",
    "T_Zombie": ART_ROOT / "02_Enemies/Zombie/01_Zombie_Walker_Basic/T_Zombie_WalkerBasic_01.png",
    "T_Boss": ART_ROOT / "02_Enemies/Boss_Overlord/Actions/Idle/Dir_01_Down/T_Boss_Idle_Dir_01_Down_01.png",
    "T_Bullet": ART_ROOT / "03_Weapons/02_AssaultRifle/T_Bullet_AssaultRifle_02_Flight.png",
    "T_Barrier": ART_ROOT / "04_Props/09_SecurityBarricade/T_Prop_Barricade_01_Intact.png",
    "T_Health": ART_ROOT / "07_UI/01_CombatHUD/T_UI_HUD_01_HealthBar_Fill.png",
    "T_BossBar": ART_ROOT / "07_UI/03_BossHealthBar/T_UI_BossBar_01_Seg1_Fill.png",
}


def log(message: str) -> None:
    unreal.log(f"[GGBOM-Build] {message}")


def ensure(path: str) -> None:
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)


def import_texture(name: str, source: Path) -> unreal.Texture2D:
    if ART_ROOT not in source.parents:
        raise RuntimeError(f"Non-game source rejected: {source}")
    if not source.is_file():
        raise RuntimeError(f"Missing game art: {source}")
    folder = f"{GEN}/Art/Textures"
    ensure(folder)
    path = f"{folder}/{name}"
    if ASSETS.does_asset_exist(path):
        texture = unreal.load_asset(path)
    else:
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", str(source))
        task.set_editor_property("destination_path", folder)
        task.set_editor_property("destination_name", name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)
        TOOLS.import_asset_tasks([task])
        texture = unreal.load_asset(path)
    if not texture:
        raise RuntimeError(f"Texture import failed: {name}")
    texture_group = getattr(unreal.TextureGroup, "TEXTUREGROUP_2D_PIXELS", None) or getattr(unreal.TextureGroup, "TEXTUREGROUP_UI", None)
    properties = [
        ("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON),
        ("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS),
        ("filter", unreal.TextureFilter.TF_BILINEAR),
        ("srgb", True),
    ]
    if texture_group is not None:
        properties.append(("lod_group", texture_group))
    for prop, value in properties:
        try:
            texture.set_editor_property(prop, value)
        except Exception:
            pass
    ASSETS.save_loaded_asset(texture, only_if_is_dirty=False)
    return texture


def make_sprite(name: str, texture: unreal.Texture2D) -> unreal.PaperSprite:
    folder = f"{GEN}/Art/Sprites"
    ensure(folder)
    path = f"{folder}/SP_{name}"
    sprite = unreal.load_asset(path) if ASSETS.does_asset_exist(path) else None
    if not sprite:
        sprite = TOOLS.create_asset(f"SP_{name}", folder, unreal.PaperSprite, unreal.PaperSpriteFactory())
    size_x = float(texture.blueprint_get_size_x())
    size_y = float(texture.blueprint_get_size_y())
    sprite.set_editor_property("source_texture", texture)
    sprite.set_editor_property("source_uv", unreal.Vector2D(0.0, 0.0))
    sprite.set_editor_property("source_dimension", unreal.Vector2D(size_x, size_y))
    try:
        sprite.set_editor_property("source_texture_dimension", unreal.Vector2D(size_x, size_y))
    except Exception:
        pass
    sprite.set_editor_property("pixels_per_unreal_unit", 1.0)
    pivot = getattr(unreal, "SpritePivotMode", getattr(unreal, "PaperSpritePivotMode", None))
    if pivot:
        sprite.set_editor_property("pivot_mode", pivot.CENTER_CENTER)
    material = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    if material:
        sprite.set_editor_property("default_material", material)
    # Force full-frame render geometry to avoid Paper2D Empty bounds.
    try:
        geometry = sprite.get_editor_property("render_geometry")
        geometry.set_editor_property("geometry_type", unreal.SpritePolygonMode.SOURCE_BOUNDING_BOX)
        sprite.set_editor_property("render_geometry", geometry)
    except Exception as exc:
        log(f"render geometry note {name}: {exc}")
    ASSETS.save_loaded_asset(sprite, only_if_is_dirty=False)
    return sprite


def new_bp(name: str, parent: unreal.Class) -> unreal.Blueprint:
    folder = f"{GEN}/Blueprints"
    ensure(folder)
    path = f"{folder}/{name}"
    if ASSETS.does_asset_exist(path):
        ASSETS.delete_asset(path)
    bp = BPLIB.create_blueprint_asset_with_parent(path, parent)
    if not bp:
        raise RuntimeError(f"Blueprint creation failed: {path}")
    BPLIB.compile_blueprint(bp)
    return bp


def add_component(bp: unreal.Blueprint, name: str, cls: unreal.Class) -> unreal.ActorComponent:
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", handles[0])
    params.set_editor_property("new_class", cls)
    params.set_editor_property("blueprint_context", bp)
    handle, reason = SUBOBJECTS.add_new_subobject(params)
    if not unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(handle):
        raise RuntimeError(f"Component {name} failed: {reason}")
    SUBOBJECTS.rename_subobject(handle, unreal.Text(name))
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    component = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    if not component:
        raise RuntimeError(f"Component template missing: {name}")
    return component


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
        raise RuntimeError(f"Default rejected: {name}={value}; type={PINLIB.get_pin_type_display_string(target)}")


def connect(a: unreal.K2Node, a_pin: str, b: unreal.K2Node, b_pin: str) -> None:
    source, target = pin(a, a_pin, True), pin(b, b_pin, False)
    if not PINLIB.try_create_connection(source, target):
        raise RuntimeError(f"Connection rejected: {a_pin} -> {b_pin}")
    forward = PINLIB.list_connected_pins(source)
    reverse = PINLIB.list_connected_pins(target)
    if not any(PINLIB.is_same_native_pin(x, target) for x in forward) or not any(PINLIB.is_same_native_pin(x, source) for x in reverse):
        raise RuntimeError(f"Connection readback failed: {a_pin} -> {b_pin}")


def fn(editor: unreal.BlueprintGraphEditor, path: str, x: int, y: int) -> unreal.K2Node:
    node = editor.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"Function node failed: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node


def compile_save(bp: unreal.Blueprint) -> dict[str, Any]:
    ok = bool(BPLIB.compile_blueprint(bp))
    graph = BPLIB.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    errors = [str(n.error_msg) for n in editor.list_nodes_with_errors()]
    saved = bool(ASSETS.save_loaded_asset(bp, only_if_is_dirty=False))
    if not ok or errors or not saved:
        raise RuntimeError(f"Compile/save failed {bp.get_name()}: ok={ok} errors={errors} saved={saved}")
    connections = 0
    for node in editor.list_all_nodes():
        for p in BPLIB.list_output_pins(node):
            connections += len(PINLIB.list_connected_pins(p))
    return {"asset": bp.get_path_name(), "compiled": ok, "saved": saved, "errors": errors, "connections": connections}


def configure_visual(component: unreal.PaperSpriteComponent, sprite: unreal.PaperSprite, scale: float) -> None:
    component.set_editor_property("source_sprite", sprite)
    component.set_editor_property("relative_scale3d", unreal.Vector(scale, scale, scale))
    component.set_editor_property("cast_shadow", False)
    component.set_editor_property("translucency_sort_priority", 20)


def build_projectile(sprite: unreal.PaperSprite) -> tuple[unreal.Blueprint, dict[str, Any]]:
    bp = new_bp("BP_GGBOM_Projectile", unreal.Actor.static_class())
    collision = add_component(bp, "Collision", unreal.BoxComponent.static_class())
    collision.set_editor_property("box_extent", unreal.Vector(12, 12, 30))
    collision.set_collision_profile_name("OverlapAllDynamic")
    visual = add_component(bp, "Sprite", unreal.PaperSpriteComponent.static_class())
    configure_visual(visual, sprite, 0.35)
    movement = add_component(bp, "ProjectileMovement", unreal.ProjectileMovementComponent.static_class())
    movement.set_editor_property("initial_speed", 1050.0)
    movement.set_editor_property("max_speed", 1050.0)
    movement.set_editor_property("velocity", unreal.Vector(0, 0, 1050))
    movement.set_editor_property("projectile_gravity_scale", 0.0)
    return bp, compile_save(bp)


def build_enemy(sprite: unreal.PaperSprite) -> tuple[unreal.Blueprint, dict[str, Any]]:
    bp = new_bp("BP_GGBOM_Enemy", unreal.Actor.static_class())
    collision = add_component(bp, "Collision", unreal.BoxComponent.static_class())
    collision.set_editor_property("box_extent", unreal.Vector(55, 30, 70))
    collision.set_collision_profile_name("OverlapAllDynamic")
    visual = add_component(bp, "Sprite", unreal.PaperSpriteComponent.static_class())
    configure_visual(visual, sprite, 0.38)
    movement = add_component(bp, "AdvanceMovement", unreal.ProjectileMovementComponent.static_class())
    movement.set_editor_property("initial_speed", 72.0)
    movement.set_editor_property("max_speed", 72.0)
    movement.set_editor_property("velocity", unreal.Vector(0, 0, -72))
    movement.set_editor_property("projectile_gravity_scale", 0.0)
    return bp, compile_save(bp)


def build_player(sprite: unreal.PaperSprite, projectile_bp: unreal.Blueprint, enemy_bp: unreal.Blueprint) -> tuple[unreal.Blueprint, dict[str, Any]]:
    bp = new_bp("BP_GGBOM_Player", unreal.Pawn.static_class())
    collision = add_component(bp, "Collision", unreal.BoxComponent.static_class())
    collision.set_editor_property("box_extent", unreal.Vector(45, 24, 60))
    collision.set_collision_profile_name("Pawn")
    visual = add_component(bp, "Sprite", unreal.PaperSpriteComponent.static_class())
    configure_visual(visual, sprite, 0.38)
    camera = add_component(bp, "Camera", unreal.CameraComponent.static_class())
    camera.set_editor_property("absolute_location", True); camera.set_editor_property("absolute_rotation", True)
    camera.set_editor_property("relative_location", unreal.Vector(0, -500, 0))
    camera.set_editor_property("relative_rotation", unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0))
    camera.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    camera.set_editor_property("ortho_width", 1080.0); camera.set_editor_property("aspect_ratio", 0.5625)
    graph = BPLIB.find_event_graph(bp); ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick = ed.find_event_node("ReceiveTick")
    pc = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0); set_value(pc, "PlayerIndex", 0)
    left = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -80)
    right = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 140)
    set_value(left, "Key", "A"); set_value(right, "Key", "D")
    connect(pc, "ReturnValue", left, "self"); connect(pc, "ReturnValue", right, "self")
    bleft = ed.add_branch_node(); bleft.set_node_pos(unreal.IntPoint(470, -80))
    bright = ed.add_branch_node(); bright.set_node_pos(unreal.IntPoint(470, 180))
    connect(tick, "then", bleft, "execute"); connect(left, "ReturnValue", bleft, "Condition")
    connect(bleft, "else", bright, "execute"); connect(right, "ReturnValue", bright, "Condition")
    for branch, direction, ypos in ((bleft, -420, -100), (bright, 420, 200)):
        vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 700, ypos)
        set_value(vec, "X", direction); set_value(vec, "Y", 0); set_value(vec, "Z", 0)
        mul = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 900, ypos)
        move = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1120, ypos)
        set_value(move, "bSweep", "true")
        connect(vec, "ReturnValue", mul, "A"); connect(tick, "DeltaSeconds", mul, "B")
        connect(branch, "then", move, "execute"); connect(mul, "ReturnValue", move, "DeltaLocation")
    begin = ed.find_event_node("ReceiveBeginPlay")
    intro = fn(ed, "/Script/Engine.KismetSystemLibrary.PrintString", 200, -420)
    set_value(intro, "InString", "GGBOM READY | A/D MOVE | AUTO FIRE | SURVIVE 40 SEC"); set_value(intro, "Duration", 6.0)
    timer = fn(ed, "/Script/Engine.KismetSystemLibrary.K2_SetTimer", 450, -420)
    set_value(timer, "FunctionName", "AutoFire"); set_value(timer, "Time", 4.0); set_value(timer, "bLooping", "true")
    check_timer = fn(ed, "/Script/Engine.KismetSystemLibrary.K2_SetTimer", 700, -420)
    set_value(check_timer, "FunctionName", "CheckBase"); set_value(check_timer, "Time", 0.25); set_value(check_timer, "bLooping", "true")
    win_timer = fn(ed, "/Script/Engine.KismetSystemLibrary.K2_SetTimer", 950, -420)
    set_value(win_timer, "FunctionName", "WinRound"); set_value(win_timer, "Time", 40.0); set_value(win_timer, "bLooping", "false")
    connect(begin, "then", intro, "execute"); connect(intro, "then", timer, "execute")
    connect(timer, "then", check_timer, "execute"); connect(check_timer, "then", win_timer, "execute")
    auto = ed.add_custom_event_node("AutoFire"); auto.set_node_pos(unreal.IntPoint(0, 520))
    get_target = fn(ed, "/Script/Engine.GameplayStatics.GetActorOfClass", 220, 450)
    enemy_class_value = f"BlueprintGeneratedClass'{enemy_bp.get_path_name()}.{enemy_bp.get_name()}_C'"
    set_value(get_target, "ActorClass", enemy_class_value)
    target_valid = fn(ed, "/Script/Engine.KismetSystemLibrary.IsValid", 450, 380)
    fire_branch = ed.add_branch_node(); fire_branch.set_node_pos(unreal.IntPoint(650, 450))
    destroy_target = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 470, 450)
    destroy_target.set_node_pos(unreal.IntPoint(900, 450))
    connect(auto, "then", get_target, "execute")
    connect(get_target, "ReturnValue", target_valid, "Object")
    connect(get_target, "then", fire_branch, "execute")
    connect(target_valid, "ReturnValue", fire_branch, "Condition")
    connect(fire_branch, "then", destroy_target, "execute")
    connect(get_target, "ReturnValue", destroy_target, "self")
    location = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 470, 620)
    offset = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 470, 760)
    set_value(offset, "X", 0); set_value(offset, "Y", 0); set_value(offset, "Z", 100)
    add = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 440, 560)
    transform = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 650, 560)
    spawn = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 870, 520)
    finish = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 1120, 520)
    class_value = f"BlueprintGeneratedClass'{projectile_bp.get_path_name()}.{projectile_bp.get_name()}_C'"
    set_value(spawn, "ActorClass", class_value)
    connect(location, "ReturnValue", add, "A"); connect(offset, "ReturnValue", add, "B")
    connect(add, "ReturnValue", transform, "Location"); connect(transform, "ReturnValue", spawn, "SpawnTransform")
    connect(destroy_target, "then", spawn, "execute"); connect(spawn, "then", finish, "execute")
    connect(spawn, "ReturnValue", finish, "Actor"); connect(transform, "ReturnValue", finish, "SpawnTransform")
    check = ed.add_custom_event_node("CheckBase"); check.set_node_pos(unreal.IntPoint(0, 980))
    nearest = fn(ed, "/Script/Engine.GameplayStatics.GetActorOfClass", 220, 980); set_value(nearest, "ActorClass", enemy_class_value)
    nearest_valid = fn(ed, "/Script/Engine.KismetSystemLibrary.IsValid", 450, 840)
    valid_branch = ed.add_branch_node(); valid_branch.set_node_pos(unreal.IntPoint(660, 840))
    enemy_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 470, 920)
    player_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 470, 1080)
    distance = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_Distance", 700, 980)
    close = fn(ed, "/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 900, 980)
    danger = ed.add_branch_node(); danger.set_node_pos(unreal.IntPoint(1100, 980))
    lose = fn(ed, "/Script/Engine.GameplayStatics.OpenLevel", 1320, 980); set_value(lose, "LevelName", "MAP_GGBOM_Lose")
    connect(check, "then", nearest, "execute")
    connect(nearest, "ReturnValue", nearest_valid, "Object")
    connect(nearest, "then", valid_branch, "execute")
    connect(nearest_valid, "ReturnValue", valid_branch, "Condition")
    connect(nearest, "ReturnValue", enemy_loc, "self")
    connect(enemy_loc, "ReturnValue", distance, "V1"); connect(player_loc, "ReturnValue", distance, "V2")
    connect(distance, "ReturnValue", close, "A"); set_value(close, "B", 125.0)
    connect(valid_branch, "then", danger, "execute"); connect(close, "ReturnValue", danger, "Condition")
    connect(danger, "then", lose, "execute")
    win_event = ed.add_custom_event_node("WinRound"); win_event.set_node_pos(unreal.IntPoint(0, 1320))
    win = fn(ed, "/Script/Engine.GameplayStatics.OpenLevel", 250, 1320); set_value(win, "LevelName", "MAP_GGBOM_Win")
    connect(win_event, "then", win, "execute")
    return bp, compile_save(bp)


def build_manager() -> tuple[unreal.Blueprint, dict[str, Any]]:
    bp = new_bp("BP_GGBOM_GameManager", unreal.Actor.static_class())
    graph = BPLIB.find_event_graph(bp); ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    begin = ed.find_event_node("ReceiveBeginPlay")
    intro = fn(ed, "/Script/Engine.KismetSystemLibrary.PrintString", 240, -100)
    set_value(intro, "InString", "GGBOM READY | A/D MOVE | AUTO FIRE | SURVIVE 40 SEC")
    set_value(intro, "Duration", 6.0)
    timer = fn(ed, "/Script/Engine.KismetSystemLibrary.K2_SetTimer", 500, -100)
    set_value(timer, "FunctionName", "WinRound"); set_value(timer, "Time", 40.0); set_value(timer, "bLooping", "false")
    win_event = ed.add_custom_event_node("WinRound"); win_event.set_node_pos(unreal.IntPoint(520, 180))
    win = fn(ed, "/Script/Engine.GameplayStatics.OpenLevel", 780, 180); set_value(win, "LevelName", "MAP_GGBOM_Win")
    connect(begin, "then", intro, "execute"); connect(intro, "then", timer, "execute")
    connect(win_event, "then", win, "execute")
    return bp, compile_save(bp)


def build_end_manager() -> tuple[unreal.Blueprint, dict[str, Any]]:
    bp = new_bp("BP_GGBOM_EndManager", unreal.Actor.static_class())
    graph = BPLIB.find_event_graph(bp); ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    begin = ed.find_event_node("ReceiveBeginPlay")
    timer = fn(ed, "/Script/Engine.KismetSystemLibrary.K2_SetTimer", 250, 0)
    set_value(timer, "FunctionName", "RestartRound"); set_value(timer, "Time", 6.0); set_value(timer, "bLooping", "false")
    restart_event = ed.add_custom_event_node("RestartRound"); restart_event.set_node_pos(unreal.IntPoint(250, 260))
    restart = fn(ed, "/Script/Engine.GameplayStatics.OpenLevel", 520, 260); set_value(restart, "LevelName", "MAP_GGBOM_Main")
    connect(begin, "then", timer, "execute"); connect(restart_event, "then", restart, "execute")
    return bp, compile_save(bp)


def build_gamemode(player_bp: unreal.Blueprint) -> tuple[unreal.Blueprint, dict[str, Any]]:
    bp = new_bp("BP_GGBOM_GameMode", unreal.GameModeBase.static_class())
    BPLIB.compile_blueprint(bp)
    cls = unreal.load_class(None, f"{bp.get_path_name()}.{bp.get_name()}_C")
    if not cls:
        raise RuntimeError("GameMode generated class unavailable after compile")
    cdo = unreal.get_default_object(cls)
    player_cls = unreal.load_class(None, f"{player_bp.get_path_name()}.{player_bp.get_name()}_C")
    cdo.set_editor_property("default_pawn_class", player_cls)
    cdo.set_editor_property("start_players_as_spectators", False)
    return bp, compile_save(bp)


def spawn_text(text: str, loc: unreal.Vector, size: float, color: unreal.Color) -> unreal.TextRenderActor:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.TextRenderActor, loc, unreal.Rotator(pitch=0.0, yaw=-90.0, roll=0.0)
    )
    comp = actor.get_component_by_class(unreal.TextRenderComponent)
    comp.set_editor_property("text", unreal.Text(text))
    comp.set_editor_property("world_size", size)
    comp.set_editor_property("text_render_color", color)
    comp.set_editor_property("translucency_sort_priority", 100)
    return actor


def spawn_sprite(sprite: unreal.PaperSprite, loc: unreal.Vector, scale: float, priority: int = 0) -> unreal.PaperSpriteActor:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, loc, unreal.Rotator())
    component = actor.get_component_by_class(unreal.PaperSpriteComponent)
    if not component:
        raise RuntimeError("PaperSpriteActor missing PaperSpriteComponent")
    component.set_editor_property("source_sprite", sprite)
    component.set_editor_property("translucency_sort_priority", priority)
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    return actor


def spawn_camera() -> unreal.CameraActor:
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(0, -500, 0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    component = camera.get_component_by_class(unreal.CameraComponent)
    if not component:
        raise RuntimeError("CameraActor missing CameraComponent")
    component.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    component.set_editor_property("ortho_width", 1080.0)
    component.set_editor_property("aspect_ratio", 0.5625)
    camera.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    camera.set_actor_label("PortraitCamera_9x16")
    return camera


def save_map(path: str) -> None:
    if not unreal.EditorLoadingAndSavingUtils.save_map( unreal.EditorLevelLibrary.get_editor_world(), path):
        raise RuntimeError(f"Map save failed: {path}")


def build_main_map(sprites: dict[str, unreal.PaperSprite], player_bp: unreal.Blueprint, enemy_bp: unreal.Blueprint, game_mode_bp: unreal.Blueprint) -> None:
    ensure(f"{GEN}/Maps")
    unreal.EditorLevelLibrary.new_level(f"{GEN}/Maps/MAP_GGBOM_Main")
    world = unreal.EditorLevelLibrary.get_editor_world()
    settings = world.get_world_settings()
    settings.set_editor_property("default_game_mode", unreal.load_class(None, f"{game_mode_bp.get_path_name()}.{game_mode_bp.get_name()}_C"))
    spawn_camera()
    ground = spawn_sprite(sprites["Ground"], unreal.Vector(0, 80, 0), 1.15, -100); ground.set_actor_label("Ground_FROM_ART_ONLY")
    spawn_sprite(sprites["Boss"], unreal.Vector(0, 20, 610), 0.46, 10).set_actor_label("BossVisual")
    spawn_sprite(sprites["Barrier"], unreal.Vector(0, 15, 330), 0.62, 5).set_actor_label("DefenseLine")
    unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -10, -590), unreal.Rotator())
    enemy_cls = unreal.load_class(None, f"{enemy_bp.get_path_name()}.{enemy_bp.get_name()}_C")
    positions = [(-300,720),(-150,660),(0,760),(150,650),(300,710),(-240,470),(-80,520),(100,450),(260,540),(-330,300),(330,280)]
    for i, (x, z) in enumerate(positions):
        enemy = unreal.EditorLevelLibrary.spawn_actor_from_class(enemy_cls, unreal.Vector(x, 0, z), unreal.Rotator())
        enemy.set_actor_label(f"Enemy_{i+1:02d}")
    white, red, blue, amber = unreal.Color(245,245,245,255), unreal.Color(245,45,45,255), unreal.Color(35,190,255,255), unreal.Color(255,190,35,255)
    spawn_text("BOSS", unreal.Vector(0,-60,890), 58, white)
    spawn_text("██████████", unreal.Vector(0,-60,820), 44, red)
    spawn_text("BOSS ZONE\nZ5\nZ4\nZ3\nZ2\n◆ Z1", unreal.Vector(-455,-60,310), 39, blue)
    spawn_text("TACTICAL\nBARRIER x8\nBARREL x6\nTOXIC x5\nMINE x7\nMEDKIT x4", unreal.Vector(420,-60,-40), 27, white)
    spawn_text("HP 1200/1200     LV.10", unreal.Vector(-270,-60,-790), 30, red)
    spawn_text("[1] AUTO RIFLE   [2] SHOTGUN   [3] ROCKET   [4] TESLA", unreal.Vector(80,-60,-865), 25, amber)
    spawn_text("A / D 移动  ·  自动射击  ·  坚守 40 秒", unreal.Vector(0,-60,-930), 22, blue)
    save_map(f"{GEN}/Maps/MAP_GGBOM_Main")


def build_end_map(name: str, title: str, subtitle: str, color: unreal.Color, game_mode_bp: unreal.Blueprint) -> None:
    unreal.EditorLevelLibrary.new_level(f"{GEN}/Maps/{name}")
    world = unreal.EditorLevelLibrary.get_editor_world()
    world.get_world_settings().set_editor_property("default_game_mode", unreal.GameModeBase.static_class())
    spawn_camera()
    spawn_text(title, unreal.Vector(0,-60,120), 110, color)
    spawn_text(subtitle, unreal.Vector(0,-60,-40), 42, unreal.Color(245,245,245,255))
    spawn_text("重新运行即可开始新战局", unreal.Vector(0,-60,-180), 28, unreal.Color(35,190,255,255))
    save_map(f"{GEN}/Maps/{name}")


def main() -> None:
    started = time.time(); OUT.mkdir(parents=True, exist_ok=True)
    for source in SOURCES.values():
        if ART_ROOT not in source.parents:
            raise RuntimeError("Asset policy violation")
    textures = {name: import_texture(name, path) for name, path in SOURCES.items()}
    sprites = {name.removeprefix("T_"): make_sprite(name.removeprefix("T_"), tex) for name, tex in textures.items()}
    projectile_bp, projectile_report = build_projectile(sprites["Bullet"])
    enemy_bp, enemy_report = build_enemy(sprites["Zombie"])
    player_bp, player_report = build_player(sprites["Player"], projectile_bp, enemy_bp)
    game_mode_bp, mode_report = build_gamemode(player_bp)
    build_main_map(sprites, player_bp, enemy_bp, game_mode_bp)
    build_end_map("MAP_GGBOM_Win", "MISSION COMPLETE", "终末医疗兵守住了防线", unreal.Color(60,220,120,255), game_mode_bp)
    build_end_map("MAP_GGBOM_Lose", "DEFENSE FAILED", "感染者突破了最后防线", unreal.Color(245,45,45,255), game_mode_bp)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    report = {
        "success": True,
        "runtime": "100% Blueprint/Paper2D; editor Python is authoring-only",
        "source_policy": str(ART_ROOT),
        "source_files": {k: str(v) for k,v in SOURCES.items()},
        "blueprints": [projectile_report, enemy_report, player_report, mode_report],
        "maps": [f"{GEN}/Maps/MAP_GGBOM_Main", f"{GEN}/Maps/MAP_GGBOM_Win", f"{GEN}/Maps/MAP_GGBOM_Lose"],
        "elapsed_seconds": round(time.time()-started, 2),
    }
    (OUT / "ggbom_build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log("GGBOM_BUILD_OK")


if __name__ == "__main__":
    main()
