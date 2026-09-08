# -*- coding: utf-8 -*-
"""
行尸家族 (Zombie Family) 单蓝图独立装配脚本
- 资源：4 帧连续动画图集 (Sprite Sheet PaperFlipbook)
- 移动：基于玩家坐标的自主 AI 追踪寻路
- 避障：轴分离物理位移 (X + Z 双路 Sweep，切向滑动不卡掩体)
- 视觉：X 轴朝向自适应翻转 (左右面朝玩家)
- 物理：BoxComponent 实体阻挡碰撞 (Pawn 通道)
- 移除固定下推：清理旧有的 ProjectileMovementComponent

用法:
UnrealEditor ... -run=pythonscript -script=".../build_zombie_family.py <ENEMY_TYPE>"
"""
import sys
import unreal

# 配置表：每种行尸的 4 帧图集、移速、缩放与碰撞尺寸
ZOMBIE_CONFIGS = {
    "BP_Enemy_ZombieWalker": {
        "bp_path": "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet.FB_T_Zombie_WalkerBasic_Sheet",
        "speed": 65.0,
        "scale": 0.45,
        "box_extent": unreal.Vector(25.0, 60.0, 35.0),
    },
    "BP_Enemy_ZombieRunner": {
        "bp_path": "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieRunner",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/05_Zombie_Runner_Agile/Flipbooks/FB_T_Zombie_RunnerAgile_Sheet.FB_T_Zombie_RunnerAgile_Sheet",
        "speed": 105.0,
        "scale": 0.45,
        "box_extent": unreal.Vector(25.0, 60.0, 35.0),
    },
    "BP_Enemy_VenomShooter": {
        "bp_path": "/Game/Blueprints/Characters/Enemies/BP_Enemy_VenomShooter",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/04_Zombie_Spitter_Minor/Flipbooks/FB_T_Zombie_SpitterMinor_Sheet.FB_T_Zombie_SpitterMinor_Sheet",
        "speed": 60.0,
        "scale": 0.45,
        "box_extent": unreal.Vector(25.0, 60.0, 35.0),
    },
    "BP_Enemy_ArmoredGuard": {
        "bp_path": "/Game/Blueprints/Characters/Enemies/BP_Enemy_ArmoredGuard",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/07_Zombie_Armored_Guard/Flipbooks/FB_T_Zombie_ArmoredGuard_Sheet.FB_T_Zombie_ArmoredGuard_Sheet",
        "speed": 50.0,
        "scale": 0.50,
        "box_extent": unreal.Vector(30.0, 70.0, 40.0),
    },
    "BP_Enemy_MutantBrute": {
        "bp_path": "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantBrute",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet.FB_T_Zombie_ShamblerHeavy_Sheet",
        "speed": 42.0,
        "scale": 0.55,
        "box_extent": unreal.Vector(35.0, 75.0, 45.0),
    },
}

target_name = None
for arg in sys.argv:
    for k in ZOMBIE_CONFIGS:
        if k in arg:
            target_name = k
            break
    if target_name:
        break

if not target_name:
    # 默认如果没传，从环境变量或由外部指定
    target_name = "BP_Enemy_ZombieRunner"

cfg = ZOMBIE_CONFIGS[target_name]
print(f"=== [BUILD_ZOMBIE] Starting build for: {target_name} ===")

bp = unreal.load_asset(cfg["bp_path"])
if not bp:
    raise RuntimeError(f"Cannot load Blueprint: {cfg['bp_path']}")

bplib = unreal.BlueprintEditorLibrary
pinlib = unreal.BlueprintGraphPinLibrary
subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

# 1. 移除旧的 ProjectileMovementComponent
handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)
for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    if isinstance(obj, unreal.ProjectileMovementComponent):
        subsystems.delete_subobject(handles[0], h, bp)
        print(f"Removed ProjectileMovementComponent from {target_name}")
        break

# 2. 确保实体碰撞盒 (BoxComponent -> Pawn 通道)
box_comp = None
for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    if isinstance(obj, unreal.BoxComponent):
        box_comp = obj
        break
if box_comp:
    box_comp.set_editor_property("box_extent", cfg["box_extent"])
    box_comp.set_collision_profile_name("Pawn")
    box_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    try:
        box_comp.set_editor_property("generate_overlap_events", True)
    except Exception:
        pass

# 3. 清理 EventGraph
graph = bplib.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
tick_node = ed.find_event_node("ReceiveTick")
begin_node = ed.find_event_node("ReceiveBeginPlay")
keep_paths = {tick_node.get_path_name()}
if begin_node:
    keep_paths.add(begin_node.get_path_name())

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

