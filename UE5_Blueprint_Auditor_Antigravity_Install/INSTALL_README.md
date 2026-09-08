# UE5 Blueprint Auditor — Antigravity IDE 安装版

## 推荐：项目级安装

Antigravity 官方支持：

`<workspace-root>/.agents/skills/<skill-folder>/`

本压缩包已经预先排好：

`.agents/skills/ue5-blueprint-auditor/SKILL.md`

### 方法 A：直接解压

把本压缩包里的 `.agents` 文件夹复制到你的 UE5 项目根目录。

最终必须是：

```text
你的UE5项目/
├── xxxx.uproject
└── .agents/
    └── skills/
        └── ue5-blueprint-auditor/
            ├── SKILL.md
            ├── README.md
            ├── QUICK_COMMANDS.md
            ├── contracts/
            ├── templates/
            └── examples/
```

完全关闭再重新打开 Antigravity IDE。

### 方法 B：macOS 一键安装

双击：

`install_project.command`

输入 UE5 项目根目录，例如：

`/Users/cc/Desktop/GGBOM/xxxx`

也可以 Terminal：

```bash
./install_project.command "/Users/cc/Desktop/GGBOM/xxxx"
```

## 全局安装

想让所有工程都能使用，双击：

`install_global.command`

安装器优先使用当前 Antigravity skills 全局目录：

`~/.gemini/antigravity/skills/`

并保留兼容路径检测。

## 验证

进入项目根目录后运行：

```bash
/path/to/verify_install.command
```

或者直接确认：

```bash
ls .agents/skills/ue5-blueprint-auditor/SKILL.md
```

## IDE 中测试

重新打开 IDE 后输入：

`使用 ue5-blueprint-auditor 审核当前 Blueprint 改动；只审计不要修改。`

也可以：

`使用 ue5-blueprint-auditor 审核 /Game/Blueprints/BP_PlayerCharacter。`

正常情况下 Agent 会进入 READ_ONLY_AUDIT，而不是开始重写蓝图。
