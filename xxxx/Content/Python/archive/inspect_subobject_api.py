import unreal

sub_sys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
methods = [m for m in dir(sub_sys) if not m.startswith("__")]

bp_path = "/Game/Blueprints/Player/BP_Player_Medic"
bp = unreal.load_asset(bp_path)
handles = sub_sys.k2_gather_subobject_data_for_blueprint(bp) if bp else []

lines = [
    "=== METHODS ===",
    "\n".join(methods),
    f"=== BP_Player_Medic HANDLES: {len(handles)} ==="
]

with open("/Users/cc/Desktop/GGBOM/xxxx/Content/Python/subobject_methods.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
