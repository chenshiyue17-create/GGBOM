---
name: ue5-lite-runner
description: Fast, lightweight StandAlone game launcher and headless test runner for Unreal Engine 5 projects. Runs 360x640 windowed 30 FPS games or headless automation tests without loading the heavy Editor UI.
---

# UE5 Lite Runner

轻量独立游戏启动与无头测试运行器。

## 核心模式

### 1. 轻量独立游戏窗口 (Lite Mode)
- 分辨率：`360x640`
- 帧率：锁定 `30 FPS`
- 画质：最低渲染画质 (`sg.*Quality 0`)
- 启动：`run_lite.command`（秒级启动，不占用重型编辑器资源）

### 2. 视觉验收窗口 (Visual Mode)
- 分辨率：`540x960`
- 帧率：`60 FPS`
- 启动：`run_visual.command`

### 3. 无头测试 (Headless Mode)
- 纯命令行运行：`UnrealEditor-Cmd -nullrhi -unattended`
- 启动：`run_headless.command`

### 4. 停止运行 (Stop Runner)
- 一键杀掉后台运行实例：`stop_runner.command`

## 配置文件规范

在项目根目录创建 `.ue5-lite-runner.json`：

```json
{
  "engine_root": "/Volumes/NINJAV 2/UE_5.8/UE_5.8",
  "start_map": "/Game/GGBOM/Maps/MAP_GGBOM_Main",
  "mute_audio": false
}
```
