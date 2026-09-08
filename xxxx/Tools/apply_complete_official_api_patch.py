import os
import sys
import json
import unreal

def log(msg):
    unreal.log(f"[OFFICIAL_API_PATCH] {msg}")
    print(f"[OFFICIAL_API_PATCH] {msg}")

def ensure_sprite(tex_name, sp_name):
    # 查找已有 Sprite
    candidates = [
        f"/Game/Blueprints/Combat/Projectiles/{sp_name}",
        f"/Game/P01/Imported/Content/Asset/Art/03_Weapons/01_KineticPistol/Sprites/{sp_name}",
        f"/Game/P01/Imported/Content/Asset/Art/05_VFX/02_Inferno_Shock/Sprites/{sp_name}",
        f"/Game/GGBOM/Art/Sprites/Weapons/{sp_name}"
    ]
    for c in candidates:
        sp = unreal.EditorAssetLibrary.load_asset(c)
        if sp:
            return sp
            
    # 查找原材质/贴图
    tex_candidates = [
        f"/Game/P01/Imported/Content/Asset/Art/03_Weapons/01_KineticPistol/Textures/{tex_name}",
        f"/Game/P01/Imported/Content/Asset/Art/05_VFX/02_Inferno_Shock/Textures/{tex_name}",
        f"/Game/GGBOM/Art/Textures/Weapons/{tex_name}"
    ]
    tex = None
    for tc in tex_candidates:
        tex = unreal.EditorAssetLibrary.load_asset(tc)
        if tex:
            break
            
    if tex:
        factory = unreal.PaperSpriteFactory()
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        sp = asset_tools.create_asset(sp_name, "/Game/Blueprints/Combat/Projectiles", unreal.PaperSprite, factory)
        if sp:
            sp.set_editor_property("source_texture", tex)
            unreal.EditorAssetLibrary.save_loaded_asset(sp, only_if_is_dirty=False)
            return sp
    return None

def ensure_flipbook(fb_path, sprites, fps=15.0):
    fb = unreal.EditorAssetLibrary.load_asset(fb_path)
    if not fb:
        factory = unreal.PaperFlipbookFactory()
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        pkg = os.path.dirname(fb_path)
        name = os.path.basename(fb_path)
        fb = asset_tools.create_asset(name, pkg, unreal.PaperFlipbook, factory)
        
    if fb and sprites:
        fb.set_editor_property("frames_per_second", fps)
        kfs = []
        for s in sprites:
            if s:
                kf = unreal.PaperFlipbookKeyFrame()
                kf.set_editor_property("sprite", s)
                kf.set_editor_property("frame_run", 1)
                kfs.append(kf)
        fb.set_editor_property("key_frames", kfs)
        unreal.EditorAssetLibrary.save_loaded_asset(fb, only_if_is_dirty=False)
        log(f"Flipbook 持久化就绪: {fb_path} (帧数={len(kfs)})")
    return fb

