# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》全量战斗体系总装：
1. 攻击 (J / 鼠标左键): 播放向上射击动作 + 枪口开火 + 发射高速飞行动能子弹 BP_Projectile_Bullet
2. 子弹投射物 (BP_Projectile_Bullet): 高速向前飞行 (+1600 px/s) + 击中敌人触发打击特效
3. 受击 (H 键): 播放受击抖动动作 (FB_T_Player_Medic_Hurt_Dir_05_Up_Sheet)
4. 倒地 / 阵亡 (K 键): 播放倒地动作 (FB_T_Player_Medic_Death_Collapse_Sheet)
5. 复活 / 医疗无人机大招 (R 键 / Space): 呼叫医疗无人机大招并播放复生重生动作
================================================================================
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import unreal

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
ART_ROOT = ROOT / "Content" / "美术" / "Art"
GEN = "/Game/GGBOM"
BLUEPRINTS = f"{GEN}/Blueprints"
ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
PINLIB = unreal.BlueprintGraphPinLibrary
BPLIB = unreal.BlueprintEditorLibrary

MAP_W = 941.0
MAP_H = 1672.0
ASPECT_RATIO = MAP_W / MAP_H

def log(msg: str):
    unreal.log(f"[GGBOM-Combat] {msg}")

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
        tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
        tex.set_editor_property("filter", unreal.TextureFilter.TF_DEFAULT)
        tex.set_editor_property("srgb", True)
        tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
        tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
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
    ue_x = (MAP_W / 2.0) - screen_x
    ue_z = (MAP_H / 2.0) - screen_y
    return unreal.Vector(ue_x, y_depth, ue_z)

def build_bullet_projectile_blueprint(bullet_sprite: unreal.PaperSprite) -> unreal.Blueprint:
    log("🔨 构建高速突击步枪子弹投射物 (BP_Projectile_Bullet)...")
    bp_path = f"{BLUEPRINTS}/BP_Projectile_Bullet"
    if ASSETS.does_asset_exist(bp_path):
        bp = unreal.load_asset(bp_path)
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(bp_path, unreal.Actor.static_class())
        
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    has_sp = False
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if obj and isinstance(obj, unreal.PaperSpriteComponent):
            has_sp = True
            
    if not has_sp:
        sp_comp = add_component(bp, "BulletSprite", unreal.PaperSpriteComponent.static_class())
        if bullet_sprite:
            sp_comp.set_editor_property("source_sprite", bullet_sprite)
        mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
        if mat:
            sp_comp.set_material(0, mat)
        sp_comp.set_editor_property("translucency_sort_priority", 600)
        sp_comp.set_relative_scale3d(unreal.Vector(0.5, 0.5, 0.5))
        
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    try:
        for n in ed.list_all_nodes():
            if n.get_name() not in ["ReceiveBeginPlay", "ReceiveTick", "ReceiveActorBeginOverlap"]:
                ed.remove_node(n)
    except Exception:
        pass
        
    # Tick: 高速向前飞行 (+Z 方向 1600.0 px/s)
    tick = ed.find_event_node("ReceiveTick")
    vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 200, 0)
    set_value(vec, "X", 0.0); set_value(vec, "Y", 0.0); set_value(vec, "Z", 1600.0)
    
    mul = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 400, 0)
    connect(vec, "ReturnValue", mul, "A")
    connect(tick, "DeltaSeconds", mul, "B")
    
    move = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 620, 0)
    set_value(move, "bSweep", "true")
    connect(tick, "then", move, "execute")
    connect(mul, "ReturnValue", move, "DeltaLocation")
    
    # 飞行超出顶部自动销毁 (Z > 900)
    get_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 820, 100)
    break_vec = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 1020, 100)
    connect(get_loc, "ReturnValue", break_vec, "InVec")
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1220, 100)
    connect(break_vec, "Z", cmp_z, "A"); set_value(cmp_z, "B", 900.0)
    
    br_dest = ed.add_branch_node(); br_dest.set_node_pos(unreal.IntPoint(1420, 0))
    connect(move, "then", br_dest, "execute")
    connect(cmp_z, "ReturnValue", br_dest, "Condition")
    
    destroy_node = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 1620, 0)
    connect(br_dest, "then", destroy_node, "execute")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_Projectile_Bullet 子弹投射物构建成功！")
    return bp

