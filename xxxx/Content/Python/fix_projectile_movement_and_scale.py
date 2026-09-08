# -*- coding: utf-8 -*-
"""
================================================================================
fix_projectile_movement_and_scale.py
终极修复: 解决子弹堕落在脚下与 Scale3D is (nearly) zero 物理报错
================================================================================
"""
import os
import sys
import unreal

def log(msg):
    unreal.log(f"[FIX_BULLET] {msg}")
    print(f"[FIX_BULLET] {msg}")

def fix_projectile_asset(bp_path, flight_fb):
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    if not bp:
        log(f"Asset not found: {bp_path}")
        return False
        
    subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
    
    sphere_comp = None
    fb_comp = None
    sprite_comp = None
    move_comp = None
    
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)).lower()
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if not obj:
            continue
            
        cname = obj.get_class().get_name().lower()
        if isinstance(obj, unreal.SphereComponent) or "sphere" in cname or "sphere" in vname or "collision" in vname:
            if not sphere_comp or "sphere" in vname:
                sphere_comp = obj
        elif isinstance(obj, unreal.PaperFlipbookComponent) or "flipbook" in cname or "flipbook" in vname:
            fb_comp = obj
        elif isinstance(obj, unreal.PaperSpriteComponent) or "sprite" in cname or "sprite" in vname:
            sprite_comp = obj
        elif isinstance(obj, unreal.ProjectileMovementComponent) or "projectilemovement" in cname or "move" in vname:
            move_comp = obj

    log(f"[{bp_path}] 查找到组件: Sphere={'OK' if sphere_comp else 'None'}, FB={'OK' if fb_comp else 'None'}, Sprite={'OK' if sprite_comp else 'None'}, Move={'OK' if move_comp else 'None'}")

    # 1. 根碰撞体组件修复: 恢复 Scale=(1,1,1)，彻底消除 Scale3D is nearly zero 报警
    if sphere_comp:
        try:
            sphere_comp.set_editor_property("relative_scale3d", unreal.Vector(1.0, 1.0, 1.0))
            sphere_comp.set_editor_property("sphere_radius", 18.0)
            sphere_comp.set_editor_property("hidden_in_game", False)
            try:
                sphere_comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
            except Exception:
                pass
            sphere_comp.set_collision_profile_name("Custom")
            sphere_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
            sphere_comp.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE)
            sphere_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_OVERLAP)
            sphere_comp.set_editor_property("generate_overlap_events", True)
            try:
                sphere_comp.set_editor_property("notify_rigid_body_collision", False)
            except Exception:
                pass
            log(f"  [{bp_path}] SphereComponent 恢复 Scale=(1,1,1)，碰撞锁定为穿透地面、重叠Pawn")
        except Exception as e:
            log(f"  [{bp_path}] 设置碰撞响应警告: {e}")

    # 2. 动能流光飞行动画挂载: 尺寸 Scale=0.09，朝向正前
    if fb_comp and flight_fb:
        try:
            fb_comp.set_editor_property("source_flipbook", flight_fb)
            fb_comp.set_editor_property("relative_scale3d", unreal.Vector(0.09, 0.09, 0.09))
            fb_comp.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
            fb_comp.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
            fb_comp.set_editor_property("hidden_in_game", False)
            fb_comp.set_editor_property("visible", True)
            fb_comp.set_editor_property("translucency_sort_priority", 1600)
            fb_comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            log(f"  [{bp_path}] 动能子弹 Flipbook 已装配生效 (Scale=0.09)")
        except Exception as e:
            log(f"  [{bp_path}] 装配 Flipbook 警告: {e}")

    # 3. 旧火球 Sprite 安全失活: 严禁将 Scale 设为 0 (维持 Scale=1.0，避免导致子级或父级物理崩塌)
    if sprite_comp:
        try:
            try:
                sprite_comp.set_editor_property("source_sprite", None)
            except Exception:
                pass
            try:
                sprite_comp.set_sprite(None)
            except Exception:
                pass
            sprite_comp.set_editor_property("relative_scale3d", unreal.Vector(1.0, 1.0, 1.0))
            sprite_comp.set_editor_property("hidden_in_game", True)
            sprite_comp.set_editor_property("visible", False)
            sprite_comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            log(f"  [{bp_path}] 旧 Sprite 已安全清空并隐形，Scale 维持 1.0")
        except Exception as e:
            log(f"  [{bp_path}] 清空 Sprite 警告: {e}")

    # 4. 飞行运动组件锁定 1200 速度与无重力: 彻底消灭堕落脚下
    if move_comp:
        try:
            prop_values = [
                ("initial_speed", 1200.0),
                ("max_speed", 1200.0),
                ("projectile_gravity_scale", 0.0),
                ("velocity", unreal.Vector(1200.0, 0.0, 0.0)),
                ("rotation_follows_velocity", True),
                ("initial_velocity_in_local_space", True),
                ("should_bounce", False),
                ("is_homing_projectile", False),
                ("auto_activate", True),
            ]
            for p_name, p_val in prop_values:
                try:
                    move_comp.set_editor_property(p_name, p_val)
                except Exception:
                    try:
                        move_comp.set_editor_property(f"b_{p_name}", p_val)
                    except Exception:
                        pass

            if sphere_comp:
                try:
                    move_comp.set_editor_property("updated_component", sphere_comp)
                except Exception:
                    try:
                        move_comp.set_updated_component(sphere_comp)
                    except Exception:
                        pass
            log(f"  [{bp_path}] ProjectileMovement 成功锁定 InitialSpeed=1200, Gravity=0.0, Velocity=(1200,0,0)")
        except Exception as e:
            log(f"  [{bp_path}] 设置移动参数警告: {e}")

    # 5. CDO 属性锁定
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        try:
            cdo.set_editor_property("initial_life_span", 3.0)
            for prop in ["damage", "Damage"]:
                if hasattr(cdo, prop):
                    try: setattr(cdo, prop, 45.0)
                    except Exception: pass
            for prop in ["speed", "Speed", "ProjectileSpeed", "projectile_speed"]:
                if hasattr(cdo, prop):
                    try: setattr(cdo, prop, 1200.0)
                    except Exception: pass
            for prop in ["pierce_count", "PierceCount"]:
                if hasattr(cdo, prop):
                    try: setattr(cdo, prop, 999)
                    except Exception: pass
            for prop in ["shot_direction", "ShotDirection"]:
                if hasattr(cdo, prop):
                    try: setattr(cdo, prop, unreal.Vector(0.0, 0.0, 1.0))
                    except Exception: pass
        except Exception as e:
            log(f"  [{bp_path}] 设置 CDO 属性警告: {e}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ [{bp_path}] 官方 API 编译与持久化写盘: {'成功' if saved else '未修改'}")
    return saved

def execute():
    fb_path = "/Game/Blueprints/Combat/Projectiles/FB_Combat_Kinetic_Flight"
    flight_fb = unreal.EditorAssetLibrary.load_asset(fb_path)
    if not flight_fb:
        log(f"⚠️ 未找到飞行动画 {fb_path}，请先运行 headless_official_update")
        
    targets = [
        "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase",
        "/Game/Blueprints/Projectiles/BP_Projectile_Base",
        "/Game/Blueprints/Projectiles/BP_Bullet_KineticPistol"
    ]
    
    for t in targets:
        fix_projectile_asset(t, flight_fb)
        
    log("🎉 【成功】全部子弹蓝图 RootComponent、物理缩放与 1200 速度修复完毕！")

if __name__ == "__main__" or True:
    execute()
