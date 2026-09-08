#!/bin/bash
set -e

UE_BIN="/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd"
UPROJECT="/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"
TOOLS_DIR="/Users/cc/Desktop/GGBOM/xxxx/Tools"
LOG_DIR="/Users/cc/Desktop/GGBOM/xxxx/Saved/GGBOM/logs"
mkdir -p "$LOG_DIR"

STEPS=(
    "step1_fix_zombie.py"
    "step2_fix_hound.py"
    "step3_fix_boss.py"
    "step4_calibrate_overhead_bossbar.py"
)

for STEP in "${STEPS[@]}"; do
    echo "==================== STARTING $STEP ===================="
    LOG_FILE="$LOG_DIR/${STEP}.log"
    "$UE_BIN" "$UPROJECT" -run=PythonScript -script="$TOOLS_DIR/$STEP" -nullrhi -nosound -unattended > "$LOG_FILE" 2>&1 || {
        echo "❌ $STEP FAILED! Last 20 lines of $LOG_FILE:"
        tail -n 20 "$LOG_FILE"
        exit 1
    }
    echo "✅ $STEP COMPLETED SUCCESSFULLY!"
    grep "\[STEP" "$LOG_FILE" || tail -n 5 "$LOG_FILE"
done

echo "🎉 ALL 4 STEPS COMPLETED SUCCESSFULLY!"
