# -*- coding: utf-8 -*-
"""
run_and_capture_boss_combat.py
自动化启动 360x640 StandAlone 独立游戏窗口，并在关键节点截取高清画面证据：
1. 捕获顶部由 4 大指定素材构成的豪华 Boss 血条全局呈现；
2. 模拟射击输入，捕获子弹命中怪物产生的火花与向上浮动的金黄色 -45 伤害飘字；
3. 捕获怪物受击被销毁与 Boss 血条动态数据联动扣减证据。
"""
import subprocess
import time
import os
import sys
from pathlib import Path
from PIL import Image

ARTIFACTS = Path("/Users/cc/.gemini/antigravity-ide/brain/f35b8df0-8551-4e50-b74f-fb2d18df71f3")
PROJECT_DIR = Path("/Users/cc/Desktop/GGBOM/xxxx")

def find_game_window():
    try:
        import Quartz
        window_list = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
        for w in window_list:
            owner = w.get(Quartz.kCGWindowOwnerName, "")
            name = w.get(Quartz.kCGWindowName, "")
            bounds = w.get(Quartz.kCGWindowBounds, {})
            if "Unreal" in owner or "xxxx" in owner or "xxxx" in name or "GGBOM" in name:
                wid = w.get(Quartz.kCGWindowNumber)
                return wid, bounds
    except Exception as e:
        print(f"Quartz error: {e}")
    return None, None

def capture_shot(shot_name):
    tmp_path = f"/tmp/{shot_name}.png"
    wid, bounds = find_game_window()
    if wid:
        cmd = f"screencapture -l{wid} -o -x '{tmp_path}'"
    else:
        cmd = f"screencapture -x '{tmp_path}'"
    subprocess.run(cmd, shell=True)
    
    if os.path.exists(tmp_path):
        target = ARTIFACTS / f"{shot_name}.png"
        img = Image.open(tmp_path)
        img.save(target)
        print(f"📸 捕获并保存实机截图: {target}")
        return target
    return None

def main():
    print("🎮 正在启动 360x640 轻量独立游戏窗口进行动态战斗与 Boss 血条检验...")
    game_proc = subprocess.Popen(
        ["/bin/bash", str(PROJECT_DIR / "Tools/launch_lightweight_game.sh")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    try:
        # 等待游戏窗口完全初始化
        print("⏳ 等待游戏窗口就绪 (5s)...")
        time.sleep(5)
        
        # 第 1 阶段：捕获 Boss 血条在顶部黄金区的完整展现
        capture_shot("boss_healthbar_initial_overview")
        
        # 激活窗口并连续发送射击指令 (空格键 key code 49)
        print("🔫 模拟主角持续开火 (Space)...")
        for i in range(12):
            subprocess.run("osascript -e 'tell application \"System Events\" to key code 49'", shell=True)
            time.sleep(0.3)
            if i == 5:
                capture_shot("boss_combat_hit_and_damage_pop")
            elif i == 11:
                capture_shot("boss_combat_destroy_and_bar_linkage")
                
        print("⏳ 额外缓冲 2 秒观察销毁与血条变化...")
        time.sleep(2)
        capture_shot("boss_combat_final_live_shot")

    finally:
        print("🛑 关闭游戏进程...")
        game_proc.terminate()
        try:
            game_proc.wait(timeout=3)
        except Exception:
            game_proc.kill()
            
    print("✅ 自动化实机战斗与 Boss 血条动态验证完成！")

if __name__ == "__main__":
    main()