def build_full_combat_medic(bullet_bp: unreal.Blueprint):
    log("🔨 构建全套战斗动作与开火状态机 (BP_Player_Medic)...")
    bp_path = f"{BLUEPRINTS}/BP_Player_Medic"
    bp = unreal.load_asset(bp_path) if ASSETS.does_asset_exist(bp_path) else None
    if not bp:
        bp = BPLIB.create_blueprint_asset_with_parent(bp_path, unreal.Pawn.static_class())
        
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        cdo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.DISABLED)
        cdo.set_editor_property("auto_receive_input", unreal.AutoReceiveInput.PLAYER0)
        
    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    fb_idle = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    fb_run_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet")
    fb_run_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_01_Down_Sheet")
    fb_run_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet")
    
    # 全套战斗动作
    fb_attack = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet")
    fb_hurt = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_05_Up/Hurt/Flipbooks/FB_T_Player_Medic_Hurt_Dir_05_Up_Sheet")
    fb_death = unreal.load_asset(f"{pfx}/03_Death_Revive/Death_Collapse/Flipbooks/FB_T_Player_Medic_Death_Collapse_Sheet")
    fb_revive = unreal.load_asset(f"{pfx}/03_Death_Revive/Revive/Flipbooks/FB_T_Player_Medic_Revive_Sheet")
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    
    # 确保唯二组件
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    has_fb = False
    has_col = False
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if obj:
            if isinstance(obj, unreal.PaperFlipbookComponent):
                has_fb = True
            elif isinstance(obj, unreal.BoxComponent):
                has_col = True
                
    if not has_col:
        collision = add_component(bp, "Collision", unreal.BoxComponent.static_class())
        collision.set_editor_property("box_extent", unreal.Vector(18, 12, 25))
        collision.set_collision_profile_name("Pawn")
        
    if not has_fb:
        flipbook_comp = add_component(bp, "Flipbook", unreal.PaperFlipbookComponent.static_class())
        if fb_idle:
            flipbook_comp.set_editor_property("source_flipbook", fb_idle)
        if mat:
            flipbook_comp.set_material(0, mat)
        flipbook_comp.set_editor_property("translucency_sort_priority", 500)
        flipbook_comp.set_relative_scale3d(unreal.Vector(0.45, 0.45, 0.45))
    
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    try:
        for n in ed.list_all_nodes():
            if n.get_name() not in ["ReceiveBeginPlay", "ReceiveTick", "ReceiveActorBeginOverlap"]:
                ed.remove_node(n)
    except Exception:
        pass
        
    # 1. BeginPlay: 锁定相机
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
    
    # 2. Tick: 8向移动 + 攻击 + 受击 + 倒地 + 复生状态机
    tick = ed.find_event_node("ReceiveTick")
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)
    
    # 按键采样:
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -180); set_value(key_a, "Key", "A"); connect(pc_tick, "ReturnValue", key_a, "self")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -80);  set_value(key_d, "Key", "D"); connect(pc_tick, "ReturnValue", key_d, "self")
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 20);   set_value(key_w, "Key", "W"); connect(pc_tick, "ReturnValue", key_w, "self")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 120);  set_value(key_s, "Key", "S"); connect(pc_tick, "ReturnValue", key_s, "self")
    
    # 动作按键: J (攻击), H (受击), K (倒地), R / Space (复活)
    key_j = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 220);  set_value(key_j, "Key", "J"); connect(pc_tick, "ReturnValue", key_j, "self")
    key_h = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 320);  set_value(key_h, "Key", "H"); connect(pc_tick, "ReturnValue", key_h, "self")
    key_k = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 420);  set_value(key_k, "Key", "K"); connect(pc_tick, "ReturnValue", key_k, "self")
    key_r = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 520);  set_value(key_r, "Key", "R"); connect(pc_tick, "ReturnValue", key_r, "self")
    
    # 移动双轴计算
    sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -180); set_value(sel_a, "A", 420.0); set_value(sel_a, "B", 0.0); connect(key_a, "ReturnValue", sel_a, "bPickA")
    sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -80);  set_value(sel_d, "A", -420.0); set_value(sel_d, "B", 0.0); connect(key_d, "ReturnValue", sel_d, "bPickA")
    add_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -130); connect(sel_a, "ReturnValue", add_x, "A"); connect(sel_d, "ReturnValue", add_x, "B")
    
    sel_w = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 20);   set_value(sel_w, "A", 420.0); set_value(sel_w, "B", 0.0); connect(key_w, "ReturnValue", sel_w, "bPickA")
    sel_s = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 120);  set_value(sel_s, "A", -420.0); set_value(sel_s, "B", 0.0); connect(key_s, "ReturnValue", sel_s, "bPickA")
    add_z = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, 70); connect(sel_w, "ReturnValue", add_z, "A"); connect(sel_s, "ReturnValue", add_z, "B")
    
    make_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 880, 0)
    connect(add_x, "ReturnValue", make_vec, "X"); set_value(make_vec, "Y", 0.0); connect(add_z, "ReturnValue", make_vec, "Z")
    mul_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1080, 0)
    connect(make_vec, "ReturnValue", mul_dt, "A"); connect(tick, "DeltaSeconds", mul_dt, "B")
    
    move_node = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1300, 0)
    set_value(move_node, "bSweep", "true")
    connect(tick, "then", move_node, "execute")
    connect(mul_dt, "ReturnValue", move_node, "DeltaLocation")
    
    get_comp = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1520, -200); set_value(get_comp, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    get_curr_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 1740, -200); connect(get_comp, "ReturnValue", get_curr_fb, "self")
    
    # 状态优先级: 倒地(K) > 复活(R) > 受击(H) > 攻击(J) > 移动(WASD) > 待机
    br_k = ed.add_branch_node(); br_k.set_node_pos(unreal.IntPoint(1520, 0))
    connect(move_node, "then", br_k, "execute"); connect(key_k, "ReturnValue", br_k, "Condition")
    
    # 1. 倒地动作 (K 键)
    if fb_death:
        is_diff_death = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 1740, 0)
        connect(get_curr_fb, "ReturnValue", is_diff_death, "A"); set_value(is_diff_death, "B", f"PaperFlipbook'{fb_death.get_path_name()}'")
        br_diff_death = ed.add_branch_node(); br_diff_death.set_node_pos(unreal.IntPoint(1960, 0))
        connect(br_k, "then", br_diff_death, "execute"); connect(is_diff_death, "ReturnValue", br_diff_death, "Condition")
        set_fb_death = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2180, 0)
        set_value(set_fb_death, "NewFlipbook", f"PaperFlipbook'{fb_death.get_path_name()}'")
        connect(br_diff_death, "then", set_fb_death, "execute"); connect(get_comp, "ReturnValue", set_fb_death, "self")
        
    # 2. 复活动作 (R 键)
    br_r = ed.add_branch_node(); br_r.set_node_pos(unreal.IntPoint(1520, 120))
    connect(br_k, "else", br_r, "execute"); connect(key_r, "ReturnValue", br_r, "Condition")
    if fb_revive:
        is_diff_rev = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 1740, 120)
        connect(get_curr_fb, "ReturnValue", is_diff_rev, "A"); set_value(is_diff_rev, "B", f"PaperFlipbook'{fb_revive.get_path_name()}'")
        br_diff_rev = ed.add_branch_node(); br_diff_rev.set_node_pos(unreal.IntPoint(1960, 120))
        connect(br_r, "then", br_diff_rev, "execute"); connect(is_diff_rev, "ReturnValue", br_diff_rev, "Condition")
        set_fb_rev = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2180, 120)
        set_value(set_fb_rev, "NewFlipbook", f"PaperFlipbook'{fb_revive.get_path_name()}'")
        connect(br_diff_rev, "then", set_fb_rev, "execute"); connect(get_comp, "ReturnValue", set_fb_rev, "self")
        
    # 3. 受击动作 (H 键)
    br_h = ed.add_branch_node(); br_h.set_node_pos(unreal.IntPoint(1520, 240))
    connect(br_r, "else", br_h, "execute"); connect(key_h, "ReturnValue", br_h, "Condition")
    if fb_hurt:
        is_diff_hurt = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 1740, 240)
        connect(get_curr_fb, "ReturnValue", is_diff_hurt, "A"); set_value(is_diff_hurt, "B", f"PaperFlipbook'{fb_hurt.get_path_name()}'")
        br_diff_hurt = ed.add_branch_node(); br_diff_hurt.set_node_pos(unreal.IntPoint(1960, 240))
        connect(br_h, "then", br_diff_hurt, "execute"); connect(is_diff_hurt, "ReturnValue", br_diff_hurt, "Condition")
        set_fb_hurt = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2180, 240)
        set_value(set_fb_hurt, "NewFlipbook", f"PaperFlipbook'{fb_hurt.get_path_name()}'")
        connect(br_diff_hurt, "then", set_fb_hurt, "execute"); connect(get_comp, "ReturnValue", set_fb_hurt, "self")
        
    # 4. 攻击分支 (J 键: 播放射击动作 + 发射子弹)
    br_j = ed.add_branch_node(); br_j.set_node_pos(unreal.IntPoint(1520, 360))
    connect(br_h, "else", br_j, "execute"); connect(key_j, "ReturnValue", br_j, "Condition")
    if fb_attack:
        is_diff_atk = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 1740, 360)
        connect(get_curr_fb, "ReturnValue", is_diff_atk, "A"); set_value(is_diff_atk, "B", f"PaperFlipbook'{fb_attack.get_path_name()}'")
        br_diff_atk = ed.add_branch_node(); br_diff_atk.set_node_pos(unreal.IntPoint(1960, 360))
        connect(br_j, "then", br_diff_atk, "execute"); connect(is_diff_atk, "ReturnValue", br_diff_atk, "Condition")
        set_fb_atk = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2180, 360)
        set_value(set_fb_atk, "NewFlipbook", f"PaperFlipbook'{fb_attack.get_path_name()}'")
        connect(br_diff_atk, "then", set_fb_atk, "execute"); connect(get_comp, "ReturnValue", set_fb_atk, "self")
        
        # 发射子弹投射物
        p_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 2180, 480)
        bullet_off = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2180, 560); set_value(bullet_off, "X", 0.0); set_value(bullet_off, "Y", 0.0); set_value(bullet_off, "Z", 35.0)
        spawn_loc = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 2380, 480)
        connect(p_loc, "ReturnValue", spawn_loc, "A"); connect(bullet_off, "ReturnValue", spawn_loc, "B")
        
        make_tf = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 2580, 480)
        connect(spawn_loc, "ReturnValue", make_tf, "Location")
        
        spawn_bullet = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 2800, 360)
        bullet_cls = unreal.load_class(None, f"{bullet_bp.get_path_name()}.{bullet_bp.get_name()}_C")
        set_value(spawn_bullet, "Class", f"Class'{bullet_cls.get_path_name()}'")
        connect(br_diff_atk, "then", spawn_bullet, "execute")
        connect(make_tf, "ReturnValue", spawn_bullet, "SpawnTransform")
        
        finish_spawn = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 3050, 360)
        connect(spawn_bullet, "then", finish_spawn, "execute")
        connect(spawn_bullet, "ReturnValue", finish_spawn, "Actor")
        connect(make_tf, "ReturnValue", finish_spawn, "SpawnTransform")
        
    # 5. 移动与待机分支 (br_j.else)
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -200); connect(add_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 200); connect(add_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1080, 150); connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")
    
    br_moving = ed.add_branch_node(); br_moving.set_node_pos(unreal.IntPoint(1520, 600))
    connect(br_j, "else", br_moving, "execute"); connect(is_moving, "ReturnValue", br_moving, "Condition")
    
    # 移动中: 判别镜像
    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 1080, -100); connect(add_x, "ReturnValue", is_right, "A"); set_value(is_right, "B", 0.0)
    scale_val_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 1280, -100); set_value(scale_val_x, "A", -0.45); set_value(scale_val_x, "B", 0.45); connect(is_right, "ReturnValue", scale_val_x, "bPickA")
    scale_move_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1480, -100); connect(scale_val_x, "ReturnValue", scale_move_vec, "X"); set_value(scale_move_vec, "Y", 0.45); set_value(scale_move_vec, "Z", 0.45)
    
    set_sc_move = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 1740, 600)
    connect(br_moving, "then", set_sc_move, "execute")
    connect(get_comp, "ReturnValue", set_sc_move, "self")
    connect(scale_move_vec, "ReturnValue", set_sc_move, "NewScale3D")
    
    br_side = ed.add_branch_node(); br_side.set_node_pos(unreal.IntPoint(1960, 600))
    connect(set_sc_move, "then", br_side, "execute"); connect(cmp_x, "ReturnValue", br_side, "Condition")
    
    # 左右奔跑
    is_diff_side = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2180, 500)
    connect(get_curr_fb, "ReturnValue", is_diff_side, "A")
    if fb_run_left:
        set_value(is_diff_side, "B", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    br_diff_side = ed.add_branch_node(); br_diff_side.set_node_pos(unreal.IntPoint(2400, 500))
    connect(br_side, "then", br_diff_side, "execute"); connect(is_diff_side, "ReturnValue", br_diff_side, "Condition")
    set_fb_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2620, 500)
    if fb_run_left:
        set_value(set_fb_side, "NewFlipbook", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(br_diff_side, "then", set_fb_side, "execute"); connect(get_comp, "ReturnValue", set_fb_side, "self")
    
    # 纵向跑 (W / S)
    is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1960, 700); connect(add_z, "ReturnValue", is_up, "A"); set_value(is_up, "B", 0.0)
    br_up = ed.add_branch_node(); br_up.set_node_pos(unreal.IntPoint(2180, 700))
    connect(br_side, "else", br_up, "execute"); connect(is_up, "ReturnValue", br_up, "Condition")
    
    # 向上跑
    is_diff_up = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2400, 650)
    connect(get_curr_fb, "ReturnValue", is_diff_up, "A")
    if fb_run_up:
        set_value(is_diff_up, "B", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    br_diff_up = ed.add_branch_node(); br_diff_up.set_node_pos(unreal.IntPoint(2620, 650))
    connect(br_up, "then", br_diff_up, "execute"); connect(is_diff_up, "ReturnValue", br_diff_up, "Condition")
    set_fb_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2840, 650)
    if fb_run_up:
        set_value(set_fb_up, "NewFlipbook", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    connect(br_diff_up, "then", set_fb_up, "execute"); connect(get_comp, "ReturnValue", set_fb_up, "self")
    
    # 向下跑
    is_diff_down = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2400, 750)
    connect(get_curr_fb, "ReturnValue", is_diff_down, "A")
    if fb_run_down:
        set_value(is_diff_down, "B", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    br_diff_down = ed.add_branch_node(); br_diff_down.set_node_pos(unreal.IntPoint(2620, 750))
    connect(br_up, "else", br_diff_down, "execute"); connect(is_diff_down, "ReturnValue", br_diff_down, "Condition")
    set_fb_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2840, 750)
    if fb_run_down:
        set_value(set_fb_down, "NewFlipbook", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(br_diff_down, "then", set_fb_down, "execute"); connect(get_comp, "ReturnValue", set_fb_down, "self")
    
    # 待机分支 (br_moving.else)
    scale_idle_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1520, 900); set_value(scale_idle_vec, "X", 0.45); set_value(scale_idle_vec, "Y", 0.45); set_value(scale_idle_vec, "Z", 0.45)
    set_sc_idle = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 1740, 900)
    connect(br_moving, "else", set_sc_idle, "execute"); connect(get_comp, "ReturnValue", set_sc_idle, "self"); connect(scale_idle_vec, "ReturnValue", set_sc_idle, "NewScale3D")
    
    is_diff_idle = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 1960, 900)
    connect(get_curr_fb, "ReturnValue", is_diff_idle, "A")
    if fb_idle:
        set_value(is_diff_idle, "B", f"PaperFlipbook'{fb_idle.get_path_name()}'")
    br_diff_idle = ed.add_branch_node(); br_diff_idle.set_node_pos(unreal.IntPoint(2180, 900))
    connect(set_sc_idle, "then", br_diff_idle, "execute"); connect(is_diff_idle, "ReturnValue", br_diff_idle, "Condition")
    
    set_fb_idle = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2400, 900)
    if fb_idle:
        set_value(set_fb_idle, "NewFlipbook", f"PaperFlipbook'{fb_idle.get_path_name()}'")
    connect(br_diff_idle, "then", set_fb_idle, "execute"); connect(get_comp, "ReturnValue", set_fb_idle, "self")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ 全套战斗动作与开火状态机 BP_Player_Medic 构建成功！")
    return bp

