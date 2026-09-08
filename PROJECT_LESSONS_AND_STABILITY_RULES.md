# 《GGBOM: 终末医疗兵》工程避坑红线与稳定开发守则
> **Project Lessons Learned & Code Stability Guidelines**
> 本规范记录项目所有已验证的底层技术标准与历史踩坑经验，后续所有开发必须严格遵循，严禁擅自推翻或破坏已调通功能。

---

## 一、 已固化的核心技术基石（严禁乱改）

### 1. 2D 贴图与防闪烁/色彩保真规范
* **贴图导入与采样属性**：
  - `AddressX` / `AddressY` = `TA_Clamp`（**铁律**：防止 UV 边缘跨界采样对侧底色产生白边/闪烁）。
  - `MipGenSettings` = `TMGS_NoMipmaps`（禁用 Mipmap 下采样模糊）。
  - `TextureGroup` = `TEXTUREGROUP_Pixels2D`。
  - `Filter` = `TF_Nearest` 或带 Clamp 的 `TF_Bilinear`。
  - `sRGB` = `True`（无损直通原画色彩）。
* **渲染器与后处理（防发灰泛白/防抖动）**：
  - `r.DefaultFeature.AutoExposure = 0`（锁定 1:1 手动曝光，禁用 3D 人眼适应）。
  - `r.DynamicGlobalIlluminationMethod = 0` / `r.ReflectionMethod = 0`（彻底关闭 Lumen 3D 光照与反射）。
  - `r.AntiAliasingMethod = 0` / `r.PostProcessAAQuality = 0`（禁用 TAA/TSR 时间性子像素抖动）。
  - `r.TonemapperFilm = 0` / `r.ToneCurveAmount = 0.0`（直通原画色调，禁用电影级色调映射压缩）。

---

### 2. Pawn 单体架构与组件防重机制
* **踩坑教训**：UE5 的 `add_component` 在反复保存资产时会持续向同一个 Blueprint 追加 Subobject，导致 Pawn 内部堆积多层 Flipbook，产生“双层/套娃角色”。
* **开发守则**：
  - 在修改或生成 Blueprint 前，必须先检索是否已存在对应组件（`has_fb` / `has_col`），严禁无条件重复追加。
  - 保证主角 Pawn 内部**永久仅有且只有 1 个 `PaperFlipbookComponent` 和 1 个 `Collision` 盒**。

---

### 3. 真 8 向数学走位与动画连续播放保护
* **踩坑教训**：
  1. 采用 `If-Else` 单链判断按键会造成分支互斥，导致斜向复合键（如 `W+A`、`W+D`）被阻断。
  2. 在 `Tick` 中无条件每帧调用 `SetFlipbook` 会导致动画每秒被重置 60 次，定格在第 0 帧无法播放。
* **开发守则**：
  - **位移计算**：采用双轴数学向量合成 $(V_x, 0, V_z) \times \Delta t$ 驱动单一位移节点，即按即走。
  - **转向逻辑**：D 键（向右走）动态翻转 `ScaleX = -1.0`，A 键（向左走）恢复 `ScaleX = 1.0`。
  - **动画播放保护**：切换动画前必须接入 `GetFlipbook != TargetFlipbook` 判定节点，仅在方向改变时切换，同方向奔跑时保持帧动画平滑轮播。

---

### 4. 双层全景地图与 100% 满屏视野
* **双层层级标准**：
  - **地面底层 (`Ground_Stage00`)**：`Y = +80.0`, `Translucency Sort Priority = 0`。
  - **遮挡顶层 (`Overhead_Stage00`)**：`Y = -80.0`, `Translucency Sort Priority = 1000`（角色从建筑/路灯下方穿行时自然产生遮挡）。
* **相机画幅**：
  - `OrthoWidth` = `941.0`（严格匹配地图真实原生宽度）。
  - `AspectRatio` = `941 / 1672 ≈ 0.5628`，实现 100% 满屏全景无裁切呈现。

---

## 二、 后续功能增量开发规范（避免覆盖正常）

1. **增量式开发，非侵入式挂载**：
   - 后续新增战斗系统（射击开火、子弹投射物、碰撞掉血、卡牌选择弹窗等）时，直接以独立 Actor/ActorComponent 或 UMG 形式增量接入。
   - **绝不推翻或重写已验证的移动、地图、相机与材质管线**。
2. **改前核对，改后验证**：
   - 每次代码变更前必须核查影响面，严禁为了局部小功能引入破坏性全局改动。
   - 每次提交前在 StandAlone 游戏窗口中运行验证，确保既有功能（8向走位、动画轮播、视野画幅、双层遮挡、原画色彩）100% 稳定运行。
