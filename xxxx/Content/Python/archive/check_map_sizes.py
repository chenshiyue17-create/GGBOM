# -*- coding: utf-8 -*-
from PIL import Image
from pathlib import Path

map_dir = Path("/Users/cc/Desktop/GGBOM/xxxx/Content/美术/Art/08_Maps")
for f in sorted(map_dir.glob("*/*.png")):
    img = Image.open(f)
    print(f"Map: {f.name} | Size: {img.size} (W={img.size[0]}, H={img.size[1]})")
