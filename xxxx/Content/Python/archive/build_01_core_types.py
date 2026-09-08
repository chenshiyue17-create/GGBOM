# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》UE5 纯蓝图系统构建套件: 01 核心类型、枚举与数据表
================================================================================
"""

import os
import json

try:
    import unreal
    UNREAL = True
except ImportError:
    UNREAL = False

CONTENT_ROOT = "/Game/Blueprints"

def log(msg):
    print(f"[CoreTypes] {msg}")
    if UNREAL:
        unreal.log(f"[CoreTypes] {msg}")

# 1. 武器配置数据字典
WEAPONS_DATA = [
    {
        "RowName": "AssaultRifle",
        "DisplayName": "AUTO RIFLE",
        "WeaponType": "AssaultRifle",
        "BaseDamage": 28.0,
        "FireInterval": 0.12,
        "PelletCount": 1,
        "SpreadAngle": 2.5,
        "ProjectileSpeed": 1500.0,
        "MaxAmmo": 30,
        "ReloadTime": 1.2,
        "AoeRadius": 0.0,
        "ProjectileClass": "/Game/Blueprints/Combat/Projectiles/BP_Bullet_AssaultRifle"
    },
    {
        "RowName": "BuckshotShotgun",
        "DisplayName": "SHOTGUN",
        "WeaponType": "BuckshotShotgun",
        "BaseDamage": 16.0,
        "FireInterval": 0.65,
        "PelletCount": 6,
        "SpreadAngle": 22.0,
        "ProjectileSpeed": 1300.0,
        "MaxAmmo": 6,
        "ReloadTime": 1.8,
        "AoeRadius": 0.0,
        "ProjectileClass": "/Game/Blueprints/Combat/Projectiles/BP_Bullet_Buckshot"
    },
    {
        "RowName": "RocketLauncher",
        "DisplayName": "ROCKET LAUNCHER",
        "WeaponType": "MicroMissile",
        "BaseDamage": 140.0,
        "FireInterval": 1.2,
        "PelletCount": 1,
        "SpreadAngle": 0.0,
        "ProjectileSpeed": 900.0,
        "MaxAmmo": 12,
        "ReloadTime": 2.2,
        "AoeRadius": 220.0,
        "ProjectileClass": "/Game/Blueprints/Combat/Projectiles/BP_Bullet_Rocket"
    },
    {
        "RowName": "TeslaGun",
        "DisplayName": "TESLA GUN",
        "WeaponType": "TeslaGun",
        "BaseDamage": 45.0,
        "FireInterval": 0.4,
        "PelletCount": 1,
        "SpreadAngle": 0.0,
        "ProjectileSpeed": 1800.0,
        "MaxAmmo": 8,
        "ReloadTime": 1.5,
        "AoeRadius": 140.0,
        "ProjectileClass": "/Game/Blueprints/Combat/Projectiles/BP_Bullet_TeslaGun"
    }
]

# 2. 战术放置道具数据字典
TACTICAL_PROPS_DATA = [
    {
        "RowName": "Barrier",
        "DisplayName": "BARRIER",
        "PropType": "Barrier",
        "MaxDurability": 450.0,
        "InitialInventory": 8,
        "Width": 220.0,
        "Height": 70.0,
        "EffectRadius": 0.0,
        "DamageOnDestroy": 0.0,
        "ActorClass": "/Game/Blueprints/TacticalProps/BP_Prop_Barrier"
    },
    {
        "RowName": "ExplosiveBarrel",
        "DisplayName": "EXPLOSIVE BARREL",
        "PropType": "ExplosiveBarrel",
        "MaxDurability": 50.0,
        "InitialInventory": 6,
        "Width": 64.0,
        "Height": 85.0,
        "EffectRadius": 260.0,
        "DamageOnDestroy": 220.0,
        "ActorClass": "/Game/Blueprints/TacticalProps/BP_Prop_ExplosiveBarrel"
    },
    {
        "RowName": "ToxicBarrel",
        "DisplayName": "TOXIC BARREL",
        "PropType": "ToxicBarrel",
        "MaxDurability": 60.0,
        "InitialInventory": 5,
        "Width": 62.0,
        "Height": 82.0,
        "EffectRadius": 200.0,
        "DamageOnDestroy": 20.0,
        "ActorClass": "/Game/Blueprints/TacticalProps/BP_Prop_ToxicBarrel"
    },
    {
        "RowName": "LandMine",
        "DisplayName": "LAND MINE",
        "PropType": "LandMine",
        "MaxDurability": 1.0,
        "InitialInventory": 7,
        "Width": 50.0,
        "Height": 50.0,
        "EffectRadius": 120.0,
        "DamageOnDestroy": 190.0,
        "ActorClass": "/Game/Blueprints/TacticalProps/BP_Prop_LandMine"
    },
    {
        "RowName": "HealingStation",
        "DisplayName": "HEALING STATION",
        "PropType": "HealingStation",
        "MaxDurability": 180.0,
        "InitialInventory": 4,
        "Width": 85.0,
        "Height": 105.0,
        "EffectRadius": 200.0,
        "DamageOnDestroy": 0.0,
        "ActorClass": "/Game/Blueprints/TacticalProps/BP_Prop_HealingStation"
    }
]

# 3. 升级卡牌数据字典 (3选1)
CARD_UPGRADES_DATA = [
    {
        "RowName": "NaniteCore",
        "Title": "纳米自愈核心",
        "Description": "最大生命值 +250，每秒生命恢复 +15 HP",
        "Rarity": "Epic",
        "ModType": "Health",
        "Value": 250.0,
        "Icon": "/Game/Art/06_Cards/03_TacticalAbilityCards/Icons/T_Icon_Tactical_01_DeployStation"
    },
    {
        "RowName": "CorrosiveAmmo",
        "Title": "穿甲腐蚀弹头",
        "Description": "武器攻击附带 25% 生化酸蚀伤害，穿透 +1",
        "Rarity": "Rare",
        "ModType": "Damage",
        "Value": 25.0,
        "Icon": "/Game/Art/06_Cards/01_UpgradeCards_3Choice/Cards/T_Card_Upgrade_02_CorrosiveAmmo"
    },
    {
        "RowName": "TrajectoryOverload",
        "Title": "多联弹道过载",
        "Description": "主武器单次发射弹丸数量 +2，射速提升 30%",
        "Rarity": "Legendary",
        "ModType": "Pellets",
        "Value": 2.0,
        "Icon": "/Game/Art/06_Cards/01_UpgradeCards_3Choice/Cards/T_Card_Upgrade_04_Overdrive"
    },
    {
        "RowName": "TacticalRoll",
        "Title": "战术翻滚冲刺",
        "Description": "移动速度 +20%，闪避无敌帧增加 0.2 秒",
        "Rarity": "Rare",
        "ModType": "Speed",
        "Value": 20.0,
        "Icon": "/Game/Art/06_Cards/02_PassiveBuffCards/Icons/T_Icon_Buff_02_MovementSpeed"
    }
]

def export_json_data_tables():
    output_dir = "/Users/cc/Desktop/GGBOM/xxxx/Content/Blueprints/Core/Types"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "DT_WeaponsConfig.json"), "w", encoding="utf-8") as f:
        json.dump(WEAPONS_DATA, f, ensure_ascii=False, indent=2)
    with open(os.path.join(output_dir, "DT_TacticalPropsConfig.json"), "w", encoding="utf-8") as f:
        json.dump(TACTICAL_PROPS_DATA, f, ensure_ascii=False, indent=2)
    with open(os.path.join(output_dir, "DT_CardUpgradesConfig.json"), "w", encoding="utf-8") as f:
        json.dump(CARD_UPGRADES_DATA, f, ensure_ascii=False, indent=2)
        
    log("数据表 JSON 规约导出完毕。")

if __name__ == "__main__":
    export_json_data_tables()
