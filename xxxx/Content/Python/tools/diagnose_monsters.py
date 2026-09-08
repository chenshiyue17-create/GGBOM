# -*- coding: utf-8 -*-
import unreal
import json
from pathlib import Path

out_path = Path("/Users/cc/Desktop/GGBOM/xxxx/output/monster_diagnosis.json")
out_path.parent.mkdir(parents=True, exist_ok=True)

report = {
    "enemy_flipbooks": [],
    "enemy_blueprints": [],
    "level_actors": [],
    "data_tables": []
}

ASSETS = unreal.EditorAssetLibrary

# 1. 扫描关卡所有 Actor
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if world:
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for a in actors:
        lbl = a.get_actor_label()
        cls_name = a.get_class().get_name()
        loc = a.get_actor_location()
        scale = a.get_actor_scale3d()
        
        info = {
            "label": lbl,
            "class": cls_name,
            "pos": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
            "scale": [round(scale.x, 3), round(scale.y, 3), round(scale.z, 3)],
        }
        
        # 检查 Sprite / Flipbook 组件
        sp_comp = a.get_component_by_class(unreal.PaperSpriteComponent)
        if sp_comp:
            sp = sp_comp.get_editor_property("source_sprite")
            info["source_sprite"] = sp.get_path_name() if sp else None
            info["sprite_hidden"] = sp_comp.get_editor_property("hidden_in_game")
            
        fb_comp = a.get_component_by_class(unreal.PaperFlipbookComponent)
        if fb_comp:
            fb = fb_comp.get_editor_property("source_flipbook")
            info["source_flipbook"] = fb.get_path_name() if fb else None
            info["fb_hidden"] = fb_comp.get_editor_property("hidden_in_game")
            if fb:
                info["fb_fps"] = fb.get_editor_property("frames_per_second")
                info["fb_num_frames"] = fb.get_num_frames()
                info["fb_num_keyframes"] = fb.get_num_key_frames()
                
        report["level_actors"].append(info)

# 2. 搜索 Enemy Flipbook 资产
fb_assets = ASSETS.list_assets("/Game", recursive=True, include_folder=False)
for p in fb_assets:
    if "Flipbook" in p or "/FB_" in p or "FB_T_" in p:
        if any(k in p.lower() for k in ["zombie", "enemy", "boss", "hound", "mutant", "crawler", "shambler", "spitter"]):
            asset = unreal.load_asset(p)
            if asset and isinstance(asset, unreal.PaperFlipbook):
                report["enemy_flipbooks"].append({
                    "path": p,
                    "name": asset.get_name(),
                    "fps": asset.get_editor_property("frames_per_second"),
                    "num_frames": asset.get_num_frames(),
                    "num_keyframes": asset.get_num_key_frames()
                })

# 3. 搜索 Enemy Blueprint 资产
for p in fb_assets:
    if any(k in p.lower() for k in ["enemy", "boss", "zombie", "hound"]):
        if p.endswith("_C") or "/BP_" in p:
            bp = unreal.load_asset(p)
            if bp and isinstance(bp, unreal.Blueprint):
                try:
                    parent_cls = bp.parent_class
                    p_name = parent_cls.get_name() if parent_cls else None
                except Exception:
                    p_name = str(getattr(bp, "parent_class", None))
                report["enemy_blueprints"].append({
                    "path": p,
                    "name": bp.get_name(),
                    "parent": p_name
                })

out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"DIAGNOSIS_WRITTEN: {len(report['level_actors'])} actors, {len(report['enemy_flipbooks'])} enemy flipbooks, {len(report['enemy_blueprints'])} enemy bps")
