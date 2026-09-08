import unreal

map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
unreal.EditorLevelLibrary.load_level(map_path)
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

print(f"Total actors in level: {len(actors)}")
for a in actors:
    loc = a.get_actor_location()
    scale = a.get_actor_scale3d()
    sprite_name = ""
    comp = a.get_component_by_class(unreal.PaperSpriteComponent)
    if comp:
        sp = comp.get_editor_property("source_sprite")
        if sp:
            sprite_name = sp.get_name()
    print(f"[{a.get_actor_label()}] Class={a.get_class().get_name()} Loc=({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) Scale=({scale.x:.2f}) Sprite={sprite_name}")
