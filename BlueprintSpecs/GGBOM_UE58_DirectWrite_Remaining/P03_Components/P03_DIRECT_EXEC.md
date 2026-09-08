# P03 DIRECT EXEC

前置：P02_STATUS=PASS

不要解释，不要重规划。读取 `P03_DIRECT_SPEC.json`，严格按以下顺序直接施工：

1. 创建8个ActorComponent和测试Actor。
2. BPC_Health完整实现：Shield先吸收；HP Clamp；OnDeath只触发一次。
3. Targeting只用0.15s Timer刷新，禁止Tick全场搜索。
4. WeaponInventory P03只广播OnFireRequested，不Spawn Projectile。
5. Experience必须支持一次AddXP连续升多级。
6. StatusEffects用TimerHandle定时移除，不做每帧倒计时。
7. CardModifiers限制MaxStack。
8. 测试Actor挂Health/Experience/Inventory/CardModifiers。
9. Compile All → Save All → 放L_Stage00_Start → PIE。
10. 日志必须出现P03_COMPONENTS_OK。

最终只返回：
P03_STATUS=PASS/FAIL
ASSET_ERRORS=n
COMPILE_ERRORS=n
RUNTIME_ERRORS=n
ACCESSED_NONE=n
BLOCKING_ERROR=NONE/<text>
NEXT_GATE=<as defined in TEST_SPEC>
