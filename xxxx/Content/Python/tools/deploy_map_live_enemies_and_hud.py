# -*- coding: utf-8 -*-
"""
UE5.8 2D 竖屏游戏主关卡 MAP_GGBOM_Main 组装:
1. 9:16 精密正交相机对齐 (OrthoWidth=941.0, 纵向 16:9 画幅)
2. 全动态动画怪物军团 (Zombie, MutantHound, Shambler, Boss Overlord) 播放真实 Flipbook 步态帧动画
3. 9:16 像素级 HUD 对齐 (Boss血条, 暂停按钮, 玩家血条, 经验条, 弹药盘)
"""
from __future__ import annotations
import unreal

GEN = "/Game/GGBOM"
MAP_PATH = f"{GEN}/Maps/MAP_GGBOM_Main"

ASSETS = unreal.EditorAssetLibrary

def main():
    print("🗺️ 正在组装 MAP_GGBOM_Main (9:16 像素级 HUD + 动态动画怪物军团)...")
    
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 清理所有非玩家旧实体
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        if not lbl.startswith("PlayerStart"):
            unreal.EditorLevelLibrary.destroy_actor(a)
            
    # 1. 9:16 正交相机 (100% 满屏正视 X-Z 平面, OrthoWidth=941.0)
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(0, -600, 0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    cam_comp.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    cam_comp.set_editor_property("ortho_width", 941.0)
    cam_comp.set_editor_property("aspect_ratio", 0.5628)
    cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    cam.set_actor_label("PortraitCamera_9x16")
    
    # 2. 地面底层 (Y=+80) 与 战术掩体
    sp_ground = unreal.load_asset(f"{GEN}/Art/Sprites/SP_Ground")
    if sp_ground:
        g = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, unreal.Vector(0, 80, 0), unreal.Rotator())
        g.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("source_sprite", sp_ground)
        g.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("translucency_sort_priority", -100)
        g.set_actor_scale3d(unreal.Vector(1.15, 1.15, 1.15))
        g.set_actor_label("Ground_Stage00")
        
    sp_barricade = unreal.load_asset(f"{GEN}/Art/Sprites/SP_Barricade")
    if sp_barricade:
        for x, z, lbl in ((-180, 420, "Barricade_Top_L"), (180, 420, "Barricade_Top_R"), (-220, 0, "DefenseLine_L"), (220, 0, "DefenseLine_R")):
            b = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, unreal.Vector(x, 15, z), unreal.Rotator())
            b.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("source_sprite", sp_barricade)
            b.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("translucency_sort_priority", 6)
            b.set_actor_scale3d(unreal.Vector(0.55, 0.55, 0.55))
            b.set_actor_label(lbl)

    # 3. 部署【动态动画怪物军团】(使用原生 PaperFlipbookActor，100% 播放连续帧动画)
    fb_zombie = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet")
    fb_hound = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet")
    fb_shambler = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet")
    fb_boss = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet")

    live_enemies = [
        (fb_zombie, -140, 260, 0.45, "Live_Zombie_01"),
        (fb_zombie, 0, 320, 0.45, "Live_Zombie_02"),
        (fb_zombie, 140, 280, 0.45, "Live_Zombie_03"),
        (fb_shambler, 0, 180, 0.55, "Live_Shambler_Elite"),
        (fb_hound, -180, 120, 0.48, "Live_Hound_01"),
        (fb_hound, 180, 140, 0.48, "Live_Hound_02"),
        (fb_boss, 0, 500, 0.72, "Live_Boss_Overlord"),
    ]

    for fb, x, z, scale, lbl in live_enemies:
        if fb:
            act = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperFlipbookActor, unreal.Vector(x, 0, z), unreal.Rotator())
            comp = act.get_component_by_class(unreal.PaperFlipbookComponent)
            comp.set_editor_property("source_flipbook", fb)
            comp.set_editor_property("translucency_sort_priority", 200)
            comp.set_editor_property("visible", True)
            comp.set_editor_property("hidden_in_game", False)
            act.set_actor_scale3d(unreal.Vector(scale, scale, scale))
            act.set_actor_label(lbl)
            print(f"  + 部署动态动画怪物: {lbl} @ ({x}, 0, {z})")

    # 4. 玩家出生点 (下方中央)
    p_starts = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label().startswith("PlayerStart")]
    if not p_starts:
        ps = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -10, -500), unreal.Rotator())
        ps.set_actor_label("PlayerStart")
    else:
        p_starts[0].set_actor_location(unreal.Vector(0, -10, -500), False, False)

    # 5. 精密对齐 HUD 部件 (按 9:16 安全画幅严格排布)
    hud_items = [
        # 顶部 Boss 血条 (居中偏上 Z=+720)
        (f"{GEN}/Art/Sprites/SP_Boss_Bar_Bg", unreal.Vector(0, -60, 720), 0.75, 90, "UI_BossBar_Bg"),
        (f"{GEN}/Art/Sprites/SP_Boss_Bar_Fill", unreal.Vector(0, -60, 720), 0.72, 95, "UI_BossBar_Fill"),
        (f"{GEN}/Art/Sprites/SP_Boss_Skull", unreal.Vector(-200, -60, 720), 0.55, 100, "UI_Boss_SkullIcon"),
        # 顶部右上角暂停按钮 (Z=+720, X=+360)
        (f"{GEN}/Art/Sprites/SP_Btn_Pause", unreal.Vector(360, -60, 720), 0.25, 100, "UI_Btn_Pause"),
        # 底部血条与经验条 (居中偏下 Z=-680)
        (f"{GEN}/Art/Sprites/SP_HUD_HP_Bg", unreal.Vector(-200, -60, -680), 0.58, 90, "UI_Player_HP_Bg"),
        (f"{GEN}/Art/Sprites/SP_HUD_HP_Fill", unreal.Vector(-200, -60, -680), 0.56, 95, "UI_Player_HP_Fill"),
        (f"{GEN}/Art/Sprites/SP_HUD_Exp_Fill", unreal.Vector(-200, -60, -730), 0.48, 95, "UI_Player_EXP_Fill"),
        # 底部右侧弹药盘
        (f"{GEN}/Art/Sprites/SP_HUD_AmmoRadial", unreal.Vector(320, -60, -680), 0.45, 95, "UI_HUD_AmmoRadial"),
    ]
    for sp_p, loc, sc, prio, lbl in hud_items:
        sp = unreal.load_asset(sp_p)
        if sp:
            act = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, loc, unreal.Rotator())
            act.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("source_sprite", sp)
            act.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("translucency_sort_priority", prio)
            act.set_actor_scale3d(unreal.Vector(sc, sc, sc))
            act.set_actor_label(lbl)

    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    print("ALL_MAP_ENTITIES_AND_HUD_DEPLOYED_SUCCESSFULLY")

if __name__ == "__main__":
    main()
