#!/bin/bash
set -e

UE_BIN="/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
UPROJECT="/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"
SCRIPT_PATH="/Users/cc/Desktop/GGBOM/xxxx/Content/Python/tools/apply_fix_single_bp.py"

TARGETS=(
  "BP_Player_Medic"
  "BP_Boss_Overlord"
  "BP_Enemy_MutantHound"
  "BP_Enemy_ZombieWalker"
  "BP_Enemy_ZombieRunner"
  "BP_Enemy_VenomShooter"
  "BP_Enemy_ArmoredGuard"
  "BP_Enemy_MutantBrute"
)

for target in "${TARGETS[@]}"; do
  echo "=================================================="
  echo ">>> Fixing Visuals & Physics for: $target"
  echo "=================================================="
  "$UE_BIN" "$UPROJECT" \
    -run=pythonscript \
    -script="$SCRIPT_PATH $target" \
    -nullrhi -nosound -unattended -nopause -stdout
  echo ">>> Finished: $target"
done

echo "=================================================="
echo "ALL BLUEPRINTS VISUALS & PHYSICS SUCCESSFULLY FIXED!"
echo "=================================================="
