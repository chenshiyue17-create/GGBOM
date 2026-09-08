# P09 DIRECT EXEC

前置：P08_STATUS=PASS

不要解释，不要重规划。读取 `P09_DIRECT_SPEC.json`，严格按以下顺序直接施工：

1. 创建/复用4后续地图。
2. Ground/Overhead层严格设置。
3. 创建StageManager/WaveSpawner/EncounterZone/StageExit。
4. 关卡条件严格按JSON，不准改成Z4/Z5。
5. Wave从DT_StageWaveConfig读。
6. Clear只触发一次→StopSpawning→Reward→ExitOpen。
7. Test允许DebugInject计数快速验证。
8. 日志P09_STAGE_OK。

最终只返回：
P09_STATUS=PASS/FAIL
ASSET_ERRORS=n
COMPILE_ERRORS=n
RUNTIME_ERRORS=n
ACCESSED_NONE=n
BLOCKING_ERROR=NONE/<text>
NEXT_GATE=<as defined in TEST_SPEC>