def run_patch():
    report = {}
    
    # 1. 动能飞行贴图与命中火环素材落盘
    sp_flight = ensure_sprite("T_Bullet_KineticPistol_02_Flight", "SP_T_Bullet_KineticPistol_02_Flight")
    sp_impact = ensure_sprite("T_Bullet_KineticPistol_03_Impact", "SP_T_Bullet_KineticPistol_03_Impact")
    
    inferno_sprites = []
    for i in range(1, 5):
        s = ensure_sprite(f"T_VFX_Inferno_Shock_0{i}", f"SP_T_VFX_Inferno_Shock_0{i}")
        if s:
            inferno_sprites.append(s)
            
    fb_flight = ensure_flipbook("/Game/Blueprints/Combat/Projectiles/FB_Combat_Kinetic_Flight", [sp_flight] if sp_flight else [], 15.0)
    
    hit_sprites = []
    if sp_impact:
        hit_sprites.append(sp_impact)
    hit_sprites.extend(inferno_sprites)
    fb_explosion = ensure_flipbook("/Game/Blueprints/Combat/Projectiles/FB_Combat_Inferno_Shock", hit_sprites, 18.0)
    
    report["FB_Combat_Kinetic_Flight_Ready"] = fb_flight is not None
    report["FB_Combat_Inferno_Shock_Ready"] = fb_explosion is not None

    # 2. 全量修改所有子弹蓝图资产
    target_projectile_bps = [
        "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase",
        "/Game/Blueprints/Projectiles/BP_Projectile_Base",
        "/Game/Blueprints/Projectiles/BP_Bullet_KineticPistol",
        "/Game/Blueprints/Projectiles/BP_Bullet_AssaultRifle"
    ]
    
    subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    
    for bp_path in target_projectile_bps:
        bp = unreal.EditorAssetLibrary.load_asset(bp_path)
        if not bp:
            report[f"{bp_path}_Status"] = "NOT_FOUND"
            continue
            
        handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
        fb_comp = None
        sprite_comp = None
        move_comp = None
        sphere_comp = None
        
        for h in handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)).lower()
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
            if not obj:
                continue
            if "flipbook" in vname or isinstance(obj, unreal.PaperFlipbookComponent):
                fb_comp = obj
            elif "sprite" in vname or isinstance(obj, unreal.PaperSpriteComponent):
                sprite_comp = obj
            elif "move" in vname or isinstance(obj, unreal.ProjectileMovementComponent):
                move_comp = obj
            elif "sphere" in vname or "collision" in vname or isinstance(obj, unreal.SphereComponent):
                sphere_comp = obj
                
        # 清空并禁用旧火球 Sprite
        if sprite_comp:
            try:
                sprite_comp.set_editor_property("sprite", None)
                sprite_comp.set_editor_property("relative_scale3d", unreal.Vector(0.0, 0.0, 0.0))
                sprite_comp.set_editor_property("hidden_in_game", True)
                sprite_comp.set_editor_property("visible", False)
                log(f"  [{bp_path}] 旧 Sprite 组件已彻底清空并隐藏")
            except Exception as e:
                log(f"  [{bp_path}] 清空 Sprite 异常: {e}")
                
        # 赋予动能子弹 Flipbook
        if fb_comp and fb_flight:
            try:
                fb_comp.set_editor_property("source_flipbook", fb_flight)
                fb_comp.set_editor_property("relative_scale3d", unreal.Vector(0.09, 0.09, 0.09))
                fb_comp.set_editor_property("hidden_in_game", False)
                fb_comp.set_editor_property("visible", True)
                fb_comp.set_editor_property("translucency_sort_priority", 1600)
                log(f"  [{bp_path}] 动能子弹 Flipbook 已装配成功 (Scale=0.09)")
            except Exception as e:
                log(f"  [{bp_path}] 绑定 Flipbook 异常: {e}")
                
        # 设置高速移动组件
        if move_comp:
            try:
                move_comp.set_editor_property("initial_speed", 1200.0)
                move_comp.set_editor_property("max_speed", 1200.0)
                move_comp.set_editor_property("projectile_gravity_scale", 0.0)
                move_comp.set_editor_property("velocity", unreal.Vector(1200.0, 0.0, 0.0))
                log(f"  [{bp_path}] 弹道速度已锁定 1200.0 (无重力)")
            except Exception as e:
                log(f"  [{bp_path}] 设置移动参数异常: {e}")
                
        # 设置球体碰撞通道
        if sphere_comp:
            try:
                sphere_comp.set_editor_property("sphere_radius", 14.0)
                sphere_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC, unreal.CollisionResponse.ECR_IGNORE)
                sphere_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponse.ECR_OVERLAP)
                sphere_comp.set_editor_property("generate_overlap_events", True)
                log(f"  [{bp_path}] 碰撞通道已锁定 (穿透地面，重叠敌人)")
            except Exception as e:
                log(f"  [{bp_path}] 设置碰撞异常: {e}")
                
        # CDO 默认值设置
        gen_cls = bp.generated_class()
        cdo = unreal.get_default_object(gen_cls) if gen_cls else None
        if cdo:
            try:
                cdo.set_editor_property("initial_life_span", 2.5)
                for prop in ["damage", "Damage"]:
                    if hasattr(cdo, prop):
                        setattr(cdo, prop, 45.0)
                for prop in ["speed", "Speed"]:
                    if hasattr(cdo, prop):
                        setattr(cdo, prop, 1200.0)
                for prop in ["pierce_count", "PierceCount"]:
                    if hasattr(cdo, prop):
                        setattr(cdo, prop, 999)
            except Exception as e:
                log(f"  [{bp_path}] CDO 属性设置异常: {e}")
                
        # 编译并强制落盘
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        saved = unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
        report[f"{bp_path}_Saved"] = saved
        log(f"✅ [{bp_path}] 官方 API 修改与持久化写盘: {'成功' if saved else '未修改'}")

    # 3. 命中爆炸蓝图 BP_Combat_HitExplosion 官方 API 修改落盘
    exp_bp = unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion")
    if exp_bp and fb_explosion:
        exp_handles = subsys.k2_gather_subobject_data_for_blueprint(exp_bp)
        for h in exp_handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)).lower()
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, exp_bp)
            if obj and ("flipbook" in vname or isinstance(obj, unreal.PaperFlipbookComponent)):
                obj.set_editor_property("source_flipbook", fb_explosion)
                obj.set_editor_property("relative_scale3d", unreal.Vector(0.35, 0.35, 0.35))
                obj.set_editor_property("translucency_sort_priority", 1800)
                log("  [BP_Combat_HitExplosion] 炼狱火环命中震波已装配成功")
                
        exp_cdo = unreal.get_default_object(exp_bp.generated_class())
        if exp_cdo:
            exp_cdo.set_editor_property("initial_life_span", 0.6)
            
        unreal.BlueprintEditorLibrary.compile_blueprint(exp_bp)
        exp_saved = unreal.EditorAssetLibrary.save_loaded_asset(exp_bp, only_if_is_dirty=False)
        report["BP_Combat_HitExplosion_Saved"] = exp_saved
        log(f"✅ [BP_Combat_HitExplosion] 命中爆炸蓝图已持久化写盘: {'成功' if exp_saved else '未修改'}")

    # 输出全量铁证报告
    out_path = "/Users/cc/Desktop/GGBOM/xxxx/output/official_complete_patch_report.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    log(f"🎉 官方 API 全量修改与落盘任务圆满完成！报告已生成: {out_path}")

try:
    run_patch()
except Exception as e:
    log(f"Patch run failed: {e}")
    sys.exit(1)
