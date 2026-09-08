# P11 DIRECT EXEC

前置：P10_STATUS=PASS

不要解释，不要重规划。读取 `P11_DIRECT_SPEC.json`，严格按以下顺序直接施工：

1. 构建全部Widget，复用已有GameHUD。
2. 精确Anchor/Pos/Size；WeaponBar 4*132+3*8=552。
3. 禁止Property Binding/Tick查询；只用Dispatcher。
4. 图标固定SizeBox，不准负Padding/RenderTranslation纠偏。
5. CardModal接P07；Reroll/Skip。
6. BossHUD仅Boss存在显示。
7. Item drag直接ScreenSpacePosition→PlacementManager，禁止DPI二次除法。
8. Pause/GameOver完整。
9. 测4种分辨率。
10. 日志P11_UMG_OK。

最终只返回：
P11_STATUS=PASS/FAIL
ASSET_ERRORS=n
COMPILE_ERRORS=n
RUNTIME_ERRORS=n
ACCESSED_NONE=n
BLOCKING_ERROR=NONE/<text>
NEXT_GATE=<as defined in TEST_SPEC>
