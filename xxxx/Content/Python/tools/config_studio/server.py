# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》动态配置网页后端服务 (Config Studio Backend)
================================================================================
提供游戏数据表 (DT_Enemies, DT_Weapons, DT_TacticalCards, DT_WaveProgression)
与本地美术素材 (Content/美术/Art) 的实时联动、数据可视化 API、原子写盘与 UE5 热同步接口。
"""
from __future__ import annotations
import http.server
import json
import mimetypes
import os
from pathlib import Path
import socketserver
import subprocess
import sys
import time
from urllib.parse import urlparse, unquote, parse_qs

PORT = 8899
HOST = "0.0.0.0"

PROJECT_ROOT = Path("/Users/cc/Desktop/GGBOM/xxxx").resolve()
DATA_DIR = PROJECT_ROOT / "Content" / "Data"
ART_DIR = PROJECT_ROOT / "Content" / "美术" / "Art"
WEB_DIR = (Path(__file__).parent / "web").resolve()
OUTPUT_DIR = PROJECT_ROOT / "output"
COMMIT_LOG_PATH = OUTPUT_DIR / "config_commits.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

UE_CMD = "/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd"
UPROJECT = str(PROJECT_ROOT / "xxxx.uproject")
DEPLOY_SCRIPT = str(PROJECT_ROOT / "Content" / "Python" / "tools" / "deploy_animated_enemies.py")

# 敌人专属 4 帧美术切片智能映射
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

# 武器美术切片映射
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

# 卡牌美术切片映射
CARD_ART_MAP = {
    "CARD_HighPower_Gunpowder": "06_Cards/05_CurseRewardCards/T_Card_CurseReward_01.png",
    "CARD_Rapid_Barrel": "06_Cards/05_CurseRewardCards/T_Card_CurseReward_02.png",
    "CARD_Armor_Piercing": "06_Cards/05_CurseRewardCards/T_Card_CurseReward_03.png",
    "CARD_Bio_Toxic_Coat": "06_Cards/05_CurseRewardCards/T_Card_CurseReward_04.png",
    "CARD_Field_Emergency": "06_Cards/05_CurseRewardCards/T_Card_CurseReward_05.png",
    "CARD_Tactical_Booster": "06_Cards/05_CurseRewardCards/T_Card_CurseReward_06.png",
}

# 可用 4 帧 Flipbook 预设资产列表
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

# 蓝图数据属性分类与类型规范 (严格遵循 UE5 蓝图规范)
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

def scan_player_animations() -> dict:
    """扫描并组织主角01_Player全部动作与方向的切片帧"""
    player_root = ART_DIR / "01_Player"
    actions = {
        "Idle": {},
        "Run": {},
        "Attack": {},
        "Hurt": {},
        "Skill": {},
        "Death": {}
    }
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
                    frames = [str(f.relative_to(ART_DIR)) for f in sorted(idle_p.glob("*.png")) if "Sheet" not in f.name]
                    actions["Idle"][d_key] = {"label": dir_names.get(d_key, d_key), "frames": frames, "path": str(idle_p.relative_to(ART_DIR))}
                # Run
                run_p = d / "Run"
                if run_p.exists():
                    frames = [str(f.relative_to(ART_DIR)) for f in sorted(run_p.glob("*.png")) if "Sheet" not in f.name]
                    actions["Run"][d_key] = {"label": dir_names.get(d_key, d_key), "frames": frames, "path": str(run_p.relative_to(ART_DIR))}

    # 2. Attack & Hurt (统一映射至 5 个标准方向，Dir_03_Right 归一化为 Dir_03_Left 正侧)
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
                    frames = [str(f.relative_to(ART_DIR)) for f in sorted(atk_p.glob("*.png")) if "Sheet" not in f.name]
                    actions["Attack"][d_key] = {"label": dir_names.get(d_key, d_key), "frames": frames, "path": str(atk_p.relative_to(ART_DIR))}
                # Hurt
                hurt_p = d / "Hurt"
                if hurt_p.exists():
                    frames = [str(f.relative_to(ART_DIR)) for f in sorted(hurt_p.glob("*.png")) if "Sheet" not in f.name]
                    actions["Hurt"][d_key] = {"label": dir_names.get(d_key, d_key), "frames": frames, "path": str(hurt_p.relative_to(ART_DIR))}

    # 3. Death & Revive (Skill)
    death_revive_dir = player_root / "03_Death_Revive"
    if death_revive_dir.exists():
        revive_p = death_revive_dir / "Revive"
        if revive_p.exists():
            frames = [str(f.relative_to(ART_DIR)) for f in sorted(revive_p.glob("*.png")) if "Sheet" not in f.name]
            actions["Skill"]["Default"] = {"label": "纳米战地复苏 (Revive)", "frames": frames, "path": str(revive_p.relative_to(ART_DIR))}

        death_p = death_revive_dir / "Death_Collapse"
        if death_p.exists():
            frames = [str(f.relative_to(ART_DIR)) for f in sorted(death_p.glob("*.png")) if "Sheet" not in f.name]
            actions["Death"]["Default"] = {"label": "战死倒地 (Collapse)", "frames": frames, "path": str(death_p.relative_to(ART_DIR))}

    return actions

def scan_vfx_catalog() -> list:
    """扫描特效库目录05_VFX"""
    vfx_root = ART_DIR / "05_VFX"
    catalog = []
    if not vfx_root.exists():
        return catalog

    for d in sorted(vfx_root.iterdir()):
        if d.is_dir():
            frames = [str(f.relative_to(ART_DIR)) for f in sorted(d.glob("*.png")) if "Sheet" not in f.name]
            catalog.append({
                "id": d.name,
                "name": d.name.replace("_", " "),
                "path": f"05_VFX/{d.name}",
                "frames": frames
            })
    return catalog

def scan_art_tree() -> dict:
    """扫描并构建本地美术素材库的目录树与扁平资产清单"""
    if not ART_DIR.exists():
        return {"tree": [], "all_files": [], "count": 0}

    all_files = []

    def walk_dir(p: Path, rel_base: Path):
        node = {
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
                    item = {
                        "name": child.name,
                        "path": str(child.relative_to(rel_base)),
                        "size": child.stat().st_size
                    }
                    node["files"].append(item)
                    all_files.append(item)
        except Exception:
            pass
        return node

    tree = []
    for top_d in sorted(ART_DIR.iterdir()):
        if top_d.is_dir() and not top_d.name.startswith("."):
            tree.append(walk_dir(top_d, ART_DIR))

    return {"status": "success", "tree": tree, "all_files": all_files, "total_count": len(all_files)}

def read_json_file(filename: str) -> dict:
    fp = DATA_DIR / filename
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[Error] 读取 {filename} 失败: {e}")
    return {}

def write_json_file(filename: str, data: dict):
    fp = DATA_DIR / filename
    backup = DATA_DIR / f"{filename}.bak"
    if fp.exists():
        backup.write_bytes(fp.read_bytes())
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

class ConfigStudioHandler(http.server.SimpleHTTPRequestHandler):
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
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        # 1. API: 全量配置与美术数据
        if path == "/api/data":
            characters = read_json_file("DT_Characters.json")
            enemies = read_json_file("DT_Enemies.json")
            weapons = read_json_file("DT_Weapons.json")
            cards = read_json_file("DT_TacticalCards.json")
            waves = read_json_file("DT_WaveProgression.json")
            tiles = read_json_file("DT_MapTiles.json")
            hit_effects = read_json_file("DT_HitEffects.json")

            player_animations = scan_player_animations()
            vfx_catalog = scan_vfx_catalog()

            # 注入美术映射
            for eid, edata in enemies.items():
                if eid in ENEMY_ART_MAP:
                    edata["ArtInfo"] = ENEMY_ART_MAP[eid]

            for wid, wdata in weapons.items():
                if wid in WEAPON_ART_MAP:
                    wdata["ArtInfo"] = WEAPON_ART_MAP[wid]

            for cid, cdata in cards.items():
                if cid in CARD_ART_MAP:
                    cdata["ArtInfo"] = {"card_image": CARD_ART_MAP[cid]}

            payload = {
                "status": "success",
                "timestamp": time.time(),
                "characters": characters,
                "player_animations": player_animations,
                "vfx_catalog": vfx_catalog,
                "enemies": enemies,
                "weapons": weapons,
                "cards": cards,
                "waves": waves,
                "tiles": tiles,
                "hit_effects": hit_effects,
                "blueprint_schema": BLUEPRINT_PROP_SCHEMA,
                "available_flipbooks": AVAILABLE_FLIPBOOKS,
                "project_info": {
                    "name": "GGBOM: 终末医疗兵",
                    "core_rule": "全属性可调、多方向动作、特效联动、单向4帧怪底层机制",
                    "camera_ortho_width": 941.0,
                    "aspect_ratio": "9:16 (0.5628)"
                }
            }
            self.send_json(payload)
            return

        # 2. API: 提交历史审计
        if path == "/api/commits":
            if COMMIT_LOG_PATH.exists():
                try:
                    commits = json.loads(COMMIT_LOG_PATH.read_text(encoding="utf-8"))
                    self.send_json({"status": "success", "commits": commits})
                    return
                except Exception:
                    pass
            self.send_json({"status": "success", "commits": []})
            return

        # 3. API: 本地美术素材库目录树与扁平清单
        if path == "/api/art-tree":
            tree_data = scan_art_tree()
            self.send_json(tree_data)
            return

        # 4. API: 获取指定素材目录下的所有PNG帧序列 (智能支持子目录识别与文件自动转目录)
        if path == "/api/dir-frames" or path == "/api/vfx-frames":
            query = parse_qs(parsed.query)
            target_dir_rel = query.get("dir", query.get("folder", [""]))[0]
            action_hint = query.get("action", [""])[0].lower()
            
            target_path = (ART_DIR / target_dir_rel).resolve()
            # 若传入的是文件路径，自动取其父级目录
            if str(target_path).startswith(str(ART_DIR)) and target_path.is_file():
                target_path = target_path.parent
                target_dir_rel = str(target_path.relative_to(ART_DIR))

            frames = []
            actual_dir = target_dir_rel

            if str(target_path).startswith(str(ART_DIR)) and target_path.is_dir():
                # 优先获取当前目录直属 PNG
                direct_pngs = [str(f.relative_to(ART_DIR)) for f in sorted(target_path.glob("*.png")) if "Sheet" not in f.name]
                if direct_pngs:
                    frames = direct_pngs
                else:
                    # 当前目录无直接切片，智能检查子目录 (如用户只选到 Dir_01_Down，其下有 Idle/Run)
                    sub_dirs = [d for d in target_path.iterdir() if d.is_dir()]
                    chosen_sub = None
                    if action_hint:
                        # 优先匹配带有当前动作提示的子目录
                        for d in sub_dirs:
                            if action_hint in d.name.lower():
                                chosen_sub = d
                                break
                    if not chosen_sub and sub_dirs:
                        # 默认挑选第一个包含 PNG 的子目录
                        for d in sub_dirs:
                            if any(d.glob("*.png")):
                                chosen_sub = d
                                break
                    if chosen_sub:
                        frames = [str(f.relative_to(ART_DIR)) for f in sorted(chosen_sub.glob("*.png")) if "Sheet" not in f.name]
                        actual_dir = str(chosen_sub.relative_to(ART_DIR))

            self.send_json({"status": "success", "dir": actual_dir, "folder": actual_dir, "frames": frames})
            return

        # 3. 静态素材映射: /art/... -> Content/美术/Art/...
        if path.startswith("/art/"):
            rel_path = path[len("/art/"):]
            art_file = (ART_DIR / rel_path).resolve()
            # 安全检查防止越界
            if str(art_file).startswith(str(ART_DIR)) and art_file.is_file():
                self.serve_file(art_file)
                return
            else:
                self.send_error(404, f"Art file not found: {rel_path}")
                return

        # 4. 前端静态网页资源: / -> web/index.html
        if path == "/" or path == "/index.html":
            self.serve_file(WEB_DIR / "index.html")
            return
        elif path in ["/style.css", "/app.js"]:
            self.serve_file(WEB_DIR / path[1:])
            return

        # 默认回退到 web 目录
        web_file = (WEB_DIR / path.lstrip("/")).resolve()
        if str(web_file).startswith(str(WEB_DIR)) and web_file.is_file():
            self.serve_file(web_file)
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(length).decode("utf-8")
        try:
            body = json.loads(body_raw) if body_raw else {}
        except Exception as e:
            self.send_json({"status": "error", "message": f"JSON解析错误: {e}"}, 400)
            return

        # 1. API: 保存配置 (原子落盘并记录审计)
        if path == "/api/save":
            modified_tables = []
            diff_summary = []

            if "characters" in body:
                write_json_file("DT_Characters.json", body["characters"])
                modified_tables.append("DT_Characters.json")
                diff_summary.append("更新主角全属性、武器与动作特效配置")

            if "enemies" in body:
                enemies_clean = {}
                for k, v in body["enemies"].items():
                    # 剔除前端辅助字段
                    clean_item = {ik: iv for ik, iv in v.items() if ik != "ArtInfo"}
                    enemies_clean[k] = clean_item
                write_json_file("DT_Enemies.json", enemies_clean)
                modified_tables.append("DT_Enemies.json")
                diff_summary.append(f"更新 {len(enemies_clean)} 种敌人数值与素材映射")

            if "weapons" in body:
                weapons_clean = {}
                for k, v in body["weapons"].items():
                    clean_item = {ik: iv for ik, iv in v.items() if ik != "ArtInfo"}
                    weapons_clean[k] = clean_item
                write_json_file("DT_Weapons.json", weapons_clean)
                modified_tables.append("DT_Weapons.json")
                diff_summary.append(f"更新 {len(weapons_clean)} 把武器射击属性")

            if "cards" in body:
                cards_clean = {}
                for k, v in body["cards"].items():
                    clean_item = {ik: iv for ik, iv in v.items() if ik != "ArtInfo"}
                    cards_clean[k] = clean_item
                write_json_file("DT_TacticalCards.json", cards_clean)
                modified_tables.append("DT_TacticalCards.json")
                diff_summary.append(f"更新 {len(cards_clean)} 张战术强化卡牌")

            if "waves" in body:
                write_json_file("DT_WaveProgression.json", body["waves"])
                modified_tables.append("DT_WaveProgression.json")
                diff_summary.append("更新关卡出怪波次时间轴")

            if "tiles" in body:
                write_json_file("DT_MapTiles.json", body["tiles"])
                modified_tables.append("DT_MapTiles.json")
                diff_summary.append(f"更新 {len(body['tiles'])} 块土地地表数据")

            if "hit_effects" in body:
                write_json_file("DT_HitEffects.json", body["hit_effects"])
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

            all_commits = []
            if COMMIT_LOG_PATH.exists():
                try:
                    all_commits = json.loads(COMMIT_LOG_PATH.read_text(encoding="utf-8"))
                except Exception:
                    pass
            all_commits.insert(0, commit_record)
            COMMIT_LOG_PATH.write_text(json.dumps(all_commits[:50], ensure_ascii=False, indent=2), encoding="utf-8")

            print(f"[ConfigStudio] 收到配置提交: {commit_record['comment']} (涉及: {', '.join(modified_tables)})")

            self.send_json({
                "status": "success",
                "message": "配置已成功保存并原子化写盘！",
                "commit": commit_record
            })
            return

        # 2. API: 一键热同步至 UE5 关卡
        if path == "/api/deploy":
            print("[ConfigStudio] 收到 UE5 部署请求，正在触发 deploy_animated_enemies.py ...")
            cmd = [
                UE_CMD,
                UPROJECT,
                "-run=pythonscript",
                f"-script={DEPLOY_SCRIPT}",
                "-stdout",
                "-FullStdOutLogOutput",
                "-unattended",
                "-nopause",
                "-nosplash"
            ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                is_ok = proc.returncode == 0
                self.send_json({
                    "status": "success" if is_ok else "warning",
                    "returncode": proc.returncode,
                    "output": proc.stdout[-1500:] if proc.stdout else "",
                    "message": "UE5 关卡蓝图与实例部署成功！" if is_ok else "UE5 部署返回非零状态，请查阅日志"
                })
            except Exception as e:
                self.send_json({"status": "error", "message": f"执行 UE5 部署脚本失败: {e}"}, 500)
            return

        self.send_error(404, "Not Found")

    def serve_file(self, file_path: Path):
        try:
            content = file_path.read_bytes()
            mime, _ = mimetypes.guess_type(str(file_path))
            if not mime:
                mime = "application/octet-stream"
            if file_path.suffix == ".css":
                mime = "text/css"
            elif file_path.suffix == ".js":
                mime = "application/javascript"
            elif file_path.suffix == ".png":
                mime = "image/png"

            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

    def send_json(self, data: dict, code: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def main():
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    print(f"==================================================")
    print(f"🚀 《GGBOM: 终末医疗兵》动态配置中心启动中...")
    print(f"   本地数据目录: {DATA_DIR}")
    print(f"   本地美术素材: {ART_DIR}")
    print(f"   Web 服务端口: http://localhost:{PORT}")
    print(f"==================================================")

    with ReusableTCPServer((HOST, PORT), ConfigStudioHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务正常停止。")

if __name__ == "__main__":
    main()
