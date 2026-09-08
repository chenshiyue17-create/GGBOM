# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》UE5 纯蓝图资产总装构建入口 (Master Asset Pipeline)
================================================================================
"""

import os
import sys

# 运行各子模块
import build_01_core_types
import build_02_projectiles_and_tactical_props
import build_03_characters_and_stage_manager

def main():
    print("==================================================================")
    print("🚀 [GGBOM 终末医疗兵] 正在执行 UE5 纯蓝图 2D 竖屏单屏幕资产总装...")
    print("==================================================================")
    
    build_01_core_types.export_json_data_tables()
    build_02_projectiles_and_tactical_props.export_combat_specs()
    build_03_characters_and_stage_manager.export_stage_specs()
    
    print("\n✅ 所有纯蓝图类规约、数据表（DT_WeaponsConfig, DT_TacticalPropsConfig, DT_CardUpgradesConfig）与 Stage00 关卡波次控制器已全部构建并组装就绪！")
    print("==================================================================")

if __name__ == "__main__":
    main()
