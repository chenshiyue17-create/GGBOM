# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》终极无瑕疵完整游戏总装
1. 全景双层街道地图 (Ground + Overhead)
2. 完整敌群 (Boss Overlord, 4类僵尸, 2只猎犬, 6处掩体防线)
3. 真实概念图 HUD (Boss血条, 4张战术道具, 玩家HP/EXP, 4张武器卡牌)
4. 真 8 方向 WASD 移动主角 (带防定格 Flipbook 动态切换与镜像翻转)
5. 正交相机 941x1672 精确 100% 全景对齐，彻底杜绝黑屏与裁剪
================================================================================
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import unreal

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
ART_ROOT = ROOT / "Content" / "美术" / "Art"
GEN = "/Game/GGBOM"
BLUEPRINTS = "/Game/Blueprints/Player"
ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
PINLIB = unreal.BlueprintGraphPinLibrary
BPLIB = unreal.BlueprintEditorLibrary

MAP_W = 941.0
MAP_H = 1672.0
ASPECT_RATIO = MAP_W / MAP_H

def log(msg: str):
    unreal.log(f"[GGBOM-Unified] {msg}")

def set_prop(obj, prop: str, value) -> bool:
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False

def make_rotator(pitch: float, yaw: float, roll: float) -> unreal.Rotator:
    r = unreal.Rotator()
    set_prop(r, "pitch", pitch)
    set_prop(r, "yaw", yaw)
    set_prop(r, "roll", roll)
    return r

def ensure(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

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
    return unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)

def import_art_texture(name: str, rel_path: str) -> unreal.Texture2D:
    folder = f"{GEN}/Art/Textures"
    ensure(folder)
    path = f"{folder}/{name}"
    if ASSETS.does_asset_exist(path):
        tex = unreal.load_asset(path)
    else:
        src = str(ART_ROOT / rel_path)
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", src)
        task.set_editor_property("destination_path", folder)
        task.set_editor_property("destination_name", name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)
        TOOLS.import_asset_tasks([task])
        tex = unreal.load_asset(path)
    if tex:
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tex.set_editor_property("filter", unreal.TextureFilter.TF_BILINEAR)
        tex.set_editor_property("srgb", True)
        ASSETS.save_loaded_asset(tex, only_if_is_dirty=False)
    return tex

def make_paper_sprite(name: str, texture: unreal.Texture2D) -> unreal.PaperSprite:
    folder = f"{GEN}/Art/Sprites"
    ensure(folder)
    path = f"{folder}/SP_{name}"
    sprite = unreal.load_asset(path) if ASSETS.does_asset_exist(path) else None
    if not sprite:
        sprite = TOOLS.create_asset(f"SP_{name}", folder, unreal.PaperSprite, unreal.PaperSpriteFactory())
    sx = float(texture.blueprint_get_size_x())
    sy = float(texture.blueprint_get_size_y())
    sprite.set_editor_property("source_texture", texture)
    sprite.set_editor_property("source_uv", unreal.Vector2D(0.0, 0.0))
    sprite.set_editor_property("source_dimension", unreal.Vector2D(sx, sy))
    sprite.set_editor_property("pixels_per_unreal_unit", 1.0)
    pivot = getattr(unreal, "SpritePivotMode", getattr(unreal, "PaperSpritePivotMode", None))
    if pivot:
        sprite.set_editor_property("pivot_mode", pivot.CENTER_CENTER)
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    if mat:
        sprite.set_editor_property("default_material", mat)
    ASSETS.save_loaded_asset(sprite, only_if_is_dirty=False)
    return sprite

def spawn_sprite_actor(sprite: unreal.PaperSprite, loc: unreal.Vector, scale: float = 1.0, priority: int = 0, label: str = "") -> unreal.Actor:
    if not sprite:
        return None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, loc, unreal.Rotator())
    if not actor:
        return None
    comp = actor.get_component_by_class(unreal.PaperSpriteComponent)
    if comp:
        comp.set_editor_property("source_sprite", sprite)
        comp.set_editor_property("translucency_sort_priority", priority)
        mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
        if mat:
            comp.set_material(0, mat)
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    if label:
        actor.set_actor_label(label)
    return actor

