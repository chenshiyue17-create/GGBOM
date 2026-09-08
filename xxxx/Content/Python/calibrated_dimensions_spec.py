# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》概念图 1:1 像素级比例与尺寸校准规范
Calibrated Pixel Dimensions & Transform Scales for UE5.8 Paper2D Pipeline
================================================================================
"""

# 设计基准画布 (9:16 竖屏正交全景)
VIRTUAL_SCREEN_WIDTH = 1080.0
VIRTUAL_SCREEN_HEIGHT = 1920.0
PIXELS_PER_UNREAL_UNIT = 1.0 # 1 UE Unit = 1 Pixel in 2D Orthographic Mode

# ==============================================================================
# 1. 角色与实体真实像素尺寸规范 (Actor Proportions matching Concept Art)
# ==============================================================================

ACTOR_SCALES_SPEC = {
    # 玩家主角 (医疗兵)
    "Player_Medic": {
        "SpriteWidth": 130.0,
        "SpriteHeight": 150.0,
        "CollisionCapsule": {"Radius": 28.0, "HalfHeight": 50.0},
        "TacticalRingDiameter": 200.0, # 脚底发光战术光环直径
        "SpawnLocation": {"X": 540.0, "Y": 1480.0, "Z": 20.0}, # 屏幕下方中轴
        "RelativeScale": 1.0
    },

    # 终极领主 (深渊领主 Boss - 庞大压迫感)
    "Boss_Overlord": {
        "SpriteWidth": 360.0,  # 约占屏幕宽度 33%
        "SpriteHeight": 380.0,
        "CollisionCapsule": {"Radius": 80.0, "HalfHeight": 120.0},
        "SpawnLocation": {"X": 540.0, "Y": 260.0, "Z": 20.0}, # 屏幕最顶端中心
        "BarricadeGateLocation": {"X": 540.0, "Y": 400.0, "Width": 680.0, "Height": 85.0}, # Boss门前重型隔离带
        "RelativeScale": 2.5
    },

    # 精英蛮兽 (Mutant Brute - 紫色重型精英)
    "Enemy_MutantBrute": {
        "SpriteWidth": 180.0,
        "SpriteHeight": 200.0,
        "CollisionCapsule": {"Radius": 45.0, "HalfHeight": 65.0},
        "SpawnLocation": {"X": 540.0, "Y": 650.0, "Z": 20.0},
        "RelativeScale": 1.4
    },

    # 毒液射手 (Venom Shooter - 绿色酸液中程喷射)
    "Enemy_VenomShooter": {
        "SpriteWidth": 95.0,
        "SpriteHeight": 115.0,
        "CollisionCapsule": {"Radius": 25.0, "HalfHeight": 40.0},
        "ProjectileStream": {"Width": 20.0, "Length": 100.0, "Color": "#76FF03"},
        "RelativeScale": 0.95
    },

    # 变异猎犬 (Mutant Hound - 敏捷四足突袭)
    "Enemy_MutantHound": {
        "SpriteWidth": 130.0,
        "SpriteHeight": 95.0,
        "CollisionCapsule": {"Radius": 28.0, "HalfHeight": 35.0},
        "RelativeScale": 0.95
    },

    # 步兵行尸 (Zombie Walker - 群体杂兵)
    "Enemy_ZombieWalker": {
        "SpriteWidth": 85.0,
        "SpriteHeight": 105.0,
        "CollisionCapsule": {"Radius": 22.0, "HalfHeight": 36.0},
        "RelativeScale": 0.85
    },

    # 经验宝石 (EXP Crystal 💎 - 自动磁吸)
    "Pickup_ExpGem": {
        "SpriteWidth": 34.0,
        "SpriteHeight": 44.0,
        "MagnetRadius": 220.0,
        "RelativeScale": 1.0
    }
}

# ==============================================================================
# 2. 战术放置道具尺寸规范 (Tactical Props Dimensions)
# ==============================================================================

TACTICAL_PROPS_SPEC = {
    "Prop_Barrier": {
        "Width": 220.0,
        "Height": 70.0,
        "BlockCollision": True,
        "HP": 450.0
    },
    "Prop_ExplosiveBarrel": {
        "Width": 64.0,
        "Height": 85.0,
        "ExplosionRadius": 260.0,
        "ExplosionDamage": 220.0,
        "HP": 50.0
    },
    "Prop_ToxicBarrel": {
        "Width": 62.0,
        "Height": 82.0,
        "PuddleRadius": 200.0,
        "PuddleDuration": 6.0,
        "HP": 60.0
    },
    "Prop_LandMine": {
        "Diameter": 50.0,
        "TriggerRadius": 55.0,
        "ExplosionDamage": 190.0,
        "HP": 1.0
    },
    "Prop_HealingStation": {
        "Width": 85.0,
        "Height": 105.0,
        "AuraRadius": 180.0,
        "HealPerSec": 35.0,
        "HP": 180.0
    }
}

# ==============================================================================
# 3. 9:16 UMG 界面绝对尺寸与锚点规范 (UMG Layout Anchors & Proportions)
# ==============================================================================

UMG_LAYOUT_SPEC = {
    # 顶部 Boss 血条栏
    "Top_BossHeader": {
        "Anchor": "TopCenter",
        "Position": {"X": 0.0, "Y": 40.0},
        "Size": {"Width": 680.0, "Height": 75.0},
        "BossIconSize": {"Width": 64.0, "Height": 64.0}
    },

    # 顶部右上角统计 (Kills & Crystals)
    "Top_Stats": {
        "Anchor": "TopRight",
        "Position": {"X": -30.0, "Y": 40.0},
        "Size": {"Width": 160.0, "Height": 80.0}
    },

    # 左侧关卡阶段竖向流转栏 (Z1 ~ Z5 -> BOSS ZONE)
    "Left_ZoneTracker": {
        "Anchor": "LeftCenter",
        "Position": {"X": 25.0, "Y": 0.0},
        "Width": 75.0,
        "HexagonNodeSize": {"Width": 58.0, "Height": 58.0},
        "BossZoneBadgeSize": {"Width": 68.0, "Height": 85.0}
    },

    # 右侧战术建造背包栏 (5 组卡片)
    "Right_TacticalSidebar": {
        "Anchor": "RightCenter",
        "Position": {"X": -25.0, "Y": 60.0},
        "Width": 125.0,
        "CardSlotSize": {"Width": 108.0, "Height": 125.0},
        "CardIconSize": {"Width": 64.0, "Height": 64.0}
    },

    # 底部左侧玩家血量与经验
    "Bottom_PlayerStatus": {
        "Anchor": "BottomLeft",
        "Position": {"X": 30.0, "Y": -40.0},
        "Size": {"Width": 260.0, "Height": 95.0},
        "HPBarWidth": 220.0,
        "EXPBarWidth": 180.0
    },

    # 底部 4 武器切换栏 (突击步枪 / 霰弹枪 / 火箭筒 / 特斯拉枪)
    "Bottom_WeaponBar": {
        "Anchor": "BottomCenter",
        "Position": {"X": 80.0, "Y": -40.0},
        "Size": {"Width": 520.0, "Height": 125.0},
        "SlotSize": {"Width": 118.0, "Height": 120.0},
        "ActiveGoldBorderThickness": 3.0
    }
}
