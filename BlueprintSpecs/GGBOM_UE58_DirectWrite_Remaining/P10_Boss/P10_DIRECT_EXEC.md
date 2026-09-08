# P10 DIRECT EXEC

前置：P09_STATUS=PASS

不要解释，不要重规划。读取 `P10_DIRECT_SPEC.json`，严格按以下顺序直接施工：

1. 创建Boss+SkillBase+10 Skill child。
2. HP8000、Capsule65/110。
3. 阶段阈值70/30；每次转阶段只一次Enrage且Invulnerable。
4. HeavyCleave Damage120。
5. 10技能参数严格按JSON。
6. 所有伤害技能必须有Telegraph；EarthSpikes 1秒。
7. BioShield=3晶体全破才解除无敌；Egg=10秒孵化。
8. Boss死→StageManager BossDefeated。
9. DebugSetHPPercent只给Tests。
10. 日志P10_BOSS_OK。

最终只返回：
P10_STATUS=PASS/FAIL
ASSET_ERRORS=n
COMPILE_ERRORS=n
RUNTIME_ERRORS=n
ACCESSED_NONE=n
BLOCKING_ERROR=NONE/<text>
NEXT_GATE=<as defined in TEST_SPEC>
