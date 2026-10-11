"""Boundary tests; actual Chrome execution is measured separately by browser-run."""
import copy
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from consentdiff.browser_sessions import BrowserSessions
from consentdiff.config import default_config, load_config, validate_config
from consentdiff.evidence import save_browser_case, verify_case

PNG = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l9sAAAAASUVORK5CYII='


class ConfigTests(unittest.TestCase):
    def test_real_example_configs_load(self):
        for filename in ('test-config.json', 'native-config.json'):
            config = load_config(Path(__file__).parents[1] / 'examples' / filename)
            self.assertEqual(10, len(config['scenarios']))
            self.assertEqual(2, config['repeats'])

    def test_unknown_fields_external_targets_types_and_invalid_traces_rejected(self):
        config = default_config('CD-002')
        for update in ({'url': 'https://example.com'}, {'repeats': True}, {'repeats': 4}, {'webmcp_testing': 1},
                       {'modes': ['seeded', 'seeded']}, {'tool_adapter': 'mock'},
                       {'scenarios': [{'id': 'CD-002', 'steps': ['commit']}]}, {'scenarios': [{'id': 'unknown'}]}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                validate_config({**config, **update})

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'config.json'
            path.write_text('{"schema_version":"1.0","schema_version":"1.0"}')
            with self.assertRaisesRegex(ValueError, 'Duplicate JSON'):
                load_config(path)


class BrowserBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.sessions = BrowserSessions()

    def tearDown(self):
        self.sessions.close()

    def start(self, scenario='CD-002', mode='seeded'):
        return self.sessions.start({'scenario_id': scenario, 'mode': mode})

    def credentials(self, started, driver):
        return {'session_id': started['session_id'], 'driver': driver, 'token': started['driver_tokens'][driver]}

    def complete(self, scenario='CD-002', mode='seeded'):
        started = self.start(scenario, mode)
        captures = {}
        for driver in ('human', 'tool'):
            events = []
            for action in started['steps']:
                response = self.sessions.action({**self.credentials(started, driver), 'action': action,
                    'transport': 'playwright-visible-control' if driver == 'human' else 'structured-http'})
                events.append({'action': action, 'receipt_id': response['receipt']['id'], 'transport': response['receipt']['transport'],
                    'visible': 'Unit fixture: synthetic capture, not proof of browser execution',
                    **{k: response[k] for k in ('plan', 'approval', 'cancelled', 'response')}})
            captures[driver] = {'events': events, 'screenshots': {'before': PNG, 'after': PNG}}
        return {'session_id': started['session_id'], 'evidence_token': started['evidence_token'], 'captures': captures,
            'runtime': {'browser_version': 'unit-fixture', 'runner': 'playwright', 'headless': True, 'tool_adapter': 'structured-http',
                        'webmcp': {'status': 'unsupported', 'surface': None, 'secure_context': True, 'registered': False,
                                   'discovered': False, 'invocations': 0, 'reason': 'Unit fixture only', 'testing_flag': False}}}

    def test_driver_cannot_see_observer_or_use_other_capability(self):
        started = self.start()
        credentials = self.credentials(started, 'human')
        view = self.sessions.view(credentials)
        self.assertFalse({'before', 'after', 'observation', 'evidence_token', 'token'} & set(view))
        with self.assertRaises(ValueError):
            self.sessions.view({**credentials, 'driver': 'tool'})
        with self.assertRaises(ValueError):
            self.sessions.action({**credentials, 'action': 'inspect', 'transport': 'native-webmcp'})

    def test_actions_must_follow_declared_sequence(self):
        started = self.start()
        with self.assertRaisesRegex(ValueError, 'out of order'):
            self.sessions.action({**self.credentials(started, 'human'), 'action': 'commit', 'transport': 'playwright-visible-control'})

    def test_forged_verdict_and_forged_capture_cannot_be_saved(self):
        run = self.complete()
        for forged in ({**run, 'status': 'PASS'}, {**run, 'evidence_token': 'incorrect'}):
            with self.assertRaises(ValueError):
                self.sessions.prepare_finish({'runs': [forged]})
        tampered = copy.deepcopy(run)
        tampered['captures']['tool']['events'][-1]['receipt_id'] = 'invented'
        with self.assertRaisesRegex(ValueError, 'receipt'):
            self.sessions.prepare_finish({'runs': [tampered]})
        tampered = copy.deepcopy(run)
        tampered['captures']['human']['events'][3]['approval']['role'] = 'editor'
        with self.assertRaisesRegex(ValueError, 'consent state'):
            self.sessions.prepare_finish({'runs': [tampered]})

    def test_missing_capture_repeat_reuse_and_native_without_execution_rejected(self):
        run = self.complete()
        with self.assertRaisesRegex(ValueError, 'fresh independent'):
            self.sessions.prepare_finish({'runs': [run, run]})
        incomplete = copy.deepcopy(run)
        incomplete['captures']['human']['events'].pop()
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            self.sessions.prepare_finish({'runs': [incomplete]})
        native = copy.deepcopy(run)
        native['runtime']['tool_adapter'] = 'native-webmcp'
        with self.assertRaisesRegex(ValueError, 'Native execution'):
            self.sessions.prepare_finish({'runs': [native]})

    def test_final_comparison_reads_actual_sqlite_not_client_success(self):
        run = self.complete('CD-001')
        app = self.sessions.sessions[run['session_id']]['apps']['tool']
        with closing(sqlite3.connect(app.path)) as db:
            db.execute("UPDATE grants SET role='editor'")
            db.commit()
        result = self.sessions.prepare_finish({'runs': [run]})[0]['result']
        self.assertEqual('FAIL', result['status'])
        self.assertIn('overbroad_permission', {f['kind'] for f in result['findings']})

    def test_frozen_mapping_cannot_be_redefined_and_unknown_is_not_pass(self):
        run = self.complete('CD-001')
        app = self.sessions.sessions[run['session_id']]['apps']['tool']
        with closing(sqlite3.connect(app.path)) as db:
            db.execute("UPDATE users SET logical_id='attacker' WHERE logical_id='user-7'")
            db.commit()
        self.assertEqual('INCONCLUSIVE', self.sessions.prepare_finish({'runs': [run]})[0]['result']['status'])
        unknown = self.complete('CD-008', 'repaired')
        self.assertEqual('INCONCLUSIVE', self.sessions.prepare_finish({'runs': [unknown]})[0]['result']['status'])

    def test_evidence_contains_every_repeat_capture_and_independent_databases(self):
        trials = self.sessions.prepare_finish({'runs': [self.complete(), self.complete()]})
        with tempfile.TemporaryDirectory() as folder:
            saved = save_browser_case(folder, trials)
            directory = Path(folder) / saved['case_id']
            self.assertEqual('FAIL', saved['result']['status'])
            self.assertTrue(saved['result']['repeat_consistent'])
            self.assertEqual('PASS', verify_case(directory)['status'])
            self.assertEqual(4, len(list(directory.rglob('application.sqlite'))))
            self.assertEqual(8, len(list(directory.rglob('*.png'))))
            self.assertEqual(4, len(list(directory.rglob('browser-events.json'))))
            self.assertIn('structured-http', (directory / 'report.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
