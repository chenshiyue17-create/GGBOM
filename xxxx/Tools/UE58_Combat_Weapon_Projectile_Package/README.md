# UE5.8 Combat / Weapon / Projectile Blueprint Package

目标：为 UE5.8 纯蓝图竖屏射击项目实现完整的攻击、自动寻敌、武器、子弹、伤害、暴击、穿透、爆炸、换弹与武器数值系统。

## 包含模块

- BPC_WeaponComponent
- BP_WeaponBase
- BP_ProjectileBase
- BPI_Damageable
- ST_WeaponData
- DT_Weapons 数据规范
- 自动寻敌
- 自动射击
- 弹匣 / 自动换弹
- 暴击
- 穿透
- 爆炸
- 霰弹多弹丸
- 运行时升级倍率
- 事件驱动弹药 UI
- 移动端性能约束
- IDE Agent 严格验收标准

## 推荐目录

```text
Content/
└── Blueprints/
    ├── Combat/
    │   ├── Components/
    │   │   └── BPC_WeaponComponent
    │   ├── Interfaces/
    │   │   └── BPI_Damageable
    │   ├── Weapons/
    │   │   ├── BP_WeaponBase
    │   │   ├── BP_Weapon_AR01
    │   │   ├── BP_Weapon_SMG01
    │   │   ├── BP_Weapon_SG01
    │   │   ├── BP_Weapon_SR01
    │   │   └── BP_Weapon_GL01
    │   ├── Projectiles/
    │   │   ├── BP_ProjectileBase
    │   │   ├── BP_Bullet_Normal
    │   │   ├── BP_Bullet_Piercing
    │   │   └── BP_Bullet_Explosive
    │   └── Data/
    │       ├── ST_WeaponData
    │       └── DT_Weapons
    └── Characters/
        └── BP_PlayerCharacter
```

## 核心运行链

```text
BP_PlayerCharacter
        ↓
BPC_WeaponComponent
        ↓
CurrentWeapon
        ↓
BP_WeaponBase.TryFire()
        ↓
Spawn BP_ProjectileBase
        ↓
Projectile Hit
        ↓
BPI_Damageable.ReceiveDamage()
        ↓
Enemy Health
        ↓
Death
        ↓
XP
        ↓
Player Level Up
```

详细实现见：

- `COMBAT_BLUEPRINT_SPEC.md`
- `WEAPON_DATA_SPEC.md`
- `IDE_AGENT_TASK.md`
- `IMPLEMENTATION_ORDER.md`
- `ACCEPTANCE_CHECKLIST.md`
- `COMBAT_CONTRACT.json`
