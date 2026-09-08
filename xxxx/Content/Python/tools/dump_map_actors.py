import unreal

world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/GGBOM/Maps/MAP_GGBOM_Main")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
print(f"Total Actors in MAP_GGBOM_Main: {len(actors)}")
for a in actors:
    lbl = a.get_actor_label()
    cls = a.get_class().get_name()
    loc = a.get_actor_location()
    print(f"  {lbl:30s} | {cls:25s} | loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")
