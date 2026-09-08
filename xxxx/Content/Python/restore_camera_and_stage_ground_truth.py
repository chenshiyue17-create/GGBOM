# -*- coding: utf-8 -*-
"""
================================================================================
restore_camera_and_stage_ground_truth.py
严格将摄像机和主地图坐标恢复至官方标准视觉基准 (Ground Truth Baseline)
1. 摄像机恢复:
   - 唯一保留 PortraitCamera_9x16，消除所有副相机
   - Location: (0, -600, 0)
   - Rotation: Rotator(pitch=0.0, yaw=90.0, roll=0.0) [严禁直接传位置参数导致 pitch 变为 90!]
   - OrthoWidth: 941.0, AspectRatio: 0.562799 (9:16 全屏满视口), NearClip=-10000, FarClip=10000
2. 地图所有 PaperSpriteActor 旋转归零 (彻底撤销 90 度旋转历史错误):
   - Ground_Stage00: Loc(0, 80, 0), Rot(0, 0, 0), Scale(1.15, 1.15, 1.15)
   - Barricade_Top_L/R: Rot(0, 0, 0)
   - DefenseLine_L/R: Rot(0, 0, 0)
3. 玩家出生点与动态敌人坐标对齐:
   - PlayerStart: (0, 0, -480), Rot(0, 0, 0)
   - 敌人实体全部确保 Y=0 平面，Rot(0, 0, 0)
================================================================================
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"

def log(msg):
    print(f"[RESTORE] {msg}", flush=True)

def restore_ground_truth():
    log("==================================================")
    log("🚀 正在执行【编辑器内实时热更新】摄像机与地图坐标官方基线恢复...")
    world = unreal.EditorLevelLibrary.get_editor_world()
    curr_map = ""
    try:
        curr_map = unreal.EditorLevelLibrary.get_path_name_for_loaded_level()
    except Exception:
        pass
        
    if not world or "MAP_GGBOM_Main" not in curr_map:
        world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
        
    if not world:
        raise RuntimeError(f"无法加载或获取当前地图: {MAP_PATH}")

    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    
    # 1. 恢复摄像机
    cameras = [a for a in actors if isinstance(a, unreal.CameraActor)]
    target_cam = None
    for cam in cameras:
        lbl = cam.get_actor_label()
        if lbl == "PortraitCamera_9x16" or lbl == "Master_Orthographic_Camera":
            if not target_cam:
                target_cam = cam
                target_cam.set_actor_label("PortraitCamera_9x16")
            else:
                log(f"  🗑️ 删除重复多余相机: {lbl}")
                unreal.EditorLevelLibrary.destroy_actor(cam)
        else:
            if not target_cam:
                target_cam = cam
                target_cam.set_actor_label("PortraitCamera_9x16")
            else:
                log(f"  🗑️ 删除旧相机: {lbl}")
                unreal.EditorLevelLibrary.destroy_actor(cam)

    if target_cam:
        # 严格使用关键字参数，确保 pitch=0, yaw=90, roll=0!
        target_cam.set_actor_location(unreal.Vector(0.0, -600.0, 0.0), False, False)
        target_cam.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0), False)
        target_cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
        
        comp = target_cam.get_component_by_class(unreal.CameraComponent)
        if comp:
            comp.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
            comp.set_editor_property("ortho_width", 941.0)
            comp.set_editor_property("aspect_ratio", 941.0 / 1672.0)
            comp.set_editor_property("constrain_aspect_ratio", True)
            comp.set_editor_property("use_pawn_control_rotation", False)
            comp.set_editor_property("auto_calculate_ortho_planes", False)
            comp.set_editor_property("ortho_near_clip_plane", -10000.0)
            comp.set_editor_property("ortho_far_clip_plane", 10000.0)
            
        rot = target_cam.get_actor_rotation()
        loc = target_cam.get_actor_location()
        fwd = target_cam.get_actor_forward_vector()
        up = target_cam.get_actor_up_vector()
        right = target_cam.get_actor_right_vector()
        log(f"  📷 相机已恢复基线: Loc={loc}, Rot={rot}")
        log(f"     Forward={fwd}, Up={up}, Right={right}")

    # 2. 恢复所有 PaperSpriteActor 旋转归零 (Rotator(0, 0, 0))
    zero_rot = unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0)
    reset_sprite_count = 0
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        if isinstance(a, unreal.PaperSpriteActor):
            a.set_actor_rotation(zero_rot, False)
            reset_sprite_count += 1
            if lbl == "Ground_Stage00":
                a.set_actor_location(unreal.Vector(0.0, 80.0, 0.0), False, False)
                a.set_actor_scale3d(unreal.Vector(1.15, 1.15, 1.15))
                log("  🌱 地面 Ground_Stage00 已矫正: Loc=(0, 80, 0), Rot=(0, 0, 0), Scale=(1.15, 1.15, 1.15)")
            elif lbl == "Barricade_Top_L":
                a.set_actor_location(unreal.Vector(-200.0, 30.0, 420.0), False, False)
                a.set_actor_scale3d(unreal.Vector(0.55, 0.55, 0.55))
            elif lbl == "Barricade_Top_R":
                a.set_actor_location(unreal.Vector(200.0, 30.0, 420.0), False, False)
                a.set_actor_scale3d(unreal.Vector(0.55, 0.55, 0.55))
            elif lbl == "DefenseLine_L":
                a.set_actor_location(unreal.Vector(-220.0, 30.0, -50.0), False, False)
                a.set_actor_scale3d(unreal.Vector(0.55, 0.55, 0.55))
            elif lbl == "DefenseLine_R":
                a.set_actor_location(unreal.Vector(220.0, 30.0, -50.0), False, False)
                a.set_actor_scale3d(unreal.Vector(0.55, 0.55, 0.55))

    log(f"  🔄 已将 {reset_sprite_count} 个 PaperSpriteActor 的旋转全部重置为 Rot(0, 0, 0)")

    # 3. 矫正 PlayerStart 与敌人实体
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        cls_name = a.get_class().get_name()
        if isinstance(a, unreal.PlayerStart):
            a.set_actor_location(unreal.Vector(0.0, 0.0, -480.0), False, False)
            a.set_actor_rotation(zero_rot, False)
            log("  🎯 PlayerStart 已恢复: Loc=(0, 0, -480), Rot=(0, 0, 0)")
        elif "Enemy" in cls_name or "Boss" in cls_name or lbl.startswith("Live_"):
            loc = a.get_actor_location()
            # 确保处于战斗平面 Y=0
            a.set_actor_location(unreal.Vector(loc.x, 0.0, loc.z), False, False)
            a.set_actor_rotation(zero_rot, False)
            log(f"  👾 敌人实体矫正: {lbl} -> Loc=({loc.x}, 0, {loc.z}), Rot=(0, 0, 0)")

    # 4. 保存地图
    saved = unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    log(f"✅ 地图已保存: {saved}")

    report = {
        "status": "PASS" if saved else "FAIL",
        "camera_location": [0.0, -600.0, 0.0],
        "camera_rotation": [0.0, 90.0, 0.0],
        "reset_sprite_count": reset_sprite_count,
        "saved": saved
    }
    out_file = ROOT / "output/restore_ground_truth_report.json"
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    log(f"📄 还原报告已保存至: {out_file}")

if __name__ == "__main__":
    restore_ground_truth()
    log("🎉 摄像机与地图坐标已全部恢复至官方基线！")
