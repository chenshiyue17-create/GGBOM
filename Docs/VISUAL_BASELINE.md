# 《GGBOM: 终末医疗兵》视觉基准与渲染标准规范 (Visual Baseline)

> **基准版本**：Phase 0-B Corrected Visual Baseline  
> **分类治理原则**：严格将视觉基准拆分为 **技术基准 (`TECHNICAL_BASELINE`)** 与 **视觉艺术设计基准 (`VISUAL_DESIGN_BASELINE`)**。技术参数具备实机证据的予以确立；所有艺术设计风格、具体外观与特效表现，凡无明确人工视觉审批证据的，一律标记为 **`CANDIDATE`** 或 **`UNRESOLVED`**，严禁 AI 擅自批准！  
> **更新日期**：2026-09-03  

---

## 一、 技术基准 (TECHNICAL_BASELINE — 已实机验证)

技术底层指标直接关系到渲染稳定性、色彩保真与数学对齐，已通过 Standalone 运行验证并予以锁定：

| 技术指标项 | 标准设定值 | 权威技术依据 | 状态 |
| :--- | :--- | :--- | :---: |
| **相机视角 (Camera Perspective)** | 正交 2D 俯视 45° 视角 (Top-Down 45° Retro Action) | [`MAP_GGBOM_Main.umap`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/GGBOM/Maps/MAP_GGBOM_Main.umap) | **APPROVED** |
| **相机画幅 (Camera Framing)** | `OrthoWidth = 941.0`，`AspectRatio = 941 / 1672 ≈ 0.5628`，100% 满屏全景无裁切 | [`DefaultEngine.ini`](file:///Users/cc/Desktop/GGBOM/xxxx/Config/DefaultEngine.ini) | **APPROVED** |
| **贴图寻址 (`AddressX/Y`)** | `TA_Clamp`（铁律：杜绝 UV 跨界采样导致的对侧白边与闪烁） | [`PROJECT_LESSONS_AND_STABILITY_RULES.md`](file:///Users/cc/Desktop/GGBOM/PROJECT_LESSONS_AND_STABILITY_RULES.md) | **APPROVED** |
| **下采样 (`MipGenSettings`)** | `TMGS_NoMipmaps`（禁用 Mipmap，防止相机缩放时贴图发虚） | [`PROJECT_LESSONS_AND_STABILITY_RULES.md`](file:///Users/cc/Desktop/GGBOM/PROJECT_LESSONS_AND_STABILITY_RULES.md) | **APPROVED** |
| **贴图分组 (`TextureGroup`)** | `TEXTUREGROUP_Pixels2D` | 2D 贴图无损内存分组 | **APPROVED** |
| **纹理过滤 (`Filter`)** | `TF_Nearest` (点采样) / `TF_Bilinear` (带 Clamp 双线性) | 像素与 UI 高精原画直通 | **APPROVED** |
| **色彩空间 (`sRGB`)** | `True`（原画直通，禁用电影色调压缩） | `r.TonemapperFilm = 0` | **APPROVED** |
| **曝光与光照方法** | `AutoExposure = 0`, `Lumen GI = 0`, `ReflectionMethod = 0`, `AntiAliasing = 0` | 锁定手动曝光，彻底禁用 3D 动态光照与 TAA 抖动 | **APPROVED** |
| **角色轴心 (Character Pivot)** | 脚底对齐 (**`Bottom Center`**, X=0.5, Y=0.90) | 地面站位与双层正交深度对齐 | **APPROVED** |
| **投射物世界尺寸基准** | `32 × 32 uu` 至 `48 × 48 uu`（以 KineticPistol 0.25 缩放为标尺） | [`calibrated_dimensions_spec.py`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Python/calibrated_dimensions_spec.py) | **APPROVED** |
| **动画帧序列规范** | 4 帧连续动画，水平条带图（`1 行 × 4 列` Sheet），播放帧率 8~10 FPS | [`P01_final_report.md`](file:///Users/cc/Desktop/GGBOM/xxxx/output/P01_final_report.md) | **APPROVED** |
| **角色朝向翻转数学** | D 键（向右走）`ScaleX = -1.0`，A 键（向左走）`ScaleX = 1.0` | [`AI_HANDOFF_DIRECTION_STATE.md`](file:///Users/cc/Desktop/GGBOM/xxxx/Docs/AI_HANDOFF_DIRECTION_STATE.md) | **APPROVED** |
| **UI 屏幕空间与 DPI** | 严格基于 UMG 9-Slice 与 SafeZone 锚点在屏幕空间渲染，锁定 9:16 竖屏 DPI 曲线 | [`DefaultEngine.ini`](file:///Users/cc/Desktop/GGBOM/xxxx/Config/DefaultEngine.ini) | **APPROVED** |

---

## 二、 视觉设计基准 (VISUAL_DESIGN_BASELINE — 待人工评审)

以下视觉艺术设计风格、具体组件外观与特效表现，**在未获得明确人工视觉评审批准前，一律标记为 `CANDIDATE` 或 `UNRESOLVED`，严禁 AI 私自标记 APPROVED**：

| 设计维度 | 当前候选方案与描述 | 真实状态 | 治理规则 |
| :--- | :--- | :---: | :--- |
| **HUD 视觉设计风格** | 暗黑科幻废土医疗终端风格（Dark Slate Blue 背景 + 荧光青/猩红条） | **`CANDIDATE`** | 必须在 `L_Preview_UI` 离线审查 6 大状态后由人工批准 |
| **具体 UI Widget 外观** | `WBP_GGBOM_CombatHUD`、`WBP_HUD_WeaponSlot` 等具体外观与边框切片 | **`CANDIDATE`** | 当前包含占位色块，待高精 UI 切片替换并走查 |
| **武器外观设计风格** | 10 种武器的像素与写实混合工业机甲外观 | **`CANDIDATE`** | 必须在 `L_Preview_Weapon` 中逐把审核持枪与造型 |
| **具体武器子弹外观** | 各武器飞行子弹切片（AR01、SG01、LaserRail 等） | **`CANDIDATE`** | 必须在 `L_Preview_Weapon` 标尺走廊中审核尺寸与辨识度 |
| **VFX 特效视觉风格** | 18 组特效（火花、烈焰、电弧、酸液、爆炸等）的表现力 | **`CANDIDATE`** | 必须在专用 VFX 走查环境中审核帧连贯性与透明混合 |
| **VFX 世界缩放标尺** | 全局特效在世界空间中的统一像素缩放标准 | **`UNRESOLVED`** | **尚未确立权威标准**，禁止 AI 擅自发明 |
| **卡牌与技能图标风格** | 512x512 卡面与 128x128 技能圆角图标设计 | **`CANDIDATE`** | 待 UMG 抽卡弹窗整合时走查 |
| **关卡场景障碍密度** | 掩体障碍物与开阔通道的黄金密度比 | **`UNRESOLVED`** | **尚未确立权威标准**，待关卡编辑走查确认 |

---

## 三、 状态冲突消除声明 (Conflict Resolution)

> [!IMPORTANT]
> **彻底消除此前版本中的状态自相矛盾**：
> 1. 此前“HUD component style = APPROVED”与“UI.CombatHUD 存在占位符且未审核”的冲突已完全消除：**HUD 视觉风格与具体外观一律归入 `CANDIDATE`**。
> 2. 此前“武器外观 = APPROVED”与“缺少枪口/命中特效走查”的冲突已完全消除：**除 KineticPistol 子弹尺寸技术验证外，所有武器外观与特效表现一律归入 `CANDIDATE`**。
