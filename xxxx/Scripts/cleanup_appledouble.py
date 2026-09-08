# -*- coding: utf-8 -*-
"""
清理整个 UE Engine 目录中所有 AppleDouble ._*.uplugin* 资源叉文件。
扫描范围：Engine/Plugins + Engine/Platforms（全覆盖）
将文件移动到隔离目录，确保目标文件名不含 .uplugin 后缀（防止 UBT glob 扫描到）。
"""
from pathlib import Path
import shutil

# ===== 扫描整个 Engine 目录（含 Plugins / Platforms 全部子目录）=====
UE_ENGINE_ROOT  = Path('/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine')
QUARANTINE_DIR  = Path('/Users/cc/Desktop/GGBOM/xxxx/Intermediate/Quarantine_AppleDouble_UPlugins')
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

moved  = []
errors = []

print(f"开始扫描: {UE_ENGINE_ROOT}")
print("(首次扫描可能需要 10~30 秒，请等待...)\n")

for p in sorted(UE_ENGINE_ROOT.rglob('._*')):
    if '.uplugin' not in p.name:
        continue  # 只处理含 .uplugin 的文件

    rel = str(p.relative_to(UE_ENGINE_ROOT)).replace('/', '__')
    # 目标名不含 .uplugin，避免被 UBT *.uplugin 扫描到
    safe_name = rel.replace('.uplugin', '.appledouble')
    dest = QUARANTINE_DIR / safe_name

    counter = 0
    while dest.exists():
        counter += 1
        dest = QUARANTINE_DIR / (safe_name + f'.dup{counter}')

    try:
        shutil.move(str(p), str(dest))
        moved.append(str(p))
    except Exception as exc:
        errors.append(f"ERR {p}: {exc}")

print(f"=== 已移动 {len(moved)} 个 AppleDouble 文件 ===")
for m in moved:
    print(f"  MOVED: {m}")
if errors:
    print(f"\n=== 错误 {len(errors)} 个 ===")
    for e in errors:
        print(e)
else:
    print("无错误。")

# 全局验证：确认整个 Engine 目录已无 ._*.uplugin* 残留
print("\n正在做全局验证扫描...")
all_remaining = [str(p) for p in UE_ENGINE_ROOT.rglob('._*') if '.uplugin' in p.name]
if all_remaining:
    print(f"⚠️  仍有 {len(all_remaining)} 个残留，需再次运行脚本:")
    for r in all_remaining:
        print(f"  {r}")
else:
    print("✅ 全局扫描完毕：Engine 目录下已无任何 ._*.uplugin* 文件，UBT 可正常运行。")
