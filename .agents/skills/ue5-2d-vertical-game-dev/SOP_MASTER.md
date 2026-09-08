# UE5.8 2D俯视角竖屏游戏开发 SOP — MASTER

## 1. 项目固定目标
- Engine: UE5.8
- Presentation: 2D / 2.5D Top-Down
- Orientation: 9:16 Portrait
- Target UI reference: 1080×1920
- Platform: Android / iOS
- Input: 左下虚拟摇杆 + 右下技能/闪避/终极技能
- Typical loop: 移动 → 自动瞄准/攻击 → 击杀 → XP → 三选一 → 精英 → Boss
- Mobile first: 中低端设备性能预算优先

## 2. 四层工程结构
### Framework
共享 Runtime 系统，原则上不因新增内容反复修改。

### Definition
Character / Weapon / Projectile / Ability / Enemy / Boss / Pickup / Level / Environment / UI Theme 等具体对象的唯一配置源。

### Content
Paper2D Sprite / Flipbook / Texture / Material / Niagara / VFX / SFX / UI / Environment。

### Tools
Dashboard / Registry / DependencyGraph / Validator / TestHarness / Commandlet。

AI 日常工作主要在 Definition + Content；只有“真正新增共享能力”才进入 Framework。

## 3. 任何任务的固定入口
收到需求后禁止直接写代码。必须：
1. Project Scan
2. Resolve Stable Object ID
3. 读取 Definition / Blueprint Parent / Components / Runtime Art
4. 读取上游/下游依赖
5. 分类任务：DATA_CHANGE / CONTENT_ADD / CAPABILITY_ADD / BUG_FIX / ART_CHANGE / ARCHITECTURE_REFACTOR
6. 生成 Change Plan
7. 决定 Mutation Mode：STRICT_PATCH / MERGE / REGENERATE_GENERATED / MIGRATION
8. 执行允许范围
9. Duplicate Scan
10. Compile / Test
11. Before/After Diff
12. Scope Guard
13. Commit 或 Rollback
14. Final Report

## 4. 核心架构公式
- 它是什么 → Parent/Child
- 它会什么 → Component
- 它参数不同 → DataAsset/DataTable
- 它的美术/动画 → 对象 Definition / Animation Profile
- 它需要全局统计 → Registry/Dashboard 派生

## 5. 禁止行为
- 新增角色复制旧角色 Event Graph
- 一把武器一个重复实现 Fire/Reload 的 Blueprint
- 在 Concrete Blueprint 重写通用移动/受伤/死亡/方向动画
- 修改一次就 Add 一个 Component/Event/Timer/Ability
- 同 Stable ID 创建 `_2/_New/_Final`
- Dashboard 保存第二套数据
- PNG 存在就称动画完成
- Placeholder 资产算 PASS
- 没运行 PIE 就写 PIE PASS

## 6. READY 定义
READY = 架构 + 数据 + 中文属性 + 对象美术 + UE Runtime Art + UI/VFX/SFX + 绑定 + Dashboard + Compile + PIE + 必需 Build/Performance 全部通过。
