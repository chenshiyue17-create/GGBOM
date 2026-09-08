# GGBOM：终末医疗兵

UE 5.8 纯蓝图/Paper2D 竖屏防线射击游戏。界面采用上方 Boss 血条、左侧关卡进度、右侧战术道具、底部生命与武器栏的战斗信息布局。所有运行美术只取自 `Content/美术/Art`。

插件与项目设置按 P00 基线：Paper2D、PaperZD、Enhanced Input、Python Editor Script、Editor Scripting Utilities；设计分辨率 1080×1920，DPI 规则 Shortest Side，正交相机 OrthoWidth 1080。桌面调试窗口缩放为 562×1000，避免超出屏幕。

## 玩法

- `A` / `D`：左右移动
- 武器自动射击；子弹命中敌人即消灭
- 敌人由上向下推进
- 坚守 40 秒进入胜利画面；重新运行可开始新战局

## 一键运行

```bash
./Scripts/run.sh
```

## 重新生成蓝图资产

```bash
./Scripts/build.sh
```

## 测试

```bash
./Scripts/test.sh
```

## P01 全素材严格导入

`Config/AssetImportRules.json` 记录了全量素材的真实尺寸、Alpha、来源校验、切片格数和生成策略。P01 不猜测格数：动画 Sheet 只在其同目录独立帧可证明连续、等尺寸、且与 Sheet 像素尺寸完全一致时创建 Flipbook；UI/Card 非均匀 Atlas 只导入 Texture/Sprite，不进行网格切片。

Projectile Flight 使用 P01 明确规则 `Rows=1 / Columns=4 / StrictEqualCells=true`。为避免改写原始 Flight 图，流水线在 `Intermediate/P01/Generated/ProjectileFlight4` 生成四个严格等格单元，再导入与创建 Flipbook。

P01 最终 Gate 和实机播放画面见 [P01_status.json](output/P01_status.json)、[P01_final_report.md](output/P01_final_report.md)、[P01_E_Flipbook_Playback.png](output/P01_E_Flipbook_Playback.png)。

## 故障排查

- 提示 `UE5_EDITOR 不存在`：复制 `.env.example` 的路径并设置 `UE5_EDITOR`。
- 黑屏：确认默认地图为 `/Game/GGBOM/Maps/MAP_GGBOM_Main`，并重新执行构建脚本。
- 蓝图资产缺失：关闭正在编辑这些资产的 UE 窗口后，再执行构建脚本。
- 首次启动较慢：UE 5.8 会编译着色器与建立资产缓存，属于正常现象。
