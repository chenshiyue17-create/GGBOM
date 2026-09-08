# -*- coding: utf-8 -*-
import unreal

out_f = "/Users/cc/Desktop/GGBOM/xxxx/world_coords.txt"
lines = ["=" * 60, "WORLD ACTORS INSPECTION:"]
actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in actors:
    lbl = a.get_actor_label()
    if any(k in lbl for k in ["Camera", "Player", "Boundary", "Wall", "Cover", "Ground"]):
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        lines.append(f"  Actor: {lbl:25} | Loc: X={loc.x:7.1f}, Y={loc.y:7.1f}, Z={loc.z:7.1f} | Rot: P={rot.pitch:5.1f}, Y={rot.yaw:5.1f}, R={rot.roll:5.1f}")
lines.append("=" * 60)
with open(out_f, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
