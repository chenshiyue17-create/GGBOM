# P06 DIRECT EXEC

前置：P05_STATUS=PASS

不要解释，不要重规划。读取 `P06_DIRECT_SPEC.json`，严格按以下顺序直接施工：

1. 创建EnemyBase+3子类。
2. AIThink固定0.20s Timer；禁止Tick GetAllActors。
3. 用源数值设置3类敌人。
4. Zombie追击近战；Venom保持650距离并吐毒；Hound冲刺扑击。
5. 18种Zombie只作为视觉Variant，暂不虚构18套数值。
6. Death禁碰撞/停AI/播放Death/LootDrop/3秒后销毁。
7. TestArena验证三类行为和死亡。
8. 日志P06_ENEMY_OK。

最终只返回：
P06_STATUS=PASS/FAIL
ASSET_ERRORS=n
COMPILE_ERRORS=n
RUNTIME_ERRORS=n
ACCESSED_NONE=n
BLOCKING_ERROR=NONE/<text>
NEXT_GATE=<as defined in TEST_SPEC>
