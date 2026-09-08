# -*- coding: utf-8 -*-
import unreal

pt = unreal.EdGraphPinType()
print("EdGraphPinType dir:")
for d in dir(pt):
    if not d.startswith("_"):
        print(f"  {d}")
