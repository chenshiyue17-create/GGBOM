# -*- coding: utf-8 -*-
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path("/Users/cc/Desktop/GGBOM")
UE_BIN = Path("/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd")
UPROJECT = REPO_ROOT / "xxxx/xxxx.uproject"
TOOLS_DIR = REPO_ROOT / "xxxx/Tools"

steps = [
    "step1_fix_zombie.py",
    "step2_fix_hound.py",
    "step3_fix_boss.py",
    "step4_calibrate_overhead_bossbar.py"
]

for step in steps:
    script_path = TOOLS_DIR / step
    print(f"\n==================== RUNNING {step} ====================")
    cmd = [
        str(UE_BIN),
        str(UPROJECT),
        f"-run=PythonScript",
        f"-script={script_path}",
        "-nullrhi",
        "-nosound",
        "-unattended"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAILED {step} with return code {res.returncode}")
        print("STDOUT:\n" + res.stdout[-2000:])
        print("STDERR:\n" + res.stderr[-2000:])
        sys.exit(res.returncode)
    else:
        print(f"SUCCESS {step}")
        for line in res.stdout.splitlines():
            if "[STEP" in line:
                print("  " + line)

print("\n🎉 ALL 4 STEPS COMPLETED SUCCESSFULLY!")
