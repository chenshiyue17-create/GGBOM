# 11 命名与目录

## 前缀
BP_ Blueprint
WBP_ Widget
DA_ DataAsset
DT_ DataTable
T_ Texture
SPR_ Paper2D Sprite
FB_ Paper2D Flipbook
M_ Material
MI_ Material Instance
VFX_ Effect
SFX_ Sound
L_ Level

## 角色目录
/Game/Characters/<ID>/
- Data/
- Art/Source/
- Art/Sprites/
- Animation/
- Blueprints/
- UI/
- Test/

## 对象StableID与资产名分离
StableID: Character.Assault
资产：DA_CHR_Assault / BP_CHR_Assault
显示名：突击兵
显示名可改，StableID默认不可改。

## 禁止目录/命名
/Game/NewFolder3、temp、Test2、Final、New、copy、_2、_final 等无语义命名。
