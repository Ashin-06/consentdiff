import contextlib
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import zipfile

from consentdiff.cli import main
from consentdiff.core import run_pair
from consentdiff.evidence import bundle_case, list_cases, load_case, run_case, verify_case
from consentdiff.reports import render_report
from consentdiff.server import create_server


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_saved_run_replay_matches_and_bundle_contains_both_real_databases(self):
        case = run_case(self.root)
        folder = self.root / case['case_id']
        self.assertTrue(case['result']['witness_matches'])
        self.assertEqual('PASS', verify_case(folder)['status'])
        self.assertEqual(11, verify_case(folder)['checked_files'])
        self.assertEqual(case, load_case(self.root, case['case_id']))
        self.assertEqual(1, len(list_cases(self.root)))
        with zipfile.ZipFile(io.BytesIO(bundle_case(self.root, case['case_id']))) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(2, len([n for n in archive.namelist() if n.endswith('.sqlite')]))

    def test_tamper_missing_extra_and_manifest_traversal(self):
        case = run_case(self.root, repeats=1)
        folder = self.root / case['case_id']
        (folder / 'report.html').write_text('altered', encoding='utf-8')
        (folder / 'evidence/intent.json').unlink()
        (folder / 'extra.txt').write_text('extra', encoding='utf-8')
        result = verify_case(folder)
        self.assertEqual('FAIL', result['status'])
        self.assertEqual(3, len(result['errors']))
        with self.assertRaises(ValueError):
            bundle_case(self.root, case['case_id'])
        manifest = json.loads((folder / 'manifest.json').read_text())
        manifest['files']['../outside'] = 'fake'
        (folder / 'manifest.json').write_text(json.dumps(manifest))
        self.assertIn('Unsafe manifest path', ' '.join(verify_case(folder)['errors']))
        with self.assertRaises(ValueError):
            load_case(self.root, '../outside')

    def test_witness_replay_disagreement_is_not_a_verified_failure(self):
        repeated = run_pair()
        repeated.update(repeats=2, repeat_consistent=True)
        repeated['journeys']['human']['after']['state_digest'] = 'different'
        with patch('consentdiff.evidence.run_scenario', return_value=repeated):
            case = run_case(self.root)
        self.assertFalse(case['result']['witness_matches'])
        self.assertEqual('INCONCLUSIVE', case['result']['status'])
        self.assertEqual([], case['result']['findings'])

    def test_report_escapes_evidence(self):
        case = run_case(self.root, repeats=1)
        case['result']['intent']['resource'] = '<script>bad()</script>'
        rendered = render_report(case)
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)

    def test_cli_verdict_codes_and_bundle_overwrite_guard(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(1, main(['run', '--output-dir', str(self.root)]))
            self.assertEqual(0, main(['run', '--mode', 'repaired', '--output-dir', str(self.root)]))
            self.assertEqual(2, main(['run', '--scenario', 'CD-008', '--output-dir', str(self.root)]))
            self.assertEqual(2, main(['run', '--scenario', 'unknown', '--output-dir', str(self.root)]))
            folder = next(p for p in self.root.iterdir() if p.is_dir())
            self.assertEqual(0, main(['verify', str(folder)]))
            destination = self.root / 'evidence.zip'
            self.assertEqual(0, main(['bundle', str(folder), '--output', str(destination)]))
            self.assertEqual(2, main(['bundle', str(folder), '--output', str(destination)]))
            self.assertEqual(2, main(['bundle', str(folder), '--output', str(folder / 'bad.zip')]))


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.server = create_server(0, cls.temp.name)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.temp.cleanup()

    def request(self, path, body=None, headers=None):
        request = Request(self.url + path, data=json.dumps(body).encode() if body is not None else None,
                          headers={'Content-Type': 'application/json', **(headers or {})})
        try:
            with urlopen(request, timeout=30) as response:
                return response.status, response.read()
        except HTTPError as response:
            return response.code, response.read()

    def test_api_run_export_reduce_and_suite(self):
        self.assertEqual(10, len(json.loads(self.request('/api/demo')[1])['scenarios']))
        code, data = self.request('/api/run', {})
        self.assertEqual(200, code)
        case = json.loads(data)
        self.assertEqual('FAIL', case['result']['status'])
        for url in case['artifacts'].values():
            self.assertEqual(200, self.request(url)[0])
        self.assertEqual('PASS', json.loads(self.request('/api/cases/' + case['case_id'] + '/verify')[1])['status'])
        self.assertTrue(json.loads(self.request('/api/minimize', {})[1])['one_minimal'])
        self.assertEqual('PASS', json.loads(self.request('/api/suite', {})[1])['status'])

    def test_visible_controller_endpoints_mutate_separate_states(self):
        code, payload = self.request('/api/sandbox/start', {})
        self.assertEqual(200, code)
        sid = json.loads(payload)['session_id']
        for driver in ('human', 'tool'):
            for action in ('stage', 'confirm', 'commit'):
                code, payload = self.request('/api/sandbox/action', {'session_id': sid, 'driver': driver, 'action': action})
                self.assertEqual(200, code)
            observed = json.loads(payload)['observation']
            self.assertEqual('viewer' if driver == 'human' else 'editor', observed['effects'][0]['role'])

    def test_input_guards_origin_host_and_no_source_exposure(self):
        self.assertEqual(403, self.request('/api/run', {}, {'Origin': 'https://example.com'})[0])
        self.assertEqual(403, self.request('/api/demo', headers={'Host': 'evil.invalid'})[0])
        self.assertEqual(415, self.request('/api/run', {}, {'Content-Type': 'text/plain'})[0])
        for body in ({'mode': 'bad'}, {'scenario_id': 'bad'}, {'repeats': True}, []):
            self.assertEqual(400, self.request('/api/run', body)[0])
        self.assertEqual(400, self.request('/api/sandbox/action', {'session_id': '../x'})[0])
        self.assertEqual(404, self.request('/consentdiff/core.py')[0])


if __name__ == '__main__':
    unittest.main()
