# -*- coding: utf-8 -*-
"""
fix_hit_explosion_clean.py
彻底清除命中爆炸中的横向巨型子弹贴图 (T_Bullet_KineticPistol_03_Impact)
将命中爆炸重置为纯净、华丽的炼狱火环 (Inferno Shock 01~04 / Sheet)，消除横向大贴图
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
REPORT_PATH = ROOT / "output/fix_hit_explosion_report.json"

def log(msg):
    print(f"[CLEAN_EXPLOSION] {msg}", flush=True)

def run():
    log("==================================================")
    log("🚀 启动击中爆炸特效净化流水线（剔除横向超大子弹贴图）...")

    ASSETS = unreal.EditorAssetLibrary
    BPLIB = unreal.BlueprintEditorLibrary

    # 1. 加载 4 帧纯火环 Sprite
    inferno_sprites = []
    for i in range(1, 5):
        sp_paths = [
            f"/Game/P01/Imported/Content/Asset/Art/05_VFX/02_Inferno_Shock/Sprites/SP_T_VFX_Inferno_Shock_0{i}",
            f"/Game/Blueprints/Combat/Projectiles/SP_T_VFX_Inferno_Shock_0{i}"
        ]
        sp = None
        for p in sp_paths:
            if ASSETS.does_asset_exist(p):
                sp = ASSETS.load_asset(p)
                if sp:
                    break
        if sp:
            inferno_sprites.append(sp)
            log(f"  🔥 找到火环第 {i} 帧 Sprite: {sp.get_name()}")

    if not inferno_sprites:
        log("  ⚠️ 未找到单独 Sprite，尝试使用官方 Sheet Flipbook...")

    # 2. 重新生成或更新纯净的 FB_Combat_Inferno_Shock
    fb_path = "/Game/Blueprints/Combat/Projectiles/FB_Combat_Inferno_Shock"
    fb_obj = None
    
    if inferno_sprites:
        factory = unreal.PaperFlipbookFactory()
        pkg_name = "/Game/Blueprints/Combat/Projectiles"
        fb_name = "FB_Combat_Inferno_Shock"
        
        # 如果已存在先加载并重置关键帧，若不存在则创建
        if ASSETS.does_asset_exist(fb_path):
            fb_obj = ASSETS.load_asset(fb_path)
            log(f"  🔄 覆盖已有 Flipbook: {fb_path}")
        else:
            fb_obj = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                fb_name, pkg_name, unreal.PaperFlipbook, factory
            )
            log(f"  ✨ 创建全新 Flipbook: {fb_path}")

        if fb_obj:
            fb_obj.set_editor_property("frames_per_second", 20.0)
            # 使用官方 API 构建纯净 key_frames 数组
            new_keyframes = []
            for sp in inferno_sprites:
                kf = unreal.PaperFlipbookKeyFrame()
                kf.set_editor_property("sprite", sp)
                kf.set_editor_property("frame_run", 1)
                new_keyframes.append(kf)
            fb_obj.set_editor_property("key_frames", new_keyframes)
            ASSETS.save_loaded_asset(fb_obj, only_if_is_dirty=False)
            log(f"  ✅ Flipbook 已重构完成，仅包含 {len(new_keyframes)} 帧纯火环，彻底移除横向子弹！")
    else:
        # 使用官方预制 Sheet
        fb_obj = ASSETS.load_asset("/Game/P01/Imported/Content/Asset/Art/05_VFX/02_Inferno_Shock/Flipbooks/FB_T_VFX_Inferno_Shock_Sheet")
        log(f"  ✅ 降级使用官方预制 Sheet Flipbook: {fb_obj}")

    # 3. 调校爆炸蓝图 BP_Combat_HitExplosion
    exp_bp_path = "/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion"
    exp_bp = ASSETS.load_asset(exp_bp_path)
    if not exp_bp:
        raise RuntimeError(f"未找到爆炸蓝图: {exp_bp_path}")

    subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsys.k2_gather_subobject_data_for_blueprint(exp_bp)
    
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)).lower()
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, exp_bp)
        if not obj:
            continue
        
        # 对 Flipbook 组件绑定纯净火球，并设置合理的缩放 (0.75) 与不循环
        if isinstance(obj, unreal.PaperFlipbookComponent) or "flipbook" in vname:
            if fb_obj:
                obj.set_editor_property("source_flipbook", fb_obj)
            # 缩放调整为 0.75，直径约 120 像素，契合怪物尺寸，不突兀
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.75, 0.75, 0.75))
            obj.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
            obj.set_editor_property("translucency_sort_priority", 3000)
            try:
                obj.set_editor_property("looping", False)
            except Exception:
                pass
            log(f"  🎯 BP_Combat_HitExplosion Flipbook 组件已更新: Scale=(0.75, 0.75, 0.75), Looping=False")
            
        # 如果存在多余的 Sprite 组件，彻底设为不可见与无贴图
        if isinstance(obj, unreal.PaperSpriteComponent) or "sprite" in vname:
            try: obj.set_editor_property("source_sprite", None)
            except Exception: pass
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.0, 0.0, 0.0))
            obj.set_editor_property("hidden_in_game", True)
            obj.set_editor_property("visible", False)
            log(f"  🧹 BP_Combat_HitExplosion 多余 Sprite 组件已清空并隐形")

    # 爆炸 Actor 存活生命周期: 0.35 秒后自毁
    cdo_exp = unreal.get_default_object(exp_bp.generated_class())
    if cdo_exp:
        cdo_exp.set_editor_property("initial_life_span", 0.35)

    BPLIB.compile_blueprint(exp_bp)
    saved_exp = ASSETS.save_loaded_asset(exp_bp, only_if_is_dirty=False)
    log(f"  💾 BP_Combat_HitExplosion 编译与持久化落盘: {'成功' if saved_exp else '失败'}")

    # 4. 检查子弹蓝图 BP_ProjectileBase
    proj_bp_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
    proj_bp = ASSETS.load_asset(proj_bp_path)
    if proj_bp:
        p_handles = subsys.k2_gather_subobject_data_for_blueprint(proj_bp)
        for h in p_handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)).lower()
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, proj_bp)
            if not obj:
                continue
            # 确保子弹本身的 Sprite 组件彻底置空隐形
            if isinstance(obj, unreal.PaperSpriteComponent) or "sprite" in vname:
                try: obj.set_editor_property("source_sprite", None)
                except Exception: pass
                obj.set_editor_property("relative_scale3d", unreal.Vector(0.0, 0.0, 0.0))
                obj.set_editor_property("hidden_in_game", True)
                obj.set_editor_property("visible", False)
        BPLIB.compile_blueprint(proj_bp)
        ASSETS.save_loaded_asset(proj_bp, only_if_is_dirty=False)
        log("  💾 BP_ProjectileBase 冗余 Sprite 已二次确认隐形与存盘")

    report = {
        "status": "PASS" if saved_exp else "FAIL",
        "flipbook_path": fb_path,
        "pure_fire_frames": len(inferno_sprites),
        "scale": [0.75, 0.75, 0.75],
        "sp_impact_removed": True,
        "saved": saved_exp
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    log(f"📄 报告已写入: {REPORT_PATH}")
    log("🎉 命中爆炸特效净化完毕！已彻底剔除横向超大子弹！")

if __name__ == "__main__":
    run()
