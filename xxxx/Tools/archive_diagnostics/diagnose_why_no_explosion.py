# -*- coding: utf-8 -*-
import unreal

unreal.log("==================================================")
unreal.log("🔍 诊断为什么没爆炸...")

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

# 1. 检查 Branch 节点的输出引脚名字到底叫什么
proj_bp = unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
graph = BPLIB.find_event_graph(proj_bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
nodes = ed.list_all_nodes()

for n in nodes:
    title = str(BPLIB.get_node_title(n))
    if "分支" in title or "branch" in title.lower() or "ifthen" in n.get_class().get_name().lower():
        unreal.log(f"📌 找到分支节点: {title} (Class: {n.get_class().get_name()})")
        out_pins = BPLIB.list_output_pins(n)
        for p in out_pins:
            pname = str(PINLIB.get_pin_name(p))
            unreal.log(f"   Output Pin: '{pname}'")

# 2. 检查怪物的碰撞配置与 ObjectType
enemy_bp = unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Characters/Enemies/BP_Enemy_Zombie_Base") or unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Enemies/BP_Enemy_Base")
if not enemy_bp:
    # 搜索关卡中的怪物
    for a in unreal.EditorAssetLibrary.list_assets("/Game/Blueprints"):
        if "enemy" in a.lower() or "boss" in a.lower():
            unreal.log(f"   候选敌人资产: {a}")

# 3. 检查子弹当前的 SphereComponent 配置
handles = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem).k2_gather_subobject_data_for_blueprint(proj_bp)
for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, proj_bp)
    if isinstance(obj, unreal.SphereComponent):
        col_type = obj.get_collision_object_type()
        gen_overlap = obj.get_editor_property("generate_overlap_events")
        col_enabled = obj.get_collision_enabled()
        unreal.log(f"🎯 子弹 SphereComponent: ObjectType={col_type}, GenerateOverlap={gen_overlap}, Enabled={col_enabled}")

unreal.log("==================================================")
