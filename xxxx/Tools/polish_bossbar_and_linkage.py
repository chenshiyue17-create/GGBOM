# -*- coding: utf-8 -*-
"""
polish_bossbar_and_linkage.py
精细化调整 MAP_GGBOM_Main 中由用户指定的 4 大 UI 素材构筑的 Boss 豪华血条：
1. T_UI_HUD_08_Minimap_Frame (Boss 徽章头像框)
2. T_UI_Modal_02_HeaderRibbon (顶部领主称号横幅)
3. T_UI_Modal_10_GlowBorder (外围金色流光发光框)
4. T_UI_Modal_09_ProgressTrack (血槽金属刻度底轨)
5. SP_T_UI_BossBar_01_Seg1_Fill (鲜红能量填充)
6. SP_T_UI_BossBar_05_Skull_Normal (首领骷髅徽章)
下移至屏幕黄金视野区 (Z=640~685)，隐藏旧的杂乱方块。
"""
import unreal
from pathlib import Path
import traceback

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/polish_bossbar.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

ASSETS = unreal.EditorAssetLibrary
LEVEL_SUBSYS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUBSYS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def log(msg):
    print(f"[POLISH_BOSSBAR] {msg}", flush=True)

def run():
    map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
    log(f"🗺️ 加载关卡: {map_path}")
    LEVEL_SUBSYS.load_level(map_path)

    actors = ACTOR_SUBSYS.get_all_level_actors()
    actor_map = {a.get_actor_label(): a for a in actors}

    mat = ASSETS.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")

    # 隐藏旧的冲突 Actor
    legacy_labels = ["UI_BossBar_Bg", "UI_Btn_Pause"]
    for l in legacy_labels:
        if l in actor_map:
            actor_map[l].set_actor_hidden_in_game(True)
            log(f"🙈 隐藏旧 UI: {l}")

    # 精确黄金视觉区布局 (360x640 竖屏视野顶部)
    bossbar_elements = [
        # 1. 顶部领主称号横幅 HeaderRibbon
        ("UI_Boss_Ribbon", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_02_HeaderRibbon", unreal.Vector(0.0, -58.0, 680.0), unreal.Vector(0.50, 1.0, 0.42)),
        # 2. 血槽底轨 ProgressTrack
        ("UI_BossBar_Track", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_09_ProgressTrack", unreal.Vector(25.0, -59.0, 638.0), unreal.Vector(0.44, 1.0, 0.40)),
        # 3. 外围发光流光框 GlowBorder
        ("UI_BossBar_Glow", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_10_GlowBorder", unreal.Vector(25.0, -60.0, 638.0), unreal.Vector(0.44, 1.0, 0.40)),
        # 4. 血条红色填充 Seg1_Fill
        ("UI_BossBar_Fill", "/Game/P01/Imported/Content/Asset/Art/07_UI/03_BossHealthBar/Sprites/SP_T_UI_BossBar_01_Seg1_Fill", unreal.Vector(25.0, -61.0, 638.0), unreal.Vector(0.43, 1.0, 0.38)),
        # 5. 头像外框 Minimap_Frame
        ("UI_Boss_Frame", "/Game/P01/Imported/Content/Asset/Art/07_UI/01_CombatHUD/Sprites/SP_T_UI_HUD_08_Minimap_Frame", unreal.Vector(-135.0, -60.0, 638.0), unreal.Vector(0.38, 1.0, 0.38)),
        # 6. 头像内骷髅徽章 Skull_Normal
        ("UI_Boss_SkullIcon", "/Game/P01/Imported/Content/Asset/Art/07_UI/03_BossHealthBar/Sprites/SP_T_UI_BossBar_05_Skull_Normal", unreal.Vector(-135.0, -61.0, 638.0), unreal.Vector(0.30, 1.0, 0.30)),
    ]

    for label, sp_path, loc, scale in bossbar_elements:
        sp = ASSETS.load_asset(sp_path)
        if not sp:
            log(f"⚠️ 未找到 Sprite: {sp_path}")
            continue

        actor = actor_map.get(label)
        if not actor:
            actor = ACTOR_SUBSYS.spawn_actor_from_class(unreal.PaperSpriteActor, loc)
            actor.set_actor_label(label)
            log(f"➕ 生成新 Actor: {label}")
        else:
            actor.set_actor_location(loc, False, False)
            log(f"🔄 更新已有 Actor: {label}")

        actor.set_actor_scale3d(scale)
        actor.set_actor_enable_collision(False)
        actor.set_actor_hidden_in_game(False)

        comp = actor.get_component_by_class(unreal.PaperSpriteComponent)
        if comp:
            comp.set_editor_property("source_sprite", sp)
            if mat:
                comp.set_material(0, mat)
            comp.set_editor_property("translucency_sort_priority", 3500)
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

    saved = LEVEL_SUBSYS.save_current_level()
    log(f"💾 关卡保存成功: {saved}")
    OUT.write_text(f"SAVED: {saved}\n", encoding="utf-8")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        err = traceback.format_exc()
        log(f"ERROR: {err}")
        OUT.write_text(f"ERROR: {err}\n", encoding="utf-8")
        raise
