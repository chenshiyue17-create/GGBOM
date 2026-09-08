# P05 DIRECT EXEC

前置：P04_STATUS=PASS

不要解释，不要重规划。读取 `P05_DIRECT_SPEC.json`，严格按以下顺序直接施工：

1. 完成ProjectileBase和10个子类。
2. DT_WeaponConfig扩展10行，数据列顺序=ID|Damage|Interval|PPS|Spread|Pierce|Speed|Mag|Reload|ExplosionRadius|DamageTag。
3. 除Pistol默认外其余数值是BALANCE_SEED，不得宣称源值。
4. 绑定P01真实Muzzle/Flight/Impact；缺失引用允许空但必须报告MISSING_VFX。
5. Projectile overlap走BPI_CombatInterface；Pierce去重；爆炸AOE。
6. BPC_Targeting有目标时0.05s FireCheck。
7. TestDummy HP100；4发Pistol应死亡；Shotgun应生成7弹。
8. PIE日志P05_COMBAT_OK。

最终只返回：
P05_STATUS=PASS/FAIL
ASSET_ERRORS=n
COMPILE_ERRORS=n
RUNTIME_ERRORS=n
ACCESSED_NONE=n
BLOCKING_ERROR=NONE/<text>
NEXT_GATE=<as defined in TEST_SPEC>
