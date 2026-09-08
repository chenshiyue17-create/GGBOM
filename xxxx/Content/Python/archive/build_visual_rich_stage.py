# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》1:1 概念图级高精美术关卡与 HUD 实装系统
将所有 TextRender 替换为 1:1 像素级对齐的真实 PaperSprite 美术贴图部件
================================================================================
"""
from __future__ import annotations
import math
from pathlib import Path
import unreal

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
ART_ROOT = ROOT / "Content" / "美术" / "Art"
GEN = "/Game/GGBOM"

def log(msg: str):
    unreal.log(f"[GGBOM-VisualHUD] {msg}")

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

def build_art_stage_00():
    log("==================================================================")
    log("🎨 正在执行 1:1 概念图级高精美术关卡与 HUD 总装...")
    log("==================================================================")
    
    # 1. 批量导入概念图对应的核心美术资产
    art_map = {
        # 地图与基础
        "Ground": "08_Maps/Stage00_Start/T_Map_Stage00_Start_Ground.png",
        # 角色与 Boss
        "Player": "01_Player/01_Idle_Run/Dir_05_Up/Idle/T_Player_Medic_Idle_Dir_05_Up_01.png",
        "Boss": "02_Enemies/Boss_Overlord/Actions/Idle/Dir_01_Down/T_Boss_Idle_Dir_01_Down_01.png",
        "ZombieWalker": "02_Enemies/Zombie/01_Zombie_Walker_Basic/T_Zombie_WalkerBasic_01.png",
        "Brute": "02_Enemies/Zombie/11_Zombie_Shambler_Heavy/T_Zombie_ShamblerHeavy_01.png",
        "Shooter": "02_Enemies/VenomShooter/Actions/Aim/Dir_01_Down/T_Shooter_Aim_Dir_01_Down_01.png",
        "Hound": "02_Enemies/MutantHound/Actions/Run/Dir_01_Down/T_Hound_Run_Dir_01_Down_01.png",
        # 战术道具
        "Barricade": "04_Props/09_SecurityBarricade/T_Prop_Barricade_01_Intact.png",
        "ExplosiveBarrel": "04_Props/01_RedExplosiveBarrel/T_Prop_Barrel_Red_01_Idle.png",
        "ToxicBarrel": "04_Props/02_ToxicWasteDrum/T_Prop_Barrel_Green_01_Idle.png",
        "MedSupply": "04_Props/05_MedicalSupplyPod/T_Prop_MedSupply_01_Closed.png",
        # 武器
        "Wpn_AutoRifle": "03_Weapons/02_AssaultRifle/T_Weapon_AssaultRifle_01_Side.png",
        "Wpn_Shotgun": "03_Weapons/03_BuckshotShotgun/T_Weapon_Shotgun_01_Side.png",
        "Wpn_Rocket": "03_Weapons/09_MicroMissileLauncher/T_Weapon_Rocket_01_Side.png",
        "Wpn_Tesla": "03_Weapons/08_PlasmaArcBlaster/T_Weapon_Tesla_01_Side.png",
        # HUD 部件
        "HUD_HP_Fill": "07_UI/01_CombatHUD/T_UI_HUD_01_HealthBar_Fill.png",
        "HUD_HP_Bg": "07_UI/01_CombatHUD/T_UI_HUD_02_HealthBar_Bg.png",
        "HUD_Exp_Fill": "07_UI/01_CombatHUD/T_UI_HUD_04_ExpBar_Fill.png",
        "Boss_Bar_Fill": "07_UI/03_BossHealthBar/T_UI_BossBar_01_Seg1_Fill.png",
        "Boss_Bar_Bg": "07_UI/03_BossHealthBar/T_UI_BossBar_04_Frame_Bg.png",
        "Boss_Skull": "07_UI/03_BossHealthBar/T_UI_BossBar_05_Skull_Normal.png",
        "Btn_Pause": "07_UI/04_PauseSettingsMenu/T_UI_Settings_11_Btn_Resume.png"
    }
    
    textures = {}
    sprites = {}
    for name, rel in art_map.items():
        tex = import_art_texture(name, rel)
        textures[name] = tex
        if tex:
            sprites[name] = make_paper_sprite(name, tex)
            
    # 2. 打开并重新组装主关卡 MAP_GGBOM_Main
    map_path = f"{GEN}/Maps/MAP_GGBOM_Main"
    ensure(f"{GEN}/Maps")
    unreal.EditorLevelLibrary.new_level(map_path)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 绑定 GameMode
    gm_path = f"{GEN}/Blueprints/BP_GGBOM_GameMode"
    gm_cls = unreal.load_class(None, f"{gm_path}.BP_GGBOM_GameMode_C")
    if gm_cls:
        world.get_world_settings().set_editor_property("default_game_mode", gm_cls)
        
    # 3. 生成 9:16 正交摄像机
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(0, -500, 0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    cam_comp.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    cam_comp.set_editor_property("ortho_width", 1080.0)
    cam_comp.set_editor_property("aspect_ratio", 0.5625)
    cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    cam.set_actor_label("PortraitCamera_9x16")
    
    # 4. 生成战场美术实体 (Layering & Z-Order)
    # 4.1 背景地面
    spawn_sprite_actor(sprites.get("Ground"), unreal.Vector(0, 80, 0), 1.15, -100, "Ground_1to1_ConceptArt")
    
    # 4.2 领主 Boss 视觉 (顶端中心)
    spawn_sprite_actor(sprites.get("Boss"), unreal.Vector(0, 20, 620), 0.68, 10, "Boss_Overlord_Visual")
    
    # 4.3 Boss 前方重型防线与隔离带
    spawn_sprite_actor(sprites.get("Barricade"), unreal.Vector(-180, 15, 480), 0.55, 6, "Barricade_Top_L")
    spawn_sprite_actor(sprites.get("Barricade"), unreal.Vector(0, 15, 480), 0.55, 6, "Barricade_Top_M")
    spawn_sprite_actor(sprites.get("Barricade"), unreal.Vector(180, 15, 480), 0.55, 6, "Barricade_Top_R")
    
    # 4.4 中部防线隔离带
    spawn_sprite_actor(sprites.get("Barricade"), unreal.Vector(-240, 15, 0), 0.58, 6, "DefenseLine_L")
    spawn_sprite_actor(sprites.get("Barricade"), unreal.Vector(0, 15, 0), 0.58, 6, "DefenseLine_M")
    spawn_sprite_actor(sprites.get("Barricade"), unreal.Vector(240, 15, 0), 0.58, 6, "DefenseLine_R")
    
    # 4.5 敌人矩阵实体 (按概念图分布)
    enemy_cls = unreal.load_class(None, f"{GEN}/Blueprints/BP_GGBOM_Enemy.BP_GGBOM_Enemy_C")
    enemy_specs = [
        # 行尸群
        (sprites.get("ZombieWalker"), -220, 380, 0.42, "Zombie_01"),
        (sprites.get("ZombieWalker"), -100, 420, 0.42, "Zombie_02"),
        (sprites.get("ZombieWalker"), 160, 410, 0.42, "Zombie_03"),
        # 精英紫色蛮兽
        (sprites.get("Brute"), 0, 320, 0.58, "Brute_Elite"),
        # 毒液射手
        (sprites.get("Shooter"), -180, 260, 0.45, "VenomShooter_01"),
        (sprites.get("Shooter"), 50, 180, 0.45, "VenomShooter_02"),
        # 变异猎犬
        (sprites.get("Hound"), -260, 120, 0.48, "Hound_01"),
        (sprites.get("Hound"), 160, 200, 0.48, "Hound_02"),
    ]
    for sp, x, z, scale, label in enemy_specs:
        spawn_sprite_actor(sp, unreal.Vector(x, 0, z), scale, 20, label)
        
    # 4.6 玩家出生点与主角
    unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -10, -520), unreal.Rotator())
    
    # 5. 生成 1:1 概念图 HUD 美术部件 (全面使用真实 Sprite 部件，绝非纯文字)
    
    # 5.1 顶部 Boss 血条 HUD
    spawn_sprite_actor(sprites.get("Boss_Bar_Bg"), unreal.Vector(0, -60, 880), 0.85, 90, "UI_BossBar_Bg")
    spawn_sprite_actor(sprites.get("Boss_Bar_Fill"), unreal.Vector(0, -60, 880), 0.82, 95, "UI_BossBar_Fill")
    spawn_sprite_actor(sprites.get("Boss_Skull"), unreal.Vector(-240, -60, 880), 0.65, 100, "UI_Boss_SkullIcon")
    
    # 5.2 顶部右上角暂停按钮
    spawn_sprite_actor(sprites.get("Btn_Pause"), unreal.Vector(450, -60, 880), 0.28, 100, "UI_Btn_Pause")
    
    # 5.3 右侧 5 组战术道具面板 (使用真实道具切图)
    tactical_items = [
        ("Barricade", 440, 20, 0.38, "UI_Prop_Barrier"),
        ("ExplosiveBarrel", 440, -110, 0.42, "UI_Prop_ExplosiveBarrel"),
        ("ToxicBarrel", 440, -240, 0.42, "UI_Prop_ToxicBarrel"),
        ("MedSupply", 440, -500, 0.38, "UI_Prop_HealingStation"),
    ]
    for sp_key, x, z, scale, label in tactical_items:
        spawn_sprite_actor(sprites.get(sp_key), unreal.Vector(x, -60, z), scale, 95, label)
        
    # 5.4 底部 4 武器切换栏 (使用真实武器切图)
    weapon_items = [
        ("Wpn_AutoRifle", -120, -780, 0.45, "UI_Weapon_AutoRifle_Active"),
        ("Wpn_Shotgun", 30, -780, 0.45, "UI_Weapon_Shotgun"),
        ("Wpn_Rocket", 180, -780, 0.45, "UI_Weapon_Rocket"),
        ("Wpn_Tesla", 330, -780, 0.45, "UI_Weapon_Tesla"),
    ]
    for sp_key, x, z, scale, label in weapon_items:
        spawn_sprite_actor(sprites.get(sp_key), unreal.Vector(x, -60, z), scale, 95, label)
        
    # 5.5 底部玩家血条与经验条
    spawn_sprite_actor(sprites.get("HUD_HP_Bg"), unreal.Vector(-360, -60, -750), 0.65, 90, "UI_Player_HP_Bg")
    spawn_sprite_actor(sprites.get("HUD_HP_Fill"), unreal.Vector(-360, -60, -750), 0.63, 95, "UI_Player_HP_Fill")
    spawn_sprite_actor(sprites.get("HUD_Exp_Fill"), unreal.Vector(-360, -60, -810), 0.55, 95, "UI_Player_EXP_Fill")

    # 6. 保存关卡
    unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    log("==================================================================")
    log("🎉 1:1 概念图高精美术关卡与 HUD 实装构建完成！MAP_GGBOM_Main SAVED!")
    log("==================================================================")

if __name__ == "__main__":
    build_art_stage_00()
