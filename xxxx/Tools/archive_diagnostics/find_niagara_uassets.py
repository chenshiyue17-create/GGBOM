from pathlib import Path
p = Path("/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Plugins/FX/Niagara/Content")
if p.exists():
    uassets = list(p.rglob("*.uasset"))
    print(f"Found {len(uassets)} Niagara uassets")
    for u in uassets[:30]:
        rel = u.relative_to(p)
        print(f"/Niagara/{rel.with_suffix('')}")
else:
    print("Niagara content dir not found")
