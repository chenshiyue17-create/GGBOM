import ast
import base64
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
from ggbom import config_io, config_service, data_validation, editor_apply, paths, runner
from validate_weapon_core_diff import compare
from snapshot_blueprint_structure import TARGETS


def sample():
    return {
        "DT_Enemies.json": {"enemy": {"DisplayName": "行尸", "BlueprintClass": "/Game/Enemy.Enemy_C",
            "MaxHealth": 65, "MoveSpeed": 75, "Scale": 0.45, "ContactDamage": 15, "ExpGemValue": 5}},
        "DT_Weapons.json": {"rifle": {"DisplayName": "步枪", "Damage": 45, "FireRate": 0.15,
            "ProjectileSpeed": 1200, "LifeSpan": 3.0, "PelletCount": 1}},
        "DT_WaveProgression.json": {"stage": {"TotalDuration": 40, "SpawnLanesX": [-10.5, 10.5],
            "Waves": [{"TimeOffset": 1.5, "LaneIndex": 0, "EnemyType": "enemy", "Count": 2, "Interval": 0.5}]}}}


def seed(directory):
    for name, data in sample().items():
        (Path(directory) / name).write_text(json.dumps(data), encoding="utf-8")


class DataValidationTests(unittest.TestCase):
    def test_current_repository_data(self):
        self.assertEqual(data_validation.validate_tables(data_validation.load_tables(paths.DATA_DIR)), [])

    def test_valid_fractional_coordinates_and_time(self):
        self.assertEqual(data_validation.validate_tables(sample()), [])

    def test_negative_and_wrong_numeric_types(self):
        for key, value in [("PelletCount", -3), ("PelletCount", 1.5), ("PelletCount", True),
                           ("LifeSpan", -1), ("Damage", "45"), ("Damage", float("nan")),
                           ("ProjectileSpeed", float("inf")), ("FireRate", 0)]:
            with self.subTest(key=key, value=value):
                tables = sample()
                tables["DT_Weapons.json"]["rifle"][key] = value
                self.assertTrue(data_validation.validate_tables(tables))

    def test_invalid_wave_boundaries(self):
        for key, value in [("TimeOffset", 999), ("Count", -2), ("Count", True), ("Interval", -1),
                           ("LaneIndex", 2), ("EnemyType", "absent")]:
            with self.subTest(key=key):
                tables = sample()
                tables["DT_WaveProgression.json"]["stage"]["Waves"][0][key] = value
                self.assertTrue(data_validation.validate_tables(tables))

    def test_final_spawn_cannot_exceed_duration(self):
        tables = sample()
        tables["DT_WaveProgression.json"]["stage"]["Waves"][0].update(TimeOffset=39, Count=3, Interval=1)
        self.assertTrue(data_validation.validate_tables(tables))

    def test_malformed_table_types(self):
        for name in data_validation.CORE_TABLES:
            for value in (None, [], {}, {"bad": 12}):
                tables = sample(); tables[name] = value
                self.assertTrue(data_validation.validate_tables(tables))

    def test_duplicate_keys_and_nonfinite_json_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "bad.json"
            for text in ('{"x":1,"x":2}', '{"x":NaN}'):
                file.write_text(text)
                with self.assertRaises(ValueError):
                    data_validation.load_json(file)


class PersistenceTests(unittest.TestCase):
    def test_dictionary_damage_change_detected(self):
        old = sample()["DT_Weapons.json"]; new = copy.deepcopy(old)
        new["rifle"]["Damage"] = 999
        diff = config_io.diff_rows(old, new)
        self.assertEqual(diff["modified"], ["rifle"])
        self.assertEqual(diff["changes"]["rifle"]["old"]["Damage"], 45)

    def test_row_add_remove_and_duplicate(self):
        diff = config_io.diff_rows({"a": {}}, {"b": {}})
        self.assertEqual(diff["added"], ["b"]); self.assertEqual(diff["removed"], ["a"])
        with self.assertRaises(ValueError):
            config_io.diff_rows([], [{"Name": "a"}, {"Name": "a"}])

    def test_valid_save_and_invalid_save_are_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            seed(tmp)
            weapons = sample()["DT_Weapons.json"]; weapons["rifle"]["Damage"] = 50
            result = config_service.save_request(tmp, {"weapons": weapons})
            self.assertEqual(result["runtime_status"], "NOT_RUN")
            path = Path(tmp) / "DT_Weapons.json"; before = path.read_bytes()
            weapons["rifle"]["LifeSpan"] = -1
            with self.assertRaises(ValueError):
                config_service.save_request(tmp, {"weapons": weapons})
            self.assertEqual(path.read_bytes(), before)

    def test_multi_file_failure_rolls_back_all_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            seed(tmp)
            before = {p.name: p.read_bytes() for p in Path(tmp).glob('*.json')}
            write = config_io.atomic_bytes
            failed = False
            def fail_once(path, data):
                nonlocal failed
                if Path(path).name == 'DT_Weapons.json' and not failed:
                    failed = True
                    raise OSError("injected disk error")
                return write(path, data)
            with patch.object(config_io, 'atomic_bytes', side_effect=fail_once):
                with self.assertRaises(OSError):
                    config_io.commit_json_files(tmp, {"DT_Enemies.json": {"changed": {}}, "DT_Weapons.json": {"changed": {}}})
            self.assertEqual({p.name: p.read_bytes() for p in Path(tmp).glob('*.json')}, before)
            self.assertFalse((Path(tmp) / '.ggbom-transaction.json').exists())

    def test_startup_recovers_uncommitted_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'data.json'; old = b'{"old":true}'
            file.write_bytes(b'{"new":true}')
            (Path(tmp)/'.ggbom-transaction.json').write_text(json.dumps({'data.json': base64.b64encode(old).decode()}))
            config_io.recover_pending(tmp)
            self.assertEqual(file.read_bytes(), old)

    def test_lock_prevents_second_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            with config_io.config_lock(tmp):
                with self.assertRaises(RuntimeError):
                    config_io.commit_json_files(tmp, {'a.json': {}})

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                config_io.commit_json_files(tmp, {'../escape.json': {}})


