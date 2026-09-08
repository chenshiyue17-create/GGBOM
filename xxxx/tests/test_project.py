from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectSmokeTests(unittest.TestCase):
    def test_project_is_blueprint_only(self) -> None:
        data = json.loads((ROOT / "xxxx.uproject").read_text(encoding="utf-8"))
        self.assertFalse(data.get("Modules"), "运行项目不得包含 C++ 模块")
        enabled = {p["Name"] for p in data.get("Plugins", []) if p.get("Enabled")}
        for plugin in ("Paper2D", "PaperZD", "EnhancedInput", "PythonScriptPlugin", "EditorScriptingUtilities"):
            with self.subTest(plugin=plugin):
                self.assertIn(plugin, enabled)

    def test_art_policy(self) -> None:
        script = (ROOT / "Content/Python/build_ggbom_game.py").read_text(encoding="utf-8")
        self.assertIn('ART_ROOT = ROOT / "Content" / "美术" / "Art"', script)
        self.assertNotIn('ROOT / "Content" / "美术" / "角色设定"', script)

    def test_generated_runtime_assets(self) -> None:
        expected = [
            "Content/GGBOM/Blueprints/BP_GGBOM_Player.uasset",
            "Content/GGBOM/Blueprints/BP_GGBOM_Enemy.uasset",
            "Content/GGBOM/Blueprints/BP_GGBOM_Projectile.uasset",
            "Content/GGBOM/Blueprints/BP_GGBOM_GameMode.uasset",
            "Content/GGBOM/Maps/MAP_GGBOM_Main.umap",
            "Content/GGBOM/Maps/MAP_GGBOM_Win.umap",
        ]
        for rel in expected:
            with self.subTest(rel=rel):
                self.assertTrue((ROOT / rel).is_file(), rel)

    def test_build_report(self) -> None:
        report = json.loads((ROOT / "output/ggbom_build_report.json").read_text(encoding="utf-8"))
        self.assertTrue(report["success"])
        self.assertEqual(Path(report["source_policy"]), ROOT / "Content/美术/Art")
        self.assertTrue(all(bp["compiled"] and not bp["errors"] for bp in report["blueprints"]))

    def test_default_map(self) -> None:
        config = (ROOT / "Config/DefaultEngine.ini").read_text(encoding="utf-8")
        self.assertIn("GameDefaultMap=/Game/GGBOM/Maps/MAP_GGBOM_Main", config)

    def test_p00_portrait_project_settings(self) -> None:
        config = (ROOT / "Config/DefaultEngine.ini").read_text(encoding="utf-8")
        for setting in (
            "ResolutionSizeX=1080",
            "ResolutionSizeY=1920",
            "ApplicationScale=1.000000",
            "UIScaleRule=ShortestSide",
            "Orientation=Portrait",
        ):
            with self.subTest(setting=setting):
                self.assertIn(setting, config)

    def test_p01_strict_asset_import_gate(self) -> None:
        status = json.loads((ROOT / "output/P01_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["P01_STATUS"], "PASS")
        self.assertEqual(status["NEXT_GATE"], "ALLOW_P02")
        self.assertEqual(status["ImportFailCount"], 0)
        for gate in (
            "Player8Dir", "Enemy4Dir", "Boss4Dir", "ProjectileStrict4Equal",
            "VFX", "Props", "UI", "MapsGroundOverhead", "P01_C", "P01_D", "P01_E",
        ):
            with self.subTest(gate=gate):
                self.assertEqual(status[gate], "PASS")

    def test_p01_manifest_and_import_counts(self) -> None:
        manifest = json.loads((ROOT / "Config/AssetImportRules.json").read_text(encoding="utf-8"))
        report = json.loads((ROOT / "output/P01_D_full_import.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["records"]), 811)
        self.assertEqual(report["ImportFailCount"], 0)
        self.assertEqual(report["texture_count"], 811)
        self.assertEqual(report["flipbook_count"], 139)
        self.assertTrue((ROOT / "Content/P01/Maps/MAP_P01_FlipbookValidation.umap").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
