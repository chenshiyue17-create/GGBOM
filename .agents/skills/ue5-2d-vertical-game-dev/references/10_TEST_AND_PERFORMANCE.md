# 10 自动测试与移动端性能

## 通用 Test Harness
- BP_TEST_CharacterHarness(CharacterDefinition)
- BP_TEST_WeaponHarness(WeaponDefinition)
- BP_TEST_AbilityHarness(AbilityDefinition)
- BP_TEST_EnemyHarness(EnemyDefinition)

不要每对象复制测试逻辑。

## Character Test
Definition / Parent / Components / Idle / Move / 5方向 / 3镜像 / Attack / Hurt / Dead / Flipbook / FPS / Pivot / Scale / Weapon / Ability / Damage / Death / UI Event。

## Weapon Test
Definition / Fire / FireRate / Damage / Magazine / Reload / Projectile / Speed / Collision / Crit / Pierce / Range / MuzzleVFX / ImpactVFX / SFX / Icon / DPS formula。

## Performance Budget
建议初版：
- 同屏敌人 PASS50 WARN60 FAIL70
- 同屏弹丸 PASS120 WARN180 FAIL250
- 活跃VFX PASS40 WARN60 FAIL80
- Actor Tick PASS50 WARN80 FAIL120
- DrawCalls PASS150 WARN220 FAIL300
- GPU Frame PASS12ms WARN14ms FAIL16.6ms
- Game Thread PASS8ms WARN12ms FAIL16.6ms
- Memory PASS800MB WARN1000MB FAIL1200MB

预算必须 DataTable 化，可项目调整。

## 性能策略
Projectile/Enemy/Pickup/VFX/DamageNumber 优先 Object Pool。
大量单位禁止每Actor Tick + GetPlayer + Distance；优先 Timer/Batch/Subsystem/Event/Spatial Query。

## Build阶梯
Editor Compile → Blueprint Compile → PIE → Standalone → Development Android → Shipping Android。
不要到最后才第一次打 Android。
