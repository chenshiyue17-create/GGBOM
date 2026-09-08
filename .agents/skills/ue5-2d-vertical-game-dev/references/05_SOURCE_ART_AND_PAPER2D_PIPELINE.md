# 05 Source Art 与 UE Paper2D Runtime Pipeline

## 严格分层
Source Art = PNG/生成图/源序列，仅生产输入。
Runtime Art = Paper2D Sprite / Paper2D Flipbook / Material / Niagara / Texture / Sound，才是游戏资产。

## 角色源素材默认标准
- 1792×1024 PNG RGBA
- 2行×4列
- 单格 448×512
- 上排 ActionA 4帧
- 下排 ActionB 4帧
- 5基础方向：S/SE/E/NE/N
- 镜像：SW←SE, W←E, NW←NE
- 默认配对：Idle+Run, Attack+Hurt, Dead+Reserved
- 默认 15 张动画 Source Sheet + 1 Master

## 体量锁定
Standing 类动作 ReferenceStandingHeightPx 推荐 430px，容差 ±5%。
Dead 不按垂直高度，而按 BodyLengthPx≈ReferenceStandingHeightPx±5%，并检查头盔、躯干、四肢、武器、像素密度一致；Dead 缩小 → FAIL。

## 自动导入链
Source PNG
→ Source Validator
→ Texture Import
→ 448×512 Grid Slice
→ 8 Sprites
→ Pivot配置
→ 2 Flipbooks
→ FPS配置
→ DA_ANIM绑定
→ Character Runtime Binding
→ PIE Playback Validation

1张2×4源图 = 8 Sprites + 2 Flipbooks。

基础角色最终：5动作×5方向×4帧=100 Sprites；5动作×5方向=25 Flipbooks。

## DA_ANIM
每个动作使用 DirectionalFlipbookSet：South/SouthEast/East/NorthEast/North。
每槽至少：Flipbook / FPS / Loop / PlayRate。

推荐FPS：Idle6 / Run10 / Attack12 / Hurt8 / Dead8。

## Runtime Ready Gate
SOURCE ART
TEXTURE IMPORT
SPRITE SLICING
PAPER2D SPRITES
PAPER2D FLIPBOOKS
ANIMATION PROFILE
RUNTIME BINDING
PIE PLAYBACK
全部 PASS 才算动画美术 READY。
