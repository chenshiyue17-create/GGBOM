# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
ASSETS = unreal.EditorAssetLibrary
LEVEL_SUBSYS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUBSYS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def run():
    LEVEL_SUBSYS.load_level("/Game/GGBOM/Maps/MAP_GGBOM_Main")
    actors = ACTOR_SUBSYS.get_all_level_actors()

    boss = None
    for a in actors:
        if a.get_actor_label() == "Live_Boss_Overlord":
            boss = a
            break
    if not boss:
        raise RuntimeError("Live_Boss_Overlord not found in map")

    # 1. 确保 GlowBorder 轴心为 CENTER_LEFT
    sp_fill_path = "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_10_GlowBorder"
    sp_fill = ASSETS.load_asset(sp_fill_path)
    if sp_fill:
        sp_fill.set_editor_property("pivot_mode", unreal.SpritePivotMode.CENTER_LEFT)
        ASSETS.save_loaded_asset(sp_fill)

    # 2. 精确相对坐标与比例
    configs = {
        "BossBar_Armor": {
            "sprite": "/Game/P01/Imported/Content/Asset/Art/07_UI/01_CombatHUD/Sprites/SP_T_UI_HUD_08_Minimap_Frame",
            "rel_loc": unreal.Vector(0.0, -5.0, 115.0),
            "scale": unreal.Vector(0.32, 1.0, 0.30),
            "tags": ["BossBarGroup"]
        },
        "BossBar_Track": {
            "sprite": "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_09_ProgressTrack",
            "rel_loc": unreal.Vector(0.0, -8.0, 115.0),
            "scale": unreal.Vector(0.30, 1.0, 0.30),
            "tags": ["BossBarGroup"]
        },
        "BossBar_Fill": {
            "sprite": sp_fill_path,
            "rel_loc": unreal.Vector(-32.0, -12.0, 115.0),
            "scale": unreal.Vector(0.20, 1.0, 0.16),
            "tags": ["BossBarGroup", "BossBarFill"]
        },
        "BossBar_Insignia": {
            "sprite": "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_02_HeaderRibbon",
            "rel_loc": unreal.Vector(-62.0, -16.0, 115.0),
            "scale": unreal.Vector(0.24, 1.0, 0.24),
            "tags": ["BossBarGroup"]
        }
    }

    for a in actors:
        lbl = a.get_actor_label()
        if lbl in configs:
            cfg = configs[lbl]
            root = a.get_editor_property("root_component")
            root.set_mobility(unreal.ComponentMobility.MOVABLE)
            sp_comp = a.get_component_by_class(unreal.PaperSpriteComponent)
            if sp_comp:
                sp_comp.set_mobility(unreal.ComponentMobility.MOVABLE)
                sp_obj = ASSETS.load_asset(cfg["sprite"])
                if sp_obj:
                    sp_comp.set_editor_property("source_sprite", sp_obj)
            
            a.set_actor_enable_collision(False)
            a.attach_to_actor(boss, unreal.Name(), unreal.AttachmentRule.KEEP_RELATIVE,
                             unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_WORLD, False)
            root.set_editor_property("relative_location", cfg["rel_loc"])
            a.set_actor_scale3d(cfg["scale"])
            a.tags = [unreal.Name(t) for t in cfg["tags"]]
            print(f"[STEP4] {lbl} configured: {cfg['rel_loc']}")

    saved_lvl = LEVEL_SUBSYS.save_current_level()
    print(f"[STEP4] MAP_GGBOM_Main SAVED: {saved_lvl}")

if __name__ == "__main__":
    run()
