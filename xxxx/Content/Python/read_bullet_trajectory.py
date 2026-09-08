# -*- coding: utf-8 -*-
"""
================================================================================
read_bullet_trajectory.py
实时读取虚幻引擎运行场景中的子弹弹道数据 (位置、速度、朝向、物理状态、飞行轨迹)
================================================================================
"""
import os
import json
import time
import unreal

def capture_bullet_trajectory(sample_count=1, sample_interval=0.1):
    report_history = []
    
    bp_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    bullet_cls = bp.generated_class() if bp else None
    
    unreal.log("==================================================")
    unreal.log("🎯 [实时弹道捕获启动] 正在检索场景中所有战斗抛射物...")
    
    for s in range(sample_count):
        all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
        bullet_actors = []
        for a in all_actors:
            if not a:
                continue
            cname = a.get_class().get_name()
            aname = a.get_name()
            if "BP_ProjectileBase" in cname or "BP_ProjectileBase" in aname or (bullet_cls and isinstance(a, bullet_cls)):
                bullet_actors.append(a)
                
        snapshot = {
            "sample_index": s,
            "timestamp": time.time(),
            "count": len(bullet_actors),
            "bullets": []
        }
        
        for idx, b in enumerate(bullet_actors):
            loc = b.get_actor_location()
            rot = b.get_actor_rotation()
            vel = b.get_velocity()
            speed = vel.length()
            
            # 组件与物理参数检查
            move_comp = b.get_component_by_class(unreal.ProjectileMovementComponent)
            initial_speed = move_comp.get_editor_property("initial_speed") if move_comp else 0.0
            max_speed = move_comp.get_editor_property("max_speed") if move_comp else 0.0
            gravity = move_comp.get_editor_property("projectile_gravity_scale") if move_comp else 0.0
            is_active = move_comp.is_active() if move_comp else False
            
            root_comp = b.get_editor_property("root_component")
            scale = root_comp.get_editor_property("relative_scale3d") if root_comp else unreal.Vector(1, 1, 1)
            
            b_info = {
                "name": b.get_name(),
                "location": {"X": round(loc.x, 2), "Y": round(loc.y, 2), "Z": round(loc.z, 2)},
                "rotation": {"Pitch": round(rot.pitch, 2), "Yaw": round(rot.yaw, 2), "Roll": round(rot.roll, 2)},
                "velocity": {"X": round(vel.x, 2), "Y": round(vel.y, 2), "Z": round(vel.z, 2)},
                "speed": round(speed, 2),
                "initial_speed": initial_speed,
                "gravity": gravity,
                "scale3d": {"X": round(scale.x, 3), "Y": round(scale.y, 3), "Z": round(scale.z, 3)},
                "movement_active": is_active
            }
            snapshot["bullets"].append(b_info)
            
            if s == 0:
                unreal.log(f"  📍 [{idx}] {b.get_name()}:")
                unreal.log(f"     • 空间坐标 Location : ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")
                unreal.log(f"     • 实时速度 Velocity : ({vel.x:.1f}, {vel.y:.1f}, {vel.z:.1f}) | 标量速率: {speed:.1f}")
                unreal.log(f"     • 弹道俯仰 Pitch/Yaw: ({rot.pitch:.1f}°, {rot.yaw:.1f}°)")
                unreal.log(f"     • 物理缩放 Scale3D  : ({scale.x:.2f}, {scale.y:.2f}, {scale.z:.2f}) | 重力系数: {gravity}")
                unreal.log(f"     • 动能组件活跃状态   : {'ACTIVE 正在全速推进' if is_active else 'INACTIVE 停止'}")
                
        report_history.append(snapshot)
        if sample_count > 1 and s < sample_count - 1:
            time.sleep(sample_interval)
            
    # 输出落盘
    out_dir = "/Users/cc/Desktop/GGBOM/xxxx/output"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "live_bullet_trajectory.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report_history, f, ensure_ascii=False, indent=2)
        
    latest_count = report_history[-1]["count"] if report_history else 0
    if latest_count == 0:
        unreal.log("⚠️ 当前视口世界中暂无活跃子弹（请按住 J 键射击开火，并同时在控制台采样）")
    else:
        unreal.log(f"✅ 成功捕获 {latest_count} 颗活跃子弹的完整弹道参数！已写盘: {out_file}")
    unreal.log("==================================================")
    return report_history

if __name__ == "__main__" or True:
    capture_bullet_trajectory()
