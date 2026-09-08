#!/bin/bash
set -e

UE_BIN="/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
UPROJECT="/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"
SCRIPT_PATH="/Users/cc/Desktop/GGBOM/xxxx/Content/Python/tools/build_zombie_family.py"

TARGETS=(
  "BP_Enemy_ZombieWalker"
  "BP_Enemy_VenomShooter"
  "BP_Enemy_ArmoredGuard"
  "BP_Enemy_MutantBrute"
)

for target in "${TARGETS[@]}"; do
  echo "=================================================="
  echo ">>> Building Zombie: $target"
  echo "=================================================="
  "$UE_BIN" "$UPROJECT" \
    -run=pythonscript \
    -script="$SCRIPT_PATH $target" \
    -nullrhi -nosound -unattended -nopause -stdout
  echo ">>> Finished: $target"
done

echo "=================================================="
echo "ALL ZOMBIE FAMILY BLUEPRINTS SUCCESSFULLY BUILT!"
echo "=================================================="
