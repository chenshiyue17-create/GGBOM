# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》UE5 纯蓝图系统构建套件: 03 角色、Boss、经验掉落与关卡管理器
================================================================================
"""

import os
import json

try:
    import unreal
    UNREAL = True
except ImportError:
    UNREAL = False

def log(msg):
    print(f"[StageManager] {msg}")
    if UNREAL:
        unreal.log(f"[StageManager] {msg}")

CHARACTERS_SPEC = {
    "BP_Player_Medic": {
        "BaseHealth": 1200.0,
        "MoveSpeed": 350.0,
        "SpriteIdle": "/Game/Art/01_Player/01_Idle_Run/Dir_01_Down/Idle/T_Player_Medic_Idle_Dir_01_Down_01",
        "SpriteRun": "/Game/Art/01_Player/01_Idle_Run/Dir_01_Down/Run/T_Player_Medic_Run_Dir_01_Down_01",
        "TacticalRingColor": [0.0, 0.95, 1.0, 1.0],
        "Components": [
            "BPC_WeaponInventoryComponent",
            "BPC_TacticalPlacementComponent",
            "BPC_HealthComponent"
        ]
    },
    "BP_Enemy_ZombieWalker": {
        "Health": 65.0,
        "Speed": 90.0,
        "Damage": 15.0,
        "Score": 10,
        "Sprite": "/Game/Art/02_Enemies/Zombie/01_Zombie_Walker_Basic/T_Zombie_WalkerBasic_01"
    },
    "BP_Enemy_VenomShooter": {
        "Health": 95.0,
        "Speed": 70.0,
        "AttackRange": 550.0,
        "FireInterval": 1.4,
        "ProjectileClass": "/Game/Blueprints/Combat/Projectiles/BP_Bullet_VenomAcidStream",
        "Sprite": "/Game/Art/02_Enemies/VenomShooter/Actions/Aim/Dir_01_Down/T_Shooter_Aim_Dir_01_Down_01"
    },
    "BP_Enemy_MutantHound": {
        "Health": 130.0,
        "Speed": 220.0,
        "PounceSpeed": 450.0,
        "Damage": 25.0,
        "Sprite": "/Game/Art/02_Enemies/MutantHound/Actions/Run/Dir_01_Down/T_Hound_Run_Dir_01_Down_01"
    },
    "BP_Enemy_MutantBrute": {
        "Health": 480.0,
        "Speed": 50.0,
        "Damage": 45.0,
        "ArmorDamageReduction": 0.25,
        "Sprite": "/Game/Art/02_Enemies/Zombie/11_Zombie_Shambler_Heavy/T_Zombie_ShamblerHeavy_01"
    },
    "BP_Boss_Overlord": {
        "Health": 4500.0,
        "Segments": 3,
        "Sprite": "/Game/Art/02_Enemies/Boss_Overlord/Actions/Idle/Dir_01_Down/T_Boss_Idle_Dir_01_Down_01",
        "Skills": [
            {"Name": "FlameWave", "VFX": "/Game/Art/02_Enemies/Boss_Overlord/Skills/01_FlameWave/T_BossSkill_FlameWave_01"},
            {"Name": "EarthSpikes", "VFX": "/Game/Art/02_Enemies/Boss_Overlord/Skills/03_EarthSpikes/T_BossSkill_EarthSpikes_01"},
            {"Name": "AcidPool", "VFX": "/Game/Art/02_Enemies/Boss_Overlord/Skills/04_AcidPool/T_BossSkill_AcidPool_01"}
        ]
    }
}

STAGE_PROGRESSION_SPEC = {
    "LevelName": "MAP_Stage00_Start_SingleScreen",
    "OrthoWidth": 1080.0,
    "GroundTexture": "/Game/Art/08_Maps/Stage00_Start/T_Map_Stage00_Start_Ground",
    "OverheadTexture": "/Game/Art/08_Maps/Stage00_Start/T_Map_Stage00_Start_Overhead",
    "ProgressionZones": [
        {"Zone": "Z1", "RequiredKills": 15, "BarricadeY": 490.0},
        {"Zone": "Z2", "RequiredKills": 40, "BarricadeY": 490.0},
        {"Zone": "Z3", "RequiredKills": 80, "BarricadeY": 350.0},
        {"Zone": "Z4", "RequiredKills": 130, "BarricadeY": 300.0},
        {"Zone": "Z5", "RequiredKills": 200, "BarricadeY": 200.0},
        {"Zone": "BossZone", "RequiredKills": 350, "BarricadeY": 195.0, "TriggerBoss": True}
    ]
}

def export_stage_specs():
    out_p = "/Users/cc/Desktop/GGBOM/xxxx/Content/Blueprints/Stage/stage_progression_spec.json"
    os.makedirs(os.path.dirname(out_p), exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump({"Characters": CHARACTERS_SPEC, "StageProgression": STAGE_PROGRESSION_SPEC}, f, ensure_ascii=False, indent=2)
    log("关卡波次与角色规格已导出完毕。")

if __name__ == "__main__":
    export_stage_specs()
