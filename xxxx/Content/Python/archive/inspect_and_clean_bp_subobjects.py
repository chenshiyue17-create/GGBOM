# -*- coding: utf-8 -*-
import unreal

bp_paths = [
    "/Game/Blueprints/Player/BP_Player_Medic",
    "/Game/GGBOM/Blueprints/BP_Player_Medic"
]

sub_sys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
sub_lib = unreal.SubobjectDataBlueprintFunctionLibrary

out = []

for p in bp_paths:
    if not unreal.EditorAssetLibrary.does_asset_exist(p):
        continue
    bp = unreal.load_asset(p)
    out.append(f"============================================================")
    out.append(f"BP: {p}")
    handles = sub_sys.k2_gather_subobject_data_for_blueprint(bp)
    out.append(f"Total Subobjects: {len(handles)}")
    
    fb_handles = []
    for h in handles:
        data = sub_lib.get_data(h)
        obj = sub_lib.get_object_for_blueprint(data, bp)
        cls_name = obj.get_class().get_name() if obj else "None"
        var_name = str(sub_lib.get_variable_name(data))
        out.append(f"  Subobject: '{var_name}' | Class: {cls_name} | ObjName: {obj.get_name() if obj else 'None'}")
        if cls_name == "PaperFlipbookComponent":
            fb_handles.append((h, var_name, obj))
            
    out.append(f"Found {len(fb_handles)} PaperFlipbookComponents in BP!")
    
    # 如果有多个 PaperFlipbookComponent，保留第一个，删除后面的
    if len(fb_handles) > 1:
        out.append("--> MULTIPLE FLIPBOOKS DETECTED! Cleaning up duplicates...")
        for h, vname, obj in fb_handles[1:]:
            out.append(f"  Deleting duplicate subobject: {vname}")
            sub_sys.delete_subobject(handles[0], h, bp)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
        out.append("--> Cleanup finished and saved!")

with open("/Users/cc/Desktop/GGBOM/xxxx/Content/Python/subobjects_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("Completed subobject inspection and cleanup.")
