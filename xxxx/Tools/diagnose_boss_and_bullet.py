# -*- coding: utf-8 -*-
import unreal
import json
from pathlib import Path

out_dir = Path("/Users/cc/Desktop/GGBOM/xxxx/output")
out_dir.mkdir(parents=True, exist_ok=True)

report = {}

# 1. 检查 BP_Boss_Overlord 蓝图与组件
boss_bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
boss_bp = unreal.EditorAssetLibrary.load_asset(boss_bp_path)
if boss_bp:
    bplib = unreal.BlueprintEditorLibrary
    vars_list = [str(v) for v in bplib.find_blueprint_variables(boss_bp)]
    report["boss_bp_vars"] = vars_list
    
    subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsys.k2_gather_subobject_data_for_blueprint(boss_bp)
    comps = []
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, boss_bp)
        c_info = {"name": vname, "class": obj.get_class().get_name() if obj else None}
        if isinstance(obj, unreal.PrimitiveComponent):
            c_info["collision_enabled"] = str(obj.get_collision_enabled())
            c_info["collision_profile"] = str(obj.get_collision_profile_name())
            c_info["object_type"] = str(obj.get_collision_object_type())
            c_info["generate_overlap"] = obj.get_generate_overlap_events()
        comps.append(c_info)
    report["boss_bp_comps"] = comps

# 2. 检查关卡中的 Live_Boss_Overlord
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in all_actors:
    lbl = a.get_actor_label()
    if "Boss_Overlord" in lbl or "BossBar" in lbl:
        a_info = {
            "label": lbl,
            "class": a.get_class().get_name(),
            "collision_enabled": a.actor_has_tag(""), # placeholder
            "bActorEnableCollision": a.get_actor_enable_collision(),
            "tags": [str(t) for t in a.tags],
            "parent": a.get_attach_parent_actor().get_actor_label() if a.get_attach_parent_actor() else None,
            "location": [round(a.get_actor_location().x, 2), round(a.get_actor_location().y, 2), round(a.get_actor_location().z, 2)],
            "scale": [round(a.get_actor_scale3d().x, 4), round(a.get_actor_scale3d().y, 4), round(a.get_actor_scale3d().z, 4)],
        }
        root = a.get_editor_property("root_component")
        if isinstance(root, unreal.PrimitiveComponent):
            a_info["root_collision_enabled"] = str(root.get_collision_enabled())
            a_info["root_collision_profile"] = str(root.get_collision_profile_name())
            a_info["root_object_type"] = str(root.get_collision_object_type())
            a_info["root_generate_overlap"] = root.get_generate_overlap_events()
        report[f"actor_{lbl}"] = a_info

# 3. 检查血条 Sprite 的原始尺寸和轴心
sprite_paths = {
    "track": "/Game/GGBOM/Art/UI/SP_T_UI_Modal_09_ProgressTrack",
    "fill": "/Game/GGBOM/Art/UI/SP_T_UI_Modal_10_GlowBorder",
    "armor": "/Game/GGBOM/Art/UI/SP_T_UI_HUD_08_Minimap_Frame",
    "insignia": "/Game/GGBOM/Art/UI/SP_T_UI_Modal_02_HeaderRibbon",
}
sprites_info = {}
for k, path in sprite_paths.items():
    sp = unreal.EditorAssetLibrary.load_asset(path)
    if sp:
        sprites_info[k] = {
            "source_size": [sp.get_source_size().x, sp.get_source_size().y] if hasattr(sp, "get_source_size") else None,
            "pivot_mode": str(sp.get_editor_property("pivot_mode")) if hasattr(sp, "get_editor_property") else None,
            "custom_pivot_point": [sp.get_editor_property("custom_pivot_point").x, sp.get_editor_property("custom_pivot_point").y] if hasattr(sp, "get_editor_property") else None,
        }
report["sprites_info"] = sprites_info

out_file = out_dir / "diagnose_boss_and_bullet_result.json"
out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"SUCCESS: 诊断报告写入 {out_file}", flush=True)
