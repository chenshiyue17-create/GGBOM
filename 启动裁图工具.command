#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${PROJECT_DIR}/tools/unreal_canvas_studio/launcher.sh" --slicer
