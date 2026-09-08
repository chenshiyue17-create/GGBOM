# -*- coding: utf-8 -*-
import unreal

bp_lib_methods = [m for m in dir(unreal.BlueprintEditorLibrary) if not m.startswith("_")]
graph_ed_methods = [m for m in dir(unreal.BlueprintGraphEditor) if not m.startswith("_")]
pin_lib_methods = [m for m in dir(unreal.BlueprintGraphPinLibrary) if not m.startswith("_")]

with open("/Users/cc/Desktop/GGBOM/xxxx/output/bp_apis.txt", "w", encoding="utf-8") as f:
    f.write("=== BlueprintEditorLibrary ===\n")
    for m in bp_lib_methods:
        f.write(f"  {m}\n")
    f.write("\n=== BlueprintGraphEditor ===\n")
    for m in graph_ed_methods:
        f.write(f"  {m}\n")
    f.write("\n=== BlueprintGraphPinLibrary ===\n")
    for m in pin_lib_methods:
        f.write(f"  {m}\n")

print("Done writing bp_apis.txt")
