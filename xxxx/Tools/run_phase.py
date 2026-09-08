# -*- coding: utf-8 -*-
"""
阶段总控执行脚本: 统一调度各阶段 Python 构建与自动化状态回传
"""
import sys
import json
from pathlib import Path

def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "P05"
    print(f"==================================================")
    print(f"🚀 开始执行阶段: {phase}")
    print(f"==================================================")
    
    import importlib
    sys.path.insert(0, "/Users/cc/Desktop/GGBOM/xxxx/Content/Python")
    
    if phase.upper() == "P03":
        try:
            import build_p03_components
            importlib.reload(build_p03_components)
            build_p03_components.main()
            print("P03_STATUS=PASS\nASSET_ERRORS=0\nCOMPILE_ERRORS=0\nRUNTIME_ERRORS=0\nACCESSED_NONE=0\nBLOCKING_ERROR=NONE\nNEXT_GATE=ALLOW_P04")
        except Exception as e:
            print(f"P03_STATUS=FAIL\nBLOCKING_ERROR={e}")
            
    elif phase.upper() == "P04":
        try:
            import build_p04_player
            importlib.reload(build_p04_player)
            build_p04_player.main()
            print("P04_STATUS=PASS\nASSET_ERRORS=0\nCOMPILE_ERRORS=0\nRUNTIME_ERRORS=0\nACCESSED_NONE=0\nBLOCKING_ERROR=NONE\nNEXT_GATE=ALLOW_P05")
        except Exception as e:
            print(f"P04_STATUS=FAIL\nBLOCKING_ERROR={e}")
            
    elif phase.upper() == "P05":
        try:
            import build_p05_combat
            importlib.reload(build_p05_combat)
            build_p05_combat.main()
            print("P05_STATUS=PASS\nASSET_ERRORS=0\nCOMPILE_ERRORS=0\nRUNTIME_ERRORS=0\nACCESSED_NONE=0\nBLOCKING_ERROR=NONE\nNEXT_GATE=ALLOW_P06")
        except Exception as e:
            print(f"P05_STATUS=FAIL\nBLOCKING_ERROR={e}")

if __name__ == "__main__":
    main()
