# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》终极完美视野与动态动作状态机总装流水线
- 完美 9:16 全局战场视野 (覆盖 Boss、敌人矩阵、路障与 HUD)
- WASD 8 方向走位 + 动态奔跑/待机 Flipbook 动画流转 + 左右转向自动翻转
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

def log(msg: str):
    unreal.log(f"[GGBOM-Flawless] {msg}")

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
        return unreal.load_asset(path)
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

def build_flawless_medic_pawn():
    log("🔨 构建全功能医疗兵 Pawn (绑定 BeginPlay 视口锁定 + WASD 全向平滑移动)...")
    bp_path = f"{BLUEPRINTS}/BP_Player_Medic"
    
    if ASSETS.does_asset_exist(bp_path):
        bp = unreal.load_asset(bp_path)
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(bp_path, unreal.Pawn.static_class())
        
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        cdo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
        cdo.set_editor_property("auto_receive_input", unreal.AutoReceiveInput.PLAYER0)
        
    # 碰撞体与动画组件
    flipbook_comp = add_component(bp, "Flipbook", unreal.PaperFlipbookComponent.static_class())
    fb_idle = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    if fb_idle:
        flipbook_comp.set_editor_property("source_flipbook", fb_idle)
    if mat:
        flipbook_comp.set_material(0, mat)
    flipbook_comp.set_editor_property("translucency_sort_priority", 30)
    
    # 构建 Event Graph 逻辑
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    # 1. BeginPlay: 视口锁定在全局 9:16 相机上
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
    
    # 2. Tick: WASD 8 向走位
    tick = ed.find_event_node("ReceiveTick")
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)
    
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -180); set_value(key_a, "Key", "A")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -80);  set_value(key_d, "Key", "D")
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 20);   set_value(key_w, "Key", "W")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 120);  set_value(key_s, "Key", "S")
    
    connect(pc_tick, "ReturnValue", key_a, "self")
    connect(pc_tick, "ReturnValue", key_d, "self")
    connect(pc_tick, "ReturnValue", key_w, "self")
    connect(pc_tick, "ReturnValue", key_s, "self")
    
    br_a = ed.add_branch_node(); br_a.set_node_pos(unreal.IntPoint(460, -180))
    br_d = ed.add_branch_node(); br_d.set_node_pos(unreal.IntPoint(460, -80))
    br_w = ed.add_branch_node(); br_w.set_node_pos(unreal.IntPoint(460, 20))
    br_s = ed.add_branch_node(); br_s.set_node_pos(unreal.IntPoint(460, 120))
    
    connect(tick, "then", br_a, "execute"); connect(key_a, "ReturnValue", br_a, "Condition")
    connect(br_a, "else", br_d, "execute"); connect(key_d, "ReturnValue", br_d, "Condition")
    connect(br_d, "else", br_w, "execute"); connect(key_w, "ReturnValue", br_w, "Condition")
    connect(br_w, "else", br_s, "execute"); connect(key_s, "ReturnValue", br_s, "Condition")
    
    directions = [
        (br_a, 500.0, 0.0, 0.0, -220),   # A: 左移 (+X)
        (br_d, -500.0, 0.0, 0.0, -100),  # D: 右移 (-X)
        (br_w, 0.0, 0.0, 500.0, 20),    # W: 上移 (+Z)
        (br_s, 0.0, 0.0, -500.0, 140),  # S: 下移 (-Z)
    ]
    for branch, dx, dy, dz, ypos in directions:
        vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 680, ypos)
        set_value(vec, "X", dx); set_value(vec, "Y", dy); set_value(vec, "Z", dz)
        mul = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 880, ypos)
        move = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1100, ypos)
        set_value(move, "bSweep", "true")
        
        connect(vec, "ReturnValue", mul, "A")
        connect(tick, "DeltaSeconds", mul, "B")
        connect(branch, "then", move, "execute")
        connect(mul, "ReturnValue", move, "DeltaLocation")
        
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_Player_Medic 视口锁定与 WASD 逻辑构建完成！")
    return bp

