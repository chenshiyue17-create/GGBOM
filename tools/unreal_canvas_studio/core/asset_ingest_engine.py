# -*- coding: utf-8 -*-
"""
Unreal Canvas Studio - 通用资产安全摄取、自动备份与解耦引擎 (Asset Ingestion & Decoupling Engine)
核心职责：
1. 接收任意外部拖入的图片流，自动存入当前 UE5 工程内部标准目录，彻底解除对外部原始路径的绑定；
2. 自动在工程内建立 .source_backup 原始存档仓库，保留带时间戳与数字指纹的生肉备份，永不怕素材丢失；
3. 智能执行去黑底、透明通道规整、边界对齐等预处理流水线；
4. 输出干净的项目内相对路径 (01_Player/...) 与 UE 虚幻资产引用路径 (/Game/...)。
"""

import os
import io
import time
import hashlib
import shutil
from pathlib import Path
from PIL import Image

class AssetIngestEngine:
    def __init__(self, project_adapter):
        self.adapter = project_adapter

    def get_art_root(self) -> Path:
        """获取首选美术素材存储根目录"""
        if self.adapter and self.adapter.art_dirs:
            return Path(self.adapter.art_dirs[0])
        if self.adapter and self.adapter.content_dir:
            cand = self.adapter.content_dir / "美术" / "Art"
            cand.mkdir(parents=True, exist_ok=True)
            return cand
        return Path("Content/Art")

    def ingest_image_asset(self, file_bytes: bytes, filename: str, category: str = "general", 
                           entity_id: str = "", auto_remove_black: bool = False, 
                           auto_trim: bool = False, target_dir_override: str = None) -> dict:
        """
        全生命周期安全摄取图像资产
        :param file_bytes: 二进制图片流
        :param filename: 原始文件名
        :param category: 资产分类 (avatar, weapon, vfx, enemy, card, ui, tile, general)
        :param entity_id: 关联实体 ID (如 Player_Medic, WPN_Rifle_Standard, 11_Hit_Kinetic)
        :param auto_remove_black: 是否自动执行去黑底转透明 PNG
        :param auto_trim: 是否自动裁剪外围全透明空白
        :param target_dir_override: 显式覆盖目标存储目录
        :return: 摄取结果字典
        """
        art_root = self.get_art_root()
        art_root.mkdir(parents=True, exist_ok=True)

        # 1. 计算文件哈希指纹防冲突与追溯
        sha = hashlib.sha256(file_bytes).hexdigest()
        sha_short = sha[:8]
        clean_ext = os.path.splitext(filename)[1].lower() or ".png"
        base_name = os.path.splitext(filename)[0]

        # 2. 原始文件自动持久化备份 (Raw Source Archive)
        backup_root = art_root / ".source_backup" / category
        backup_root.mkdir(parents=True, exist_ok=True)
        timestamp_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        safe_orig_filename = f"{timestamp_str}_{sha_short}_{filename}"
        backup_file = backup_root / safe_orig_filename
        backup_file.write_bytes(file_bytes)
        backup_rel = str(backup_file.relative_to(art_root))

        # 3. 规划项目内部标准存放路径与规范化命名
        clean_base = base_name.replace(" ", "_")
        if target_dir_override:
            dest_dir = art_root / target_dir_override
            dest_filename = f"{clean_base}.png" if clean_base.startswith("T_") else f"T_{clean_base}.png"
        elif category == "avatar":
            dest_dir = art_root / "01_Player" / "Avatar"
            entity_tag = entity_id or "Player"
            if clean_base.lower() in ("avatar", "touxiang", "icon", "head", "player"):
                dest_filename = f"T_{entity_tag}_Avatar.png"
            elif clean_base.startswith("T_"):
                dest_filename = f"{clean_base}.png"
            else:
                dest_filename = f"T_{entity_tag}_{clean_base}.png"
        elif category.startswith("weapon"):
            w_dir_name = entity_id or "Custom_Weapons"
            dest_dir = art_root / "03_Weapons" / w_dir_name
            dest_filename = f"{clean_base}.png" if clean_base.startswith("T_") else f"T_{clean_base}.png"
        elif category == "vfx":
            v_dir_name = entity_id or f"Custom_VFX_{timestamp_str}"
            dest_dir = art_root / "05_VFX" / v_dir_name
            dest_filename = f"{clean_base}.png" if clean_base.startswith("T_") else f"T_{clean_base}.png"
        elif category == "enemy":
            e_dir_name = entity_id or "Custom_Enemy"
            dest_dir = art_root / "02_Enemies" / e_dir_name
            dest_filename = f"{clean_base}.png" if clean_base.startswith("T_") else f"T_{clean_base}.png"
        elif category == "pipeline":
            dest_dir = art_root / "04_Props" / "Raw_Imports"
            dest_filename = f"{clean_base}.png" if clean_base.startswith("T_") else f"T_{clean_base}.png"
        elif category == "card":
            dest_dir = art_root / "06_Cards"
            dest_filename = f"{clean_base}.png" if clean_base.startswith("T_") else f"T_Card_{clean_base}.png"
        elif category == "ui":
            dest_dir = art_root / "07_UI"
            dest_filename = f"{clean_base}.png" if clean_base.startswith("T_") else f"T_UI_{clean_base}.png"
        elif category == "tile":
            dest_dir = art_root / "08_Maps"
            dest_filename = f"{clean_base}.png" if clean_base.startswith("T_") else f"T_MapTile_{clean_base}.png"
        else:
            dest_dir = art_root / "Imported" / category
            dest_filename = f"T_{clean_base}_{sha_short}.png"

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / dest_filename

        # 4. 图像智能预处理 (PIL)
        try:
            image = Image.open(io.BytesIO(file_bytes)).convert("RGBA")
        except Exception as e:
            # 容错：无法解析为图片则直接写入二进制
            dest_file.write_bytes(file_bytes)
            project_rel = str(dest_file.relative_to(art_root))
            return {
                "status": "success",
                "project_rel_path": project_rel,
                "game_path": self.adapter.local_to_game_path(str(dest_file)) if self.adapter else project_rel,
                "backup_rel_path": backup_rel,
                "web_url": f"/art/{project_rel}",
                "filename": dest_filename,
                "warning": f"图片解码异常，已原始转存: {e}"
            }

        # 自动去黑底 (可选)
        if auto_remove_black:
            datas = image.getdata()
            new_data = []
            for item in datas:
                # 接近黑色的像素 (R<25, G<25, B<25) 转为全透明
                if item[0] < 25 and item[1] < 25 and item[2] < 25:
                    new_data.append((0, 0, 0, 0))
                else:
                    new_data.append(item)
            image.putdata(new_data)

        # 自动边界裁剪 (可选)
        if auto_trim:
            bbox = image.getbbox()
            if bbox:
                image = image.crop(bbox)

        # 5. 保存为标准优化 PNG 格式存入项目
        image.save(dest_file, format="PNG", optimize=True)

        project_rel = str(dest_file.relative_to(art_root))
        game_path = self.adapter.local_to_game_path(str(dest_file)) if self.adapter else f"/Game/Art/{project_rel}"

        return {
            "status": "success",
            "project_rel_path": project_rel,
            "game_path": game_path,
            "backup_rel_path": backup_rel,
            "web_url": f"/art/{project_rel}",
            "abs_path": str(dest_file),
            "filename": dest_filename,
            "size": [image.width, image.height],
            "file_size": dest_file.stat().st_size,
            "sha256": sha,
            "message": f"素材已安全存入项目内部 [{project_rel}]，原始文件已建立存档备份，完全解耦外部原始路径！"
        }
