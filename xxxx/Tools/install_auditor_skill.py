# -*- coding: utf-8 -*-
"""
安装 UE5 Blueprint Auditor Skill 到 Antigravity 工作区与项目目录
"""
import zipfile
from pathlib import Path

zip_path = Path("/Users/cc/Desktop/GGBOM/UE5_BLUEPRINT_AUDITOR_ANTIGRAVITY_INSTALL.zip")
target_roots = [
    Path("/Users/cc/Desktop/GGBOM/.agents/skills/ue5-blueprint-auditor"),
    Path("/Users/cc/Desktop/GGBOM/xxxx/.agents/skills/ue5-blueprint-auditor")
]

with zipfile.ZipFile(zip_path, 'r') as z:
    prefix = "UE5_Blueprint_Auditor_Antigravity_Install/.agents/skills/ue5-blueprint-auditor/"
    members = [m for m in z.namelist() if m.startswith(prefix) and not m.endswith("/")]
    
    for target in target_roots:
        target.mkdir(parents=True, exist_ok=True)
        for m in members:
            rel = m[len(prefix):]
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            with z.open(m) as src_f, open(dest, 'wb') as dst_f:
                dst_f.write(src_f.read())
        print(f"✅ 部署完成: {target}")

print("所有 Skill 文件已成功安装。")
