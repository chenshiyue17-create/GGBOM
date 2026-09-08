# -*- coding: utf-8 -*-
"""
================================================================================
fix_projectile_collision_filter.py
彻底拆除旧火球组件 + 换装动能手枪子弹 + 1200 极速穿透弹道
与 master_combat_system.py 保持 100% 对齐，杜绝任何未捕获异常
================================================================================
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import unreal

from master_combat_system import execute_master_combat_closure

if __name__ == "__main__":
    execute_master_combat_closure()
