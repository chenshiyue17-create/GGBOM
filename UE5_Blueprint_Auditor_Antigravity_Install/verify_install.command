#!/bin/bash
set -e

echo "UE5 Blueprint Auditor - Installation Check"
echo "==========================================="

FOUND=0

if [ -f ".agents/skills/ue5-blueprint-auditor/SKILL.md" ]; then
  echo "PROJECT_SKILL=FOUND"
  echo "PATH=$(pwd)/.agents/skills/ue5-blueprint-auditor"
  FOUND=1
fi

if [ -f "$HOME/.gemini/antigravity/skills/ue5-blueprint-auditor/SKILL.md" ]; then
  echo "GLOBAL_SKILL=FOUND"
  echo "PATH=$HOME/.gemini/antigravity/skills/ue5-blueprint-auditor"
  FOUND=1
fi

if [ -f "$HOME/.gemini/config/skills/ue5-blueprint-auditor/SKILL.md" ]; then
  echo "GLOBAL_COMPAT_SKILL=FOUND"
  echo "PATH=$HOME/.gemini/config/skills/ue5-blueprint-auditor"
  FOUND=1
fi

if [ "$FOUND" -eq 1 ]; then
  echo "VERIFY_STATUS=PASS"
else
  echo "VERIFY_STATUS=FAIL"
  exit 1
fi
