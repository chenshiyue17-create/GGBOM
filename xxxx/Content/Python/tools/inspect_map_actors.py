# -*- coding: utf-8 -*-
import unreal

map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
unreal.EditorLevelLibrary.load_level(map_path)
actors = unreal.EditorLevelLibrary.get_all_level_actors()

out_lines = []
out_lines.append(f"=== [ACTOR_LIST] TOTAL ACTORS IN MAP: {len(actors)} ===")
for a in actors:
    loc = a.get_actor_location()
    line = f"[ACTOR] Label: {a.get_actor_label()} | Class: {a.get_class().get_name()} | Pos: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})"
    out_lines.append(line)
    unreal.log(line)

with open("/Users/cc/Desktop/GGBOM/xxxx/Content/Python/tools/map_actors.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))
unreal.log("Finished writing map_actors.txt")
