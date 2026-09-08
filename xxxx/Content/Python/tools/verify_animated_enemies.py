# -*- coding: utf-8 -*-
"""
验证 MAP_GGBOM_Main 中敌人动画与组件状态
"""
from __future__ import annotations
import json
from pathlib import Path
import unreal

ROOT = Path("/Users/cc/Desktop/GGBOM/xxxx")
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"

def log(msg: str):
    print(f"[VerifyEnemies] {msg}")
    unreal.log(f"[VerifyEnemies] {msg}")

def main():
    log("=== 开始全面审查关卡敌人动画绑定与场景完整性 ===")
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        log("❌ 无法加载地图！")
        return

    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    log(f"当前场景 Actor 总数: {len(actors)}")

    enemy_details = []
    has_cam = False
    has_ground = False
    cam_details = {}

    for a in actors:
        lbl = a.get_actor_label()
        cls_name = a.get_class().get_name()

        if lbl == "PortraitCamera_9x16":
            has_cam = True
            cam_comp = a.get_component_by_class(unreal.CameraComponent)
            if cam_comp:
                cam_details = {
                    "projection_mode": str(cam_comp.get_editor_property("projection_mode")),
                    "ortho_width": cam_comp.get_editor_property("ortho_width"),
                    "aspect_ratio": cam_comp.get_editor_property("aspect_ratio")
                }

        if lbl == "Ground_Stage00":
            has_ground = True

        # 检查是否为敌人相关
        if any(k in lbl.lower() for k in ["enemy", "zombie", "hound", "brute", "boss", "spitter", "runner"]):
            fb_comp = a.get_component_by_class(unreal.PaperFlipbookComponent)
            sp_comp = a.get_component_by_class(unreal.PaperSpriteComponent)
            
            fb_info = None
            if fb_comp:
                fb_asset = fb_comp.get_editor_property("source_flipbook")
                scale = fb_comp.get_editor_property("relative_scale3d")
                num_frames = fb_asset.get_num_frames() if fb_asset else 0
                fb_info = {
                    "has_flipbook_comp": True,
                    "flipbook_name": fb_asset.get_name() if fb_asset else None,
                    "num_frames": num_frames,
                    "total_duration": fb_asset.get_total_duration() if fb_asset else 0.0,
                    "scale": [scale.x, scale.y, scale.z],
                    "looping": fb_comp.is_looping() if hasattr(fb_comp, "is_looping") else None
                }

            loc = a.get_actor_location()
            enemy_details.append({
                "label": lbl,
                "class": cls_name,
                "location": [loc.x, loc.y, loc.z],
                "has_sprite_comp": sp_comp is not None,
                "flipbook_info": fb_info
            })

    report = {
        "status": "PASS" if all(e["flipbook_info"] and e["flipbook_info"]["flipbook_name"] for e in enemy_details) else "FAIL",
        "has_camera": has_cam,
        "camera_details": cam_details,
        "has_ground": has_ground,
        "enemy_count": len(enemy_details),
        "enemies": enemy_details
    }

    out_file = OUT_DIR / "verified_animated_enemies.json"
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"审查结果已写入: {out_file}")
    log(f"总计检测到 {len(enemy_details)} 个敌人实例，状态: {report['status']}")
    for e in enemy_details:
        fb_name = e["flipbook_info"]["flipbook_name"] if e["flipbook_info"] else "NONE"
        frames = e["flipbook_info"]["num_frames"] if e["flipbook_info"] else 0
        log(f"  - [{e['label']}] Class={e['class']}, Flipbook={fb_name}, 帧数={frames}")

if __name__ == "__main__":
    main()
