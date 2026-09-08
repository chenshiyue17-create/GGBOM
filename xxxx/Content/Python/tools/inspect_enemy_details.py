import unreal

bplib = unreal.BlueprintEditorLibrary
enemies = [
    "BP_Enemy_ZombieWalker", "BP_Enemy_ZombieRunner", "BP_Enemy_MutantHound",
    "BP_Enemy_VenomShooter", "BP_Enemy_ArmoredGuard", "BP_Enemy_MutantBrute",
    "BP_Boss_Overlord"
]

lines = []
for name in enemies:
    path = f"/Game/Blueprints/Characters/Enemies/{name}"
    bp = unreal.load_asset(path)
    if not bp:
        continue
    graphs = [str(x) for x in bplib.list_graph_names(bp)]
    vars = [str(x) for x in bplib.list_member_variable_names(bp, False)]
    lines.append(f"=== {name} ===")
    lines.append(f"  Graphs: {graphs}")
    lines.append(f"  Vars: {vars}")

with open("/Users/cc/Desktop/GGBOM/xxxx/output/enemy_details.txt", "w") as f:
    f.write("\n".join(lines))
unreal.log("Saved enemy details to output/enemy_details.txt")

