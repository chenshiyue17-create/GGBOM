import os
import json
import unreal

def inspect_player_and_gamemode():
    results = {}
    
    paths = [
        "/Game/Blueprints/Player/BP_Player_Medic",
        "/Game/GGBOM/Blueprints/BP_GGBOM_GameMode"
    ]
    
    for p in paths:
        bp = unreal.EditorAssetLibrary.load_asset(p)
        if not bp:
            results[p] = {"exists": False}
            continue
            
        gen_cls = bp.generated_class()
        cdo = unreal.get_default_object(gen_cls) if gen_cls else None
        
        # 搜集所有变量
        var_names = [str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(bp, False)]
        
        # 搜集所有组件
        components = []
        subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        for h in subsys.k2_gather_subobject_data_for_blueprint(bp):
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
            if obj:
                components.append({
                    "var_name": vname,
                    "class": obj.get_class().get_name()
                })
                
        # 搜集所有图表中的所有节点
        editor = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))
        node_summaries = []
        if editor:
            for n in editor.list_all_nodes():
                title = n.get_node_title(unreal.NodeTitleType.FULL_TITLE) if hasattr(n, "get_node_title") else str(n)
                n_cls = n.get_class().get_name()
                pins = []
                for pin in unreal.BlueprintEditorLibrary.list_all_pins(n):
                    p_name = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                    p_val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin) if hasattr(unreal.BlueprintGraphPinLibrary, "get_pin_value") else ""
                    # 检查是否有默认对象
                    pins.append(f"{p_name}={p_val}")
                node_summaries.append({
                    "title": str(title),
                    "class": n_cls,
                    "pins": pins[:8]
                })
                
        results[p] = {
            "variables": var_names,
            "components": components,
            "node_count": len(node_summaries),
            "nodes": node_summaries
        }
        
    out_path = "/Users/cc/Desktop/GGBOM/xxxx/output/player_gamemode_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Audit done: {out_path}")

inspect_player_and_gamemode()
