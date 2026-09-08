# -*- coding: utf-8 -*-
"""
Unreal Canvas Studio - 通用 UE 工程适配器 (Project Adapter)
功能：解耦具体项目硬编码，自适应探测与挂载任意 UE5 工程，定位 Content、Data、Art、UI 资产。
"""

import os
import glob
import json
from pathlib import Path

class UEProjectAdapter:
    def __init__(self, project_path=None):
        self.project_path = None
        self.content_dir = None
        self.data_dir = None
        self.art_dirs = []
        self.ui_dir = None
        self.config_dir = None
        self.uproject_file = None
        self.project_name = "Default Project"
        
        if project_path:
            self.mount(project_path)

    def mount(self, path_str):
        """挂载指定 UE 工程路径"""
        p = Path(path_str).resolve()
        if not p.exists():
            raise FileNotFoundError(f"项目路径不存在: {path_str}")

        # 如果传入的是 Content 目录
        if p.name.lower() == "content":
            self.content_dir = p
            self.project_path = p.parent
        # 如果传入的是工程根目录 (包含 Content 文件夹)
        elif (p / "Content").exists():
            self.project_path = p
            self.content_dir = p / "Content"
        # 兼容当前 GGBOM 嵌套结构 (例如 GGBOM/xxxx)
        elif (p / "xxxx" / "Content").exists():
            self.project_path = p / "xxxx"
            self.content_dir = self.project_path / "Content"
        else:
            # 搜索任意子目录下的 Content 文件夹
            found = list(p.glob("**/Content"))
            if found:
                self.content_dir = found[0]
                self.project_path = self.content_dir.parent
            else:
                # 容错：直接将当前路径作为虚拟 Content 根
                self.project_path = p
                self.content_dir = p

        # 定位 .uproject 文件
        uprojects = list(self.project_path.glob("*.uproject"))
        if uprojects:
            self.uproject_file = uprojects[0]
            self.project_name = self.uproject_file.stem
        else:
            self.project_name = self.project_path.name

        # 定位数据表目录 (Data / DataTables)
        candidates_data = [
            self.content_dir / "Data",
            self.content_dir / "DataTables",
            self.content_dir / "Blueprints" / "Data",
        ]
        self.data_dir = None
        for cd in candidates_data:
            if cd.exists():
                self.data_dir = cd
                break
        if not self.data_dir:
            self.data_dir = self.content_dir / "Data"
            self.data_dir.mkdir(parents=True, exist_ok=True)

        # 定位美术素材目录 (美术/Art / 美术 / Art / Textures / Sprites)
        self.art_dirs = []
        possible_arts = ["美术/Art", "美术", "Art", "Asset/Art", "Textures", "Sprites"]
        for pa in possible_arts:
            candidate = self.content_dir / pa
            if candidate.exists() and candidate not in self.art_dirs:
                self.art_dirs.append(candidate)
        if not self.art_dirs:
            self.art_dirs = [self.content_dir]

        # 定位 UI 目录
        self.ui_dir = self.content_dir / "UI"
        self.ui_dir.mkdir(parents=True, exist_ok=True)

        # 定位 Config 目录
        self.config_dir = self.project_path / "Config"

        print(f"✅ [ProjectAdapter] 已成功挂载 UE 工程: {self.project_name}")
        print(f"    - 工程根目录: {self.project_path}")
        print(f"    - Content: {self.content_dir}")
        print(f"    - 数据表 (Data): {self.data_dir}")
        print(f"    - 美术素材 (Art): {[str(d) for d in self.art_dirs]}")

        return self.get_project_summary()

    def get_project_summary(self):
        """返回项目当前概览"""
        return {
            "projectName": self.project_name,
            "projectPath": str(self.project_path),
            "contentDir": str(self.content_dir),
            "dataDir": str(self.data_dir),
            "artDirs": [str(d) for d in self.art_dirs],
            "uiDir": str(self.ui_dir),
            "tables": self.list_datatables(),
        }

    def list_datatables(self):
        """扫描并返回所有可用的 DataTable (JSON / CSV)"""
        tables = []
        if not self.data_dir or not self.data_dir.exists():
            return tables

        for ext in ["*.json", "*.csv"]:
            for f in sorted(self.data_dir.glob(ext)):
                if not f.name.endswith(".bak") and not f.name.endswith(".tmp"):
                    tables.append({
                        "filename": f.name,
                        "stem": f.stem,
                        "path": str(f),
                        "format": f.suffix.replace(".", "").lower(),
                        "sizeBytes": f.stat().st_size
                    })
        return tables

    def resolve_asset_path(self, virtual_ue_path):
        """将 /Game/... 虚拟资产路径转换为本地物理绝对路径"""
        if not virtual_ue_path:
            return None
        clean_path = virtual_ue_path.split(".")[0]
        if clean_path.startswith("/Game/"):
            rel = clean_path[len("/Game/"):]
            candidate = self.content_dir / rel
            for ext in [".png", ".uasset", ".jpg"]:
                p = candidate.with_suffix(ext)
                if p.exists():
                    return str(p)
                p2 = candidate.parent / (candidate.name + ext)
                if p2.exists():
                    return str(p2)
        return None

    def local_to_game_path(self, local_path):
        """将本地磁盘文件路径转换为 UE5 /Game/... 虚拟路径"""
        try:
            rel = Path(local_path).resolve().relative_to(self.content_dir.resolve())
            stem = rel.stem
            ue_path = f"/Game/{rel.parent.as_posix()}/{stem}.{stem}"
            return ue_path.replace("//", "/")
        except Exception:
            return local_path
