# -*- coding: utf-8 -*-
import unreal

MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)

cam = None
actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in actors:
    if "PortraitCamera" in a.get_actor_label():
        cam = a
        break

out = []
if cam:
    loc = cam.get_actor_location()
    rot = cam.get_actor_rotation()
    fwd = cam.get_actor_forward_vector()
    right = cam.get_actor_right_vector()
    up = cam.get_actor_up_vector()
    out.append(f"Camera: {cam.get_actor_label()}")
    out.append(f"Loc: {loc}")
    out.append(f"Rot: {rot}")
    out.append(f"ForwardVector: {fwd}")
    out.append(f"RightVector:   {right}")
    out.append(f"UpVector:      {up}")
else:
    out.append("Camera not found!")

with open("/Users/cc/Desktop/GGBOM/camera_vectors.txt", "w") as f:
    f.write("\n".join(out))
print("DONE_CAMERA_VECTORS")
