# 01 项目架构与全局控制层

## 模块建议
Plugins/
- MSCore
- MSCharacter
- MSAnimation2D
- MSWeapon
- MSProjectile
- MSCombat
- MSAbility
- MSStatus
- MSEnemy
- MSAI
- MSSpawn
- MSUpgrade
- MSLevel
- MSUI
- MSVFX
- MSAudio
- MSDashboard
- MSTest

## 模块通信
只通过：Interface / GameplayTag / Event/Message / Component / Subsystem / DataAsset / DataTable。

禁止具体对象互相硬 Cast。

## Project Control Plane
必须有全局项目状态生成器，输出到：
`/Saved/MSAI/`
- ProjectSnapshot.json
- ObjectRegistry.json
- DependencyGraph.json
- AssetStatus.json
- ValidationReport.json
- PerformanceReport.json

这些文件由 UE 扫描真实工程生成，不由 AI 手工维护。

## Object Registry
每个对象必须有 Stable ID：
- Character.Assault
- Weapon.AR01
- Projectile.AR01
- Ability.Dash
- Enemy.Shambler

Registry 唯一映射：StableID → 唯一 Definition。

## Dependency Graph
至少扫描：
- SoftObjectReference
- DataAsset 引用
- Blueprint Parent
- Components
- Interface/Tag dependency
- Runtime Art 引用

必须支持正向依赖和反向依赖。
