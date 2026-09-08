# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》1:1 概念图战斗 HUD 与场景全量总装流水线 (Master 1:1 Engine Assembler)
- 严格遵循审核通过的 reference_design_mockup.md 坐标与规格
- 正交屏幕坐标映射:
    ue_x = 540 - screen_x
    ue_z = 960 - screen_y
    ue_y = -60 (HUD), 0~20 (Characters), 80 (Ground)
================================================================================
"""
from __future__ import annotations
from pathlib import Path
import unreal

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
ART_ROOT = ROOT / "Content" / "美术" / "Art"
GEN = "/Game/GGBOM"

def log(msg: str):
    unreal.log(f"[GGBOM-1to1-Master] {msg}")

def ensure(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def import_art_texture(name: str, rel_path: str) -> unreal.Texture2D:
    src_file = ART_ROOT / rel_path
    if not src_file.is_file():
        log(f"⚠️ 美术文件未找到: {src_file}")
        return None
        
    folder = f"{GEN}/Art/Textures"
    ensure(folder)
    path = f"{folder}/{name}"
    if ASSETS.does_asset_exist(path):
        return unreal.load_asset(path)
        
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(src_file))
    task.set_editor_property("destination_path", folder)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    TOOLS.import_asset_tasks([task])
    
    tex = unreal.load_asset(path)
    if tex:
        properties = [
            ("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON),
            ("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS),
            ("filter", unreal.TextureFilter.TF_BILINEAR),
            ("srgb", True),
        ]
        for prop, val in properties:
            try:
                tex.set_editor_property(prop, val)
            except Exception:
                pass
        ASSETS.save_loaded_asset(tex, only_if_is_dirty=False)
    return tex

def make_paper_sprite(name: str, texture: unreal.Texture2D) -> unreal.PaperSprite:
    if not texture:
        return None
    folder = f"{GEN}/Art/Sprites"
    ensure(folder)
    path = f"{folder}/SP_{name}"
    if ASSETS.does_asset_exist(path):
        sprite = unreal.load_asset(path)
    else:
        sprite = TOOLS.create_asset(f"SP_{name}", folder, unreal.PaperSprite, unreal.PaperSpriteFactory())
        
    sx = float(texture.blueprint_get_size_x())
    sy = float(texture.blueprint_get_size_y())
    sprite.set_editor_property("source_texture", texture)
    sprite.set_editor_property("source_dimension", unreal.Vector2D(sx, sy))
    sprite.set_editor_property("pixels_per_unreal_unit", 1.0)
    
    pivot = getattr(unreal, "SpritePivotMode", getattr(unreal, "PaperSpritePivotMode", None))
    if pivot:
        sprite.set_editor_property("pivot_mode", pivot.CENTER_CENTER)
        
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    if mat:
        sprite.set_editor_property("default_material", mat)
        
    try:
        geo = sprite.get_editor_property("render_geometry")
        geo.set_editor_property("geometry_type", unreal.SpritePolygonMode.SOURCE_BOUNDING_BOX)
        sprite.set_editor_property("render_geometry", geo)
    except Exception:
        pass
        
    ASSETS.save_loaded_asset(sprite, only_if_is_dirty=False)
    return sprite

def spawn_sprite_actor(sprite: unreal.PaperSprite, loc: unreal.Vector, scale: float, priority: int = 0, label: str = "") -> unreal.PaperSpriteActor:
    if not sprite:
        return None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, loc, unreal.Rotator())
    comp = actor.get_component_by_class(unreal.PaperSpriteComponent)
    if comp:
        comp.set_editor_property("source_sprite", sprite)
        comp.set_editor_property("translucency_sort_priority", priority)
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    if label:
        actor.set_actor_label(label)
    return actor

def to_ue_pos(screen_x: float, screen_y: float, y_depth: float = -60.0) -> unreal.Vector:
    """将 1080x1920 概念图设计坐标精准转换为 UE5 9:16 正交视口三维坐标"""
    ue_x = 540.0 - screen_x
    ue_z = 960.0 - screen_y
    return unreal.Vector(ue_x, y_depth, ue_z)

def execute_master_1to1_assembly():
    log("==================================================================")
    log("🚀 开始执行 1:1 概念图级关卡与 HUD 精准全量实装...")
    log("==================================================================")
    
    art_map = {
        # 关卡与背景
        "Ground": "08_Maps/Stage00_Start/T_Map_Stage00_Start_Ground.png",
        
        # 角色与首领
        "Player": "01_Player/01_Idle_Run/Dir_05_Up/Idle/T_Player_Medic_Idle_Dir_05_Up_01.png",
        "Boss": "02_Enemies/Boss_Overlord/Actions/Idle/Dir_01_Down/T_Boss_Idle_Dir_01_Down_01.png",
        
        # 敌人矩阵
        "ZombieWalker": "02_Enemies/Zombie/01_Zombie_Walker_Basic/T_Zombie_WalkerBasic_01.png",
        "ZombieBrute": "02_Enemies/Zombie/11_Zombie_Shambler_Heavy/T_Zombie_ShamblerHeavy_01.png",
        "ZombieSpitter": "02_Enemies/Zombie/04_Zombie_Spitter_Minor/T_Zombie_SpitterMinor_01.png",
        "ZombieArmored": "02_Enemies/Zombie/07_Zombie_Armored_Guard/T_Zombie_ArmoredGuard_01.png",
        "Hound": "02_Enemies/MutantHound/Run/Dir_01_Down/T_Hound_Run_Dir_01_Down_01.png",
        
        # 掩体与道具
        "Barricade": "04_Props/09_SecurityBarricade/T_Prop_Barricade_01_Intact.png",
        "RedBarrel": "04_Props/01_RedExplosiveBarrel/T_Prop_Barrel_01_Intact.png",
        "ToxicDrum": "04_Props/02_ToxicWasteDrum/T_Prop_ToxicDrum_01_Intact.png",
        "MedPod": "04_Props/05_MedicalSupplyPod/T_Prop_MedPod_01_Intact.png",
        
        # 4 真实武器装备卡牌 (全新唯一资产命名)
        "Card_AutoRifle": "06_Cards/04_WeaponModCards/T_Card_WeaponMod_01.png",
        "Card_Shotgun": "06_Cards/04_WeaponModCards/T_Card_WeaponMod_02.png",
        "Card_Rocket": "06_Cards/04_WeaponModCards/T_Card_WeaponMod_03.png",
        "Card_Tesla": "06_Cards/04_WeaponModCards/T_Card_WeaponMod_04.png",
        
        # 真实战斗 HUD 核心条带部件 (精确映射)
        "HUD_BossBar_Bg": "07_UI/02_CardSelectionModal/T_UI_Modal_09_ProgressTrack.png",
        "HUD_BossBar_Fill": "07_UI/02_CardSelectionModal/T_UI_Modal_10_GlowBorder.png",
        "Boss_Skull": "07_UI/03_BossHealthBar/T_UI_BossBar_05_Skull_Normal.png",
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
            
    # 加载并重置主关卡 MAP_GGBOM_Main
    map_path = f"{GEN}/Maps/MAP_GGBOM_Main"
    ensure(f"{GEN}/Maps")
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
            
    # 绑定 GameMode
    gm_path = f"{GEN}/Blueprints/BP_GGBOM_GameMode"
    gm_cls = unreal.load_class(None, f"{gm_path}.BP_GGBOM_GameMode_C")
    if gm_cls:
        world.get_world_settings().set_editor_property("default_game_mode", gm_cls)
        
    # 9:16 正交摄像机
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(0, -500, 0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    cam_comp.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    cam_comp.set_editor_property("ortho_width", 1080.0)
    cam_comp.set_editor_property("aspect_ratio", 0.5625)
    cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    cam.set_actor_label("PortraitCamera_9x16")
    
    # =========================================================================
    # 1. 战场场景与角色实体 (World Layering)
    # =========================================================================
    # 地面 (ScreenCenter: 540, 960)
    spawn_sprite_actor(sprites.get("Ground"), to_ue_pos(540, 960, 80), 1.15, -100, "Ground_Stage00")
    
    # Boss (ScreenCenter: 540, 520)
    spawn_sprite_actor(sprites.get("Boss"), to_ue_pos(540, 520, 20), 0.68, 10, "Boss_Overlord_Visual")
    
    # 顶部三联防线路障 (Screen: 340, 540, 740, Y=650)
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
        
    # 中部三联防线路障 (Screen: 300, 540, 780, Y=1140)
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(300, 1140, 15), 0.58, 6, "DefenseLine_L")
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(540, 1140, 15), 0.58, 6, "DefenseLine_M")
    spawn_sprite_actor(sprites.get("Barricade"), to_ue_pos(780, 1140, 15), 0.58, 6, "DefenseLine_R")
    
    # 医疗兵主角 (Screen: 540, 1560) - 搭载朝上待机呼吸 Flipbook 动画
    p_pos = to_ue_pos(540, 1560, -10)
    unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, p_pos, unreal.Rotator())
    
    fb_idle = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    if fb_idle:
        p_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperFlipbookActor, p_pos, unreal.Rotator())
        if p_actor:
            p_comp = p_actor.get_component_by_class(unreal.PaperFlipbookComponent)
            if p_comp:
                p_comp.set_editor_property("source_flipbook", fb_idle)
                p_comp.set_editor_property("translucency_sort_priority", 30)
                mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
                if mat:
                    p_comp.set_material(0, mat)
            p_actor.set_actor_scale3d(unreal.Vector(0.65, 0.65, 0.65))
            p_actor.set_actor_label("Player_Medic_Animated")
    
    # =========================================================================
    # 2. 1:1 战斗 HUD 实装 (槽位底框 Priority 500, 内部填充 Priority 520)
    # =========================================================================
    
    # 2.1 顶部 Boss 战况栏 (Screen: 540, 95)
    # 槽位底框 (Priority 500, Y = -58)
    spawn_sprite_actor(sprites.get("HUD_BossBar_Bg"), to_ue_pos(540, 95, -58.0), 0.90, 500, "HUD_BossBar_Bg")
    # 内部红色血条 (Priority 520, Y = -62)
    spawn_sprite_actor(sprites.get("HUD_BossBar_Fill"), to_ue_pos(520, 95, -62.0), 0.82, 520, "HUD_BossBar_Fill")
    # 顶层暂停按钮 (Priority 560, Y = -64)
    spawn_sprite_actor(sprites.get("Btn_Pause"), to_ue_pos(985, 95, -64.0), 0.22, 560, "HUD_Btn_Pause")
    
    # 2.2 右侧 4 组战术道具面板 (Screen: 985, Y: 540, 675, 810, 945)
    tactical_items = [
        ("Barricade", 985, 540, 0.32, "HUD_Tactical_Barricade"),
        ("RedBarrel", 985, 675, 0.34, "HUD_Tactical_RedBarrel"),
        ("ToxicDrum", 985, 810, 0.34, "HUD_Tactical_ToxicDrum"),
        ("MedPod", 985, 945, 0.32, "HUD_Tactical_MedPod"),
    ]
    for sp_key, sx, sy, sc, label in tactical_items:
        spawn_sprite_actor(sprites.get(sp_key), to_ue_pos(sx, sy, -60.0), sc, 540, label)
        
    # 2.3 左下角玩家状态 (底框 Priority 500, 内部填充条 Priority 520)
    # HP Bar: 底框在下，红血条在上
    spawn_sprite_actor(sprites.get("HUD_Player_HP_Bg"), to_ue_pos(215, 1740, -58.0), 0.80, 500, "HUD_Player_HP_Bg")
    spawn_sprite_actor(sprites.get("HUD_Player_HP_Fill"), to_ue_pos(185, 1740, -62.0), 0.68, 520, "HUD_Player_HP_Fill")
    
    # EXP Bar: 底框在下，蓝经验条在上
    spawn_sprite_actor(sprites.get("HUD_Player_EXP_Bg"), to_ue_pos(215, 1820, -58.0), 0.55, 500, "HUD_Player_EXP_Bg")
    spawn_sprite_actor(sprites.get("HUD_Player_EXP_Fill"), to_ue_pos(205, 1820, -62.0), 0.50, 520, "HUD_Player_EXP_Fill")
    
    # 2.4 底部 4 武器装备卡牌切换栏 (Screen: 450, 600, 750, 900, Y: 1780)
    weapon_items = [
        ("Card_AutoRifle", 450, 1780, 0.34, "HUD_Card_AutoRifle_Active"),
        ("Card_Shotgun", 600, 1780, 0.32, "HUD_Card_Shotgun"),
        ("Card_Rocket", 750, 1780, 0.32, "HUD_Card_Rocket"),
        ("Card_Tesla", 900, 1780, 0.32, "HUD_Card_Tesla"),
    ]
    for sp_key, sx, sy, sc, label in weapon_items:
        spawn_sprite_actor(sprites.get(sp_key), to_ue_pos(sx, sy, -60.0), sc, 540, label)
        
    # 保存关卡与资产
    unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    log("🎉 1:1 概念图关卡与 HUD 全量总装完成！MAP_GGBOM_Main SAVED!")

if __name__ == "__main__":
    execute_master_1to1_assembly()
