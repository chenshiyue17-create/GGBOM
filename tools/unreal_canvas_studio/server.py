import numpy as np
from PIL import Image, ImageDraw
import scipy.ndimage as ndi
import skimage.measure
# -*- coding: utf-8 -*-
"""
Unreal Canvas Studio - 通用独立服务引擎 (Server Engine)
功能：跨项目挂载、多工作台数据全量加载、美术切片流水线、动态属性扩展、HUD 画布拖拽与 AI 接口。
"""

import os
import sys
import json
import time
import re
import argparse
import mimetypes
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# 引入核心组件
CURRENT_DIR = Path(__file__).parent.resolve()
WORKSPACE_ROOT = CURRENT_DIR.parent.parent
sys.path.insert(0, str(CURRENT_DIR))

from core.project_adapter import UEProjectAdapter
from core.datatable_engine import DataTableEngine
from core.property_engine import PropertyEngine
from core.asset_pipeline import AssetPipelineEngine
from core.hud_engine import HUDEngine
from core.ai_schema import AISchemaEngine
from core.asset_ingest_engine import AssetIngestEngine

# 全局上下文
adapter = None
dt_engine = None
prop_engine = None
asset_engine = None
hud_engine = None
schema_engine = None
ingest_engine = None

# ==============================================================================
# 敌人/武器/卡牌美术切片映射配置 (向下兼容项目缺省配置)
# ==============================================================================
ENEMY_ART_MAP = {
    "Enemy_Zombie_Walker": {
        "dir": "02_Enemies/Zombie/01_Zombie_Walker_Basic",
        "sheet": "02_Enemies/Zombie/01_Zombie_Walker_Basic/T_Zombie_WalkerBasic_Sheet.png",
        "frames": [
            "02_Enemies/Zombie/01_Zombie_Walker_Basic/T_Zombie_WalkerBasic_01.png",
            "02_Enemies/Zombie/01_Zombie_Walker_Basic/T_Zombie_WalkerBasic_02.png",
            "02_Enemies/Zombie/01_Zombie_Walker_Basic/T_Zombie_WalkerBasic_03.png",
            "02_Enemies/Zombie/01_Zombie_Walker_Basic/T_Zombie_WalkerBasic_04.png",
        ]
    },
    "Enemy_Zombie_Runner": {
        "dir": "02_Enemies/Zombie/05_Zombie_Runner_Agile",
        "sheet": "02_Enemies/Zombie/05_Zombie_Runner_Agile/T_Zombie_RunnerAgile_Sheet.png",
        "frames": [
            "02_Enemies/Zombie/05_Zombie_Runner_Agile/T_Zombie_RunnerAgile_01.png",
            "02_Enemies/Zombie/05_Zombie_Runner_Agile/T_Zombie_RunnerAgile_02.png",
            "02_Enemies/Zombie/05_Zombie_Runner_Agile/T_Zombie_RunnerAgile_03.png",
            "02_Enemies/Zombie/05_Zombie_Runner_Agile/T_Zombie_RunnerAgile_04.png",
        ]
    },
    "Enemy_Venom_Shooter": {
        "dir": "02_Enemies/Zombie/04_Zombie_Spitter_Minor",
        "sheet": "02_Enemies/Zombie/04_Zombie_Spitter_Minor/T_Zombie_SpitterMinor_Sheet.png",
        "frames": [
            "02_Enemies/Zombie/04_Zombie_Spitter_Minor/T_Zombie_SpitterMinor_01.png",
            "02_Enemies/Zombie/04_Zombie_Spitter_Minor/T_Zombie_SpitterMinor_02.png",
            "02_Enemies/Zombie/04_Zombie_Spitter_Minor/T_Zombie_SpitterMinor_03.png",
            "02_Enemies/Zombie/04_Zombie_Spitter_Minor/T_Zombie_SpitterMinor_04.png",
        ]
    },
    "Enemy_Armored_Guard": {
        "dir": "02_Enemies/Zombie/07_Zombie_Armored_Guard",
        "sheet": "02_Enemies/Zombie/07_Zombie_Armored_Guard/T_Zombie_ArmoredGuard_Sheet.png",
        "frames": [
            "02_Enemies/Zombie/07_Zombie_Armored_Guard/T_Zombie_ArmoredGuard_01.png",
            "02_Enemies/Zombie/07_Zombie_Armored_Guard/T_Zombie_ArmoredGuard_02.png",
            "02_Enemies/Zombie/07_Zombie_Armored_Guard/T_Zombie_ArmoredGuard_03.png",
            "02_Enemies/Zombie/07_Zombie_Armored_Guard/T_Zombie_ArmoredGuard_04.png",
        ]
    },
    "Enemy_Mutant_Brute": {
        "dir": "02_Enemies/Zombie/11_Zombie_Shambler_Heavy",
        "sheet": "02_Enemies/Zombie/11_Zombie_Shambler_Heavy/T_Zombie_ShamblerHeavy_Sheet.png",
        "frames": [
            "02_Enemies/Zombie/11_Zombie_Shambler_Heavy/T_Zombie_ShamblerHeavy_01.png",
            "02_Enemies/Zombie/11_Zombie_Shambler_Heavy/T_Zombie_ShamblerHeavy_02.png",
            "02_Enemies/Zombie/11_Zombie_Shambler_Heavy/T_Zombie_ShamblerHeavy_03.png",
            "02_Enemies/Zombie/11_Zombie_Shambler_Heavy/T_Zombie_ShamblerHeavy_04.png",
        ]
    },
    "Enemy_Mutant_Hound": {
        "dir": "02_Enemies/MutantHound/Run/Dir_01_Down",
        "sheet": "02_Enemies/MutantHound/Run/Dir_01_Down/T_Hound_Run_Dir_01_Down_Sheet.png",
        "frames": [
            "02_Enemies/MutantHound/Run/Dir_01_Down/T_Hound_Run_Dir_01_Down_01.png",
            "02_Enemies/MutantHound/Run/Dir_01_Down/T_Hound_Run_Dir_01_Down_02.png",
            "02_Enemies/MutantHound/Run/Dir_01_Down/T_Hound_Run_Dir_01_Down_03.png",
            "02_Enemies/MutantHound/Run/Dir_01_Down/T_Hound_Run_Dir_01_Down_04.png",
        ]
    },
    "Boss_Overlord": {
        "dir": "02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down",
        "sheet": "02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/T_Boss_Walk_Dir_01_Down_Sheet.png",
        "frames": [
            "02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/T_Boss_Walk_Dir_01_Down_01.png",
            "02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/T_Boss_Walk_Dir_01_Down_02.png",
            "02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/T_Boss_Walk_Dir_01_Down_03.png",
            "02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/T_Boss_Walk_Dir_01_Down_04.png",
        ]
    }
}

WEAPON_ART_MAP = {
    "WPN_Rifle_Standard": {
        "bullet": "03_Weapons/02_AssaultRifle/T_Bullet_AssaultRifle_02_Flight.png",
        "muzzle": "03_Weapons/02_AssaultRifle/T_Bullet_AssaultRifle_01_Muzzle.png",
        "impact": "03_Weapons/02_AssaultRifle/T_Bullet_AssaultRifle_03_Impact.png"
    },
    "WPN_Shotgun_Heavy": {
        "bullet": "03_Weapons/03_BuckshotShotgun/T_Bullet_Buckshot_02_Flight.png",
        "muzzle": "03_Weapons/03_BuckshotShotgun/T_Bullet_Buckshot_01_Muzzle.png",
        "impact": "03_Weapons/03_BuckshotShotgun/T_Bullet_Buckshot_03_Impact.png"
    },
    "WPN_Venom_Blaster": {
        "bullet": "03_Weapons/04_BioAcidLauncher/T_Bullet_BioAcid_02_Flight.png",
        "muzzle": "03_Weapons/04_BioAcidLauncher/T_Bullet_BioAcid_01_Muzzle.png",
        "impact": "03_Weapons/04_BioAcidLauncher/T_Bullet_BioAcid_03_Impact.png"
    }
}

CARD_ART_MAP = {
    "CARD_HighPower_Gunpowder": "06_Cards/05_CurseRewardCards/T_Card_CurseReward_01.png",
    "CARD_Rapid_Barrel": "06_Cards/05_CurseRewardCards/T_Card_CurseReward_02.png",
    "CARD_Armor_Piercing": "06_Cards/05_CurseRewardCards/T_Card_CurseReward_03.png",
    "CARD_Bio_Toxic_Coat": "06_Cards/05_CurseRewardCards/T_Card_CurseReward_04.png",
    "CARD_Field_Emergency": "06_Cards/05_CurseRewardCards/T_Card_CurseReward_05.png",
    "CARD_Tactical_Booster": "06_Cards/05_CurseRewardCards/T_Card_CurseReward_06.png",
}

AVAILABLE_FLIPBOOKS = [
    {
        "name": "基础感染行尸 (4帧单向)",
        "path": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet.FB_T_Zombie_WalkerBasic_Sheet",
        "enemy_key": "Enemy_Zombie_Walker"
    },
    {
        "name": "敏捷疾跑行尸 (4帧单向)",
        "path": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/05_Zombie_Runner_Agile/Flipbooks/FB_T_Zombie_RunnerAgile_Sheet.FB_T_Zombie_RunnerAgile_Sheet",
        "enemy_key": "Enemy_Zombie_Runner"
    },
    {
        "name": "远程毒液喷射者 (4帧单向)",
        "path": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/04_Zombie_Spitter_Minor/Flipbooks/FB_T_Zombie_SpitterMinor_Sheet.FB_T_Zombie_SpitterMinor_Sheet",
        "enemy_key": "Enemy_Venom_Shooter"
    },
    {
        "name": "重装防暴行尸 (4帧单向)",
        "path": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/07_Zombie_Armored_Guard/Flipbooks/FB_T_Zombie_ArmoredGuard_Sheet.FB_T_Zombie_ArmoredGuard_Sheet",
        "enemy_key": "Enemy_Armored_Guard"
    },
    {
        "name": "变异重锤蛮兽 (4帧单向)",
        "path": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet.FB_T_Zombie_ShamblerHeavy_Sheet",
        "enemy_key": "Enemy_Mutant_Brute"
    },
    {
        "name": "疾行变异猎犬 (4帧单向)",
        "path": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet.FB_T_Hound_Run_Dir_01_Down_Sheet",
        "enemy_key": "Enemy_Mutant_Hound"
    },
    {
        "name": "深渊异化领主·行走 (4帧单向)",
        "path": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet.FB_T_Boss_Walk_Dir_01_Down_Sheet",
        "enemy_key": "Boss_Overlord"
    },
    {
        "name": "深渊异化领主·待机 (4帧单向)",
        "path": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord/Actions/Idle/Dir_01_Down/Flipbooks/FB_T_Boss_Idle_Dir_01_Down_Sheet.FB_T_Boss_Idle_Dir_01_Down_Sheet",
        "enemy_key": "Boss_Overlord"
    }
]

