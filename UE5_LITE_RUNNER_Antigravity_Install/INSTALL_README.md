# 安装

1. 解压本包。
2. 双击 `install_project.command`
3. 输入 UE5 项目根目录。
4. 安装器会复制 Skill 到：

`<Project>/.agents/skills/ue5-lite-runner/`

并自动生成：

`<Project>/.ue5-lite-runner.json`

5. 检查配置文件中的：

`engine_root`

例如：

`/Users/Shared/Epic Games/UE_5.8`

6. 完全重启 Antigravity IDE。

## IDE 测试

`使用 ue5-lite-runner 轻量运行当前项目。`

预期只弹一个 360×640 的游戏小窗，而不是完整 Unreal Editor。