def assemble_master_game():
    log("🚀 重新组装主关卡 MAP_GGBOM_Main (含子弹与全套战斗动作)...")
    
    art_map = {
        "Map_Ground": "08_Maps/Stage00_Start/T_Map_Stage00_Start_Ground.png",
        "Map_Overhead": "08_Maps/Stage00_Start/T_Map_Stage00_Start_Overhead.png",
        
        "Bullet_Flight": "03_Weapons/02_AssaultRifle/T_Bullet_AssaultRifle_02_Flight.png",
        
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
            
    bullet_bp = build_bullet_projectile_blueprint(sprites.get("Bullet_Flight"))
    player_bp = build_full_combat_medic(bullet_bp)
    
    gm_path = f"{BLUEPRINTS}/BP_GGBOM_GameMode"
    gm_bp = unreal.load_asset(gm_path)
    if gm_bp:
        gm_cdo = unreal.get_default_object(gm_bp.generated_class())
        if gm_cdo:
            player_cls = unreal.load_class(None, f"{player_bp.get_path_name()}.{player_bp.get_name()}_C")
            gm_cdo.set_editor_property("default_pawn_class", player_cls)
        BPLIB.compile_blueprint(gm_bp)
        ASSETS.save_loaded_asset(gm_bp, only_if_is_dirty=False)
        
    map_path = f"{GEN}/Maps/MAP_GGBOM_Main"
    if ASSETS.does_asset_exist(map_path):
        unreal.EditorLevelLibrary.load_level(map_path)
    else:
        unreal.EditorLevelLibrary.new_level(map_path)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            unreal.EditorLevelLibrary.destroy_actor(a)
        except Exception:
            pass
            
    world.get_world_settings().set_editor_property("default_game_mode", unreal.load_class(None, f"{gm_path}.BP_GGBOM_GameMode_C"))
    
    # 相机与后处理
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(0, -500, 0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    cam_comp.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    cam_comp.set_editor_property("ortho_width", MAP_W)
    cam_comp.set_editor_property("aspect_ratio", ASPECT_RATIO)
    cam.set_actor_label("Master_Orthographic_Camera")
    
    pp_vol = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator())
    pp_vol.set_actor_label("PP_2D_Color_Accuracy")
    pp_vol.set_editor_property("unbound", True)
    pp_comp = pp_vol.get_editor_property("settings")
    pp_comp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    pp_comp.set_editor_property("auto_exposure_bias", 0.0)
    pp_comp.set_editor_property("bloom_intensity", 0.0)
    pp_comp.set_editor_property("motion_blur_amount", 0.0)
    
    # 双层地图
    spawn_sprite_actor(sprites.get("Map_Ground"), unreal.Vector(0, 80.0, 0), 1.0, 0, "Ground_Stage00")
    spawn_sprite_actor(sprites.get("Map_Overhead"), unreal.Vector(0, -80.0, 0), 1.0, 1000, "Overhead_Stage00")
    
    # 战场实体
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
    
    p_pos = to_ue_pos(470, 1360, -10)
    unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, p_pos, unreal.Rotator())
    
    # HUD
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
    log("🎉 MAP_GGBOM_Main 全套战斗动作与子弹发射实装完成！")

if __name__ == "__main__":
    assemble_master_game()
