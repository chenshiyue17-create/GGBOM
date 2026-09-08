# P07 DIRECT EXEC

前置：P06_STATUS=PASS

不要解释，不要重规划。读取 `P07_DIRECT_SPEC.json`，严格按以下顺序直接施工：

1. 创建PickupBase/XP和CardManager。
2. Enemy Loot请求生成XP Pickup；Zombie XP=10。
3. Magnet只在激活后Tick追踪。
4. DT_CardUpgrades补齐6卡。
5. DrawThree排除MaxStack，按60/25/12/3抽不重复3张。
6. Nanite/Corrosive/Multishot必须有真实数值效果；另外3张至少设置Ability状态可查询。
7. LevelUpRequested→暂停→Draw3；P07测试可自动选择，P11接正式UI。
8. 测MaxHP100→选Nanite后125。
9. 日志P07_XP_CARD_OK。

最终只返回：
P07_STATUS=PASS/FAIL
ASSET_ERRORS=n
COMPILE_ERRORS=n
RUNTIME_ERRORS=n
ACCESSED_NONE=n
BLOCKING_ERROR=NONE/<text>
NEXT_GATE=<as defined in TEST_SPEC>