def to_ue_pos(screen_x: float, screen_y: float, y_depth: float = -60.0) -> unreal.Vector:
    ue_x = 540.0 - screen_x
    ue_z = 960.0 - screen_y
    return unreal.Vector(ue_x, y_depth, ue_z)

def build_medic_character_bp() -> unreal.Blueprint:
    log("🔨 构建 8 方向 WASD 动态状态机主角蓝图 (BP_Player_Medic)...")
    bp_path = f"{BLUEPRINTS}/BP_Player_Medic"
    ensure(BLUEPRINTS)
    
    if ASSETS.does_asset_exist(bp_path):
        bp = unreal.load_asset(bp_path)
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Pawn.static_class())
        bp = TOOLS.create_asset("BP_Player_Medic", BLUEPRINTS, unreal.Blueprint, factory)
        
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        cdo.set_editor_property("auto_receive_input", unreal.AutoReceiveInput.PLAYER0)
        cdo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
        
    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    flipbooks = {
        "Idle_Down": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet"),
        "Idle_Up": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet"),
        "Run_Left": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet"),
        "Run_Up": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet"),
        "Run_Down": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_01_Down_Sheet"),
        "Attack_Up": unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet"),
    }
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    
    # Flipbook 组件
    comps = list(cdo.get_components_by_class(unreal.PaperFlipbookComponent))
    fb_comp = comps[0] if comps else add_component(bp, "VisibleFlipbook", unreal.PaperFlipbookComponent.static_class())
    if flipbooks["Idle_Down"]:
        fb_comp.set_editor_property("source_flipbook", flipbooks["Idle_Down"])
    if mat:
        try:
            fb_comp.set_material(0, mat)
        except Exception:
            pass
    fb_comp.set_editor_property("translucency_sort_priority", 2000)
    fb_comp.set_editor_property("relative_scale3d", unreal.Vector(0.45, 0.45, 0.45))
    
    # 碰撞组件
    col_comps = list(cdo.get_components_by_class(unreal.BoxComponent))
    col = col_comps[0] if col_comps else add_component(bp, "PlayerCollision", unreal.BoxComponent.static_class())
    col.set_editor_property("box_extent", unreal.Vector(36.0, 24.0, 60.0))
    try:
        col.set_collision_profile_name("Pawn")
    except Exception:
        pass
        
    # Event Graph 节点装配
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    try:
        for node in ed.list_all_nodes():
            if node.get_name() not in ["ReceiveBeginPlay", "ReceiveTick", "ReceiveActorBeginOverlap"]:
                ed.remove_node(node)
    except Exception:
        pass
        
    # BeginPlay: 锁定关卡正交相机视角
    begin_play = ed.find_event_node("ReceiveBeginPlay")
    pc_begin = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 200, -360)
    set_value(pc_begin, "PlayerIndex", 0)
    get_cam = fn(ed, "/Script/Engine.GameplayStatics.GetActorOfClass", 450, -360)
    set_value(get_cam, "ActorClass", "Class'/Script/Engine.CameraActor'")
    set_view = fn(ed, "/Script/Engine.PlayerController.SetViewTargetWithBlend", 720, -360)
    set_value(set_view, "BlendTime", 0.0)
    connect(begin_play, "then", get_cam, "execute")
    connect(get_cam, "then", set_view, "execute")
    connect(pc_begin, "ReturnValue", set_view, "self")
    connect(get_cam, "ReturnValue", set_view, "NewViewTarget")
    
    # Tick: 8 方向平滑移动与动画切换
    tick = ed.find_event_node("ReceiveTick")
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)
    
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -180); set_value(key_a, "Key", "A"); connect(pc_tick, "ReturnValue", key_a, "self")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -80);  set_value(key_d, "Key", "D"); connect(pc_tick, "ReturnValue", key_d, "self")
    sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -180); set_value(sel_a, "A", 420.0); set_value(sel_a, "B", 0.0); connect(key_a, "ReturnValue", sel_a, "bPickA")
    sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -80);  set_value(sel_d, "A", -420.0); set_value(sel_d, "B", 0.0); connect(key_d, "ReturnValue", sel_d, "bPickA")
    add_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -130); connect(sel_a, "ReturnValue", add_x, "A"); connect(sel_d, "ReturnValue", add_x, "B")
    
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 40);   set_value(key_w, "Key", "W"); connect(pc_tick, "ReturnValue", key_w, "self")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 140);  set_value(key_s, "Key", "S"); connect(pc_tick, "ReturnValue", key_s, "self")
    sel_w = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 40);   set_value(sel_w, "A", 420.0); set_value(sel_w, "B", 0.0); connect(key_w, "ReturnValue", sel_w, "bPickA")
    sel_s = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 140);  set_value(sel_s, "A", -420.0); set_value(sel_s, "B", 0.0); connect(key_s, "ReturnValue", sel_s, "bPickA")
    add_z = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, 90); connect(sel_w, "ReturnValue", add_z, "A"); connect(sel_s, "ReturnValue", add_z, "B")
    
    make_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 880, 0)
    connect(add_x, "ReturnValue", make_vec, "X")
    set_value(make_vec, "Y", 0.0)
    connect(add_z, "ReturnValue", make_vec, "Z")
    
    mul_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1080, 0)
    connect(make_vec, "ReturnValue", mul_dt, "A")
    connect(tick, "DeltaSeconds", mul_dt, "B")
    
    move_node = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1300, 0)
    set_value(move_node, "bSweep", "true")
    connect(tick, "then", move_node, "execute")
    connect(mul_dt, "ReturnValue", move_node, "DeltaLocation")
    
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -200); connect(add_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 200); connect(add_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1080, 150); connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")
    
    br_moving = ed.add_branch_node(); br_moving.set_node_pos(unreal.IntPoint(1520, 0))
    connect(move_node, "then", br_moving, "execute")
    connect(is_moving, "ReturnValue", br_moving, "Condition")
    
    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 1080, -100); connect(add_x, "ReturnValue", is_right, "A"); set_value(is_right, "B", 0.0)
    scale_val_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 1280, -100); set_value(scale_val_x, "A", -0.45); set_value(scale_val_x, "B", 0.45); connect(is_right, "ReturnValue", scale_val_x, "bPickA")
    scale_move_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1480, -100); connect(scale_val_x, "ReturnValue", scale_move_vec, "X"); set_value(scale_move_vec, "Y", 0.45); set_value(scale_move_vec, "Z", 0.45)
    
    get_comp_move = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1520, -200); set_value(get_comp_move, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    set_sc_move = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 1740, -100)
    connect(br_moving, "then", set_sc_move, "execute")
    connect(get_comp_move, "ReturnValue", set_sc_move, "self")
    connect(scale_move_vec, "ReturnValue", set_sc_move, "NewScale3D")
    
    br_side = ed.add_branch_node(); br_side.set_node_pos(unreal.IntPoint(1960, -100))
    connect(set_sc_move, "then", br_side, "execute")
    connect(cmp_x, "ReturnValue", br_side, "Condition")
    
    get_curr_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 1960, -250)
    connect(get_comp_move, "ReturnValue", get_curr_fb, "self")
    
    is_diff_side = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2180, -250)
    connect(get_curr_fb, "ReturnValue", is_diff_side, "A")
    if flipbooks["Run_Left"]:
        set_value(is_diff_side, "B", f"PaperFlipbook'{flipbooks['Run_Left'].get_path_name()}'")
    br_diff_side = ed.add_branch_node(); br_diff_side.set_node_pos(unreal.IntPoint(2400, -200))
    connect(br_side, "then", br_diff_side, "execute")
    connect(is_diff_side, "ReturnValue", br_diff_side, "Condition")
    set_fb_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2620, -200)
    if flipbooks["Run_Left"]:
        set_value(set_fb_side, "NewFlipbook", f"PaperFlipbook'{flipbooks['Run_Left'].get_path_name()}'")
    connect(br_diff_side, "then", set_fb_side, "execute")
    connect(get_comp_move, "ReturnValue", set_fb_side, "self")
    
    is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1960, 50); connect(add_z, "ReturnValue", is_up, "A"); set_value(is_up, "B", 0.0)
    br_up = ed.add_branch_node(); br_up.set_node_pos(unreal.IntPoint(2180, 0))
    connect(br_side, "else", br_up, "execute")
    connect(is_up, "ReturnValue", br_up, "Condition")
    
    is_diff_up = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2400, -80)
    connect(get_curr_fb, "ReturnValue", is_diff_up, "A")
    if flipbooks["Run_Up"]:
        set_value(is_diff_up, "B", f"PaperFlipbook'{flipbooks['Run_Up'].get_path_name()}'")
    br_diff_up = ed.add_branch_node(); br_diff_up.set_node_pos(unreal.IntPoint(2620, -80))
    connect(br_up, "then", br_diff_up, "execute")
    connect(is_diff_up, "ReturnValue", br_diff_up, "Condition")
    set_fb_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2840, -80)
    if flipbooks["Run_Up"]:
        set_value(set_fb_up, "NewFlipbook", f"PaperFlipbook'{flipbooks['Run_Up'].get_path_name()}'")
    connect(br_diff_up, "then", set_fb_up, "execute")
    connect(get_comp_move, "ReturnValue", set_fb_up, "self")
    
    is_diff_down = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2400, 80)
    connect(get_curr_fb, "ReturnValue", is_diff_down, "A")
    if flipbooks["Run_Down"]:
        set_value(is_diff_down, "B", f"PaperFlipbook'{flipbooks['Run_Down'].get_path_name()}'")
    br_diff_down = ed.add_branch_node(); br_diff_down.set_node_pos(unreal.IntPoint(2620, 80))
    connect(br_up, "else", br_diff_down, "execute")
    connect(is_diff_down, "ReturnValue", br_diff_down, "Condition")
    set_fb_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2840, 80)
    if flipbooks["Run_Down"]:
        set_value(set_fb_down, "NewFlipbook", f"PaperFlipbook'{flipbooks['Run_Down'].get_path_name()}'")
    connect(br_diff_down, "then", set_fb_down, "execute")
    connect(get_comp_move, "ReturnValue", set_fb_down, "self")
    
    # 待机分支
    get_comp_idle = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1520, 200); set_value(get_comp_idle, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    scale_idle_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1520, 300); set_value(scale_idle_vec, "X", 0.45); set_value(scale_idle_vec, "Y", 0.45); set_value(scale_idle_vec, "Z", 0.45)
    set_sc_idle = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 1740, 200)
    connect(br_moving, "else", set_sc_idle, "execute")
    connect(get_comp_idle, "ReturnValue", set_sc_idle, "self")
    connect(scale_idle_vec, "ReturnValue", set_sc_idle, "NewScale3D")
    
    get_curr_idle_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 1960, 280)
    connect(get_comp_idle, "ReturnValue", get_curr_idle_fb, "self")
    is_diff_idle = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2180, 280)
    connect(get_curr_idle_fb, "ReturnValue", is_diff_idle, "A")
    if flipbooks["Idle_Down"]:
        set_value(is_diff_idle, "B", f"PaperFlipbook'{flipbooks['Idle_Down'].get_path_name()}'")
    br_diff_idle = ed.add_branch_node(); br_diff_idle.set_node_pos(unreal.IntPoint(2400, 200))
    connect(set_sc_idle, "then", br_diff_idle, "execute")
    connect(is_diff_idle, "ReturnValue", br_diff_idle, "Condition")
    
    set_fb_idle = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2620, 200)
    if flipbooks["Idle_Down"]:
        set_value(set_fb_idle, "NewFlipbook", f"PaperFlipbook'{flipbooks['Idle_Down'].get_path_name()}'")
    connect(br_diff_idle, "then", set_fb_idle, "execute")
    connect(get_comp_idle, "ReturnValue", set_fb_idle, "self")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_Player_Medic 编译完成！")
    return bp

