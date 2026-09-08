# GGBOM · 终末医疗兵

UE5.8 纯蓝图 / Paper2D 工程，项目入口：`xxxx/xxxx.uproject`。

## 多端 IDE 同步

每台电脑使用独立 Git 工作副本。通过 IDE 的 Pull/Commit/Push 同步源码、Config 和 Content；每次同步前保存并关闭正在编辑的 UE 资产。`.uasset`、`.umap` 是二进制，不要同时在两台机器编辑同一个资产。

```bash
git pull --ff-only origin main
python3 tools/dev.py test
python3 tools/dev.py validate
```

Windows 可使用 `py -3 tools/dev.py ...` 或 `dev.cmd ...`。Python 3.9+，常用工具与测试不需要第三方依赖。

每台机器把 `.ggbom.local.example.json` 复制成 `.ggbom.local.json`，填写该机的 UE 安装根目录，例如 Windows 的 `C:/Program Files/Epic Games/UE_5.8`、Mac 的 UE_5.8 文件夹。此本地文件不会提交。也可设置 `GGBOM_UE_ROOT` 或 `GGBOM_UE_BIN`。

```bash
python3 tools/dev.py doctor
python3 tools/dev.py run
python3 tools/dev.py config
```

- `test`：工具逻辑回归，不启动 UE。
- `validate`：当前 JSON 数据语法/数值/引用校验；不表示游戏功能通过。
- `doctor`：项目和该电脑引擎路径检查；不自动安装引擎。
- `run`：360×640、30FPS 上限的独立窗口；`--mode visual` 为540×960预览。
- `config`：本机配置网页，默认 `http://127.0.0.1:8899`；端口占用会报错，不结束其他进程。
- `config-plan`：显示配置应用范围。
- `apply-enemy-defaults`：读取保存后的敌人 JSON，只更新已有敌人类的数值默认值。当前游戏实例、武器、波次、主角和美术不在此命令范围内。

## 当前验收边界

工具更新修复了无断言 PASS、虚假结构快照、数据差异漏报、非法数据漏检、入口路径与保存事务问题。**尚未在 UE5.8 中验证新的数值应用脚本；资产重载、运行消费、核心蓝图、视觉和打包仍待验证。**

历史 `ProjectState`、`Changes` 和 `output` 的 PASS 不能直接作为当前提交的通过证据。请先读 `ProjectState/verification.yaml`、`Docs/MULTI_DEVICE_DEVELOPMENT.md`。

支持的日常入口是 `tools/dev.py`。历史全量恢复脚本、按阶段重建和自动生成 APPROVED 报告的入口已停用；不要从 archive 中恢复并直接执行它们。
