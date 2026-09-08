# -*- coding: utf-8 -*-
"""
修复并升级子弹投射物蓝图 BP_ProjectileBase
- CollisionSphere 确立为 RootComponent
- 碰撞预设: 针对 Pawn 和 WorldStatic 设为 Block
- 开启 Simulation Generates Hit Events (产生 OnHit 事件)
- EventGraph 架构:
  1. ReceiveHit (Event Hit): 撞击怪物时对其施加伤害 (ApplyDamage)，播放击中反馈并立即销毁自身 (DestroyActor)
  2. ReceiveBeginPlay: 2 秒自然超时安全销毁 (防止打空穿出屏幕)
"""
import unreal

bp_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
bp = unreal.load_asset(bp_path)
if not bp:
    raise RuntimeError(f"Cannot load {bp_path}")

bplib = unreal.BlueprintEditorLibrary
pinlib = unreal.BlueprintGraphPinLibrary
subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)
sphere_handle = None
sphere_comp = None
for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    if isinstance(obj, unreal.SphereComponent):
        sphere_handle = h
        sphere_comp = obj
        break

# 1. 将 SphereComponent 设为 RootComponent
if sphere_handle:
    try:
        subsystems.make_new_scene_root(handles[0], sphere_handle, bp)
        print("SphereComponent successfully set as RootComponent")
    except Exception as e:
        print(f"make_new_scene_root exception: {e}")

# 2. 配置物理碰撞属性
if sphere_comp:
    sphere_comp.set_editor_property("sphere_radius", 20.0)
    sphere_comp.set_collision_profile_name("BlockAllDynamic")
    sphere_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    sphere_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_BLOCK)
    sphere_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC, unreal.CollisionResponseType.ECR_BLOCK)
    sphere_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC, unreal.CollisionResponseType.ECR_BLOCK)
    sphere_comp.set_editor_property("body_instance", sphere_comp.get_editor_property("body_instance"))
    try:
        sphere_comp.set_editor_property("notify_rigid_body_collision", True)
        sphere_comp.set_editor_property("generate_overlap_events", True)
    except Exception as e:
        print(f"Prop setting note: {e}")

# 3. 确保外观 Sprite 材质为透明材质
mat_trans = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
cdo = unreal.get_default_object(bp.generated_class())
if cdo:
    sp_comp = cdo.get_component_by_class(unreal.PaperSpriteComponent)
    if sp_comp and mat_trans:
        sp_comp.set_material(0, mat_trans)
        sp_comp.set_editor_property("relative_scale3d", unreal.Vector(0.7, 0.7, 0.7))
        sp_comp.set_editor_property("translucency_sort_priority", 2500)

# 4. 重构 EventGraph
graph = bplib.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

# 保留系统事件节点
begin_node = ed.find_event_node("ReceiveBeginPlay")
hit_node = ed.find_event_node("ReceiveHit")

keep_paths = set()
if begin_node: keep_paths.add(begin_node.get_path_name())
if hit_node: keep_paths.add(hit_node.get_path_name())

nodes_to_remove = [n for n in ed.list_all_nodes() if n.get_path_name() not in keep_paths]
if nodes_to_remove:
    ed.remove_nodes(nodes_to_remove)

def pin(node, name, output):
    values = bplib.list_output_pins(node) if output else bplib.list_input_pins(node)
    wanted = name.lower()
    exact = [p for p in values if str(pinlib.get_pin_name(p)).lower() == wanted]
    if len(exact) == 1:
        return exact[0]
    raise RuntimeError(f"Pin {name} not found; available={[str(pinlib.get_pin_name(p)) for p in values]}")

def set_value(node, name, value):
    target = pin(node, name, False)
    if not pinlib.set_pin_value(target, str(value)):
        raise RuntimeError(f"Default rejected: {name}={value}")

def connect(a, a_pin, b, b_pin):
    source, target = pin(a, a_pin, True), pin(b, b_pin, False)
    if not pinlib.try_create_connection(source, target):
        raise RuntimeError(f"Connection rejected: {a_pin} -> {b_pin}")

def fn(path, x, y):
    node = ed.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"Cannot create node: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

# (1) BeginPlay 超时销毁
if begin_node:
    delay_node = fn("/Script/Engine.KismetSystemLibrary.Delay", 350, 300)
    set_value(delay_node, "Duration", 2.5)
    connect(begin_node, "then", delay_node, "execute")
    destroy_timeout = fn("/Script/Engine.Actor.K2_DestroyActor", 600, 300)
    connect(delay_node, "then", destroy_timeout, "execute")

# (2) 碰撞命中处理
if not hit_node and sphere_comp:
    try:
        hit_node = ed.add_component_bound_event_node(sphere_comp, "OnComponentHit")
    except Exception as e:
        print(f"add_component_bound_event_node failed: {e}")

if hit_node:
    hit_node.set_node_pos(unreal.IntPoint(100, 50))
    apply_dmg = fn("/Script/Engine.GameplayStatics.ApplyDamage", 450, 50)
    connect(hit_node, "then", apply_dmg, "execute")
    # 如果是 OnComponentHit, 目标引脚为 OtherActor; 如果是 ReceiveHit, 引脚为 Other
    other_pin_name = "OtherActor" if "OtherActor" in [str(pinlib.get_pin_name(p)) for p in bplib.list_output_pins(hit_node)] else "Other"
    connect(hit_node, other_pin_name, apply_dmg, "DamagedActor")
    set_value(apply_dmg, "BaseDamage", 35.0)

    destroy_hit = fn("/Script/Engine.Actor.K2_DestroyActor", 800, 50)
    connect(apply_dmg, "then", destroy_hit, "execute")


# 5. 编译与保存
compiled = bplib.compile_blueprint(bp)
saved = unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
print(f"PROJECTILE_FIX_STATUS: compiled={compiled}, saved={saved}")
