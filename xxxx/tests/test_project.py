"""Portable source smoke tests. Historical generated reports are not test assertions."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "tools"))
from ggbom.data_validation import load_tables, validate_tables


class ProjectSmokeTests(unittest.TestCase):
    def test_project_is_blueprint_only(self):
        data = json.loads((ROOT / "xxxx.uproject").read_text(encoding="utf-8"))
        self.assertFalse(data.get("Modules"))
        enabled = {p["Name"] for p in data.get("Plugins", []) if p.get("Enabled")}
        self.assertTrue({"Paper2D", "EnhancedInput"}.issubset(enabled))
        # PaperZD is optional. Do not force it on just to satisfy an obsolete report.

    def test_source_data_contract(self):
        self.assertEqual(validate_tables(load_tables(ROOT / "Content/Data")), [])

    def test_default_map(self):
        config = (ROOT / "Config/DefaultEngine.ini").read_text(encoding="utf-8")
        self.assertIn("GameDefaultMap=/Game/GGBOM/Maps/MAP_GGBOM_Main", config)

    def test_supported_entries_exist(self):
        for rel in ("Content/Python/apply_data_config.py", "Tools/launch_lightweight_game.sh", "Tools/run_config_studio.sh"):
            with self.subTest(rel=rel):
                self.assertTrue((ROOT / rel).is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
