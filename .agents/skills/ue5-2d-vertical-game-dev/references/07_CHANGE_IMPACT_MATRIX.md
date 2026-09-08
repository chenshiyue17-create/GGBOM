# 07 Change Impact Matrix

AI不得自行猜影响范围，至少按以下规则：

| 变更 | 默认影响 | 美术STALE | 必测 |
|---|---|---|---|
| Character.MaxHealth | Gameplay/Balance | 否 | Character Test |
| Character.MoveSpeed | Gameplay/Balance | 否 | Character Move |
| Character.Portrait | UI Art | 否 | CharacterSelect/UI |
| Character.AnimationProfile | Animation Binding | 否 | Character Animation |
| Character.MasterVisual | 全依赖动画视觉 | 是：全部相关Source/Sprite/Flipbook | Full Character Visual |
| Animation.Run.NE | 单动画链 | 仅该动画链/同Source Sheet需复验 | Run_NE + Source sibling |
| Weapon.Damage | Balance | 否 | Weapon Damage/DPS |
| Weapon.FireRate | Balance/Fire cadence | 否 | Weapon Fire/DPS |
| Weapon.WorldSprite | Weapon Art | 否 | Weapon Visual |
| Weapon.ProjectileDefinition | Runtime dependency | 否 | Weapon+Projectile |
| Projectile.Speed | Projectile Runtime | 否 | Projectile+Weapons using it |
| Ability.Damage | Ability Balance | 否 | Ability Test |
| Ability.VFX | Presentation | 否 | Ability Visual |
| UITheme | UI Visual | 否 | UI Regression |
| Wave.SpawnRate | Encounter Balance | 否 | Wave/Performance |
| Parent Blueprint | Architecture wide | 视情况 | All affected children |
| Shared Component Logic | Framework wide | 否 | All users of component |

## STALE规则
只有影响源视觉契约的变更才传播 STALE。普通数值修改不得污染美术状态。

## Impact Report固定字段
DIRECT / AFFECTED / INDIRECT / REBUILD_REQUIRED / ART_REGEN / FLIPBOOK_REGEN / REQUIRED_TESTS / RISKS。
