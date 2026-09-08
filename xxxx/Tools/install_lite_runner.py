# -*- coding: utf-8 -*-
"""
部署 UE5 Lite Runner 技能并设置可执行权限
"""
import os
import shutil
from pathlib import Path

src = Path("/Users/cc/Desktop/GGBOM/UE5_LITE_RUNNER_Antigravity_Install/.agents/skills/ue5-lite-runner")

targets = [
    Path("/Users/cc/Desktop/GGBOM/.agents/skills/ue5-lite-runner"),
    Path("/Users/cc/Desktop/GGBOM/xxxx/.agents/skills/ue5-lite-runner"),
    Path.home() / ".gemini/config/skills/ue5-lite-runner",
    Path.home() / ".gemini/antigravity/skills/ue5-lite-runner"
]

for t in targets:
    t.parent.mkdir(parents=True, exist_ok=True)
    if t.exists():
        shutil.rmtree(t)
    shutil.copytree(src, t)
    # 给 scripts 下的 .command 文件加执行权限
    scripts_dir = t / "scripts"
    if scripts_dir.is_dir():
        for f in scripts_dir.glob("*.command"):
            os.chmod(f, 0o755)
    print(f"✅ 已部署到: {t}")

print("UE5 Lite Runner 技能全量安装完成！")
