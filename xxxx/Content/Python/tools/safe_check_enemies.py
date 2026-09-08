import unreal

GEN = "/Game/Blueprints/Characters/Enemies"
enemies = [
    "BP_Enemy_ZombieWalker",
    "BP_Enemy_ZombieRunner",
    "BP_Enemy_MutantHound",
    "BP_Enemy_VenomShooter",
    "BP_Enemy_ArmoredGuard",
    "BP_Enemy_MutantBrute",
    "BP_Boss_Overlord"
]

log_lines = []
for name in enemies:
    path = f"{GEN}/{name}"
    bp = unreal.load_asset(path)
    if not bp:
        log_lines.append(f"MISSING: {path}")
        continue
    gen_cls = bp.generated_class()
    super_cls = gen_cls.get_super_class().get_name() if gen_cls else "None"
    cdo = unreal.get_default_object(gen_cls) if gen_cls else None
    comps = []
    if cdo:
        for c in cdo.get_components_by_class(unreal.ActorComponent):
            comps.append(f"{c.get_name()}:{c.__class__.__name__}")
    log_lines.append(f"BP: {name} | Super: {super_cls} | Comps: {comps}")

out_text = "\n".join(log_lines)
print(out_text)
unreal.log(out_text)
with open("/Users/cc/Desktop/GGBOM/xxxx/output/enemy_bp_audit.txt", "w") as f:
    f.write(out_text)
