# -*- coding: utf-8 -*-
"""
capture_combat_flocking.py
启动独立游戏并在战斗合围阶段（10s, 14s, 18s）精准截取战斗特写
"""
import subprocess
import time
import os
import sys
from pathlib import Path
from PIL import Image

ROOT = Path("/Users/cc/Desktop/GGBOM/xxxx")
ARTIFACTS = Path("/Users/cc/.gemini/antigravity-ide/brain/f35b8df0-8551-4e50-b74f-fb2d18df71f3")

def find_game_window():
    # 使用 Quartz 获取窗口列表
    try:
        import Quartz
        window_list = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
        for w in window_list:
            owner = w.get(Quartz.kCGWindowOwnerName, "")
            name = w.get(Quartz.kCGWindowName, "")
            bounds = w.get(Quartz.kCGWindowBounds, {})
            w_w = bounds.get("Width", 0)
            w_h = bounds.get("Height", 0)
            if "Unreal" in owner or "xxxx" in owner or "xxxx" in name:
                wid = w.get(Quartz.kCGWindowNumber)
                return wid, bounds
    except Exception as e:
        print(f"Quartz error: {e}")
    return None, None

def capture(name):
    tmp_path = f"/tmp/{name}.png"
    wid, bounds = find_game_window()
    if wid:
        cmd = f"screencapture -l{wid} -o -x '{tmp_path}'"
    else:
        cmd = f"screencapture -x '{tmp_path}'"
    subprocess.run(cmd, shell=True)
    
    if os.path.exists(tmp_path):
        target = ARTIFACTS / f"{name}.png"
        img = Image.open(tmp_path)
        # 如果是全屏，尝试裁切
        if not wid and bounds:
            x, y, w, h = int(bounds['X']), int(bounds['Y']), int(bounds['Width']), int(bounds['Height'])
            img = img.crop((x, y, x + w, y + h))
        img.save(target)
        print(f"✅ Saved screenshot to {target}")
        return target
    return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        capture(sys.argv[1])
    else:
        capture("flocking_combat_shot")
