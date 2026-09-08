# -*- coding: utf-8 -*-
"""
UE5.8 2D 竖屏游戏: 全量怪物美术资源动画配置与数据驱动实体管线
1. 自动化扫描并校准所有 18 种丧尸、猎犬全动作各朝向、领主 Boss 全部动作与 10 大技能 Flipbooks
2. 设置科学合理的采样帧率，消除鬼畜，呈现自然张力
3. 部署主关卡全怪物阵列
"""
from __future__ import annotations
import unreal
from pathlib import Path

GEN = "/Game/GGBOM"
MAP_PATH = f"{GEN}/Maps/MAP_GGBOM_Main"

ASSETS = unreal.EditorAssetLibrary

def build_all_enemy_flipbooks():
    print("🧟 [1/3] 正在全盘构建与校准所有怪物动作/技能动画 Flipbooks...")
    
    # 1. 丧尸 18 种系列
    zombie_types = [
        ("01_Zombie_Walker_Basic", "FB_T_Zombie_WalkerBasic_Sheet", 4.0),
        ("02_Zombie_Crawler_Low", "FB_T_Zombie_CrawlerLow_Sheet", 3.5),
        ("03_Zombie_Infected_Civilian", "FB_T_Zombie_InfectedCiv_Sheet", 4.0),
        ("04_Zombie_Spitter_Minor", "FB_T_Zombie_SpitterMinor_Sheet", 3.8),
        ("05_Zombie_Runner_Agile", "FB_T_Zombie_RunnerAgile_Sheet", 5.5),
        ("06_Zombie_Bloater_Minor", "FB_T_Zombie_BloaterMinor_Sheet", 3.0),
        ("07_Zombie_Armored_Guard", "FB_T_Zombie_ArmoredGuard_Sheet", 3.2),
        ("08_Zombie_Acid_Carrier", "FB_T_Zombie_AcidCarrier_Sheet", 3.8),
        ("09_Zombie_Husk_Dried", "FB_T_Zombie_HuskDried_Sheet", 3.5),
        ("10_Zombie_Leaper_Small", "FB_T_Zombie_LeaperSmall_Sheet", 5.0),
        ("11_Zombie_Shambler_Heavy", "FB_T_Zombie_ShamblerHeavy_Sheet", 3.2),
        ("12_Zombie_Corrosive_Spawn", "FB_T_Zombie_CorrosiveSpawn_Sheet", 4.5),
        ("13_Zombie_Flesh_Stalker", "FB_T_Zombie_FleshStalker_Sheet", 4.2),
        ("14_Zombie_Decayed_Worker", "FB_T_Zombie_DecayedWorker_Sheet", 3.6),
        ("15_Zombie_Mutated_Ghouls", "FB_T_Zombie_MutatedGhouls_Sheet", 4.8),
        ("16_Zombie_Toxic_Walker", "FB_T_Zombie_ToxicWalker_Sheet", 3.8),
        ("17_Zombie_Subterranean_Burrower", "FB_T_Zombie_Burrower_Sheet", 4.0),
        ("18_Zombie_Berserk_Thrall", "FB_T_Zombie_BerserkThrall_Sheet", 5.2),
    ]

    base_pfx = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie"
    for z_name, fb_name, fps in zombie_types:
        fb_pkg = f"{base_pfx}/{z_name}/Flipbooks/{fb_name}"
        fb = unreal.load_asset(fb_pkg)
        if fb:
            fb.set_editor_property("frames_per_second", fps)
            ASSETS.save_loaded_asset(fb, only_if_is_dirty=False)
            print(f"  + 丧尸动画已就绪: {z_name} -> {fb_name} @ {fps} FPS")

    # 2. 猎犬 5 大动作 × 4 方向
    hound_actions = [
        ("Run", 6.0),
        ("Bite_Combo", 6.5),
        ("Pounce", 5.5),
        ("Howl", 4.0),
        ("Death", 4.5),
    ]
    hound_dirs = ["Dir_01_Down", "Dir_02_Right", "Dir_03_Up", "Dir_04_Left"]
    hound_base = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound"
    for act, fps in hound_actions:
        short_act = "Bite" if act == "Bite_Combo" else act
        for d in hound_dirs:
            fb_pkg = f"{hound_base}/{act}/{d}/Flipbooks/FB_T_Hound_{short_act}_{d}_Sheet"
            fb = unreal.load_asset(fb_pkg)
            if fb:
                fb.set_editor_property("frames_per_second", fps)
                ASSETS.save_loaded_asset(fb, only_if_is_dirty=False)
                print(f"  + 猎犬动作就绪: {act}/{d} @ {fps} FPS")

    # 3. 领主 Boss 5 大动作 × 4 方向 + 10 大技能
    boss_actions = [
        ("Walk", "Walk", 3.5),
        ("Heavy_Cleave", "Cleave", 5.0),
        ("Ground_Slam", "Slam", 4.5),
        ("Enrage_Roar", "Enrage", 4.0),
        ("Death_Collapse", "Death", 3.5),
    ]
    boss_dirs = ["Dir_01_Down", "Dir_02_Right", "Dir_03_Up", "Dir_04_Left"]
    boss_base = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord"
    for act_dir, act_short, fps in boss_actions:
        for d in boss_dirs:
            fb_pkg = f"{boss_base}/Actions/{act_dir}/{d}/Flipbooks/FB_T_Boss_{act_short}_{d}_Sheet"
            fb = unreal.load_asset(fb_pkg)
            if fb:
                fb.set_editor_property("frames_per_second", fps)
                ASSETS.save_loaded_asset(fb, only_if_is_dirty=False)
                print(f"  + Boss 动作就绪: {act_dir}/{d} @ {fps} FPS")

    # Boss 技能
    boss_skills = [
        ("01_FlameWave", "FB_T_BossSkill_FlameWave_Sheet", 7.0),
        ("03_EarthSpikes", "FB_T_BossSkill_EarthSpikes_Sheet", 6.0),
        ("04_AcidPool", "FB_T_BossSkill_AcidPool_Sheet", 5.0),
        ("05_SporeBomb", "FB_T_BossSkill_SporeBomb_Sheet", 6.0),
        ("06_EggSummon", "FB_T_BossSkill_EggSummon_Sheet", 5.5),
        ("08_BlightBreath", "FB_T_BossSkill_BlightBreath_Sheet", 6.5),
        ("09_MeteorRain", "FB_T_BossSkill_MeteorRain_Sheet", 7.0),
        ("10_BioShield", "FB_T_BossSkill_BioShield_Sheet", 5.0),
    ]
    for sk_folder, fb_name, fps in boss_skills:
        fb_pkg = f"{boss_base}/Skills/{sk_folder}/Flipbooks/{fb_name}"
        fb = unreal.load_asset(fb_pkg)
        if fb:
            fb.set_editor_property("frames_per_second", fps)
            ASSETS.save_loaded_asset(fb, only_if_is_dirty=False)
            print(f"  + Boss 技能特效就绪: {sk_folder} @ {fps} FPS")

