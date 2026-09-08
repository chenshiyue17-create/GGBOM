# P12 DIRECT EXEC

前置：P11_STATUS=PASS

不要解释，不要重规划。读取 `P12_DIRECT_SPEC.json`，严格按以下顺序直接施工：

1. 扩展GI并创建SaveManager/SaveGame。
2. Boot加载Profile→MainMenu。
3. StartNewRun清Run数据→START→Playing。
4. Stage按固定链推进。
5. CardSelection/Pause/BossIntro更新FlowState。
6. Player死亡：bReviveAvailable时允许一次Revive，不接真实广告；用后false；否则GameOver。
7. Victory汇总→持久金币→Save→Victory UI。
8. GameOver不保存临时卡牌/HP/XP。
9. Retry完全重置Run。
10. 日志P12_FLOW_OK。

最终只返回：
P12_STATUS=PASS/FAIL
ASSET_ERRORS=n
COMPILE_ERRORS=n
RUNTIME_ERRORS=n
ACCESSED_NONE=n
BLOCKING_ERROR=NONE/<text>
NEXT_GATE=<as defined in TEST_SPEC>