class EditorApplyTests(unittest.TestCase):
    def fake_unreal(self, missing=False, fail_save=False):
        values = {"MaxHealth": 65, "CurrentHealth": 65, "MoveSpeed": 75, "ContactDamage": 15, "ExpGemValue": 5}
        if missing:
            del values['MoveSpeed']
        cdo = types.SimpleNamespace(get_editor_property=lambda key: values[key], set_editor_property=lambda key, value: values.__setitem__(key, value))
        api = types.SimpleNamespace(load_asset=lambda path: object(), load_class=lambda _, path: object(),
                                    get_default_object=lambda cls: cdo,
                                    EditorAssetLibrary=types.SimpleNamespace(save_loaded_asset=lambda *args, **kw: not fail_save))
        return api, values

    def test_plan_uses_saved_values_and_explicit_scope(self):
        enemies = sample()['DT_Enemies.json']; enemies['enemy']['MaxHealth'] = 130
        plan = config_service.enemy_binding_plan(enemies)
        self.assertEqual(plan['bindings'][0]['properties']['MaxHealth'], 130)
        self.assertIn('weapons', plan['not_applied'])
        api, values = self.fake_unreal()
        result = editor_apply.apply_enemy_defaults(api, plan)
        self.assertEqual(values['MaxHealth'], 130); self.assertEqual(values['CurrentHealth'], 130)
        self.assertEqual(result['runtime_status'], 'NOT_RUN')
        self.assertEqual(result['status'], 'APPLIED_EDITOR_DEFAULTS')

    def test_missing_property_blocks_before_any_write(self):
        api, values = self.fake_unreal(missing=True); before = dict(values)
        plan = config_service.enemy_binding_plan(sample()['DT_Enemies.json'])
        with self.assertRaises(KeyError):
            editor_apply.apply_enemy_defaults(api, plan)
        self.assertEqual(values, before)

    def test_failed_save_restores_defaults(self):
        api, values = self.fake_unreal(fail_save=True); before = dict(values)
        enemies = sample()['DT_Enemies.json']; enemies['enemy']['MaxHealth'] = 130
        with self.assertRaises(RuntimeError):
            editor_apply.apply_enemy_defaults(api, config_service.enemy_binding_plan(enemies))
        self.assertEqual(values, before)

    def test_duplicate_blueprint_bindings_rejected(self):
        enemies = sample()['DT_Enemies.json']; enemies['other'] = dict(enemies['enemy'])
        with self.assertRaises(ValueError):
            config_service.enemy_binding_plan(enemies)

    def test_old_success_report_is_not_current_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp); seed(directory)
            (directory / 'config_apply.json').write_text(json.dumps({'run_id': 'old', 'status': 'APPLIED_EDITOR_DEFAULTS'}))
            with patch.object(runner, 'DATA_DIR', directory), patch.object(runner, 'REPORT_DIR', directory), \
                 patch.object(runner, 'engine_binary', return_value=Path('fake')), \
                 patch.object(runner.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')):
                result = runner.apply_config()
            self.assertEqual(result['status'], 'error')
            self.assertEqual(result['report'], {})


class EvidenceAndPortabilityTests(unittest.TestCase):
    def test_binary_diff_requires_complete_inventory(self):
        before = {'kind': 'ASSET_BINARY_INVENTORY', 'assets': [{'asset_path': path, 'exists': True, 'sha256': 'a'*64} for path in TARGETS]}
        after = copy.deepcopy(before); after['assets'][0]['sha256'] = 'b'*64
        self.assertEqual(compare(before, after)['status'], 'FAIL')
        self.assertEqual(compare(before, before)['scope'], 'CORE_ASSET_BYTES_ONLY')
        after['assets'].pop()
        with self.assertRaises(ValueError):
            compare(before, after)

    def test_preview_does_not_claim_approval_without_engine(self):
        result = subprocess.run([sys.executable, str(REPO/'tools/test_weapon_preview.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['status'], 'BLOCKED')

    def test_validate_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(REPO/'tools/dev.py'), 'validate'], cwd=tmp, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['runtime_status'], 'NOT_RUN')

    def test_machine_local_engine_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); executable = root/'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
            executable.parent.mkdir(parents=True); executable.touch()
            with patch.dict(os.environ, {'GGBOM_UE_ROOT': str(root)}, clear=True), patch.object(paths, 'local_settings', return_value={}):
                self.assertEqual(paths.engine_binary(commandlet=True), executable)

    def test_registry_count_mismatch_reports_error_without_nameerror(self):
        tree = ast.parse((REPO/'tools/validate_art_registry.py').read_text())
        for count_name in ('approved', 'candidate', 'placeholder', 'legacy'):
            block = next(node for node in tree.body if isinstance(node, ast.If) and f'actual_{count_name}' in ast.unparse(node.test))
            scope = {f'actual_{count_name}': 1, 'summary': {f'{count_name}_count': 2}, 'errors': []}
            exec(compile(ast.Module(body=[block], type_ignores=[]), 'registry', 'exec'), scope)
            self.assertEqual(len(scope['errors']), 1)

    def test_retired_phase_returns_blocked_exit(self):
        result = subprocess.run([sys.executable, str(REPO/'xxxx/Tools/run_phase.py'), 'P03'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['status'], 'BLOCKED')


if __name__ == '__main__':
    unittest.main()