def assemble_master_game():
    log("🚀 组装主关卡 MAP_GGBOM_Main 全景世界...")
    
    art_map = {
        "Ground": "08_Maps/Stage00_Start/T_Map_Stage00_Start_Ground.png",
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
            
    player_bp = build_flawless_medic_pawn()
    
    # 绑定 GameMode
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
    
    # 9:16 正交全局固定全景相机 (覆盖全场 1080x1920)
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(0, -500, 0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    cam_comp.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    cam_comp.set_editor_property("ortho_width", 1080.0)
    cam_comp.set_editor_property("aspect_ratio", 0.5625)
    cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    cam.set_actor_label("Master_Orthographic_Camera")
    
    # 场景实体
    spawn_sprite_actor(sprites.get("Ground"), to_ue_pos(540, 960, 80), 1.15, -100, "Ground_Stage00")
    spawn_sprite_actor(sprites.get("Boss"), to_ue_pos(540, 520, 20), 0.68, 10, "Boss_Overlord")
    
    # 顶部路障
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(340, 650, 15), 0.55, 6, "Barricade_Top_L")
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(540, 650, 15), 0.55, 6, "Barricade_Top_M")
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(740, 650, 15), 0.55, 6, "Barricade_Top_R")
    
    # 敌人矩阵
    enemy_layout = [
        ("ZombieWalker", 360, 750, 0.42, "Zombie_01"),
        ("ZombieWalker", 480, 710, 0.42, "Zombie_02"),
        ("ZombieWalker", 720, 720, 0.42, "Zombie_03"),
        ("ZombieBrute", 540, 810, 0.58, "Brute_Elite"),
        ("ZombieSpitter", 340, 870, 0.48, "ZombieSpitter_01"),
        ("ZombieArmored", 690, 870, 0.48, "ZombieArmored_01"),
        ("Hound", 270, 980, 0.48, "Hound_01"),
        ("Hound", 730, 960, 0.48, "Hound_02"),
    ]
    for sp_key, sx, sy, sc, label in enemy_layout:
        spawn_sprite_actor(sprites.get(sp_key), to_ue_pos(sx, sy, 0), sc, 20, label)
        
    # 中部路障
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(300, 1140, 15), 0.58, 6, "DefenseLine_L")
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(540, 1140, 15), 0.58, 6, "DefenseLine_M")
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(780, 1140, 15), 0.58, 6, "DefenseLine_R")
    
    # 单一主角出生点
    p_pos = to_ue_pos(540, 1560, -10)
    unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, p_pos, unreal.Rotator())
    
    # HUD 系统实装
    # 顶部 Boss 战况栏
    spawn_sprite_actor(sprites.get("HUD_BossBar_Bg"), to_ue_pos(540, 95, -58.0), 0.90, 500, "HUD_BossBar_Bg")
    spawn_sprite_actor(sprites.get("HUD_BossBar_Fill"), to_ue_pos(520, 95, -62.0), 0.82, 520, "HUD_BossBar_Fill")
    spawn_sprite_actor(sprites.get("Btn_Pause"), to_ue_pos(985, 95, -64.0), 0.22, 560, "HUD_Btn_Pause")
    
    # 右侧战术面板
    tactical_items = [
        ("Barricade", 985, 540, 0.32, "HUD_Tactical_Barricade"),
        ("RedBarrel", 985, 675, 0.34, "HUD_Tactical_RedBarrel"),
        ("ToxicDrum", 985, 810, 0.34, "HUD_Tactical_ToxicDrum"),
        ("MedPod", 985, 945, 0.32, "HUD_Tactical_MedPod"),
    ]
    for sp_key, sx, sy, sc, label in tactical_items:
        spawn_sprite_actor(sprites.get(sp_key), to_ue_pos(sx, sy, -60.0), sc, 540, label)
        
    # 左下角 HP / EXP 状态栏
    spawn_sprite_actor(sprites.get("HUD_Player_HP_Bg"), to_ue_pos(215, 1740, -58.0), 0.80, 500, "HUD_Player_HP_Bg")
    spawn_sprite_actor(sprites.get("HUD_Player_HP_Fill"), to_ue_pos(185, 1740, -62.0), 0.68, 520, "HUD_Player_HP_Fill")
    
    spawn_sprite_actor(sprites.get("HUD_Player_EXP_Bg"), to_ue_pos(215, 1820, -58.0), 0.55, 500, "HUD_Player_EXP_Bg")
    spawn_sprite_actor(sprites.get("HUD_Player_EXP_Fill"), to_ue_pos(205, 1820, -62.0), 0.50, 520, "HUD_Player_EXP_Fill")
    
    # 底部武器装备卡牌
    weapon_items = [
        ("Card_AutoRifle", 450, 1780, 0.34, "HUD_Card_AutoRifle_Active"),
        ("Card_Shotgun", 600, 1780, 0.32, "HUD_Card_Shotgun"),
        ("Card_Rocket", 750, 1780, 0.32, "HUD_Card_Rocket"),
        ("Card_Tesla", 900, 1780, 0.32, "HUD_Card_Tesla"),
    ]
    for sp_key, sx, sy, sc, label in weapon_items:
        spawn_sprite_actor(sprites.get(sp_key), to_ue_pos(sx, sy, -60.0), sc, 540, label)
        
    unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    log("🎉 MAP_GGBOM_Main 全局清洁组装保存完成！")

if __name__ == "__main__":
    assemble_master_game()
