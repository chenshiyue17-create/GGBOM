# P04 DIRECT EXEC

前置：P03_STATUS=PASS

不要解释，不要重规划。读取 `P04_DIRECT_SPEC.json`，严格按以下顺序直接施工：

1. 修改现有BP_Player_Medic，不重建；删除P00临时TXT。
2. 挂P03的7个Player组件。
3. IA_Move/IA_Dash按节点表绑定。
4. UpdateFacing8固定8扇区。
5. 创建PaperZD ABP状态机；只绑定P01实际存在Flipbook，缺失就FAIL并报告。
6. Dash 0.25s无敌；DashDuration/Cooldown按JSON种子。
7. 实现YSort。
8. PIE用WASD八向+Dash，日志P04_PLAYER_OK。

最终只返回：
P04_STATUS=PASS/FAIL
ASSET_ERRORS=n
COMPILE_ERRORS=n
RUNTIME_ERRORS=n
ACCESSED_NONE=n
BLOCKING_ERROR=NONE/<text>
NEXT_GATE=<as defined in TEST_SPEC>
