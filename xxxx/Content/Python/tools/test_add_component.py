import unreal

world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/GGBOM/Maps/MAP_GGBOM_Main")
actors = unreal.EditorLevelLibrary.get_all_level_actors()

test_enemy = None
for a in actors:
    if a.get_actor_label() == "Enemy_Zombie_01":
        test_enemy = a
        break

if test_enemy:
    print(f"Found {test_enemy.get_actor_label()}")
    # 尝试添加 BoxComponent
    box = test_enemy.add_component_by_class(unreal.BoxComponent, False, unreal.Transform(), False)
    if box:
        box.set_editor_property("box_extent", unreal.Vector(30.0, 80.0, 35.0))
        box.set_collision_profile_name("Pawn")
        box.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        print("Successfully added BoxComponent to Enemy_Zombie_01!")
    else:
        print("add_component_by_class returned None")
else:
    print("Enemy_Zombie_01 not found")
