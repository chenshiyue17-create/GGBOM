# UE5 Lite Runner

## 默认小窗

`run_lite.command`

- 360x640
- 30 FPS
- low scalability
- `UnrealEditor -game`
- 不打开完整 Editor UI

## 视觉验收

`run_visual.command`

- 540x960
- 60 FPS

## Headless

`run_headless.command`

- UnrealEditor-Cmd
- nullrhi
- unattended
- Automation Test

## 项目配置

复制：

`templates/.ue5-lite-runner.example.json`

到 UE5 项目根目录：

`.ue5-lite-runner.json`

修改 `engine_root` / `start_map` 即可。

如果 start_map 为空，使用项目 Game Default Map。
