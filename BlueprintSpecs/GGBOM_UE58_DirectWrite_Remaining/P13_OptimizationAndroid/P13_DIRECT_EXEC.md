# P13 DIRECT EXEC

前置：P12_STATUS=PASS

不要解释，不要重规划。读取 `P13_DIRECT_SPEC.json`，严格按以下顺序直接施工：

1. 创建PoolManager并替换高频Spawn/Destroy为Acquire/Release。
2. Release必须ClearTimer、禁Tick/Collision、Hidden；Acquire完整Reset。
3. 预热Projectile100/VFX50/Pickup50/DamageNumber30，Enemy按关卡。
4. 检查Target/AI/Wave/HUD更新频率。
5. Android Portrait和触控，无鼠标依赖。
6. Stress 120秒。
7. 记录Game/GPU/Memory。
8. 打APK/AAB并真机启动；至少完成核心流程/完整Run优先。
9. 只有真机证据且无Crash/MissingTexture/Touch问题才P13_PERF_ANDROID_OK。

最终只返回：
P13_STATUS=PASS/FAIL
ASSET_ERRORS=n
COMPILE_ERRORS=n
RUNTIME_ERRORS=n
ACCESSED_NONE=n
BLOCKING_ERROR=NONE/<text>
NEXT_GATE=<as defined in TEST_SPEC>
