# -*- coding: utf-8 -*-
import unreal

MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
OUT_FILE = "/Users/cc/Desktop/GGBOM/all_actors_dump.txt"

def run():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        return
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    lines = []
    for a in sorted(actors, key=lambda x: x.get_actor_label()):
        lines.append(f"{a.get_actor_label():<35} | Cls: {a.get_class().get_name():<25} | Loc: {a.get_actor_location()} | Rot: {a.get_actor_rotation()} | Scale: {a.get_actor_scale3d()}")
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"DONE_{len(lines)}_ACTORS")

if __name__ == "__main__":
    run()
