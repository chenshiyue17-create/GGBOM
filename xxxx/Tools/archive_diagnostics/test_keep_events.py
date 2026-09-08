# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/keep_events_result.txt"

BPLIB = unreal.BlueprintEditorLibrary
ASSETS = unreal.EditorAssetLibrary

lines = []
def log(msg):
    lines.append(str(msg))
    print(msg, flush=True)

try:
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
    bp = ASSETS.load_asset(bp_path)
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    events = [n for n in ed.list_all_nodes() if isinstance(n, unreal.K2Node_Event)]
    non_events = [n for n in ed.list_all_nodes() if not isinstance(n, unreal.K2Node_Event)]
    
    log(f"Events: {[n.get_name() for n in events]}")
    log(f"Non-events count: {len(non_events)}")
    
    # 安全移除非事件节点
    ed.remove_nodes(non_events)
    log(f"Remaining nodes after remove: {len(ed.list_all_nodes())}")
    
    # 尝试添加一个测试节点
    test_node = ed.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerPawn")
    log(f"Successfully added node: {test_node.get_name()}")
    
    BPLIB.compile_blueprint(bp)
    log("Successfully compiled!")
except Exception as e:
    log(f"Exception: {e}")

OUT.write_text("\n".join(lines), encoding="utf-8")
