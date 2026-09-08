# P01 全素材发现与严格导入验收

P01_STATUS = PASS

## Gate

| Gate | 结果 | 证据 |
| --- | --- | --- |
| P01-A 全素材审计 | PASS | 801 PNG；801 RGBA；801 含透明像素；尺寸、Alpha、SHA-256 完整记录 |
| P01-B AssetImportRules Manifest | PASS | `Config/AssetImportRules.json`：811 条导入记录，严格格数规则已写入 |
| P01-C 10 个代表资产 | PASS | 10 Texture、24 Sprite、5 Flipbook，`ImportFailCount=0` |
| P01-D 全量批处理 | PASS | 811 Texture、1,190 Sprite、139 Flipbook，`ImportFailCount=0` |
| P01-E 冷启动打开与播放 | PASS | 冷启动打开 10 个代表资产、5 个 Flipbook 自动播放；验证地图已保存 |

## 严格切片政策

- `Width % Columns != 0` → FAIL；`Height % Rows != 0` → FAIL。
- 未通过严格等格验证的资产不生成切片 Sprite 或 Flipbook。
- 129 个动画 Sheet 由真实独立帧验证格数和单元尺寸。
- 11 个 UI/Card 非均匀 Atlas 仅导入 Texture/Sprite，禁止猜测网格。
- Projectile Flight：`Rows=1`，`Columns=4`，`StrictEqualCells=true`。10 张原图保持不变；每张生成可验证的四等格派生 Sheet。

## 素材能力 Gate

```text
Player8Dir = PASS
Enemy4Dir = PASS
Boss4Dir = PASS
ProjectileStrict4Equal = PASS
VFX = PASS
Props = PASS
UI = PASS
MapsGroundOverhead = PASS

ImportFailCount = 0
NEXT_GATE = ALLOW_P02
```

## 运行证据

- [全量审计 JSON](P01_asset_audit.json)
- [逐图 CSV](P01_asset_audit.csv)
- [代表资产导入报告](P01_C_representative_import.json)
- [全量导入报告](P01_D_full_import.json)
- [冷启动与 Flipbook 播放报告](P01_E_asset_open_playback.json)
- [最终 Gate](P01_status.json)
- [Flipbook 实机播放截图](P01_E_Flipbook_Playback.png)
- 验证地图：`/Game/P01/Maps/MAP_P01_FlipbookValidation`
