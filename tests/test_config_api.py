"""Local HTTP contract checks with temporary configuration files; no UE process."""
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import HTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from unittest.mock import patch
from test_tooling import REPO, seed, sample

spec = importlib.util.spec_from_file_location('config_studio_test', REPO/'xxxx/Content/Python/tools/config_studio/server.py')
studio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(studio)


class ConfigAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        seed(self.directory)
        self.overrides = [patch.object(studio, 'DATA_DIR', self.directory),
                          patch.object(studio, 'COMMIT_LOG_PATH', self.directory/'commits.json')]
        for override in self.overrides:
            override.start()
        self.server = HTTPServer(('127.0.0.1', 0), studio.ConfigStudioHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        for override in self.overrides:
            override.stop()
        self.tmp.cleanup()

    def post(self, path, body):
        request = Request(f'http://127.0.0.1:{self.server.server_port}{path}',
                          data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def test_save_records_real_diff_and_not_runtime_success(self):
        weapons = sample()['DT_Weapons.json']; weapons['rifle']['Damage'] = 50
        status, body = self.post('/api/save', {'weapons': weapons, 'raw_diff': {'forged': True}})
        self.assertEqual(status, 200)
        self.assertEqual(body['status'], 'success')
        self.assertEqual(body['runtime_status'], 'NOT_RUN')
        self.assertEqual(body['commit']['raw_diff']['DT_Weapons.json']['modified'], ['rifle'])

    def test_invalid_save_returns_400_and_preserves_file(self):
        file = self.directory/'DT_Weapons.json'; before = file.read_bytes()
        weapons = sample()['DT_Weapons.json']; weapons['rifle']['PelletCount'] = -3
        status, body = self.post('/api/save', {'weapons': weapons})
        self.assertEqual(status, 400)
        self.assertEqual(body['status'], 'error')
        self.assertEqual(file.read_bytes(), before)

    def test_deploy_preserves_blocked_scope(self):
        with patch.object(studio, 'apply_config', return_value={'status': 'blocked', 'message': 'No UE', 'runtime_status': 'NOT_RUN'}):
            status, body = self.post('/api/deploy', {})
        self.assertEqual(body['status'], 'blocked')
        self.assertEqual(body['runtime_status'], 'NOT_RUN')