# ==============================================================================
# 2. 组装主关卡 MAP_GGBOM_Main 全怪物精美陈列
# ==============================================================================
def assemble_showcase_level():
    print("🗺️ [2/3] 正在主关卡 MAP_GGBOM_Main 部署全套动态怪物与技能阵容...")
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        if not lbl.startswith("PlayerStart"):
            unreal.EditorLevelLibrary.destroy_actor(a)
            
    # 1. 9:16 正交相机 (满屏正视 X-Z 平面, OrthoWidth=941.0)
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(0, -600, 0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    cam_comp.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    cam_comp.set_editor_property("ortho_width", 941.0)
    cam_comp.set_editor_property("aspect_ratio", 0.5628)
    cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    cam.set_actor_label("PortraitCamera_9x16")
    
    # 2. 地面与掩体
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

    # 3. 部署精选怪物矩阵 (前排丧尸行者、中排敏捷突击与装甲、后排重锤与狂暴领主)
    pfx_z = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie"
    pfx_h = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound"
    pfx_b = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord"

    showcase_units = [
        # 前锋线 (Z=+150 ~ +260)
        (f"{pfx_z}/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet", -150, 220, 0.45, "Unit_Zombie_Walker"),
        (f"{pfx_z}/05_Zombie_Runner_Agile/Flipbooks/FB_T_Zombie_RunnerAgile_Sheet", 0, 240, 0.45, "Unit_Zombie_Runner"),
        (f"{pfx_z}/04_Zombie_Spitter_Minor/Flipbooks/FB_T_Zombie_SpitterMinor_Sheet", 150, 220, 0.45, "Unit_Zombie_Spitter"),
        
        # 中坚突击犬与装甲线 (Z=+300 ~ +380)
        (f"{pfx_h}/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet", -200, 320, 0.48, "Unit_Hound_Run"),
        (f"{pfx_h}/Bite_Combo/Dir_01_Down/Flipbooks/FB_T_Hound_Bite_Dir_01_Down_Sheet", -80, 340, 0.48, "Unit_Hound_Bite"),
        (f"{pfx_z}/07_Zombie_Armored_Guard/Flipbooks/FB_T_Zombie_ArmoredGuard_Sheet", 80, 340, 0.48, "Unit_Zombie_Armored"),
        (f"{pfx_h}/Pounce/Dir_01_Down/Flipbooks/FB_T_Hound_Pounce_Dir_01_Down_Sheet", 200, 320, 0.48, "Unit_Hound_Pounce"),

        # 重装与压轴领主 (Z=+440 ~ +540)
        (f"{pfx_z}/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet", -140, 440, 0.58, "Unit_Zombie_Shambler"),
        (f"{pfx_z}/18_Zombie_Berserk_Thrall/Flipbooks/FB_T_Zombie_BerserkThrall_Sheet", 140, 440, 0.55, "Unit_Zombie_Berserk"),
        (f"{pfx_b}/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet", 0, 520, 0.72, "Unit_Boss_Overlord"),

        # Boss 两侧护法技能特效
        (f"{pfx_b}/Skills/01_FlameWave/Flipbooks/FB_T_BossSkill_FlameWave_Sheet", -240, 520, 0.50, "FX_FlameWave"),
        (f"{pfx_b}/Skills/10_BioShield/Flipbooks/FB_T_BossSkill_BioShield_Sheet", 240, 520, 0.50, "FX_BioShield"),
    ]

    for fb_path, x, z, scale, lbl in showcase_units:
        fb = unreal.load_asset(fb_path)
        if fb:
            act = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperFlipbookActor, unreal.Vector(x, 0, z), unreal.Rotator())
            comp = act.get_component_by_class(unreal.PaperFlipbookComponent)
            comp.set_editor_property("source_flipbook", fb)
            comp.set_editor_property("translucency_sort_priority", 200)
            comp.set_editor_property("visible", True)
            comp.set_editor_property("hidden_in_game", False)
            act.set_actor_scale3d(unreal.Vector(scale, scale, scale))
            act.set_actor_label(lbl)
            print(f"  + 关卡实装怪物单位: {lbl} @ ({x}, 0, {z})")

    # 4. 玩家出生点 (下方中央)
    p_starts = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label().startswith("PlayerStart")]
    if not p_starts:
        ps = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -10, -500), unreal.Rotator())
        ps.set_actor_label("PlayerStart")
    else:
        p_starts[0].set_actor_location(unreal.Vector(0, -10, -500), False, False)

    # 5. 精密对齐 HUD 部件
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
    ASSETS.save_directory("/Game/P01/Imported/Content/Asset/Art/02_Enemies", only_if_is_dirty=False, recursive=True)
    print("ALL_ENEMY_ANIMATIONS_AND_LEVEL_DEPLOYMENT_COMPLETE")

def main():
    build_all_enemy_flipbooks()
    assemble_showcase_level()

if __name__ == "__main__":
    main()