BLUEPRINT_PROP_SCHEMA = [
    {
        "category": "🛡️ 战斗属性 (Combat Stats)",
        "props": [
            {"key": "MaxHealth", "name": "最大生命值 (MaxHealth)", "type": "Float", "step": 5.0, "desc": "敌人最大生命值 CDO 默认值"},
            {"key": "MoveSpeed", "name": "移动速度 (MoveSpeed)", "type": "Float", "step": 5.0, "desc": "向玩家行进的基础步速 (uu/s)"},
            {"key": "ContactDamage", "name": "接触伤害 (ContactDamage)", "type": "Float", "step": 1.0, "desc": "触碰玩家或防线造成的近战伤害"}
        ]
    },
    {
        "category": "🎬 材质与动画渲染 (Render & Animation)",
        "props": [
            {"key": "Flipbook", "name": "源4帧Flipbook (SourceFlipbook)", "type": "AssetReference", "options": "flipbooks", "desc": "绑定的 4 帧单向连续 Flipbook 资产路径"},
            {"key": "Scale", "name": "相对缩放 (RelativeScale3D)", "type": "Float", "step": 0.02, "min": 0.1, "max": 2.0, "desc": "PaperFlipbookComponent 相对缩放比例"},
            {"key": "TranslucencySortPriority", "name": "半透明排序优先级 (SortPriority)", "type": "Integer", "step": 10, "default": 200, "desc": "2D 渲染分层深度排序优先级"}
        ]
    },
    {
        "category": "💎 击杀奖励 (Rewards & Drops)",
        "props": [
            {"key": "ScoreReward", "name": "击杀积分 (ScoreReward)", "type": "Integer", "step": 5, "desc": "击杀该怪物获得的局内分数"},
            {"key": "ExpGemValue", "name": "经验宝石 (ExpGemValue)", "type": "Integer", "step": 1, "desc": "掉落经验水晶提供的经验值"}
        ]
    },
    {
        "category": "⚙️ 游戏机制 (Game Mechanics)",
        "props": [
            {"key": "UnidirectionalForwardOnly", "name": "单向推进锁定 (UnidirectionalForwardOnly)", "type": "Boolean", "default": True, "desc": "严格单向朝下行进，不回头，无多余状态机"},
            {"key": "PhaseSegments", "name": "领主多阶段数 (PhaseSegments)", "type": "Integer", "default": 1, "desc": "仅 Boss 生效：领主转阶段生命分段数"},
            {"key": "BlueprintClass", "name": "蓝图生成类 (BlueprintClass)", "type": "String", "readonly": True, "desc": "引擎生成的完整蓝图类引用路径"}
        ]
    }
]

def get_primary_art_dir() -> Path:
    """获取首选美术素材根目录"""
    if adapter and adapter.art_dirs:
        return Path(adapter.art_dirs[0])
    return Path(".")

def resolve_incoming_path(raw_p: str) -> Path:
    """
    智能解析前端传入的素材路径：
    自动兼容：绝对路径、工程相对路径 (Content/美术/Art/...)、美术相对路径 (01_Player/...)
    """
    if not raw_p:
        return Path(".")
    p = Path(raw_p)
    if p.is_absolute() and p.exists():
        return p

    art_dir = get_primary_art_dir()
    cand1 = (art_dir / raw_p).resolve()
    if cand1.exists():
        return cand1

    if adapter and getattr(adapter, "project_path", None):
        cand2 = (Path(adapter.project_path) / raw_p).resolve()
        if cand2.exists():
            return cand2

    if adapter and getattr(adapter, "content_dir", None):
        cand2_c = (Path(adapter.content_dir) / raw_p).resolve()
        if cand2_c.exists():
            return cand2_c

    rel_str = str(raw_p).replace("\\", "/")
    for prefix in ["Content/美术/Art/", "/Content/美术/Art/", "美术/Art/", "/美术/Art/"]:
        if prefix in rel_str:
            stripped = rel_str.split(prefix, 1)[1]
            cand3 = (art_dir / stripped).resolve()
            if cand3.exists():
                return cand3

    return cand1


def scan_player_animations() -> dict:
    """扫描并组织主角 01_Player 全部动作与 5 方向切片帧"""
    actions = {
        "Idle": {},
        "Run": {},
        "Attack": {},
        "Hurt": {},
        "Skill": {},
        "Death": {}
    }
    art_dir = get_primary_art_dir()
    player_root = art_dir / "01_Player"
    if not player_root.exists():
        # 在所有候选目录中查找 01_Player
        if adapter:
            for ad in adapter.art_dirs:
                cand = Path(ad) / "01_Player"
                if cand.exists():
                    player_root = cand
                    art_dir = Path(ad)
                    break

    if not player_root.exists():
        return actions

    dir_names = {
        "Dir_01_Down": "正下 (Dir_01_Down)",
        "Dir_02_DownLeft": "左下 (Dir_02_DownLeft)",
        "Dir_03_Left": "正侧 (Dir_03_Left)",
        "Dir_04_UpLeft": "左上 (Dir_04_UpLeft)",
        "Dir_05_Up": "正上 (Dir_05_Up)"
    }

    # 1. Idle & Run (5 个标准方向)
    idle_run_dir = player_root / "01_Idle_Run"
    if idle_run_dir.exists():
        for d in sorted(idle_run_dir.iterdir()):
            if d.is_dir() and d.name.startswith("Dir_"):
                d_key = d.name
                if d_key not in dir_names:
                    continue
                # Idle
                idle_p = d / "Idle"
                if idle_p.exists():
                    frames = [str(f.relative_to(art_dir)) for f in sorted(idle_p.glob("*.png")) if "Sheet" not in f.name and not f.name.startswith("._")]
                    actions["Idle"][d_key] = {"label": dir_names.get(d_key, d_key), "frames": frames, "path": str(idle_p.relative_to(art_dir))}
                # Run
                run_p = d / "Run"
                if run_p.exists():
                    frames = [str(f.relative_to(art_dir)) for f in sorted(run_p.glob("*.png")) if "Sheet" not in f.name and not f.name.startswith("._")]
                    actions["Run"][d_key] = {"label": dir_names.get(d_key, d_key), "frames": frames, "path": str(run_p.relative_to(art_dir))}

    # 2. Attack & Hurt (统一映射至 5 个标准方向)
    atk_hurt_dir = player_root / "02_Attack_Hurt"
    if atk_hurt_dir.exists():
        for d in sorted(atk_hurt_dir.iterdir()):
            if d.is_dir() and d.name.startswith("Dir_"):
                d_key = "Dir_03_Left" if d.name == "Dir_03_Right" else d.name
                if d_key not in dir_names:
                    continue
                # Attack
                atk_p = d / "Attack"
                if atk_p.exists():
                    frames = [str(f.relative_to(art_dir)) for f in sorted(atk_p.glob("*.png")) if "Sheet" not in f.name and not f.name.startswith("._")]
                    actions["Attack"][d_key] = {"label": dir_names.get(d_key, d_key), "frames": frames, "path": str(atk_p.relative_to(art_dir))}
                # Hurt
                hurt_p = d / "Hurt"
                if hurt_p.exists():
                    frames = [str(f.relative_to(art_dir)) for f in sorted(hurt_p.glob("*.png")) if "Sheet" not in f.name and not f.name.startswith("._")]
                    actions["Hurt"][d_key] = {"label": dir_names.get(d_key, d_key), "frames": frames, "path": str(hurt_p.relative_to(art_dir))}

    # 3. Death & Revive (Skill)
    death_revive_dir = player_root / "03_Death_Revive"
    if death_revive_dir.exists():
        revive_p = death_revive_dir / "Revive"
        if revive_p.exists():
            frames = [str(f.relative_to(art_dir)) for f in sorted(revive_p.glob("*.png")) if "Sheet" not in f.name and not f.name.startswith("._")]
            actions["Skill"]["Default"] = {"label": "纳米战地复苏 (Revive)", "frames": frames, "path": str(revive_p.relative_to(art_dir))}

        death_p = death_revive_dir / "Death_Collapse"
        if death_p.exists():
            frames = [str(f.relative_to(art_dir)) for f in sorted(death_p.glob("*.png")) if "Sheet" not in f.name and not f.name.startswith("._")]
            actions["Death"]["Default"] = {"label": "战死倒地 (Collapse)", "frames": frames, "path": str(death_p.relative_to(art_dir))}

    return actions