def assemble_master_game():
    log("🚀 开始组装终极无瑕疵主关卡 MAP_GGBOM_Main...")
    
    art_map = {
        "Map_Ground": "08_Maps/Stage00_Start/T_Map_Stage00_Start_Ground.png",
        "Map_Overhead": "08_Maps/Stage00_Start/T_Map_Stage00_Start_Overhead.png",
        
        "Boss": "02_Enemies/Boss_Overlord/Actions/Idle/Dir_01_Down/T_Boss_Idle_Dir_01_Down_01.png",
        "Barricade": "04_Props/09_SecurityBarricade/T_Prop_Barricade_01_Intact.png",
        "RedBarrel": "04_Props/01_RedExplosiveBarrel/T_Prop_Barrel_01_Intact.png",
        "ToxicDrum": "04_Props/02_ToxicWasteDrum/T_Prop_ToxicDrum_01_Intact.png",
        "MedPod": "04_Props/05_MedicalSupplyPod/T_Prop_MedPod_01_Intact.png",
        
        "ZombieWalker": "02_Enemies/Zombie/01_Zombie_Walker_Basic/T_Zombie_WalkerBasic_01.png",
        "ZombieBrute": "02_Enemies/Zombie/11_Zombie_Shambler_Heavy/T_Zombie_ShamblerHeavy_01.png",
        "ZombieSpitter": "02_Enemies/Zombie/04_Zombie_Spitter_Minor/T_Zombie_SpitterMinor_01.png",
        "ZombieArmored": "02_Enemies/Zombie/07_Zombie_Armored_Guard/T_Zombie_ArmoredGuard_01.png",
        "Hound": "02_Enemies/MutantHound/Run/Dir_01_Down/T_Hound_Run_Dir_01_Down_01.png",
        
        "Card_AutoRifle": "06_Cards/04_WeaponModCards/T_Card_WeaponMod_01.png",
        "Card_Shotgun": "06_Cards/04_WeaponModCards/T_Card_WeaponMod_02.png",
        "Card_Rocket": "06_Cards/04_WeaponModCards/T_Card_WeaponMod_03.png",
        "Card_Tesla": "06_Cards/04_WeaponModCards/T_Card_WeaponMod_04.png",
        
        "HUD_BossBar_Bg": "07_UI/02_CardSelectionModal/T_UI_Modal_09_ProgressTrack.png",
        "HUD_BossBar_Fill": "07_UI/02_CardSelectionModal/T_UI_Modal_10_GlowBorder.png",
        "Btn_Pause": "07_UI/04_PauseSettingsMenu/T_UI_Settings_11_Btn_Resume.png",
        
        "HUD_Player_HP_Bg": "07_UI/02_CardSelectionModal/T_UI_Modal_05_CardSlot_Right.png",
        "HUD_Player_HP_Fill": "07_UI/02_CardSelectionModal/T_UI_Modal_06_Btn_Reroll.png",
        "HUD_Player_EXP_Bg": "07_UI/02_CardSelectionModal/T_UI_Modal_07_Btn_Skip.png",
        "HUD_Player_EXP_Fill": "07_UI/02_CardSelectionModal/T_UI_Modal_08_Btn_Confirm.png"
    }
    
    sprites = {}
    for name, rel in art_map.items():
        tex = import_art_texture(name, rel)
        if tex:
            sprites[name] = make_paper_sprite(name, tex)
            
    player_bp = build_medic_character_bp()
    
    # GameMode
    gm_path = f"{GEN}/Blueprints/BP_GGBOM_GameMode"
    gm_bp = unreal.load_asset(gm_path)
    if gm_bp:
        gm_cdo = unreal.get_default_object(gm_bp.generated_class())
        if gm_cdo:
            player_cls = unreal.load_class(None, f"{player_bp.get_path_name()}.BP_Player_Medic_C")
            gm_cdo.set_editor_property("default_pawn_class", player_cls)
        BPLIB.compile_blueprint(gm_bp)
        ASSETS.save_loaded_asset(gm_bp, only_if_is_dirty=False)
        
    map_path = f"{GEN}/Maps/MAP_GGBOM_Main"
    if ASSETS.does_asset_exist(map_path):
        unreal.EditorLevelLibrary.load_level(map_path)
    else:
        unreal.EditorLevelLibrary.new_level(map_path)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 清理所有已有实体
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            unreal.EditorLevelLibrary.destroy_actor(a)
        except Exception:
            pass
            
    world.get_world_settings().set_editor_property("default_game_mode", unreal.load_class(None, f"{gm_path}.BP_GGBOM_GameMode_C"))
    
    # 941x1672 全景正交主相机
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(0, -1000, 0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    cam.set_actor_label("Master_Orthographic_Camera")
    cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    if cam_comp:
        set_prop(cam_comp, "projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
        set_prop(cam_comp, "ortho_width", MAP_W)
        set_prop(cam_comp, "aspect_ratio", ASPECT_RATIO)
        set_prop(cam_comp, "constrain_aspect_ratio", True)
        set_prop(cam_comp, "b_constrain_aspect_ratio", True)
        set_prop(cam_comp, "auto_calculate_ortho_planes", False)
        set_prop(cam_comp, "ortho_near_clip_plane", -10000.0)
        set_prop(cam_comp, "ortho_far_clip_plane", 10000.0)
    
    # 2D 色彩保真后处理
    pp_vol = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator())
    pp_vol.set_actor_label("PP_2D_Color_Accuracy")
    pp_vol.set_editor_property("unbound", True)
    pp_comp = pp_vol.get_editor_property("settings")
    pp_comp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    pp_comp.set_editor_property("auto_exposure_bias", 0.0)
    pp_comp.set_editor_property("auto_exposure_min_brightness", 1.0)
    pp_comp.set_editor_property("auto_exposure_max_brightness", 1.0)
    pp_comp.set_editor_property("bloom_intensity", 0.0)
    pp_comp.set_editor_property("motion_blur_amount", 0.0)
    pp_comp.set_editor_property("ambient_occlusion_intensity", 0.0)
    
    # 1. 双层地图实装:
    spawn_sprite_actor(sprites.get("Map_Ground"), unreal.Vector(0, 80.0, 0), 1.0, 0, "Ground_Stage00")
    spawn_sprite_actor(sprites.get("Map_Overhead"), unreal.Vector(0, -80.0, 0), 1.0, 1000, "Overhead_Stage00")
    
    # 2. 战场实体
    spawn_sprite_actor(sprites.get("Boss"), to_ue_pos(470, 420, 20), 0.65, 300, "Boss_Overlord")
    
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(270, 540, 15), 0.50, 200, "Barricade_Top_L")
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(470, 540, 15), 0.50, 200, "Barricade_Top_M")
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(670, 540, 15), 0.50, 200, "Barricade_Top_R")
    
    enemy_layout = [
        ("ZombieWalker", 310, 630, 0.40, "Zombie_01"),
        ("ZombieWalker", 420, 600, 0.40, "Zombie_02"),
        ("ZombieWalker", 630, 610, 0.40, "Zombie_03"),
        ("ZombieBrute", 470, 690, 0.54, "Brute_Elite"),
        ("ZombieSpitter", 300, 750, 0.44, "ZombieSpitter_01"),
        ("ZombieArmored", 600, 750, 0.44, "ZombieArmored_01"),
        ("Hound", 240, 850, 0.44, "Hound_01"),
        ("Hound", 640, 830, 0.44, "Hound_02"),
    ]
    for sp_key, sx, sy, sc, label in enemy_layout:
        spawn_sprite_actor(sprites.get(sp_key), to_ue_pos(sx, sy, 0), sc, 300, label)
        
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(260, 990, 15), 0.52, 200, "DefenseLine_L")
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(470, 990, 15), 0.52, 200, "DefenseLine_M")
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(680, 990, 15), 0.52, 200, "DefenseLine_R")
    
    # 主角出生点
    p_pos = to_ue_pos(470, 1360, -20.0) # (70, -20, -400)
    unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, p_pos, unreal.Rotator())
    
    # HUD 系统
    spawn_sprite_actor(sprites.get("HUD_BossBar_Bg"), to_ue_pos(470, 80, -90.0), 0.85, 1200, "HUD_BossBar_Bg")
    spawn_sprite_actor(sprites.get("HUD_BossBar_Fill"), to_ue_pos(450, 80, -92.0), 0.78, 1220, "HUD_BossBar_Fill")
    spawn_sprite_actor(sprites.get("Btn_Pause"), to_ue_pos(860, 80, -94.0), 0.20, 1240, "HUD_Btn_Pause")
    
    tactical_items = [
        ("Barricade", 860, 460, 0.30, "HUD_Tactical_Barricade"),
        ("RedBarrel", 860, 580, 0.30, "HUD_Tactical_RedBarrel"),
        ("ToxicDrum", 860, 700, 0.30, "HUD_Tactical_ToxicDrum"),
        ("MedPod", 860, 820, 0.30, "HUD_Tactical_MedPod"),
    ]
    for sp_key, sx, sy, sc, label in tactical_items:
        spawn_sprite_actor(sprites.get(sp_key), to_ue_pos(sx, sy, -90.0), sc, 1200, label)
        
    spawn_sprite_actor(sprites.get("HUD_Player_HP_Bg"), to_ue_pos(180, 1520, -90.0), 0.72, 1200, "HUD_Player_HP_Bg")
    spawn_sprite_actor(sprites.get("HUD_Player_HP_Fill"), to_ue_pos(155, 1520, -92.0), 0.62, 1220, "HUD_Player_HP_Fill")
    
    spawn_sprite_actor(sprites.get("HUD_Player_EXP_Bg"), to_ue_pos(180, 1590, -90.0), 0.50, 1200, "HUD_Player_EXP_Bg")
    spawn_sprite_actor(sprites.get("HUD_Player_EXP_Fill"), to_ue_pos(170, 1590, -92.0), 0.45, 1220, "HUD_Player_EXP_Fill")
    
    weapon_items = [
        ("Card_AutoRifle", 380, 1555, 0.30, "HUD_Card_AutoRifle_Active"),
        ("Card_Shotgun", 510, 1555, 0.28, "HUD_Card_Shotgun"),
        ("Card_Rocket", 640, 1555, 0.28, "HUD_Card_Rocket"),
        ("Card_Tesla", 770, 1555, 0.28, "HUD_Card_Tesla"),
    ]
    for sp_key, sx, sy, sc, label in weapon_items:
        spawn_sprite_actor(sprites.get(sp_key), to_ue_pos(sx, sy, -90.0), sc, 1200, label)
        
    unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    log("🎉 MAP_GGBOM_Main 终极无瑕疵关卡保存完成！")

if __name__ == "__main__":
    assemble_master_game()
