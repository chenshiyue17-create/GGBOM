# -*- coding: utf-8 -*-
import unreal

world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/GGBOM/Maps/MAP_GGBOM_Main")
proj_cls = unreal.load_class(None, "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C")

# 测试在世界中 spawn 一个子弹
loc = unreal.Vector(0.0, 0.0, 0.0)
rot = unreal.Rotator(90.0, 0.0, 0.0) # Pitch=90
trans = unreal.Transform(location=loc, rotation=rot.to_quat(), scale=unreal.Vector(1,1,1))

actor = unreal.EditorLevelLibrary.spawn_actor_from_class(proj_cls, loc, rot)

out = []
if actor:
    out.append(f"Spawned: {actor.get_name()}")
    out.append(f"RootComponent: {actor.root_component.get_name() if actor.root_component else 'None'}")
    # 查找 ProjectileMovement
    pmc = actor.get_component_by_class(unreal.ProjectileMovementComponent)
    if pmc:
        out.append(f"PMC found: InitialSpeed={pmc.get_editor_property('initial_speed')}, Velocity={pmc.get_editor_property('velocity')}, InLocal={pmc.get_editor_property('initial_velocity_in_local_space')}")
        # 打印计算出的世界速度
        # 在 editor 下没有 tick，但可以检查组件属性
    actor.destroy_actor()

with open("/Users/cc/Desktop/GGBOM/test_bullet_spawn.txt", "w") as f:
    f.write("\n".join(out))
print("DONE_TEST_BULLET_SPAWN")
