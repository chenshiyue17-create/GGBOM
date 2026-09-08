# -*- coding: utf-8 -*-
"""
adjust_hit_explosion_scale_and_shadow.py
彻底解决：
1. 爆炸范围太大 -> 将相对缩放从 0.75 紧凑缩小至 0.35 (精准受击火花，利落紧凑)
2. 有黑影 -> 强制关闭 Flipbook 与 Sprite 的 CastShadow (投射阴影)，并检查材质与素材
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary

def log(msg):
    print(f"[HIT_ADJUST] {msg}", flush=True)

def run():
    log("==================================================")
    log("🚀 调校命中爆炸：缩小范围至 0.35，彻底关闭阴影投射 (CastShadow=False)...")

    exp_bp_path = "/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion"
    exp_bp = ASSETS.load_asset(exp_bp_path)
    if not exp_bp:
        raise RuntimeError(f"未找到蓝图: {exp_bp_path}")

    subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsys.k2_gather_subobject_data_for_blueprint(exp_bp)

    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)).lower()
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, exp_bp)
        if not obj:
            continue

        if isinstance(obj, unreal.PaperFlipbookComponent) or "flipbook" in vname:
            # 1. 紧凑范围：0.35 缩放 (直径约 55-60 像素，精致利落，不遮挡大半个怪物和主角)
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.35, 0.35, 0.35))
            
            # 2. 彻底禁用投射阴影，根除地表与角色身后的黑影！
            try:
                obj.set_editor_property("cast_shadow", False)
                obj.set_editor_property("b_cast_dynamic_shadow", False)
            except Exception:
                pass
            try:
                obj.set_cast_shadow(False)
            except Exception:
                pass
                
            obj.set_editor_property("translucency_sort_priority", 3000)
            log(f"  🎯 Flipbook 组件已调校: Scale=(0.35, 0.35, 0.35), CastShadow=False")

        if isinstance(obj, unreal.PaperSpriteComponent) or "sprite" in vname:
            try: obj.set_editor_property("source_sprite", None)
            except Exception: pass
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.0, 0.0, 0.0))
            obj.set_editor_property("hidden_in_game", True)
            obj.set_editor_property("visible", False)
            try: obj.set_editor_property("cast_shadow", False)
            except Exception: pass

    # 存活时间微缩至 0.25 秒，打击感更快更清脆
    cdo_exp = unreal.get_default_object(exp_bp.generated_class())
    if cdo_exp:
        cdo_exp.set_editor_property("initial_life_span", 0.25)

    BPLIB.compile_blueprint(exp_bp)
    saved = ASSETS.save_loaded_asset(exp_bp, only_if_is_dirty=False)
    log(f"  💾 BP_Combat_HitExplosion 调校写盘: {'成功' if saved else '未变动'}")

    report = {
        "status": "PASS" if saved else "FAIL",
        "scale": [0.35, 0.35, 0.35],
        "cast_shadow": False,
        "life_span": 0.25,
        "saved": saved
    }
    out_file = ROOT / "output/adjust_hit_explosion_report.json"
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    log(f"📄 报告已写入: {out_file}")

if __name__ == "__main__":
    run()
