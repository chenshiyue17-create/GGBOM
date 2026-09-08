# -*- coding: utf-8 -*-
"""
Unreal Canvas Studio - 动态自定义属性系统引擎 (Property Engine)
功能：管理 6 大类属性定义（数值/贴图/动画/视听/几何/逻辑），生成 Schema，支持单对象特有与全表推广。
"""

import json
from pathlib import Path

# 支持的 6 大类属性类型字典
SUPPORTED_TYPES = {
    # 1. 数值类
    "float": {"label": "浮点数 (Float)", "category": "数值", "default": 0.0, "widget": "number-step"},
    "int": {"label": "整数 (Integer)", "category": "数值", "default": 0, "widget": "number-int"},
    "percent": {"label": "百分比 (Percent)", "category": "数值", "default": 0.0, "widget": "slider-percent"},
    
    # 2. 美术与贴图
    "texture": {"label": "贴图资产 (Texture2D)", "category": "美术", "default": "", "widget": "asset-texture"},
    "sprite": {"label": "精灵切片 (PaperSprite)", "category": "美术", "default": "", "widget": "asset-sprite"},
    "icon": {"label": "UI卡牌大图标 (Icon)", "category": "美术", "default": "", "widget": "asset-icon"},

    # 3. 动画与序列
    "flipbook": {"label": "动画序列 (PaperFlipbook)", "category": "动画", "default": "", "widget": "asset-flipbook"},
    "anim_dir": {"label": "动作切片目录 (Anim Folder)", "category": "动画", "default": "", "widget": "asset-anim-dir"},

    # 4. 视听与物理
    "vfx": {"label": "特效资产 (Niagara/VFX)", "category": "视听物理", "default": "", "widget": "asset-vfx"},
    "sound": {"label": "音效资产 (SoundBase)", "category": "视听物理", "default": "", "widget": "asset-sound"},
    "capsule": {"label": "碰撞胶囊体 (Capsule R/H)", "category": "视听物理", "default": {"radius": 16, "height": 28}, "widget": "struct-capsule"},

    # 5. 逻辑与枚举
    "bool": {"label": "布尔开关 (Boolean)", "category": "逻辑", "default": False, "widget": "switch-bool"},
    "enum": {"label": "下拉枚举 (Enum)", "category": "逻辑", "default": "", "options": [], "widget": "select-enum"},
    "string": {"label": "文本字符串 (String)", "category": "逻辑", "default": "", "widget": "input-string"},

    # 6. 空间与色彩
    "vector2d": {"label": "二维挂点偏移 (Vector2D)", "category": "空间色彩", "default": {"x": 0.0, "y": 0.0}, "widget": "struct-vec2"},
    "color": {"label": "线性颜色 (LinearColor)", "category": "空间色彩", "default": "#ffffff", "widget": "color-picker"},
}

class PropertyEngine:
    def __init__(self, project_adapter):
        self.adapter = project_adapter
        self.schema_file = None
        if self.adapter.data_dir:
            self.schema_file = self.adapter.data_dir / "CustomPropertiesSchema.json"

    def get_custom_schema(self, table_name=None):
        """获取当前工程的自定义属性 Schema"""
        schema = {}
        if self.schema_file and self.schema_file.exists():
            try:
                with open(self.schema_file, "r", encoding="utf-8") as f:
                    schema = json.load(f)
            except Exception:
                schema = {}
        if table_name:
            return schema.get(table_name, {})
        return schema

    def register_property(self, table_name, prop_key, prop_def):
        """
        向指定数据表注册新自定义属性
        prop_def: {
            "displayName": "暴击伤害倍数",
            "type": "float",
            "category": "进阶战斗",
            "defaultValue": 2.0,
            "scope": "table" | "instance",
            "tooltip": "攻击暴击时造成的倍率"
        }
        """
        schema = self.get_custom_schema()
        if table_name not in schema:
            schema[table_name] = {}

        prop_type = prop_def.get("type", "float")
        if prop_type not in SUPPORTED_TYPES:
            raise ValueError(f"不支持的属性类型: {prop_type}")

        schema[table_name][prop_key] = {
            "key": prop_key,
            "displayName": prop_def.get("displayName", prop_key),
            "type": prop_type,
            "category": prop_def.get("category", "自定义扩展"),
            "defaultValue": prop_def.get("defaultValue", SUPPORTED_TYPES[prop_type]["default"]),
            "scope": prop_def.get("scope", "table"),
            "tooltip": prop_def.get("tooltip", ""),
            "options": prop_def.get("options", [])
        }

        # 保存 schema
        if self.schema_file:
            with open(self.schema_file, "w", encoding="utf-8") as f:
                json.dump(schema, f, ensure_ascii=False, indent=2)

        return schema[table_name][prop_key]

    def remove_property(self, table_name, prop_key):
        """删除指定自定义属性"""
        schema = self.get_custom_schema()
        if table_name in schema and prop_key in schema[table_name]:
            del schema[table_name][prop_key]
            if self.schema_file:
                with open(self.schema_file, "w", encoding="utf-8") as f:
                    json.dump(schema, f, ensure_ascii=False, indent=2)
            return True
        return False

    def generate_ue_struct_definition(self, table_name):
        """生成对应 UE5 Python UserDefinedStruct 蓝图结构体注入脚本"""
        table_schema = self.get_custom_schema(table_name)
        type_mapping = {
            "float": "float",
            "int": "int32",
            "percent": "float",
            "bool": "bool",
            "string": "FString",
            "texture": "UTexture2D*",
            "sprite": "UPaperSprite*",
            "flipbook": "UPaperFlipbook*",
            "vfx": "UNiagaraSystem*",
            "sound": "USoundBase*",
            "vector2d": "FVector2D",
            "color": "FLinearColor",
        }
        fields = []
        for key, info in table_schema.items():
            ue_type = type_mapping.get(info["type"], "FString")
            fields.append(f"    # {info['displayName']} ({info['tooltip']})\n    '{key}': '{ue_type}',")
        
        script = f"""# -*- coding: utf-8 -*-
# UE5 结构体声明: F{table_name}CustomRow
CUSTOM_FIELDS = {{
{chr(10).join(fields)}
}}
"""
        return script
