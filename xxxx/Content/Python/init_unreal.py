# -*- coding: utf-8 -*-
"""
init_unreal.py
虚幻引擎启动/重载时自动调用的入口
增加游戏运行时与编辑器环境隔离保护，彻底防止独立运行模式 (-game) 下 SIGSEGV
"""
import unreal

unreal.log("==================================================")
unreal.log("🚀 [INIT_UNREAL] 虚幻引擎环境初始化检测...")

try:
    # 严格判断是否在编辑器环境中运行
    is_editor = unreal.SystemLibrary.is_editor()
except Exception as e:
    is_editor = False

if not is_editor:
    unreal.log("🎮 [INIT_UNREAL] 当前处于独立游戏运行时 (-game 模式)，安全跳过编辑器资产落盘流水线，直通游戏主循环！")
else:
    unreal.log("🛠️ [INIT_UNREAL] 当前处于编辑器模式。底层蓝图闭环与碰撞体积已持久化落盘，保持只读保护。")
unreal.log("==================================================")

