# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/check_enemy_in_map.txt"

lines = []
lines.append("================ ENEMY IN MAP ================")

world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/GGBOM/Maps/MAP_GGBOM_Main")
actors = unreal.EditorLevelLibrary.get_all_level_actors()

for a in actors:
    lbl = a.get_actor_label()
    cname = a.get_class().get_name()
    if "enemy" in cname.lower() or "boss" in cname.lower() or "live_" in lbl.lower() or "pawn" in cname.lower():
        lines.append(f"Actor: {lbl} ({cname})")
        for comp in a.get_components_by_class(unreal.PrimitiveComponent):
            c_cname = comp.get_class().get_name()
            c_name = comp.get_name()
            col_en = comp.get_collision_enabled()
            col_type = comp.get_collision_object_type()
            gen_ol = comp.get_editor_property("generate_overlap_events")
            resp_dyn = comp.get_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC)
            lines.append(f"  Comp: {c_name} ({c_cname}) -> Enabled={col_en}, Type={col_type}, GenOverlap={gen_ol}, Resp_WorldDyn={resp_dyn}")

OUT.write_text("\n".join(lines), encoding="utf-8")
unreal.log("✅ ENEMY DUMP SAVED")
