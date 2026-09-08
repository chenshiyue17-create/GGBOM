# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/boss_details_inspect.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary

lines = []
def log(msg):
    print(f"[INSPECT] {msg}", flush=True)
    lines.append(str(msg))

bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
bp = ASSETS.load_asset(bp_path)
if not bp:
    log(f"ERROR: Cannot load {bp_path}")
else:
    log(f"BP: {bp.get_name()}")
    log(f"Parent Class: {bp.get_editor_property('parent_class')}")
    
    # 获取变量
    vars_list = bp.get_editor_property("new_variables")
    log(f"Variables count: {len(vars_list)}")
    for v in vars_list:
        v_name = v.get_editor_property("var_name")
        v_type = v.get_editor_property("var_type")
        cat = v_type.get_editor_property("pin_category")
        sub_cat = v_type.get_editor_property("pin_sub_category")
        log(f"  Var: {v_name} ({cat} / {sub_cat})")

    # 获取组件
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        log(f"CDO: {cdo.get_name()}")
        root = cdo.get_editor_property("root_component")
        log(f"CDO RootComponent: {root.get_name() if root else 'None'}")
        all_comps = cdo.get_components_by_class(unreal.ActorComponent)
        log(f"Comps count: {len(all_comps)}")
        for c in all_comps:
            log(f"  Comp: {c.get_name()} ({c.get_class().get_name()})")

# 检查关卡中的 Boss
LEVEL_SUBSYS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUBSYS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LEVEL_SUBSYS.load_level("/Game/GGBOM/Maps/MAP_GGBOM_Main")
actors = ACTOR_SUBSYS.get_all_level_actors()
for a in actors:
    if "Boss" in a.get_actor_label() or "Boss" in a.get_class().get_name():
        loc = a.get_actor_location()
        scale = a.get_actor_scale3d()
        log(f"Level Actor: {a.get_actor_label()} ({a.get_class().get_name()}) Loc: {loc} Scale: {scale}")

OUT.write_text("\n".join(lines), encoding="utf-8")
log("Done inspection.")
