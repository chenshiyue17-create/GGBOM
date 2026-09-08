# -*- coding: utf-8 -*-
"""
Unreal Canvas Studio - UE5 标准 DataTable 种子模板库 (DataTable Seed Templates)
功能：内置标准角色、武器、敌人、战斗特效、地图、卡牌模板，支持对全新空白 UE5 项目一键生成与初始化，零依赖目标工程。
"""

STANDARD_TEMPLATES = {
    "DT_Characters": {
        "description": "2D/2.5D 角色基础属性与全动作罗盘动画配置",
        "rowStruct": "FCharacterRow",
        "defaultRows": [
            {
                "Name": "Char_Medic_Standard",
                "CharacterName": "医疗兵",
                "MaxHP": 100.0,
                "MoveSpeed": 225.0,
                "Avatar": "/Game/Art/01_Player/Avatar/T_Avatar_Medic.T_Avatar_Medic",
                "PrimaryWeapon": "WPN_Rifle_Standard",
                "SecondaryWeapon": "WPN_Pistol_Standard",
                "Armor": 10.0,
                "CritChance": 0.05,
                "Animations": {
                    "Idle": "/Game/Art/01_Player/01_Idle_Run/Dir_01_Down/Idle",
                    "Run": "/Game/Art/01_Player/01_Idle_Run/Dir_01_Down/Run",
                    "Attack": "/Game/Art/01_Player/02_Combat_Actions/Attack",
                    "Hurt": "/Game/Art/01_Player/02_Combat_Actions/Hurt",
                    "Skill": "/Game/Art/01_Player/02_Combat_Actions/Skill",
                    "Death": "/Game/Art/01_Player/02_Combat_Actions/Death"
                }
            }
        ]
    },
    "DT_Weapons": {
        "description": "武器击发机制、子弹切片与弹道物理全要素配置",
        "rowStruct": "FWeaponRow",
        "defaultRows": [
            {
                "Name": "WPN_Rifle_Standard",
                "WeaponName": "战术步枪",
                "Damage": 45.0,
                "FireRate": 0.18,
                "PelletCount": 1,
                "SpreadAngle": 0.0,
                "Icon": "/Game/Art/06_Cards/04_WeaponModCards/T_Card_Rifle.T_Card_Rifle",
                "BulletImage": "/Game/Art/03_Weapons/02_AssaultRifle/T_Bullet.T_Bullet",
                "BulletScale": 0.35,
                "ProjectileSpeed": 950.0,
                "PierceCount": 1,
                "LifeSpan": 2.0,
                "CollisionRadius": 12.0,
                "CollisionHeight": 24.0,
                "ExplosionRadius": 0.0,
                "ExplosionDamage": 0.0
            },
            {
                "Name": "WPN_Shotgun_Heavy",
                "WeaponName": "重型霰弹枪",
                "Damage": 28.0,
                "FireRate": 0.6,
                "PelletCount": 5,
                "SpreadAngle": 25.0,
                "Icon": "/Game/Art/06_Cards/04_WeaponModCards/T_Card_Shotgun.T_Card_Shotgun",
                "BulletImage": "/Game/Art/03_Weapons/03_Buckshot/T_Bullet.T_Bullet",
                "BulletScale": 0.35,
                "ProjectileSpeed": 750.0,
                "PierceCount": 1,
                "LifeSpan": 1.2,
                "CollisionRadius": 14.0,
                "CollisionHeight": 20.0,
                "ExplosionRadius": 0.0,
                "ExplosionDamage": 0.0
            }
        ]
    },
    "DT_Enemies": {
        "description": "敌人生存数值、移动物理、阶位与 Flipbook 资产配置",
        "rowStruct": "FEnemyRow",
        "defaultRows": [
            {
                "Name": "Enemy_Zombie_Basic",
                "EnemyName": "变异行尸",
                "Tier": "Minion",
                "MaxHP": 60.0,
                "MoveSpeed": 85.0,
                "CollisionDamage": 15.0,
                "ScoreReward": 10,
                "ExpReward": 5,
                "FlipbookPath": "/Game/Art/02_Enemies/Zombie/FB_Zombie_Walk.FB_Zombie_Walk",
                "Scale": 1.0,
                "CollisionRadius": 22.0
            },
            {
                "Name": "Enemy_Venom_Shooter",
                "EnemyName": "毒液射手",
                "Tier": "Elite",
                "MaxHP": 180.0,
                "MoveSpeed": 110.0,
                "CollisionDamage": 25.0,
                "ScoreReward": 50,
                "ExpReward": 25,
                "FlipbookPath": "/Game/Art/02_Enemies/VenomShooter/FB_Venom_Walk.FB_Venom_Walk",
                "Scale": 1.15,
                "CollisionRadius": 28.0
            }
        ]
    },
    "DT_HitEffects": {
        "description": "打击爆点、顿帧(HitStop)、震屏与粒子视听配置",
        "rowStruct": "FHitEffectRow",
        "defaultRows": [
            {
                "Name": "VFX_Kinetic_Impact",
                "EffectName": "动能击中火花",
                "Category": "HitImpact",
                "VFXFolder": "/Game/Art/05_VFX/11_Hit_Kinetic",
                "FPS": 16.0,
                "Scale": 1.0,
                "LifeSpan": 0.25,
                "HitStopSeconds": 0.04,
                "CameraShakeIntensity": 0.2
            },
            {
                "Name": "VFX_Plasma_Explosion",
                "EffectName": "等离子聚能爆炸",
                "Category": "Explosion",
                "VFXFolder": "/Game/Art/05_VFX/01_Explosion_Plasma",
                "FPS": 14.0,
                "Scale": 1.5,
                "LifeSpan": 0.45,
                "HitStopSeconds": 0.08,
                "CameraShakeIntensity": 0.8
            }
        ]
    },
    "DT_MapTiles": {
        "description": "关卡地表阻力、毒沼减速与环境交互配置",
        "rowStruct": "FTileRow",
        "defaultRows": [
            {
                "Name": "Tile_Standard_Floor",
                "TileName": "标准金属甲板",
                "TexturePath": "/Game/Art/08_Environment/T_Metal_Floor.T_Metal_Floor",
                "FrictionMultiplier": 1.0,
                "HazardDamageDPS": 0.0
            },
            {
                "Name": "Tile_Toxic_Sludge",
                "TileName": "生化腐蚀毒沼",
                "TexturePath": "/Game/Art/08_Environment/T_Toxic_Sludge.T_Toxic_Sludge",
                "FrictionMultiplier": 0.6,
                "HazardDamageDPS": 12.0
            }
        ]
    },
    "DT_TacticalCards": {
        "description": "局内升级卡牌、三选一构筑与战术模组配置",
        "rowStruct": "FTacticalCardRow",
        "defaultRows": [
            {
                "Name": "Card_Damage_Boost",
                "CardName": "战术高爆火药",
                "Rarity": "Rare",
                "Description": "所有武器伤害提升 +25%",
                "Icon": "/Game/Art/06_Cards/01_UpgradeCards/T_Card_Damage.T_Card_Damage",
                "ModifierType": "DamageMult",
                "Value": 0.25
            },
            {
                "Name": "Card_Speed_Sprint",
                "CardName": "肾上腺素注射",
                "Rarity": "Common",
                "Description": "角色移动速度提升 +15%",
                "Icon": "/Game/Art/06_Cards/01_UpgradeCards/T_Card_Speed.T_Card_Speed",
                "ModifierType": "MoveSpeedMult",
                "Value": 0.15
            }
        ]
    }
}
