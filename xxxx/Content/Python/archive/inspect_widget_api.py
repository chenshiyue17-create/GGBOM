import unreal

widget_bp = unreal.load_asset("/Game/GGBOM/UI/WBP_GGBOM_CombatHUD")
lines = []
lines.append("=== WIDGET BLUEPRINT DIR ===")
for attr in dir(widget_bp):
    if not attr.startswith("__"):
        lines.append(f"  ATTR: {attr}")

gen_class = widget_bp.generated_class()
lines.append(f"=== GENERATED CLASS === {gen_class}")
if gen_class:
    cdo = unreal.get_default_object(gen_class)
    lines.append(f"=== CDO === {cdo}")
    if cdo:
        for attr in dir(cdo):
            if not attr.startswith("__"):
                lines.append(f"  CDO ATTR: {attr}")

with open("/Users/cc/Desktop/GGBOM/xxxx/Content/Python/widget_api_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