def scan_vfx_catalog() -> list:
    """扫描特效库目录 05_VFX"""
    art_dir = get_primary_art_dir()
    vfx_root = art_dir / "05_VFX"
    if not vfx_root.exists() and adapter:
        for ad in adapter.art_dirs:
            cand = Path(ad) / "05_VFX"
            if cand.exists():
                vfx_root = cand
                art_dir = Path(ad)
                break

    catalog = []
    if not vfx_root.exists():
        return catalog

    for d in sorted(vfx_root.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            frames = [str(f.relative_to(art_dir)) for f in sorted(d.glob("*.png")) if "Sheet" not in f.name and not f.name.startswith("._")]
            catalog.append({
                "id": d.name,
                "name": d.name.replace("_", " "),
                "path": f"05_VFX/{d.name}",
                "frames": frames
            })
    return catalog

def scan_art_tree_data() -> dict:
    """扫描美术素材库目录树与扁平资产清单"""
    art_dir = get_primary_art_dir()
    if not art_dir.exists():
        return {"tree": [], "all_files": [], "allFiles": [], "total": 0, "total_count": 0}

    all_files = []

    def walk_dir(p: Path, rel_base: Path):
        node = {
            "folder": str(p.relative_to(rel_base)),
            "name": p.name,
            "path": str(p.relative_to(rel_base)),
            "dirs": [],
            "files": []
        }
        try:
            for child in sorted(p.iterdir()):
                if child.name.startswith("."):
                    continue
                if child.is_dir():
                    node["dirs"].append(walk_dir(child, rel_base))
                elif child.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                    rel_p = str(child.relative_to(rel_base))
                    item = {
                        "name": child.name,
                        "path": rel_p,
                        "absPath": str(child),
                        "relPath": rel_p,
                        "url": f"/art/{urllib.parse.quote(rel_p)}",
                        "size": child.stat().st_size
                    }
                    node["files"].append(item)
                    all_files.append(item)
        except Exception:
            pass
        return node

    tree = []
    for top_d in sorted(art_dir.iterdir()):
        if top_d.is_dir() and not top_d.name.startswith("."):
            tree.append(walk_dir(top_d, art_dir))

    return {
        "status": "success",
        "tree": tree,
        "all_files": all_files,
        "allFiles": all_files,
        "total": len(all_files),
        "total_count": len(all_files)
    }

def scan_player_candidate_avatars() -> list:
    """动态遍历 01_Player 下所有候选头像与立绘图片，支持任意自定义子文件夹（如 touxiang, touxaing, Avatar 等）"""
    art_dir = get_primary_art_dir()
    player_root = art_dir / "01_Player"
    candidates = []
    if not player_root.exists() and adapter:
        for ad in adapter.art_dirs:
            cand = Path(ad) / "01_Player"
            if cand.exists():
                player_root = cand
                art_dir = Path(ad)
                break

    if not player_root.exists():
        return candidates

    for p in sorted(player_root.rglob("*.png")):
        if p.name.startswith("._") or "Sheet" in p.name:
            continue
        try:
            rel = str(p.relative_to(art_dir))
            is_priority = any(k in rel.lower() for k in ["toux", "avatar", "portrait", "icon", "医疗兵"])
            candidates.append({
                "name": p.name,
                "path": rel,
                "url": f"/art/{urllib.parse.quote(rel)}",
                "is_priority": is_priority,
                "folder": str(p.parent.relative_to(art_dir))
            })
        except Exception:
            pass

    # 优先排布头像/特有命名的图片
    candidates.sort(key=lambda x: (0 if x["is_priority"] else 1, x["path"]))
    return candidates

def get_art_system_status() -> dict:
    """获取当前美术素材库的全局最新修改状态与变动感知"""
    art_dir = get_primary_art_dir()
    if not art_dir.exists():
        return {"mtime": 0, "count": 0, "latest": []}
    
    latest_files = []
    max_mtime = 0
    total_count = 0
    try:
        for p in art_dir.rglob("*.png"):
            if p.name.startswith("._"):
                continue
            total_count += 1
            st_mtime = p.stat().st_mtime
            if st_mtime > max_mtime:
                max_mtime = st_mtime
            latest_files.append((st_mtime, str(p.relative_to(art_dir))))
    except Exception:
        pass

    latest_files.sort(key=lambda x: x[0], reverse=True)
    return {
        "mtime": max_mtime,
        "count": total_count,
        "latest": [x[1] for x in latest_files[:5]]
    }

def handle_asset_upload(body: dict) -> dict:
    """处理前端拖拽上传的图片并保存到指定目录"""
    import base64
    target_dir_rel = body.get("target_dir", "01_Player/Avatar")
    filename = body.get("filename", f"upload_{int(time.time())}.png")
    file_base64 = body.get("file_base64", "")
    auto_process = body.get("auto_process", "")

    if not file_base64:
        return {"status": "error", "error": "缺少 file_base64 数据"}

    if "," in file_base64:
        file_base64 = file_base64.split(",", 1)[1]

    try:
        img_data = base64.b64decode(file_base64)
    except Exception as e:
        return {"status": "error", "error": f"Base64 解码失败: {e}"}

    art_dir = get_primary_art_dir()
    dest_dir = art_dir / target_dir_rel
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_file = dest_dir / filename
    dest_file.write_bytes(img_data)
    rel_path = str(dest_file.relative_to(art_dir))

    res = {
        "status": "success",
        "path": rel_path,
        "url": f"/art/{urllib.parse.quote(rel_path)}",
        "message": f"成功保存文件到: {rel_path}"
    }

    if auto_process == "set_avatar":
        res_proc = process_set_avatar(rel_path)
        res["process_result"] = res_proc
    elif auto_process == "remove_black":
        out = asset_engine.remove_black_background(str(dest_file))
        res["process_result"] = {"outputPath": out}

    return res

def process_set_avatar(rel_path: str, normalize: bool = True) -> dict:
    """一键将指定图片设为主角头像，并自动更新 DT_Characters.json 与放映台"""
    import shutil
    art_dir = get_primary_art_dir()
    src_file = art_dir / rel_path
    if not src_file.exists():
        # 在各候选目录中查找
        if adapter:
            for ad in adapter.art_dirs:
                cand = Path(ad) / rel_path
                if cand.exists():
                    src_file = cand
                    art_dir = Path(ad)
                    break

    if not src_file.exists():
        return {"status": "error", "error": f"素材文件不存在: {rel_path}"}

    final_rel = rel_path
    if normalize:
        avatar_dir = art_dir / "01_Player" / "Avatar"
        avatar_dir.mkdir(parents=True, exist_ok=True)
        norm_file = avatar_dir / "T_Player_Medic_Avatar.png"
        shutil.copy2(src_file, norm_file)
        final_rel = str(norm_file.relative_to(art_dir))

    # 更新 DT_Characters 表中的主角 Avatar
    chars_data, fmt = dt_engine.load_table("DT_Characters")
    if isinstance(chars_data, dict):
        if "Player_Medic" in chars_data:
            chars_data["Player_Medic"]["Avatar"] = final_rel
        elif len(chars_data) > 0:
            first_key = list(chars_data.keys())[0]
            chars_data[first_key]["Avatar"] = final_rel
        dt_engine.save_table("DT_Characters", chars_data, fmt)
    elif isinstance(chars_data, list) and len(chars_data) > 0:
        chars_data[0]["Avatar"] = final_rel
        dt_engine.save_table("DT_Characters", chars_data, fmt)

    return {
        "status": "success",
        "avatar_path": final_rel,
        "avatar_url": f"/art/{urllib.parse.quote(final_rel)}",
        "message": f"已成功将头像设为: {final_rel} 并已原子保存至 DT_Characters！"
    }

def init_workspace(target_project_path):
    global adapter, dt_engine, prop_engine, asset_engine, hud_engine, schema_engine, ingest_engine
    adapter = UEProjectAdapter(target_project_path)
    dt_engine = DataTableEngine(adapter)
    prop_engine = PropertyEngine(adapter)
    asset_engine = AssetPipelineEngine(adapter)
    hud_engine = HUDEngine(adapter)
    schema_engine = AISchemaEngine(adapter, prop_engine)
    ingest_engine = AssetIngestEngine(adapter)

def to_dict_table(raw_data):
    """将 DataTable 数据标准化为以 Name/RowKey 为索引的字典"""
    if isinstance(raw_data, dict):
        return raw_data
    if isinstance(raw_data, list):
        res = {}
        for idx, row in enumerate(raw_data):
            key = row.get("Name") or row.get("RowName") or row.get("Id") or row.get("ID") or f"Row_{idx}"
            res[key] = row
        return res
    return {}

# ==================== Sprite Studio 智能选区与切片注册表 ====================
SLICER_IMAGE_REGISTRY = {}

WEAPON_NAMES = {
    1: ("01_KineticPistol", "T_Bullet_Pistol"),
    2: ("02_AssaultRifle", "T_Bullet_Rifle"),
    3: ("03_Buckshot", "T_Bullet_Shotgun"),
    4: ("04_BioAcid", "T_Bullet_Acid"),
    5: ("05_CryoShard", "T_Bullet_Cryo"),
    6: ("06_LightningBolt", "T_Bullet_Lightning"),
    7: ("07_SonicWave", "T_Bullet_Sonic"),
    8: ("08_PlasmaArc", "T_Bullet_Plasma"),
    9: ("09_HeavyRocket", "T_Bullet_Rocket"),
    10: ("10_LaserRail", "T_Bullet_Laser"),
}

CARD_NAMES = {
    1: ("01_UpgradeCards_3Choice", "T_Card_Upgrade"),
    2: ("02_PassiveBuffCards", "T_Card_Passive"),
    3: ("03_TacticalAbilityCards", "T_Card_Tactical"),
    4: ("04_WeaponModCards", "T_Card_WeaponMod"),
    5: ("05_CurseRewardCards", "T_Card_CurseReward"),
    6: ("06_CardFramesAndButtons", "T_Card_UI"),
}

PROP_NAMES = {
    1: ("01_ExplosiveBarrel", "T_Prop_Barrel"),
    2: ("02_BioWasteTank", "T_Prop_BioTank"),
    3: ("03_HighVoltageBox", "T_Prop_VoltageBox"),
    4: ("04_TechSafe", "T_Prop_Safe"),
    5: ("05_MedSupplyPod", "T_Prop_MedPod"),
    6: ("06_CryoCanister", "T_Prop_Cryo"),
    7: ("07_BatteryArray", "T_Prop_Battery"),
    8: ("08_OilDrumCluster", "T_Prop_OilDrum"),
    9: ("09_SecurityBarricade", "T_Prop_Barricade"),
    10: ("10_OverloadTerminal", "T_Prop_Terminal"),
}

VFX_NAMES = {
    1: ("01_Explosion_Plasma", "T_VFX_Plasma"),
    2: ("02_Explosion_BioAcid", "T_VFX_Acid"),
    3: ("03_Explosion_CryoBlast", "T_VFX_Cryo"),
    4: ("04_Explosion_ElectricShock", "T_VFX_Electric"),
    5: ("05_Explosion_Firestorm", "T_VFX_Fire"),
    6: ("06_Explosion_SonicBurst", "T_VFX_Sonic"),
    7: ("07_MuzzleFlash_Pistol", "T_VFX_MuzzlePistol"),
    8: ("08_MuzzleFlash_Rifle", "T_VFX_MuzzleRifle"),
    9: ("09_HitImpact_Flesh", "T_VFX_HitFlesh"),
    10: ("10_HitImpact_Shield", "T_VFX_HitShield"),
    11: ("11_BloodSplatter_Red", "T_VFX_BloodRed"),
    12: ("12_BloodSplatter_Green", "T_VFX_BloodGreen"),
    13: ("13_AcidPuddle_Ground", "T_VFX_AcidPuddle"),
    14: ("14_CryoIceField_Ground", "T_VFX_CryoIce"),
    15: ("15_ElectricField_Ground", "T_VFX_ElectricField"),
    16: ("16_RadiationZone_Ground", "T_VFX_RadiationZone"),
    17: ("17_LevelUp_Aura", "T_VFX_LevelUp"),
    18: ("18_Revive_LightBeam", "T_VFX_ReviveLight"),
}

def extract_file_index(filename):
    m = re.search(r'\((\d+)\)', filename)
    if m:
        return int(m.group(1))
    return 1

CURRENT_RAW_FOLDER = WORKSPACE_ROOT / "xxxx" / "Content" / "美术"
SLICER_PROGRESS_FILE = WORKSPACE_ROOT / "tools" / "sprite_slicer" / ".slicer_project_data.json"

def build_slicer_image_registry(custom_root=None):
    global SLICER_IMAGE_REGISTRY, CURRENT_RAW_FOLDER
    if custom_root:
        p = Path(custom_root).expanduser()
        if not p.is_absolute():
            p = (WORKSPACE_ROOT / custom_root).resolve()
        if p.exists() and p.is_dir():
            CURRENT_RAW_FOLDER = p
    elif SLICER_PROGRESS_FILE.exists():
        try:
            with open(SLICER_PROGRESS_FILE, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            cached_folder = c_data.get("active_folder")
            if cached_folder:
                cp = Path(cached_folder).expanduser()
                if cp.exists() and cp.is_dir():
                    CURRENT_RAW_FOLDER = cp
        except Exception:
            pass

    raw_root = CURRENT_RAW_FOLDER
    SLICER_IMAGE_REGISTRY.clear()
    img_id = 1
    tree = []
    if raw_root.exists() and raw_root.is_dir():
        for root, dirs, files in os.walk(str(raw_root)):
            pngs = [f for f in sorted(files) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) and not f.startswith("._")]
            if pngs:
                rel = os.path.relpath(root, str(raw_root))
                folder_name = rel if rel != "." else (raw_root.name or "根目录")
                file_items = []
                for fn in pngs:
                    full_p = os.path.join(root, fn)
                    rel_p = os.path.relpath(full_p, str(raw_root))
                    idx = extract_file_index(fn)
                    
                    cat = "03_Weapons"
                    sub = f"Export_{idx:02d}"
                    base = f"T_Asset_{idx:02d}"
                    align = "center"

                    if "子弹" in rel or "Bullet" in rel:
                        cat = "03_Weapons"
                        sub, base = WEAPON_NAMES.get(idx, (f"{idx:02d}_WeaponCustom", f"T_Bullet_{idx:02d}"))
                        align = "center"
                    elif "卡片" in rel or "Card" in rel:
                        cat = "06_Cards"
                        sub, base = CARD_NAMES.get(idx, (f"{idx:02d}_CardCustom", f"T_Card_{idx:02d}"))
                        align = "center"
                    elif "可破坏道具" in rel or "Prop" in rel:
                        cat = "04_Props"
                        sub, base = PROP_NAMES.get(idx, (f"{idx:02d}_PropCustom", f"T_Prop_{idx:02d}"))
                        align = "bottom_center"
                    elif "特效" in rel or "VFX" in rel:
                        cat = "05_VFX"
                        sub, base = VFX_NAMES.get(idx, (f"{idx:02d}_VFXCustom", f"T_VFX_{idx:02d}"))
                        align = "center"
                    elif "医疗兵" in rel or "Player" in rel:
                        cat = "01_Player"
                        sub = f"CustomAction_{idx:02d}"
                        base = f"T_Player_Act_{idx:02d}"
                        align = "bottom_center"
                    elif "行尸" in rel:
                        cat = "02_Enemies"
                        sub = f"Zombie/Action_{idx:02d}"
                        base = f"T_Zombie_{idx:02d}"
                        align = "bottom_center"
                    elif "猎犬" in rel:
                        cat = "02_Enemies"
                        sub = f"MutantHound/Action_{idx:02d}"
                        base = f"T_Hound_{idx:02d}"
                        align = "bottom_center"
                    elif "毒液射手" in rel:
                        cat = "02_Enemies"
                        sub = f"VenomShooter/Action_{idx:02d}"
                        base = f"T_Shooter_{idx:02d}"
                        align = "bottom_center"
                    elif "boss技能" in rel:
                        cat = "02_Enemies"
                        sub = f"Boss_Overlord/Skills/Skill_{idx:02d}"
                        base = f"T_BossSkill_{idx:02d}"
                        align = "bottom_center"
                    elif "boss/动作" in rel or "Boss" in rel:
                        cat = "02_Enemies"
                        sub = f"Boss_Overlord/Actions/Action_{idx:02d}"
                        base = f"T_BossAct_{idx:02d}"
                        align = "bottom_center"
                    elif "UI" in rel:
                        cat = "07_UI"
                        sub = f"Layout_{idx:02d}"
                        base = f"T_UI_Layout_{idx:02d}"
                        align = "center"

                    SLICER_IMAGE_REGISTRY[img_id] = {
                        "id": img_id,
                        "rel_path": rel_p,
                        "full_path": full_p,
                        "filename": fn,
                        "default_cat": cat,
                        "default_sub": sub,
                        "default_base": base,
                        "default_align": align
                    }
                    file_items.append({
                        "id": img_id,
                        "filename": fn,
                        "rel_path": rel_p,
                        "default_cat": cat,
                        "default_sub": sub,
                        "default_base": base,
                        "default_align": align
                    })
                    img_id += 1
                    
                tree.append({
                    "folder": folder_name,
                    "rel_path": rel,
                    "files": file_items
                })
    return {
        "status": "success",
        "current_folder": str(raw_root),
        "display_name": raw_root.name or str(raw_root),
        "tree": tree
    }

def get_contour_points(sub_alpha, offset_x=0, offset_y=0, max_pts=60):
    if not np.any(sub_alpha):
        return []
    padded = np.pad(sub_alpha.astype(float), 1, mode='constant', constant_values=0)
    contours = skimage.measure.find_contours(padded, 0.5)
    if not contours:
        return []
    contours.sort(key=lambda c: len(c), reverse=True)
    main_c = contours[0]
    pts = []
    step = max(1, len(main_c) // max_pts)
    for p in main_c[::step]:
        py = p[0] - 1 + offset_y
        px = p[1] - 1 + offset_x
        pts.append([round(float(px), 1), round(float(py), 1)])
    return pts

class StudioHTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(CURRENT_DIR / "web"), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        # ==================== Sprite Studio 智能选区描边工坊合并路由 ====================
        if path == "/slicer" or path == "/slicer/" or path == "/slicer/index.html":
            slicer_html = WORKSPACE_ROOT / "tools" / "sprite_slicer" / "index.html"
            if slicer_html.exists():
                self.serve_file(slicer_html)
                return
        elif path == "/slicer/style.css":
            self.serve_file(WORKSPACE_ROOT / "tools" / "sprite_slicer" / "style.css")
            return
        elif path == "/slicer/app.js":
            self.serve_file(WORKSPACE_ROOT / "tools" / "sprite_slicer" / "app.js")
            return

        elif path == "/api/current-folder":
            disp = None
            try:
                disp = str(CURRENT_RAW_FOLDER.relative_to(WORKSPACE_ROOT))
            except Exception:
                disp = CURRENT_RAW_FOLDER.name or str(CURRENT_RAW_FOLDER)
            return self.json_response({
                "current_folder": str(CURRENT_RAW_FOLDER),
                "display_name": disp
            })

        elif path == "/api/raw-tree":
            params = urllib.parse.parse_qs(parsed.query)
            target_folder = params.get('folder', [None])[0]
            data = build_slicer_image_registry(target_folder)
            tree_list = data.get('tree', []) if isinstance(data, dict) else data
            return self.json_response(tree_list)

        elif path == "/api/check-folder":
            params = urllib.parse.parse_qs(parsed.query)
            cat = params.get('cat', [''])[0]
            sub = params.get('sub', [''])[0]
            art_dir = get_primary_art_dir()
            target_path = art_dir / cat / sub
            exists = target_path.exists()
            file_count = len(list(target_path.iterdir())) if exists else 0
            return self.json_response({
                "exists": exists,
                "count": file_count,
                "folder": str(target_path.relative_to(WORKSPACE_ROOT)) if target_path.is_relative_to(WORKSPACE_ROOT) else str(target_path)
            })

        elif path == "/api/raw-image":
            params = urllib.parse.parse_qs(parsed.query)
            img_id = params.get('id', [''])[0]
            full_path = None
            if img_id and img_id.isdigit():
                item = SLICER_IMAGE_REGISTRY.get(int(img_id))
                if item and os.path.exists(item['full_path']):
                    full_path = item['full_path']
            if not full_path:
                rel_file = params.get('file', [''])[0]
                raw_root = CURRENT_RAW_FOLDER
                cand = raw_root / rel_file
                if cand.exists() and cand.is_file():
                    full_path = str(cand)
            if full_path and os.path.exists(full_path):
                self.serve_file(Path(full_path))
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        elif path == "/api/exported-image":
            params = urllib.parse.parse_qs(parsed.query)
            rel_file = params.get('file', [''])[0]
            art_dir = get_primary_art_dir()
            cand = art_dir / rel_file
            if cand.exists() and cand.is_file():
                self.serve_file(cand)
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        elif path == "/api/slicer/progress":
            if SLICER_PROGRESS_FILE.exists():
                try:
                    with open(SLICER_PROGRESS_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    return self.json_response(data)
                except Exception as e:
                    return self.json_response({"error": str(e), "files_progress": {}}, status=500)
            return self.json_response({"active_folder": "", "last_selected_rel_path": "", "files_progress": {}})

        # 1. 项目基础摘要
        if path == "/api/project/info":
            info = adapter.get_project_summary()
            existing_stems = [t["stem"] for t in info.get("tables", [])]
            from core.datatable_templates import STANDARD_TEMPLATES
            missing = [k for k in STANDARD_TEMPLATES.keys() if k not in existing_stems]
            info["missingStandardTables"] = missing
            return self.json_response(info)

        # 2. 全工作台数据回填聚合 API (/api/data)
        elif path == "/api/data":
            # 扫描/加载所有核心表
            tables_data = {}
            for t in adapter.list_datatables():
                data, fmt = dt_engine.load_table(t["stem"])
                tables_data[t["stem"]] = data

            # 结构化核心表数据（标准化为字典格式）
            characters = to_dict_table(tables_data.get("DT_Characters", {}))
            enemies = to_dict_table(tables_data.get("DT_Enemies", {}))
            weapons = to_dict_table(tables_data.get("DT_Weapons", {}))
            cards = to_dict_table(tables_data.get("DT_TacticalCards", {}))
            waves = to_dict_table(tables_data.get("DT_WaveProgression", {}))
            tiles = to_dict_table(tables_data.get("DT_MapTiles", {}))
            hit_effects = to_dict_table(tables_data.get("DT_HitEffects", {}))

            # 注入美术素材智能映射
            for eid, edata in enemies.items():
                if eid in ENEMY_ART_MAP:
                    edata["ArtInfo"] = ENEMY_ART_MAP[eid]

            for wid, wdata in weapons.items():
                if wid in WEAPON_ART_MAP:
                    wdata["ArtInfo"] = WEAPON_ART_MAP[wid]

            for cid, cdata in cards.items():
                if cid in CARD_ART_MAP:
                    cdata["ArtInfo"] = {"card_image": CARD_ART_MAP[cid]}

            # 扫描主角动作与特效切片及全量候选头像
            player_animations = scan_player_animations()
            vfx_catalog = scan_vfx_catalog()
            candidate_avatars = scan_player_candidate_avatars()

            # 注入角色候选头像列表
            if "Player_Medic" in characters:
                characters["Player_Medic"]["CandidateAvatars"] = candidate_avatars

            # 项目摘要与缺失表探测
            info = adapter.get_project_summary()
            from core.datatable_templates import STANDARD_TEMPLATES
            missing = [k for k in STANDARD_TEMPLATES.keys() if k not in tables_data]
            info["missingStandardTables"] = missing

            payload = {
                "status": "success",
                "timestamp": time.time(),
                "characters": characters,
                "candidate_avatars": candidate_avatars,
                "enemies": enemies,
                "weapons": weapons,
                "cards": cards,
                "waves": waves,
                "tiles": tiles,
                "hit_effects": hit_effects,
                "effects": hit_effects,
                "player_animations": player_animations,
                "vfx_catalog": vfx_catalog,
                "blueprint_schema": BLUEPRINT_PROP_SCHEMA,
                "available_flipbooks": AVAILABLE_FLIPBOOKS,
                "project": info,
                "project_info": info,
                "tables": tables_data,
                "customSchema": prop_engine.get_custom_schema(),
                "custom_schema": prop_engine.get_custom_schema()
            }
            return self.json_response(payload)

        # 3. 美术素材库变动监控与热刷新 API
        elif path == "/api/asset/watch-status":
            return self.json_response({"status": "success", "data": get_art_system_status()})

        elif path == "/api/asset/refresh":
            tree_data = scan_art_tree_data()
            return self.json_response(tree_data)

        # 4. 历史提交审计日志
        elif path == "/api/commits":
            commit_file = None
            if adapter.project_path:
                cand1 = adapter.project_path / "output" / "config_commits.json"
                cand2 = CURRENT_DIR / "output" / "config_commits.json"
                if cand1.exists():
                    commit_file = cand1
                elif cand2.exists():
                    commit_file = cand2

            if commit_file and commit_file.exists():
                try:
                    commits = json.loads(commit_file.read_text(encoding="utf-8"))
                    return self.json_response({"status": "success", "commits": commits})
                except Exception:
                    pass
            return self.json_response({"status": "success", "commits": []})

        # 5. 美术素材库树状清单
        elif path == "/api/art-tree":
            tree_data = scan_art_tree_data()
            return self.json_response(tree_data)

        # 5. 获取指定素材目录下的所有 PNG 帧序列
        elif path in ["/api/dir-frames", "/api/vfx-frames"]:
            params = urllib.parse.parse_qs(parsed.query)
            target_rel = params.get("dir", params.get("folder", params.get("path", [None])))[0]
            action_hint = params.get("action", [""])[0].lower()

            art_dir = get_primary_art_dir()
            if not target_rel:
                return self.json_response({"status": "error", "error": "缺少 dir 或 path 参数"}, status=400)

            # 判断是否是绝对路径
            p = Path(target_rel)
            if not p.is_absolute():
                p = (art_dir / target_rel).resolve()

            if p.is_file():
                p = p.parent

            frames = []
            actual_dir = str(p.relative_to(art_dir)) if p.is_relative_to(art_dir) else str(p)

            if p.exists() and p.is_dir():
                direct_pngs = [
                    str(f.relative_to(art_dir)) if f.is_relative_to(art_dir) else str(f)
                    for f in sorted(p.glob("*.png"))
                    if "Sheet" not in f.name and not f.name.startswith("._")
                ]
                if direct_pngs:
                    frames = direct_pngs
                else:
                    # 智能向下检索子目录
                    sub_dirs = [d for d in p.iterdir() if d.is_dir()]
                    chosen_sub = None
                    if action_hint:
                        for d in sub_dirs:
                            if action_hint in d.name.lower():
                                chosen_sub = d
                                break
                    if not chosen_sub and sub_dirs:
                        for d in sub_dirs:
                            if any(d.glob("*.png")):
                                chosen_sub = d
                                break
                    if chosen_sub:
                        frames = [
                            str(f.relative_to(art_dir)) if f.is_relative_to(art_dir) else str(f)
                            for f in sorted(chosen_sub.glob("*.png"))
                            if "Sheet" not in f.name and not f.name.startswith("._")
                        ]
                        actual_dir = str(chosen_sub.relative_to(art_dir)) if chosen_sub.is_relative_to(art_dir) else str(chosen_sub)

            return self.json_response({
                "status": "success",
                "folder": actual_dir,
                "dir": actual_dir,
                "frames": frames,
                "total": len(frames)
            })

        # 6. HUD 画布布局
        elif path == "/api/hud/layout":
            return self.json_response(hud_engine.get_layout())

        # 6.1 获取项目中真实存在的所有美术子目录列表
        elif path == "/api/asset/folders":
            art_dir = get_primary_art_dir()
            folders = []
            if art_dir.exists():
                for d in sorted(art_dir.glob("**/*")):
                    if d.is_dir() and not d.name.startswith(".") and ".source_backup" not in str(d):
                        rel = str(d.relative_to(art_dir)).replace("\\", "/")
                        folders.append(rel)
            return self.json_response({"status": "success", "folders": folders})

        # 7. AI-First Schema 导出
        elif path == "/api/schema/dump":
            return self.json_response(schema_engine.dump_project_schema())

        elif path == "/api/schema/markdown":
            md = schema_engine.dump_markdown_codebook()
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.end_headers()
            self.wfile.write(md.encode("utf-8"))
            return

        # 8. 绝对路径图片预览 (/asset-view?path=...)
        elif path == "/asset-view":
            params = urllib.parse.parse_qs(parsed.query)
            file_path = params.get("path", [None])[0]
            if file_path and os.path.exists(file_path):
                self.serve_file(Path(file_path))
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        # 9. 相对美术素材映射 (/art/...)
        elif path.startswith("/art/"):
            rel = path[len("/art/"):]
            # 候选检索目录
            search_roots = []
            if adapter:
                search_roots.extend([Path(d) for d in adapter.art_dirs])
                search_roots.append(adapter.content_dir / "美术" / "Art")
                search_roots.append(adapter.content_dir / "美术")
                search_roots.append(adapter.content_dir)

            found_file = None
            for sr in search_roots:
                target = (sr / rel).resolve()
                if target.exists() and target.is_file():
                    found_file = target
                    break

            if found_file:
                self.serve_file(found_file)
                return
            else:
                self.send_error(404, f"Art file not found: {rel}")
                return

        # 10. 前端静态页面与脚本
        if path in ["/cutter", "/cutter/", "/sprite-cutter"]:
            cutter_html = WORKSPACE_ROOT / "tools" / "sprite_cutter" / "裁图工作台.html"
            if cutter_html.exists():
                self.serve_file(cutter_html)
                return

        if path == "/" or path == "/index.html":
            self.serve_file(CURRENT_DIR / "web" / "index.html")
            return
        elif path in ["/style.css", "/app.js"]:
            self.serve_file(CURRENT_DIR / "web" / path[1:])
            return

        # 默认回退到 web 静态目录
        web_file = (CURRENT_DIR / "web" / path.lstrip("/")).resolve()
        if str(web_file).startswith(str(CURRENT_DIR / "web")) and web_file.is_file():
            self.serve_file(web_file)
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        body = self.read_json_body()

        # ==================== Sprite Studio 智能选区与导出处理 ====================
        if path == "/api/set-raw-folder":
            folder = body.get('folder', '').strip()
            if not folder:
                return self.json_response({"success": False, "error": "Folder path required"}, status=400)
            target_p = Path(folder).expanduser()
            if not target_p.is_absolute():
                target_p = (WORKSPACE_ROOT / folder).resolve()
            if not target_p.exists() or not target_p.is_dir():
                return self.json_response({"success": False, "error": f"Folder not found: {folder}"}, status=404)
            data = build_slicer_image_registry(str(target_p))
            tree_list = data.get('tree', []) if isinstance(data, dict) else data
            disp = None
            try:
                disp = str(target_p.relative_to(WORKSPACE_ROOT))
            except Exception:
                disp = target_p.name or str(target_p)
            return self.json_response({"success": True, "active_folder": str(target_p), "display_name": disp, "data": tree_list})

        elif path == "/api/select-folder-dialog":
            import subprocess
            try:
                cmd = ['osascript', '-e', 'return POSIX path of (choose folder with prompt "请选择包含原画素材的文件夹")']
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if res.returncode == 0 and res.stdout.strip():
                    chosen = res.stdout.strip()
                    data = build_slicer_image_registry(chosen)
                    tree_list = data.get('tree', []) if isinstance(data, dict) else data
                    chosen_p = Path(chosen)
                    disp = None
                    try:
                        disp = str(chosen_p.relative_to(WORKSPACE_ROOT))
                    except Exception:
                        disp = chosen_p.name or chosen
                    return self.json_response({"success": True, "folder": chosen, "active_folder": chosen, "display_name": disp, "data": tree_list})
                else:
                    return self.json_response({"success": False, "canceled": True})
            except Exception as e:
                return self.json_response({"success": False, "error": str(e)})

        elif path == "/api/compute-contour":
            raw_root = CURRENT_RAW_FOLDER
            full_path = None
            img_id = body.get('id')
            if img_id and str(img_id).isdigit():
                item = SLICER_IMAGE_REGISTRY.get(int(img_id))
                if item: full_path = item['full_path']
            if not full_path or not os.path.exists(full_path):
                return self.json_response({"error": "not found"}, status=404)

            box = body.get('box', {})
            thresh = int(body.get('threshold', 15))
            expand = int(body.get('expand', 0))

            im = Image.open(full_path).convert("RGBA")
            img_w, img_h = im.size
            arr = np.array(im)

            bx1 = max(0, int(box.get('x', 0)))
            by1 = max(0, int(box.get('y', 0)))
            bx2 = min(img_w, bx1 + int(box.get('w', 100)))
            by2 = min(img_h, by1 + int(box.get('h', 100)))

            sub_alpha = arr[by1:by2, bx1:bx2, 3] > thresh
            if expand != 0:
                if expand > 0:
                    sub_alpha = ndi.binary_dilation(sub_alpha, iterations=expand)
                else:
                    sub_alpha = ndi.binary_erosion(sub_alpha, iterations=abs(expand))

            contour_pts = get_contour_points(sub_alpha, offset_x=bx1, offset_y=by1)
            return self.json_response({"contour": contour_pts})

        elif path == "/api/detect":
            raw_root = CURRENT_RAW_FOLDER
            full_path = None
            img_id = body.get('id')
            if img_id and str(img_id).isdigit():
                item = SLICER_IMAGE_REGISTRY.get(int(img_id))
                if item: full_path = item['full_path']
            if not full_path:
                rel_file = body.get('file', '')
                cand = raw_root / rel_file
                if cand.exists(): full_path = str(cand)

            mode = body.get('mode', 'auto')
            thresh = int(body.get('threshold', 15))

            if not full_path or not os.path.exists(full_path):
                return self.json_response({"error": "not found"}, status=404)

            im = Image.open(full_path).convert("RGBA")
            arr = np.array(im)
            alpha = arr[:, :, 3] > thresh
            w, h = im.size
            boxes = []

            if mode == 'grid_2x4':
                cell_w = w / 4.0
                cell_h = h / 2.0
                for r in range(2):
                    for c in range(4):
                        x1, x2 = int(c * cell_w), int((c + 1) * cell_w)
                        y1, y2 = int(r * cell_h), int((r + 1) * cell_h)
                        sub_alpha = alpha[y1:y2, x1:x2]
                        if np.any(sub_alpha):
                            ys, xs = np.where(sub_alpha)
                            bx1 = x1 + int(np.min(xs))
                            bx2 = x1 + int(np.max(xs)) + 1
                            by1 = y1 + int(np.min(ys))
                            by2 = y1 + int(np.max(ys)) + 1
                            contour = get_contour_points(alpha[by1:by2, bx1:bx2], offset_x=bx1, offset_y=by1)
                            boxes.append({"x": bx1, "y": by1, "w": bx2 - bx1, "h": by2 - by1, "label": f"{r*4 + c + 1:02d}", "contour": contour})

            elif mode == 'horizontal_4':
                cell_w = w / 4.0
                for c in range(4):
                    x1, x2 = int(c * cell_w), int((c + 1) * cell_w)
                    sub_alpha = alpha[:, x1:x2]
                    if np.any(sub_alpha):
                        ys, xs = np.where(sub_alpha)
                        bx1 = x1 + int(np.min(xs))
                        bx2 = x1 + int(np.max(xs)) + 1
                        by1 = int(np.min(ys))
                        by2 = int(np.max(ys)) + 1
                        contour = get_contour_points(alpha[by1:by2, bx1:bx2], offset_x=bx1, offset_y=by1)
                        boxes.append({"x": bx1, "y": by1, "w": bx2 - bx1, "h": by2 - by1, "label": f"{c+1:02d}", "contour": contour})

            elif mode == 'horizontal_3':
                cell_w = w / 3.0
                for c in range(3):
                    x1, x2 = int(c * cell_w), int((c + 1) * cell_w)
                    sub_alpha = alpha[:, x1:x2]
                    if np.any(sub_alpha):
                        ys, xs = np.where(sub_alpha)
                        bx1 = x1 + int(np.min(xs))
                        bx2 = x1 + int(np.max(xs)) + 1
                        by1 = int(np.min(ys))
                        by2 = int(np.max(ys)) + 1
                        state_names = ["01_Intact", "02_Damaged", "03_Destroyed"]
                        contour = get_contour_points(alpha[by1:by2, bx1:bx2], offset_x=bx1, offset_y=by1)
                        boxes.append({"x": bx1, "y": by1, "w": bx2 - bx1, "h": by2 - by1, "label": state_names[c], "contour": contour})

            else:
                labeled, num_objs = ndi.label(alpha)
                for i in range(1, num_objs + 1):
                    m = (labeled == i)
                    if np.sum(m) > 1000:
                        ys, xs = np.where(m)
                        bx1, bx2 = int(np.min(xs)), int(np.max(xs)) + 1
                        by1, by2 = int(np.min(ys)), int(np.max(ys)) + 1
                        contour = get_contour_points(m[by1:by2, bx1:bx2], offset_x=bx1, offset_y=by1)
                        boxes.append({"x": bx1, "y": by1, "w": bx2 - bx1, "h": by2 - by1, "label": f"{len(boxes)+1:02d}", "contour": contour})
                boxes.sort(key=lambda b: (b["y"] // 80, b["x"]))

            return self.json_response({"image_size": [w, h], "boxes": boxes})

        elif path == "/api/export":
            raw_root = CURRENT_RAW_FOLDER
            full_path = None
            img_id = body.get('id')
            if img_id and str(img_id).isdigit():
                item = SLICER_IMAGE_REGISTRY.get(int(img_id))
                if item: full_path = item['full_path']
            if not full_path:
                rel_file = body.get('file', '')
                cand = raw_root / rel_file
                if cand.exists(): full_path = str(cand)

            target_cat = body.get('category', '01_Player')
            sub_folder = body.get('subfolder', 'HeavyGunner/01')
            base_name = body.get('base_name', 'T_HeavyGunner_01')
            align_mode = body.get('align', 'bottom_center')
            boxes = body.get('boxes', [])
            generate_sheet = body.get('generate_sheet', True)
            pad = int(body.get('pad', 10))
            use_polygon_mask = body.get('smart_mask', True)

            if not full_path or not os.path.exists(full_path) or not boxes:
                return self.json_response({"success": False, "error": "Invalid file or boxes"}, status=400)

            im = Image.open(full_path).convert("RGBA")
            img_w, img_h = im.size
            art_dir = get_primary_art_dir()
            dst_dir = art_dir / target_cat / sub_folder
            dst_dir.mkdir(parents=True, exist_ok=True)

            backup_root = WORKSPACE_ROOT / "tools" / "sprite_slicer" / ".backups"
            backup_root.mkdir(parents=True, exist_ok=True)

            cropped_imgs = []
            for b in boxes:
                bx1 = max(0, int(b['x']))
                by1 = max(0, int(b['y']))
                bx2 = min(img_w, bx1 + int(b['w']))
                by2 = min(img_h, by1 + int(b['h']))
                if bx2 > bx1 and by2 > by1:
                    crop = im.crop((bx1, by1, bx2, by2))
                    poly = b.get('contour', [])
                    if use_polygon_mask and len(poly) >= 3:
                        mask_img = Image.new("L", (bx2 - bx1, by2 - by1), 0)
                        draw = ImageDraw.Draw(mask_img)
                        local_poly = [(p[0] - bx1, p[1] - by1) for p in poly]
                        draw.polygon(local_poly, fill=255)
                        c_arr = np.array(crop)
                        m_arr = np.array(mask_img) > 128
                        c_arr[:, :, 3] = np.where(m_arr, c_arr[:, :, 3], 0)
                        crop = Image.fromarray(c_arr)

                    c_arr = np.array(crop)
                    c_alpha = c_arr[:, :, 3] > 10
                    if np.any(c_alpha):
                        ys, xs = np.where(c_alpha)
                        crop = crop.crop((int(np.min(xs)), int(np.min(ys)), int(np.max(xs))+1, int(np.max(ys))+1))
                    cropped_imgs.append((crop, b.get('label', '')))

            if not cropped_imgs:
                return self.json_response({"error": "no crops"}, status=400)

            max_w = max(ci[0].size[0] for ci in cropped_imgs) + pad * 2
            max_h = max(ci[0].size[1] for ci in cropped_imgs) + pad * 2
            saved_files = []
            norm_imgs = []
            for idx, (crop, label) in enumerate(cropped_imgs):
                cw, ch = crop.size
                canvas = Image.new("RGBA", (max_w, max_h), (0, 0, 0, 0))
                paste_x = (max_w - cw) // 2
                paste_y = max_h - ch - pad if align_mode == "bottom_center" else (max_h - ch) // 2
                canvas.paste(crop, (paste_x, paste_y), crop)
                norm_imgs.append(canvas)
                custom_name = label if label and not label.startswith("Entity_") else f"{idx+1:02d}"
                fn = f"{base_name}_{custom_name}.png" if not custom_name.startswith(base_name) else f"{custom_name}.png"
                out_path = dst_dir / fn
                canvas.save(str(out_path), "PNG")
                saved_files.append(fn)

            if generate_sheet and len(norm_imgs) > 1:
                sheet = Image.new("RGBA", (max_w * len(norm_imgs), max_h), (0, 0, 0, 0))
                for i, nim in enumerate(norm_imgs):
                    sheet.paste(nim, (i * max_w, 0), nim)
                sheet_fn = f"{base_name}_Sheet.png"
                sheet.save(str(dst_dir / sheet_fn), "PNG")
                saved_files.append(sheet_fn)

            try:
                import subprocess
                subprocess.run(["open", str(dst_dir)])
            except Exception:
                pass

            return self.json_response({
                "success": True,
                "saved_dir": str(dst_dir.relative_to(WORKSPACE_ROOT)),
                "full_path": str(dst_dir),
                "saved_files": saved_files,
                "frame_size": [max_w, max_h]
            })

        elif path == "/api/open-folder":
            import subprocess
            rel_folder = body.get('folder', '')
            art_dir = get_primary_art_dir()
            full_dst = art_dir / rel_folder if rel_folder else art_dir
            if not full_dst.exists(): full_dst = art_dir
            subprocess.run(["open", str(full_dst)])
            return self.json_response({"success": True})

        elif path == "/api/slicer/save-progress":
            try:
                os.makedirs(SLICER_PROGRESS_FILE.parent, exist_ok=True)
                existing = {}
                if SLICER_PROGRESS_FILE.exists():
                    try:
                        with open(SLICER_PROGRESS_FILE, "r", encoding="utf-8") as f:
                            existing = json.load(f)
                    except Exception:
                        existing = {}

                if "active_folder" in body and body["active_folder"]:
                    existing["active_folder"] = body["active_folder"]
                if "last_selected_rel_path" in body and body["last_selected_rel_path"]:
                    existing["last_selected_rel_path"] = body["last_selected_rel_path"]
                if "files_progress" in body and isinstance(body["files_progress"], dict):
                    if "files_progress" not in existing:
                        existing["files_progress"] = {}
                    existing["files_progress"].update(body["files_progress"])

                existing["last_saved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

                with open(SLICER_PROGRESS_FILE, "w", encoding="utf-8") as f:
                    json.dump(existing, f, ensure_ascii=False, indent=2)

                return self.json_response({"success": True, "saved_at": existing["last_saved_at"]})
            except Exception as e:
                return self.json_response({"success": False, "error": str(e)}, status=500)

        elif path == "/api/slicer/reset-progress":
            try:
                rel_path = body.get("rel_path")
                if SLICER_PROGRESS_FILE.exists():
                    with open(SLICER_PROGRESS_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if rel_path:
                        if "files_progress" in data and rel_path in data["files_progress"]:
                            del data["files_progress"][rel_path]
                    else:
                        data["files_progress"] = {}
                    with open(SLICER_PROGRESS_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                return self.json_response({"success": True})
            except Exception as e:
                return self.json_response({"success": False, "error": str(e)}, status=500)



        # 1. 切换工程挂载
        if path == "/api/project/switch":
            new_path = body.get("path")
            if not new_path or not os.path.exists(new_path):
                return self.json_response({"error": "路径不存在"}, status=400)
            init_workspace(new_path)
            return self.json_response({"success": True, "project": adapter.get_project_summary()})

        # 2. 空白工程核心数据表自愈脚手架
        elif path == "/api/project/scaffold-tables":
            tables = body.get("tables", None)
            res = dt_engine.scaffold_missing_tables(tables)
            return self.json_response(res)

        # 3. 数据保存 API (/api/save) - 双模兼容：支持全量实体回写与单表回写
        elif path == "/api/save":
            # 模式 A: 前端全量配置保存 (包含 characters/enemies/weapons/cards/waves/tiles/hit_effects)
            is_full_save = any(k in body for k in ["characters", "enemies", "weapons", "cards", "waves", "tiles", "hit_effects"])
            if is_full_save:
                modified_tables = []
                diff_summary = []

                if "characters" in body:
                    chars = body["characters"]
                    dt_engine.save_table("DT_Characters", chars, "json")
                    modified_tables.append("DT_Characters.json")
                    diff_summary.append("更新主角全属性、动作特效与武器挂载")

                if "enemies" in body:
                    enemies_clean = {}
                    for k, v in body["enemies"].items():
                        clean_item = {ik: iv for ik, iv in v.items() if ik != "ArtInfo"}
                        enemies_clean[k] = clean_item
                    dt_engine.save_table("DT_Enemies", enemies_clean, "json")
                    modified_tables.append("DT_Enemies.json")
                    diff_summary.append(f"更新 {len(enemies_clean)} 种敌人数值与素材映射")

                if "weapons" in body:
                    weapons_clean = {}
                    for k, v in body["weapons"].items():
                        clean_item = {ik: iv for ik, iv in v.items() if ik != "ArtInfo"}
                        weapons_clean[k] = clean_item
                    dt_engine.save_table("DT_Weapons", weapons_clean, "json")
                    modified_tables.append("DT_Weapons.json")
                    diff_summary.append(f"更新 {len(weapons_clean)} 把武器射击属性")

                if "cards" in body:
                    cards_clean = {}
                    for k, v in body["cards"].items():
                        clean_item = {ik: iv for ik, iv in v.items() if ik != "ArtInfo"}
                        cards_clean[k] = clean_item
                    dt_engine.save_table("DT_TacticalCards", cards_clean, "json")
                    modified_tables.append("DT_TacticalCards.json")
                    diff_summary.append(f"更新 {len(cards_clean)} 张战术强化卡牌")

                if "waves" in body:
                    dt_engine.save_table("DT_WaveProgression", body["waves"], "json")
                    modified_tables.append("DT_WaveProgression.json")
                    diff_summary.append("更新关卡出怪波次时间轴")

                if "tiles" in body:
                    dt_engine.save_table("DT_MapTiles", body["tiles"], "json")
                    modified_tables.append("DT_MapTiles.json")
                    diff_summary.append(f"更新 {len(body['tiles'])} 块土地地表数据")

                if "hit_effects" in body:
                    dt_engine.save_table("DT_HitEffects", body["hit_effects"], "json")
                    modified_tables.append("DT_HitEffects.json")
                    diff_summary.append(f"更新 {len(body['hit_effects'])} 种战斗特效属性与切片")

                # 记录 Commit 审计日志
                commit_record = {
                    "id": f"commit_{int(time.time()*1000)}",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "author": body.get("author", "策划/开发者"),
                    "comment": body.get("comment", "通过可视化配置中心提交数值调优"),
                    "modified_tables": modified_tables,
                    "diff_summary": diff_summary,
                    "raw_diff": body.get("raw_diff", {})
                }

                log_dir = adapter.project_path / "output" if adapter.project_path else CURRENT_DIR / "output"
                log_dir.mkdir(parents=True, exist_ok=True)
                commit_path = log_dir / "config_commits.json"
                all_commits = []
                if commit_path.exists():
                    try:
                        all_commits = json.loads(commit_path.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                all_commits.insert(0, commit_record)
                commit_path.write_text(json.dumps(all_commits, ensure_ascii=False, indent=2), encoding="utf-8")

                return self.json_response({
                    "status": "success",
                    "success": True,
                    "message": f"成功保存 {len(modified_tables)} 张数据表并记录审计！",
                    "commit": commit_record
                })

            # 模式 B: 单表标准保存 (包含 table, rows)
            table_name = body.get("table")
            rows = body.get("rows")
            fmt = body.get("format", "json")
            if not table_name or rows is None:
                return self.json_response({"status": "error", "error": "缺少 table 或 rows 参数"}, status=400)
            res = dt_engine.save_table(table_name, rows, fmt)
            res["status"] = "success" if res.get("success") else "error"
            return self.json_response(res)

        # 4. 动态自定义属性 API
        elif path == "/api/custom-props/add":
            table_name = body.get("table")
            prop_key = body.get("key")
            prop_def = body.get("definition")
            res = prop_engine.register_property(table_name, prop_key, prop_def)
            return self.json_response({"success": True, "property": res})

        elif path == "/api/custom-props/remove":
            table_name = body.get("table")
            prop_key = body.get("key")
            res = prop_engine.remove_property(table_name, prop_key)
            return self.json_response({"success": res})

        # 5. 美术素材处理流水线、通用摄取与拖拽上传
        elif path == "/api/asset/ingest":
            import base64
            file_base64 = body.get("file_base64", "")
            filename = body.get("filename", f"drop_{int(time.time())}.png")
            category = body.get("category", "general")
            entity_id = body.get("entity_id", "")
            auto_remove_black = bool(body.get("auto_remove_black", False))
            auto_trim = bool(body.get("auto_trim", False))
            target_dir = body.get("target_dir", None)

            if not file_base64:
                return self.json_response({"status": "error", "error": "缺少 file_base64 数据"}, status=400)

            if "," in file_base64:
                file_base64 = file_base64.split(",", 1)[1]

            try:
                raw_bytes = base64.b64decode(file_base64)
            except Exception as e:
                return self.json_response({"status": "error", "error": f"Base64 解码异常: {e}"}, status=400)

            res = ingest_engine.ingest_image_asset(
                file_bytes=raw_bytes,
                filename=filename,
                category=category,
                entity_id=entity_id,
                auto_remove_black=auto_remove_black,
                auto_trim=auto_trim,
                target_dir_override=target_dir
            )
            return self.json_response(res)

        elif path == "/api/asset/upload":
            res = handle_asset_upload(body)
            status_code = 200 if res.get("status") == "success" else 400
            return self.json_response(res, status=status_code)

        elif path == "/api/asset/auto-process":
            action = body.get("action", "")
            img_rel = body.get("path", "")
            if action == "set_avatar":
                normalize = body.get("normalize", True)
                res = process_set_avatar(img_rel, normalize=normalize)
                return self.json_response(res)
            elif action == "remove_black":
                art_dir = get_primary_art_dir()
                abs_p = (art_dir / img_rel).resolve()
                threshold = int(body.get("threshold", 25))
                target = asset_engine.remove_black_background(str(abs_p), threshold)
                rel_target = str(Path(target).relative_to(art_dir)) if Path(target).is_relative_to(art_dir) else str(target)
                return self.json_response({
                    "status": "success",
                    "outputPath": target,
                    "relPath": rel_target,
                    "url": f"/art/{urllib.parse.quote(rel_target)}",
                    "message": "已成功去黑底并生成透明图片！"
                })
            elif action == "slice_grid":
                art_dir = get_primary_art_dir()
                abs_p = (art_dir / img_rel).resolve()
                rows = int(body.get("rows", 2))
                cols = int(body.get("cols", 4))
                res = asset_engine.slice_grid(str(abs_p), rows, cols)
                return self.json_response(res)
            elif action == "height_check":
                art_dir = get_primary_art_dir()
                abs_p = (art_dir / img_rel).resolve()
                exp_h = int(body.get("expectedHeight", 430))
                res = asset_engine.check_character_standing_height(str(abs_p), exp_h)
                return self.json_response(res)
            return self.json_response({"status": "error", "error": f"未知操作: {action}"}, status=400)

        elif path == "/api/asset/smart-detect":
            raw_p = body.get("path", "")
            abs_p = resolve_incoming_path(raw_p)
            min_area = int(body.get("min_area", 3000))
            padding = int(body.get("padding", 4))
            res = asset_engine.detect_smart_sprites(str(abs_p), min_area=min_area, padding=padding)
            return self.json_response(res)

        elif path == "/api/asset/slice-custom":
            raw_p = body.get("path", "")
            abs_p = resolve_incoming_path(raw_p)

            boxes = body.get("boxes")
            h_lines = body.get("h_lines")
            v_lines = body.get("v_lines")

            if boxes is not None:
                res = asset_engine.slice_boxes(str(abs_p), boxes)
            elif h_lines is not None and v_lines is not None:
                res = asset_engine.slice_custom_lines(str(abs_p), h_lines, v_lines)
            else:
                rows = int(body.get("rows", 2))
                cols = int(body.get("cols", 4))
                res = asset_engine.slice_grid(str(abs_p), rows, cols)
            return self.json_response(res)

        elif path == "/api/asset/export-slices":
            raw_p = body.get("path", "")
            abs_p = resolve_incoming_path(raw_p)

            boxes = body.get("boxes", [])
            category = body.get("category", "01_Player")
            sub_dir = body.get("sub_dir", "")
            prefix = body.get("prefix", "")
            start_index = int(body.get("start_index", 1))
            auto_trim = bool(body.get("auto_trim", False))
            auto_remove_black = bool(body.get("auto_remove_black", False))

            res = asset_engine.export_slices_to_project(
                img_path=str(abs_p),
                boxes=boxes,
                category=category,
                sub_dir=sub_dir,
                prefix=prefix,
                start_index=start_index,
                auto_trim=auto_trim,
                auto_remove_black=auto_remove_black
            )
            return self.json_response(res)

        elif path == "/api/asset/export-multi-actions":
            raw_p = body.get("path", "")
            abs_p = resolve_incoming_path(raw_p)
            action_groups = body.get("action_groups", [])
            base_category = body.get("base_category", "01_Player/Actions")
            auto_trim = bool(body.get("auto_trim", True))
            auto_remove_black = bool(body.get("auto_remove_black", False))

            res = asset_engine.export_multi_actions_to_project(
                img_path=str(abs_p),
                action_groups=action_groups,
                base_category=base_category,
                auto_trim=auto_trim,
                auto_remove_black=auto_remove_black
            )
            return self.json_response(res)

        elif path == "/api/asset/slice-grid":
            img_path = body.get("path", "")
            abs_p = resolve_incoming_path(img_path)
            rows = int(body.get("rows", 2))
            cols = int(body.get("cols", 4))
            res = asset_engine.slice_grid(str(abs_p), rows, cols)
            return self.json_response(res)
            return self.json_response(res)

        elif path == "/api/asset/remove-black":
            img_path = body.get("path")
            art_dir = get_primary_art_dir()
            p = Path(img_path)
            abs_p = p if p.is_absolute() else (art_dir / img_path).resolve()
            threshold = int(body.get("threshold", 25))
            target = asset_engine.remove_black_background(str(abs_p), threshold)
            return self.json_response({"success": True, "outputPath": target})

        elif path == "/api/asset/height-check":
            img_path = body.get("path")
            art_dir = get_primary_art_dir()
            p = Path(img_path)
            abs_p = p if p.is_absolute() else (art_dir / img_path).resolve()
            exp_h = int(body.get("expectedHeight", 430))
            res = asset_engine.check_character_standing_height(str(abs_p), exp_h)
            return self.json_response(res)

        # 4.5 角色配套生态裁图工作台保存切片接口 (/api/save_slices)
        elif path == "/api/save_slices":
            try:
                dest_key = body.get("dest", "characters")
                subfolder = body.get("subfolder", "")
                art_base = adapter.content_dir / "美术" / "Art" if adapter else (WORKSPACE_ROOT / "xxxx" / "Content" / "美术" / "Art")
                
                dest_mapping = {
                    "player": art_base / "01_Player",
                    "characters": art_base / "01_Player",
                    "enemies": art_base / "02_Enemies",
                    "weapons": art_base / "03_Weapons",
                    "props": art_base / "04_Props",
                    "tiles": art_base / "04_Props",
                    "vfx": art_base / "05_VFX",
                    "cards": art_base / "06_Cards",
                    "ui": art_base / "07_UI",
                    "frames_hero": art_base / "01_Player" / "HeroAttack",
                    "frames_monster": art_base / "02_Enemies" / "MonsterAttack",
                    "frames_explosion": art_base / "05_VFX" / "Explosion",
                    "frames_buff": art_base / "05_VFX" / "Buff",
                    "frames_reward": art_base / "06_Cards" / "Reward",
                    "frames_status": art_base / "07_UI" / "Status",
                    "frames_destruction": art_base / "04_Props" / "Destruction",
                    "output": WORKSPACE_ROOT / "output" / "sliced_sprites"
                }
                
                dest_dir = dest_mapping.get(dest_key, art_base / "01_Player")
                if subfolder:
                    sub_parts = [re.sub(r"[^\w\-.]", "_", p.strip()) for p in subfolder.strip().replace("\\", "/").split("/") if p.strip()]
                    if sub_parts and sub_parts[0] in ["01_Player", "02_Enemies", "03_Weapons", "04_Props", "05_VFX", "06_Cards", "07_UI"]:
                        dest_dir = art_base
                    for sp in sub_parts:
                        dest_dir = dest_dir / sp
                
                dest_dir.mkdir(parents=True, exist_ok=True)
                backup_dir = WORKSPACE_ROOT / "output" / ".backups" / "cutter"
                backup_dir.mkdir(parents=True, exist_ok=True)

                saved_count = 0
                saved_files = []
                import base64
                for item in body.get("slices", []):
                    name = item.get("name", "sprite")
                    clean_name = re.sub(r"[^\w\-.]", "_", name)
                    if not clean_name.lower().endswith(".png"):
                        clean_name += ".png"
                    
                    # 检查切片是否指定了独立的动作子目录 (支持第1排/第2排分类归档)
                    target_out_dir = dest_dir
                    item_sub = item.get("subfolder") or item.get("subpath")
                    if item_sub:
                        sub_parts = [re.sub(r"[^\w\-.]", "_", p.strip()) for p in item_sub.strip().replace("\\", "/").split("/") if p.strip()]
                        cur_base = art_base if sub_parts and sub_parts[0] in ["01_Player", "02_Enemies", "03_Weapons", "04_Props", "05_VFX", "06_Cards", "07_UI"] else dest_dir
                        for sp in sub_parts:
                            cur_base = cur_base / sp
                        cur_base.mkdir(parents=True, exist_ok=True)
                        target_out_dir = cur_base

                    data_url = item.get("data_url", "")
                    if "," in data_url:
                        raw_bytes = base64.b64decode(data_url.split(",")[1])
                        (target_out_dir / clean_name).write_bytes(raw_bytes)
                        (backup_dir / clean_name).write_bytes(raw_bytes)
                        saved_count += 1
                        saved_files.append(clean_name)

                dest_rel = str(dest_dir.relative_to(WORKSPACE_ROOT)) if WORKSPACE_ROOT in dest_dir.parents else str(dest_dir)
                return self.json_response({
                    "success": True,
                    "count": saved_count,
                    "dest_path": dest_rel,
                    "full_path": str(dest_dir),
                    "saved_files": saved_files
                })
            except Exception as e:
                return self.json_response({"success": False, "error": str(e)}, status=500)

        elif path == "/api/open_folder":
            try:
                target = body.get("path", "")
                if not target or not os.path.exists(target):
                    target = str(adapter.content_dir / "美术" / "Art" if adapter else WORKSPACE_ROOT)
                import subprocess
                subprocess.run(["open", target])
                return self.json_response({"success": True})
            except Exception as e:
                return self.json_response({"success": False, "error": str(e)}, status=500)

        # 6. 手机 HUD 画布工坊
        elif path == "/api/hud/save":
            layout = body.get("layout")
            res = hud_engine.save_layout(layout)
            return self.json_response(res)

        elif path == "/api/hud/export-umg":
            script = hud_engine.generate_ue_umg_python_script()
            return self.json_response({"success": True, "pythonScript": script})

        return self.json_response({"error": "Not Found"}, status=404)

    def serve_file(self, file_path: Path):
        """流式返回本地文件内容并附带准确 MIME 类型"""
        try:
            mime, _ = mimetypes.guess_type(str(file_path))
            if not mime:
                mime = "application/octet-stream"
            if file_path.suffix == ".css":
                mime = "text/css"
            elif file_path.suffix == ".js":
                mime = "application/javascript"
            elif file_path.suffix == ".png":
                mime = "image/png"
            elif file_path.suffix in [".jpg", ".jpeg"]:
                mime = "image/jpeg"

            with open(file_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

    def read_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

def main():
    parser = argparse.ArgumentParser(description="Unreal Canvas Studio - 通用 UE 可视化开发套件")
    parser.add_argument("--project", "-p", default="/Users/cc/Desktop/GGBOM/xxxx", help="挂载目标 UE 工程路径")
    parser.add_argument("--port", type=int, default=8899, help="服务端口 (默认 8899)")
    args = parser.parse_args()

    print("=" * 70)
    print("🚀 Unreal Canvas Studio - 通用 UE5 2D 可视化开发与资产工坊")
    print("=" * 70)
    init_workspace(args.project)

    server = HTTPServer(("0.0.0.0", args.port), StudioHTTPHandler)
    print(f"🌟 服务已就绪: http://localhost:{args.port}")
    print("=" * 70)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务已平稳停止。")

if __name__ == "__main__":
    main()
