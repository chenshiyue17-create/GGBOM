# -*- coding: utf-8 -*-
"""
inspect_hit_explosion_and_sprites.py
详细排查 BP_Combat_HitExplosion 与 BP_ProjectileBase 中多余的横向子弹贴图
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/inspect_hit_explosion.json"

res = {}

# 1. 检查 BP_Combat_HitExplosion
exp_bp = unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion")
if exp_bp:
    subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsys.k2_gather_subobject_data_for_blueprint(exp_bp)
    components = []
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, exp_bp)
        if not obj:
            continue
        cinfo = {
            "name": vname,
            "class": obj.get_class().get_name()
        }
        if isinstance(obj, unreal.PaperFlipbookComponent):
            fb = obj.get_editor_property("source_flipbook")
            scale = obj.get_editor_property("relative_scale3d")
            rot = obj.get_editor_property("relative_rotation")
            cinfo["flipbook"] = fb.get_path_name() if fb else None
            cinfo["scale"] = [scale.x, scale.y, scale.z]
            cinfo["rotation"] = [rot.pitch, rot.yaw, rot.roll]
            if fb:
                num_kf = fb.get_num_key_frames()
                cinfo["num_keyframes"] = num_kf
                cinfo["keyframes"] = []
                for i in range(num_kf):
                    sp = fb.get_sprite_at_key_frame(i)
                    cinfo["keyframes"].append({
                        "index": i,
                        "sprite": sp.get_path_name() if sp else None
                    })
        elif isinstance(obj, unreal.PaperSpriteComponent):
            sp = obj.get_editor_property("source_sprite")
            scale = obj.get_editor_property("relative_scale3d")
            rot = obj.get_editor_property("relative_rotation")
            vis = obj.get_editor_property("visible")
            hidden = obj.get_editor_property("hidden_in_game")
            cinfo["sprite"] = sp.get_path_name() if sp else None
            cinfo["scale"] = [scale.x, scale.y, scale.z]
            cinfo["rotation"] = [rot.pitch, rot.yaw, rot.roll]
            cinfo["visible"] = vis
            cinfo["hidden_in_game"] = hidden
        components.append(cinfo)
    res["BP_Combat_HitExplosion"] = components

# 2. 检查 BP_ProjectileBase
proj_bp = unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
if proj_bp:
    subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsys.k2_gather_subobject_data_for_blueprint(proj_bp)
    p_components = []
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, proj_bp)
        if not obj:
            continue
        cinfo = {
            "name": vname,
            "class": obj.get_class().get_name()
        }
        if isinstance(obj, unreal.PaperFlipbookComponent):
            fb = obj.get_editor_property("source_flipbook")
            scale = obj.get_editor_property("relative_scale3d")
            rot = obj.get_editor_property("relative_rotation")
            vis = obj.get_editor_property("visible")
            hidden = obj.get_editor_property("hidden_in_game")
            cinfo["flipbook"] = fb.get_path_name() if fb else None
            cinfo["scale"] = [scale.x, scale.y, scale.z]
            cinfo["rotation"] = [rot.pitch, rot.yaw, rot.roll]
            cinfo["visible"] = vis
            cinfo["hidden_in_game"] = hidden
            if fb:
                num_kf = fb.get_num_key_frames()
                cinfo["num_keyframes"] = num_kf
                cinfo["keyframes"] = [
                    {"index": i, "sprite": fb.get_sprite_at_key_frame(i).get_path_name() if fb.get_sprite_at_key_frame(i) else None}
                    for i in range(num_kf)
                ]
        elif isinstance(obj, unreal.PaperSpriteComponent):
            sp = obj.get_editor_property("source_sprite")
            scale = obj.get_editor_property("relative_scale3d")
            rot = obj.get_editor_property("relative_rotation")
            vis = obj.get_editor_property("visible")
            hidden = obj.get_editor_property("hidden_in_game")
            cinfo["sprite"] = sp.get_path_name() if sp else None
            cinfo["scale"] = [scale.x, scale.y, scale.z]
            cinfo["rotation"] = [rot.pitch, rot.yaw, rot.roll]
            cinfo["visible"] = vis
            cinfo["hidden_in_game"] = hidden
        p_components.append(cinfo)
    res["BP_ProjectileBase"] = p_components

OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2))
print(f"REPORT SAVED TO {OUT}")
