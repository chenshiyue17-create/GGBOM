# -*- coding: utf-8 -*-
"""
Unreal Canvas Studio - 智能美术素材全流水线引擎 (Asset Pipeline Engine)
功能：源素材清洗、去黑底/Alpha处理、体量锁定检查、网格切片、Pivot轴心标定与5方向Flipbook批量合成。
"""

import os
import urllib.parse
from pathlib import Path
from PIL import Image, ImageOps

class AssetPipelineEngine:
    def __init__(self, project_adapter):
        self.adapter = project_adapter

    def remove_black_background(self, img_path, threshold=25, output_path=None):
        """智能去除黑底背景，转为标准 RGBA 透明图"""
        img = Image.open(img_path).convert("RGBA")
        datas = img.getdata()
        new_data = []
        for item in datas:
            # item is (R, G, B, A)
            if item[0] < threshold and item[1] < threshold and item[2] < threshold:
                new_data.append((0, 0, 0, 0)) # 全透明
            else:
                new_data.append(item)
        img.putdata(new_data)
        
        target = output_path or img_path
        img.save(target, "PNG")
        return str(target)

    def check_character_standing_height(self, img_path, expected_height=430, tolerance=0.08):
        """检测角色切片有效像素高度，防止倒地动作或新帧尺寸缩水"""
        img = Image.open(img_path).convert("RGBA")
        bbox = img.getbbox()
        if not bbox:
            return {"pass": False, "reason": "全透明空图", "actualHeight": 0}
        
        actual_height = bbox[3] - bbox[1]
        diff_ratio = abs(actual_height - expected_height) / expected_height
        is_pass = diff_ratio <= tolerance

        return {
            "pass": is_pass,
            "actualHeight": actual_height,
            "expectedHeight": expected_height,
            "diffPercent": round(diff_ratio * 100, 1),
            "bbox": bbox,
            "status": "PASS" if is_pass else "WARNING_SIZE_MISMATCH"
        }

    def detect_smart_sprites(self, img_path, min_area=3000, padding=4):
        """
        使用 OpenCV 智能识别图片中的独立精灵岛屿 (Connected Contours Extraction)
        自动定位每个精灵的最紧凑外接包围盒 (Tight Bounding Box) 并按视觉阅读顺序排序
        """
        import cv2
        import numpy as np

        img_bgr = cv2.imread(str(img_path), cv2.IMREAD_UNCHANGED)
        if img_bgr is None:
            return {"status": "error", "error": f"无法读取图片: {img_path}"}

        h, w = img_bgr.shape[:2]
        use_alpha = False
        if len(img_bgr.shape) == 3 and img_bgr.shape[2] == 4:
            alpha = img_bgr[:, :, 3]
            # 检查是否有实际透明像素 (透明像素占比 > 1% 或 最小值 < 200)
            transparent_pixels = np.count_nonzero(alpha < 200)
            if transparent_pixels > (h * w * 0.01):
                use_alpha = True

        if use_alpha:
            _, thresh = cv2.threshold(img_bgr[:, :, 3], 15, 255, cv2.THRESH_BINARY)
        else:
            # 纯黑底/近黑底前景提取 (容差阈值 25)
            gray = cv2.cvtColor(img_bgr[:, :, :3], cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)

        # 轻度形态学闭运算，将同一角色的枪口火光、碎屑等微小分离块黏合为一个主体
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        raw_boxes = []
        for cnt in contours:
            bx, by, bw, bh = cv2.boundingRect(cnt)
            if bw * bh >= min_area and bw >= 20 and bh >= 20:
                # 适当扩充 padding
                x1 = max(0, bx - padding)
                y1 = max(0, by - padding)
                x2 = min(w, bx + bw + padding)
                y2 = min(h, by + bh + padding)
                raw_boxes.append({
                    "x": int(x1),
                    "y": int(y1),
                    "w": int(x2 - x1),
                    "h": int(y2 - y1)
                })

        # 智能网格化分行排序 (根据 Y 坐标聚类排序，确保从左到右、从上到下)
        if raw_boxes:
            # 估计平均行高
            avg_h = sum(b["h"] for b in raw_boxes) / len(raw_boxes)
            row_tolerance = avg_h * 0.45
            raw_boxes.sort(key=lambda b: (round(b["y"] / max(1, row_tolerance)), b["x"]))

        # 编号
        for idx, box in enumerate(raw_boxes):
            box["index"] = idx

        return {
            "status": "success",
            "source": str(img_path),
            "imageSize": [w, h],
            "totalDetected": len(raw_boxes),
            "count": len(raw_boxes),
            "boxes": raw_boxes,
            "sprites": raw_boxes
        }

    def slice_custom_lines(self, img_path, h_lines, v_lines, output_dir=None, prefix=None):
        """
        根据用户自由拖动的水平线与垂直线像素坐标列表进行任意网格切割
        :param h_lines: 水平分割线 Y 坐标列表 [474, ...]
        :param v_lines: 垂直分割线 X 坐标列表 [414, 828, ...]
        """
        img = Image.open(img_path).convert("RGBA")
        w, h = img.size

        # 补全起始与终止边界，去重并排序
        all_y = sorted(list(set([0] + [int(y) for y in h_lines if 0 < int(y) < h] + [h])))
        all_x = sorted(list(set([0] + [int(x) for x in v_lines if 0 < int(x) < w] + [w])))

        out_path = Path(output_dir) if output_dir else Path(img_path).parent / "Slices"
        out_path.mkdir(parents=True, exist_ok=True)
        stem = prefix or Path(img_path).stem

        slices = []
        idx = 0
        for r in range(len(all_y) - 1):
            y1, y2 = all_y[r], all_y[r + 1]
            for c in range(len(all_x) - 1):
                x1, x2 = all_x[c], all_x[c + 1]
                box = (x1, y1, x2, y2)
                cell_img = img.crop(box)
                frame_name = f"{stem}_Frame_{idx:02d}.png"
                frame_file = out_path / frame_name
                cell_img.save(frame_file, "PNG")

                slices.append({
                    "frameIndex": idx,
                    "row": r,
                    "col": c,
                    "box": [x1, y1, x2 - x1, y2 - y1],
                    "filename": frame_name,
                    "path": str(frame_file),
                    "url": f"/asset-view?path={urllib.parse.quote(str(frame_file))}",
                    "size": [x2 - x1, y2 - y1]
                })
                idx += 1

        return {
            "source": str(img_path),
            "totalFrames": len(slices),
            "hLines": all_y[1:-1],
            "vLines": all_x[1:-1],
            "slices": slices
        }

    def slice_boxes(self, img_path, boxes, output_dir=None, prefix=None):
        """
        根据指定的任意矩形框列表 [{x, y, w, h}] 进行裁切
        """
        img = Image.open(img_path).convert("RGBA")
        w, h = img.size

        out_path = Path(output_dir) if output_dir else Path(img_path).parent / "Slices"
        out_path.mkdir(parents=True, exist_ok=True)
        stem = prefix or Path(img_path).stem

        slices = []
        for idx, b in enumerate(boxes):
            x1 = max(0, int(b.get("x", 0)))
            y1 = max(0, int(b.get("y", 0)))
            bw = int(b.get("w", 64))
            bh = int(b.get("h", 64))
            x2 = min(w, x1 + bw)
            y2 = min(h, y1 + bh)

            cell_img = img.crop((x1, y1, x2, y2))
            frame_name = f"{stem}_Frame_{idx:02d}.png"
            frame_file = out_path / frame_name
            cell_img.save(frame_file, "PNG")

            slices.append({
                "frameIndex": idx,
                "box": [x1, y1, x2 - x1, y2 - y1],
                "filename": frame_name,
                "path": str(frame_file),
                "url": f"/asset-view?path={urllib.parse.quote(str(frame_file))}",
                "size": [x2 - x1, y2 - y1]
            })

        return {
            "source": str(img_path),
            "totalFrames": len(slices),
            "slices": slices
        }

    def export_slices_to_project(self, img_path, boxes, category="01_Player", 
                                sub_dir="", prefix="", start_index=1, 
                                auto_trim=False, auto_remove_black=False):
        """
        全自动化：将切片批量规范命名存入项目目标目录，并持久化备份生肉原图
        :param img_path: 源图路径
        :param boxes: 裁切矩形框列表 [{x, y, w, h}]
        :param category: 目标顶级分类 (01_Player, 02_Enemies, 03_Weapons, 05_VFX, 07_UI, ...)
        :param sub_dir: 子目录 (例如 Actions/Attack_Run)
        :param prefix: 命名模板前缀 (例如 T_Player_Attack_Run)
        :param start_index: 起始帧序号 (默认 1)
        """
        import hashlib
        import time

        art_root = Path(self.adapter.art_dirs[0]) if self.adapter and self.adapter.art_dirs else Path("Content/美术/Art")
        img = Image.open(img_path).convert("RGBA")
        img_w, img_h = img.size

        # 1. 规范化前缀与目标存储路径
        stem = Path(img_path).stem
        clean_prefix = prefix.strip() if prefix else stem
        if not clean_prefix.startswith("T_"):
            clean_prefix = f"T_{clean_prefix}"

        # 目标存放目录
        clean_sub = sub_dir.strip().replace("\\", "/").strip("/")
        if clean_sub:
            dest_dir = art_root / category / clean_sub
        else:
            dest_dir = art_root / category

        dest_dir.mkdir(parents=True, exist_ok=True)

        # 2. 持久化安全生肉备份仓库
        raw_bytes = Path(img_path).read_bytes()
        sha = hashlib.sha256(raw_bytes).hexdigest()[:8]
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_dir = art_root / ".source_backup" / "pipeline" / f"{timestamp}_{sha}_{clean_prefix}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        # 备份母图
        (backup_dir / Path(img_path).name).write_bytes(raw_bytes)

        exported_files = []
        for idx, b in enumerate(boxes):
            frame_num = start_index + idx
            x1 = max(0, int(b.get("x", 0)))
            y1 = max(0, int(b.get("y", 0)))
            bw = int(b.get("w", 64))
            bh = int(b.get("h", 64))
            x2 = min(img_w, x1 + bw)
            y2 = min(img_h, y1 + bh)

            cell_img = img.crop((x1, y1, x2, y2))

            # 去黑底 (如果指定或切片完全不透明且四角为黑色)
            should_remove_black = auto_remove_black
            if not should_remove_black:
                alpha_extrema = cell_img.getextrema()[3]
                if alpha_extrema[0] == 255: # 无透明通道
                    # 检查角像素是否为近黑色
                    corner = cell_img.getpixel((0, 0))
                    if corner[0] < 30 and corner[1] < 30 and corner[2] < 30:
                        should_remove_black = True

            if should_remove_black:
                datas = cell_img.getdata()
                new_datas = []
                for p in datas:
                    if p[0] < 25 and p[1] < 25 and p[2] < 25:
                        new_datas.append((0, 0, 0, 0))
                    else:
                        new_datas.append(p)
                cell_img.putdata(new_datas)

            # 透明边界裁剪 (可选)
            if auto_trim:
                bbox = cell_img.getbbox()
                if bbox:
                    cell_img = cell_img.crop(bbox)

            out_filename = f"{clean_prefix}_{frame_num:02d}.png"
            dest_file = dest_dir / out_filename
            cell_img.save(dest_file, "PNG", optimize=True)

            # 同时在备份仓库中存一份切片产物
            cell_img.save(backup_dir / out_filename, "PNG")

            rel_path = str(dest_file.relative_to(art_root))
            game_path = self.adapter.local_to_game_path(str(dest_file)) if self.adapter else f"/Game/Art/{rel_path}"

            exported_files.append({
                "frameIndex": idx,
                "frameNumber": frame_num,
                "filename": out_filename,
                "absPath": str(dest_file),
                "projectRelPath": rel_path,
                "gamePath": game_path,
                "url": f"/art/{urllib.parse.quote(rel_path)}",
                "size": [cell_img.width, cell_img.height]
            })

        return {
            "status": "success",
            "category": category,
            "targetDir": str(dest_dir.relative_to(art_root)),
            "prefix": clean_prefix,
            "totalExported": len(exported_files),
            "backupDir": str(backup_dir.relative_to(art_root)),
            "exportedFiles": exported_files,
            "message": f"🎉 成功将 {len(exported_files)} 帧切片规范存入工程目录 [{dest_dir.relative_to(art_root)}] 并建立完整生肉备份！"
        }

    def export_multi_actions_to_project(self, img_path, action_groups, base_category="01_Player/Actions",
                                       auto_trim=True, auto_remove_black=False):
        """
        批量导出多动作组（一张图内包含多个动作，如第1行动作Attack、第2行动作Run）
        :param img_path: 源图路径
        :param action_groups: 动作组列表 [
            {
                "name": "Attack",
                "category": "01_Player/Actions", # 可选
                "sub_dir": "Attack",
                "prefix": "T_Player_Attack",
                "start_index": 1,
                "boxes": [{"x": ..., "y": ..., "w": ..., "h": ...}]
            }, ...
        ]
        :param base_category: 默认基准分类目录
        """
        import hashlib
        import time

        art_root = Path(self.adapter.art_dirs[0]) if self.adapter and self.adapter.art_dirs else Path("Content/美术/Art")
        img = Image.open(img_path).convert("RGBA")
        img_w, img_h = img.size

        # 1. 统一备份母图
        raw_bytes = Path(img_path).read_bytes()
        sha = hashlib.sha256(raw_bytes).hexdigest()[:8]
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        stem = Path(img_path).stem
        backup_dir = art_root / ".source_backup" / "pipeline" / f"{timestamp}_{sha}_{stem}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        (backup_dir / Path(img_path).name).write_bytes(raw_bytes)

        all_exported = []
        action_summaries = []

        # 2. 依次导出各个动作组
        for grp in action_groups:
            grp_name = grp.get("name", "Action")
            category = grp.get("category", base_category).strip("/")
            sub_dir = grp.get("sub_dir", grp_name).strip("/").replace("\\", "/")
            prefix = grp.get("prefix", f"T_{grp_name}").strip()
            if not prefix.startswith("T_"):
                prefix = f"T_{prefix}"
            start_index = int(grp.get("start_index", 1))
            boxes = grp.get("boxes", [])

            dest_dir = art_root / category / sub_dir if sub_dir else art_root / category
            dest_dir.mkdir(parents=True, exist_ok=True)

            grp_files = []
            for idx, b in enumerate(boxes):
                frame_num = start_index + idx
                x1 = max(0, int(b.get("x", 0)))
                y1 = max(0, int(b.get("y", 0)))
                bw = int(b.get("w", 64))
                bh = int(b.get("h", 64))
                x2 = min(img_w, x1 + bw)
                y2 = min(img_h, y1 + bh)

                cell_img = img.crop((x1, y1, x2, y2))

                # 自适应去黑底
                should_remove_black = auto_remove_black
                if not should_remove_black:
                    alpha_extrema = cell_img.getextrema()[3]
                    if alpha_extrema[0] == 255:
                        corner = cell_img.getpixel((0, 0))
                        if corner[0] < 30 and corner[1] < 30 and corner[2] < 30:
                            should_remove_black = True

                if should_remove_black:
                    datas = cell_img.getdata()
                    new_datas = []
                    for p in datas:
                        if p[0] < 25 and p[1] < 25 and p[2] < 25:
                            new_datas.append((0, 0, 0, 0))
                        else:
                            new_datas.append(p)
                    cell_img.putdata(new_datas)

                # 边缘透明留白裁剪
                if auto_trim:
                    bbox = cell_img.getbbox()
                    if bbox:
                        cell_img = cell_img.crop(bbox)

                out_filename = f"{prefix}_{frame_num:02d}.png"
                dest_file = dest_dir / out_filename
                cell_img.save(dest_file, "PNG", optimize=True)
                # 备份切片
                cell_img.save(backup_dir / out_filename, "PNG")

                rel_p = str(dest_file.relative_to(art_root))
                game_p = f"/Game/美术/Art/{rel_p.replace(chr(92), '/')[:-4]}.{dest_file.stem}"
                grp_files.append({
                    "action": grp_name,
                    "frameIndex": idx,
                    "frameNumber": frame_num,
                    "filename": out_filename,
                    "absPath": str(dest_file),
                    "projectRelPath": rel_p,
                    "gamePath": game_p,
                    "url": f"/art/{rel_p.replace(chr(92), '/')}",
                    "size": [cell_img.width, cell_img.height]
                })

            all_exported.extend(grp_files)
            action_summaries.append(f"【{grp_name}】{len(grp_files)}帧 -> {category}/{sub_dir}")

        return {
            "status": "success",
            "totalActions": len(action_groups),
            "totalExported": len(all_exported),
            "actionSummaries": action_summaries,
            "backupDir": str(backup_dir.relative_to(art_root)),
            "exportedFiles": all_exported,
            "message": f"🎉 成功批量导出 {len(action_groups)} 个动作（共 {len(all_exported)} 帧切片）存入项目各自子目录，已建立安全生肉备份！"
        }

    def slice_grid(self, img_path, rows=2, cols=4, output_dir=None, prefix=None):
        """标准网格切片 (例如 1792x1024 2x4 -> 8张 448x512)"""
        img = Image.open(img_path).convert("RGBA")
        w, h = img.size
        cell_w = w // cols
        cell_h = h // rows

        h_lines = [r * cell_h for r in range(1, rows)]
        v_lines = [c * cell_w for c in range(1, cols)]
        return self.slice_custom_lines(img_path, h_lines, v_lines, output_dir, prefix)

    def generate_paper2d_flipbook_manifest(self, character_name, anim_slices_dict, default_fps=8.0):
        """
        生成 UE5 Paper2D 5 方向动作 Flipbook 规约字典
        5核心方向: Dir_01_Down, Dir_02_DownLeft, Dir_03_Left, Dir_04_UpLeft, Dir_05_Up
        右侧 3 方向由 FlipX 自动镜像
        """
        manifest = {
            "character": character_name,
            "defaultFps": default_fps,
            "fiveDirections": [
                {"key": "Dir_01_Down", "label": "正下 (Down 270°)", "mirror": False},
                {"key": "Dir_02_DownLeft", "label": "左下 (DownLeft 225°)", "mirror": False},
                {"key": "Dir_03_Left", "label": "正侧 (Side 180°)", "mirror": False},
                {"key": "Dir_04_UpLeft", "label": "左上 (UpLeft 135°)", "mirror": False},
                {"key": "Dir_05_Up", "label": "正上 (Up 90°)", "mirror": False}
            ],
            "mirroredDirections": [
                {"key": "Dir_02_DownRight", "label": "右下 (DownRight 315°)", "source": "Dir_02_DownLeft", "flipX": True},
                {"key": "Dir_03_Right", "label": "正右 (Right 0°)", "source": "Dir_03_Left", "flipX": True},
                {"key": "Dir_04_UpRight", "label": "右上 (UpRight 45°)", "source": "Dir_04_UpLeft", "flipX": True}
            ],
            "actions": {}
        }
        for act, frames in anim_slices_dict.items():
            fps = 6.0 if act == "Idle" else (10.0 if act == "Run" else 12.0)
            manifest["actions"][act] = {
                "fps": fps,
                "frames": frames,
                "frameCount": len(frames)
            }
        return manifest