# 4. 获取玩家坐标与自身坐标
get_player = fn("/Script/Engine.GameplayStatics.GetPlayerPawn", 200, 100)
set_value(get_player, "PlayerIndex", 0)

p_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", 450, 50)
connect(get_player, "ReturnValue", p_loc, "self")

self_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", 450, 180)

# 计算差值与单位化
sub_v = fn("/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 100)
connect(p_loc, "ReturnValue", sub_v, "A")
connect(self_loc, "ReturnValue", sub_v, "B")

norm_v = fn("/Script/Engine.KismetMathLibrary.Normal", 920, 100)
connect(sub_v, "ReturnValue", norm_v, "A")

break_v = fn("/Script/Engine.KismetMathLibrary.BreakVector", 1140, 100)
connect(norm_v, "ReturnValue", break_v, "InVec")

speed = cfg["speed"]
base_scale = cfg["scale"]

# 5. 轴分离位移 (X + Z 双路 Sweep，切向滑动避障)
# X 轴位移
mul_x_speed = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1360, 50)
connect(break_v, "X", mul_x_speed, "A")
set_value(mul_x_speed, "B", speed)

mul_x_dt = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1580, 50)
connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

delta_vec_x = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1800, 50)
connect(mul_x_dt, "ReturnValue", delta_vec_x, "X")
set_value(delta_vec_x, "Y", 0.0)
set_value(delta_vec_x, "Z", 0.0)

move_x = fn("/Script/Engine.Actor.K2_AddActorWorldOffset", 2050, 50)
set_value(move_x, "bSweep", "true")
connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
connect(tick_node, "then", move_x, "execute")

# Z 轴位移
mul_z_speed = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1360, 220)
connect(break_v, "Z", mul_z_speed, "A")
set_value(mul_z_speed, "B", speed)

mul_z_dt = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1580, 220)
connect(mul_z_speed, "ReturnValue", mul_z_dt, "A")
connect(tick_node, "DeltaSeconds", mul_z_dt, "B")

delta_vec_z = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1800, 220)
set_value(delta_vec_z, "X", 0.0)
set_value(delta_vec_z, "Y", 0.0)
connect(mul_z_dt, "ReturnValue", delta_vec_z, "Z")

move_z = fn("/Script/Engine.Actor.K2_AddActorWorldOffset", 2050, 220)
set_value(move_z, "bSweep", "true")
connect(delta_vec_z, "ReturnValue", move_z, "DeltaLocation")
connect(move_x, "then", move_z, "execute")

# 6. 左右视觉翻转 (玩家在右则翻转 X=-base_scale，玩家在左则 X=base_scale)
is_right = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1360, -100)
connect(break_v, "X", is_right, "A")
set_value(is_right, "B", 0.0)

sel_scale = fn("/Script/Engine.KismetMathLibrary.SelectFloat", 1580, -100)
set_value(sel_scale, "A", -base_scale)
set_value(sel_scale, "B", base_scale)
connect(is_right, "ReturnValue", sel_scale, "bPickA")

scale_vec = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1800, -100)
connect(sel_scale, "ReturnValue", scale_vec, "X")
set_value(scale_vec, "Y", base_scale)
set_value(scale_vec, "Z", base_scale)

get_fb = fn("/Script/Engine.Actor.GetComponentByClass", 1800, -250)
set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

set_scale = fn("/Script/Engine.SceneComponent.SetRelativeScale3D", 2050, -150)
connect(get_fb, "ReturnValue", set_scale, "self")
connect(scale_vec, "ReturnValue", set_scale, "NewScale3D")
connect(move_z, "then", set_scale, "execute")

# 7. 确保默认 4 帧 Flipbook 资源正确
fb_asset = unreal.load_asset(cfg["flipbook"])
cdo = unreal.get_default_object(bp.generated_class())
if cdo:
    fb_comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
    if fb_comp:
        if fb_asset:
            fb_comp.set_editor_property("source_flipbook", fb_asset)
        fb_comp.set_editor_property("relative_scale3d", unreal.Vector(base_scale, base_scale, base_scale))
        fb_comp.set_editor_property("translucency_sort_priority", 100)

# 8. 编译并保存
compiled = bplib.compile_blueprint(bp)
saved = unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
print(f"=== [BUILD_ZOMBIE] {target_name} FINISHED: compiled={compiled}, saved={saved} ===")
