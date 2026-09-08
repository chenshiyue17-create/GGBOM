import subprocess
import sys
import os

def main():
    ue_cmd = "/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd"
    uproj = "/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"
    script = "/Users/cc/Desktop/GGBOM/xxxx/Tools/fix_projectile_movement_and_scale.py"
    
    cmd = [
        ue_cmd,
        uproj,
        "-run=pythonscript",
        f"-script={script}",
        "-nullrhi",
        "-unattended",
        "-stdout"
    ]
    
    print("Executing commandlet via subprocess...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("Return code:", res.returncode)
    print("STDOUT tail:")
    print("\n".join(res.stdout.splitlines()[-30:]))
    if res.stderr:
        print("STDERR:")
        print(res.stderr[-500:])

if __name__ == "__main__":
    main()
