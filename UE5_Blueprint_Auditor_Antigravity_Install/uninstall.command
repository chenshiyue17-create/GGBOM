#!/bin/bash
set -e

echo "UE5 Blueprint Auditor - Uninstall"
echo "================================="

if [ -f ".agents/skills/ue5-blueprint-auditor/SKILL.md" ]; then
  rm -rf ".agents/skills/ue5-blueprint-auditor"
  echo "Removed project installation."
fi

if [ -d "$HOME/.gemini/antigravity/skills/ue5-blueprint-auditor" ]; then
  rm -rf "$HOME/.gemini/antigravity/skills/ue5-blueprint-auditor"
  echo "Removed global Antigravity installation."
fi

if [ -d "$HOME/.gemini/config/skills/ue5-blueprint-auditor" ]; then
  rm -rf "$HOME/.gemini/config/skills/ue5-blueprint-auditor"
  echo "Removed global compatibility installation."
fi

echo "UNINSTALL_STATUS=PASS"
