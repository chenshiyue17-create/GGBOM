import os
import sys
import unreal

def log(msg):
    unreal.log(f"[FIX_SCALE_AND_MOVE] {msg}")
    print(f"[FIX_SCALE_AND_MOVE] {msg}")

def fix_projectile(bp_path, flight_fb):
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    if not bp:
        log(f"Asset not found: {bp_path}")
        return False
        
    subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
    
    sphere_comp = None
    sphere_handle = None
    fb_comp = None
    fb_handle = None
    sprite_comp = None
    sprite_handle = None
    move_comp = None
    root_handle = None
    
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)).lower()
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        is_root = unreal.SubobjectDataBlueprintFunctionLibrary.is_root_component(data)
        if is_root:
            root_handle = h
            
        if not obj:
            continue
            
        if "sphere" in vname or "collision" in vname or isinstance(obj, unreal.SphereComponent):
            sphere_comp = obj
            sphere_handle = h
        elif "flipbook" in vname or isinstance(obj, unreal.PaperFlipbookComponent):
            fb_comp = obj
            fb_handle = h
        elif "sprite" in vname or isinstance(obj, unreal.PaperSpriteComponent):
            sprite_comp = obj
            sprite_handle = h
        elif "move" in vname or isinstance(obj, unreal.ProjectileMovementComponent):
            move_comp = obj

    log(f"[{bp_path}] Components: Sphere={'OK' if sphere_comp else 'None'}, FB={'OK' if fb_comp else 'None'}, Sprite={'OK' if sprite_comp else 'None'}, Move={'OK' if move_comp else 'None'}")

    # 1. 根组件与缩放修复 (彻底消除 Scale3D is nearly zero 警告)
    # 确保 SphereComponent 缩放为 1,1,1
    if sphere_comp:
        sphere_comp.set_editor_property("relative_scale3d", unreal.Vector(1.0, 1.0, 1.0))
        sphere_comp.set_editor_property("sphere_radius", 16.0)
        sphere_comp.set_editor_property("hidden_in_game", False)
        # 碰撞配置：无视世界静态碰撞(穿透地面和掩体)，仅响应Pawn
        sphere_comp.set_collision_profile_name("Custom")
        sphere_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
        sphere_comp.set_collision_response_to_all_channels(unreal.CollisionResponse.ECR_IGNORE)
        sphere_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponse.ECR_OVERLAP)
        sphere_comp.set_editor_property("generate_overlap_events", True)
        log(f"  [{bp_path}] SphereComponent 恢复 Scale=(1,1,1)，碰撞设为仅重叠 Pawn")

    # 2. 动能流光 Flipbook 挂载与缩放
    if fb_comp and flight_fb:
        fb_comp.set_editor_property("source_flipbook", flight_fb)
        fb_comp.set_editor_property("relative_scale3d", unreal.Vector(0.09, 0.09, 0.09))
        fb_comp.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
        fb_comp.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
        fb_comp.set_editor_property("hidden_in_game", False)
        fb_comp.set_editor_property("visible", True)
        fb_comp.set_editor_property("translucency_sort_priority", 1600)
        fb_comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        log(f"  [{bp_path}] 动能子弹 Flipbook 激活成功 (Scale=0.09)")

    # 3. 旧 Sprite 组件安全失活 (绝不能设 Scale 为 0，避免导致子级或根级变成 0)
    if sprite_comp:
        sprite_comp.set_editor_property("sprite", None)
        sprite_comp.set_editor_property("relative_scale3d", unreal.Vector(1.0, 1.0, 1.0))
        sprite_comp.set_editor_property("hidden_in_game", True)
        sprite_comp.set_editor_property("visible", False)
        sprite_comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        log(f"  [{bp_path}] 旧 Sprite 安全清空并隐藏，Scale 维持 1.0 避免物理崩坏")

    # 4. 飞行运动组件锁定 1200 速度与无重力 (彻底解决堕落在脚下)
    if move_comp:
        move_comp.set_editor_property("initial_speed", 1200.0)
        move_comp.set_editor_property("max_speed", 1200.0)
        move_comp.set_editor_property("projectile_gravity_scale", 0.0)
        move_comp.set_editor_property("velocity", unreal.Vector(1200.0, 0.0, 0.0))
        move_comp.set_editor_property("b_rotation_follows_velocity", True)
        move_comp.set_editor_property("b_initial_velocity_in_local_space", True)
        move_comp.set_editor_property("b_should_bounce", False)
        if sphere_comp:
            move_comp.set_editor_property("updated_component", sphere_comp)
        log(f"  [{bp_path}] ProjectileMovement 锁定 Speed=1200, Gravity=0.0, Velocity=(1200,0,0)")

    # 5. CDO 属性锁定
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        cdo.set_editor_property("initial_life_span", 2.5)
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

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ [{bp_path}] 官方 API 修复与持久化写盘: {'成功' if saved else '未修改'}")
    return saved

def main():
    fb_path = "/Game/Blueprints/Combat/Projectiles/FB_Combat_Kinetic_Flight"
    flight_fb = unreal.EditorAssetLibrary.load_asset(fb_path)
    if not flight_fb:
        log(f"⚠️ 无法加载动能子弹飞行动画: {fb_path}")
        
    targets = [
        "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase",
        "/Game/Blueprints/Projectiles/BP_Projectile_Base",
        "/Game/Blueprints/Projectiles/BP_Bullet_KineticPistol"
    ]
    
    for t in targets:
        fix_projectile(t, flight_fb)
        
    log("🎉 全部子弹蓝图根组件与物理运动参数修复落盘完毕！")

try:
    main()
except Exception as e:
    log(f"Execution error: {e}")
    sys.exit(1)
