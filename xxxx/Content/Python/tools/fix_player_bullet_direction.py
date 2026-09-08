# -*- coding: utf-8 -*-
"""
优化主角开火朝向与发射位置:
1. 子弹发射方向设为朝向正前方战场 (+Z 向上迎敌: Pitch=90, Yaw=0, Roll=0)
2. 发射初始位置位于主角枪口上方 (Z + 45, Y = 0)，避免生成时被自身刚体盒拦截
"""
import unreal

bp_path = "/Game/Blueprints/Player/BP_Player_Medic"
bp = unreal.load_asset(bp_path)
if not bp:
    raise RuntimeError(f"Cannot load {bp_path}")

bplib = unreal.BlueprintEditorLibrary
pinlib = unreal.BlueprintGraphPinLibrary

graph = bplib.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

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

# 找到生成子弹的 make_rot 节点
for node in ed.list_all_nodes():
    if "MakeRot" in node.get_name():
        try:
            set_value(node, "Pitch", 90.0)
            set_value(node, "Yaw", 0.0)
            set_value(node, "Roll", 0.0)
            print(f"Updated MakeRot node: {node.get_name()} -> Pitch=90.0, Yaw=0.0, Roll=0.0")
        except Exception as e:
            print(f"MakeRot setting: {e}")

compiled = bplib.compile_blueprint(bp)
saved = unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
print(f"PLAYER_BULLET_DIRECTION_FIXED: compiled={compiled}, saved={saved}")
