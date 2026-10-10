import copy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from consentdiff.core import Application, catalog, compare, minimize, observe, run_pair, run_scenario, run_suite
from consentdiff.sandbox import Sandbox


class OracleTests(unittest.TestCase):
    def test_matching_wrong_resource_cannot_pass(self):
        result = run_pair('CD-001')
        for journey in result['journeys'].values():
            for source in ('effects', 'grants'):
                journey['after'][source][0]['resource'] = 'unapproved-file'
        compared = compare(result['intent'], result['journeys'])
        self.assertTrue(compared['parity'])
        self.assertEqual('FAIL', compared['status'])
        self.assertIn('wrong_resource', [f['kind'] for f in compared['findings']])

    def test_matching_duplicate_grants_cannot_pass_with_one_effect(self):
        result = run_pair('CD-001')
        for journey in result['journeys'].values():
            journey['after']['grants'].append(copy.deepcopy(journey['after']['grants'][0]))
        compared = compare(result['intent'], result['journeys'])
        self.assertEqual('FAIL', compared['status'])
        self.assertIn('duplicate_effect', [f['kind'] for f in compared['findings']])

    def test_cancelled_persisted_grant_without_effect_log_cannot_pass(self):
        result = run_pair('CD-010')
        grant = {'recipient': 'user-7', 'role': 'viewer', 'resource': 'file-42', 'operation': 'share-op-1'}
        for journey in result['journeys'].values():
            journey['after']['grants'] = [copy.deepcopy(grant)]
        compared = compare(result['intent'], result['journeys'])
        self.assertEqual('FAIL', compared['status'])
        self.assertIn('cancellation_violation', [f['kind'] for f in compared['findings']])

    def test_observed_effects_require_consent_even_if_response_denies_commit(self):
        result = run_pair('CD-001')
        for journey in result['journeys'].values():
            for step in journey['trace']:
                step['approval'] = None
                step['response']['committed'] = False
        compared = compare(result['intent'], result['journeys'])
        self.assertEqual('FAIL', compared['status'])
        self.assertIn('confirmation_violation', [f['kind'] for f in compared['findings']])

    def test_matching_wrong_operation_cannot_pass(self):
        result = run_pair('CD-001')
        for journey in result['journeys'].values():
            for source in ('effects', 'grants'):
                journey['after'][source][0]['operation'] = 'unapproved-operation'
        compared = compare(result['intent'], result['journeys'])
        self.assertEqual('FAIL', compared['status'])
        self.assertIn('wrong_operation', [f['kind'] for f in compared['findings']])

    def test_observed_effect_requires_unexpired_confirm_decision_at_recorded_clock(self):
        for mutation in ('expired', 'decision', 'clock', 'actor', 'cancelled'):
            result = run_pair('CD-001')
            for journey in result['journeys'].values():
                for step in journey['trace']:
                    if step['action'] not in ('commit', 'retry'):
                        continue
                    if mutation == 'expired':
                        step['clock'] = step['approval']['expires_at'] + 1
                    elif mutation == 'decision':
                        step['approval']['decision'] = 'cancel'
                    elif mutation == 'clock':
                        del step['clock']
                    elif mutation == 'actor':
                        step['plan']['actor'] = step['approval']['actor'] = 'different-owner'
                    else:
                        step['cancelled'] = True
            with self.subTest(mutation=mutation):
                compared = compare(result['intent'], result['journeys'])
                self.assertEqual('FAIL', compared['status'])
                self.assertIn('confirmation_violation', [f['kind'] for f in compared['findings']])

    def test_all_seeded_and_repaired_scenario_expectations(self):
        for mode in ('seeded', 'repaired'):
            suite = run_suite(mode)
            self.assertEqual('PASS', suite['status'])
            self.assertEqual(10, suite['summary']['passed'])
            self.assertEqual(10, len({s['id'] for s in suite['results']}))

    def test_parity_does_not_hide_both_paths_wrong(self):
        result = run_pair('CD-003')
        self.assertTrue(result['parity'])
        self.assertFalse(result['intent_satisfied'])
        self.assertEqual('FAIL', result['status'])
        self.assertIn('intent_violation', [f['kind'] for f in result['findings']])

    def test_same_names_do_not_hide_wrong_physical_recipient(self):
        result = run_pair('CD-006')
        self.assertNotEqual(result['journeys']['human']['identity_mapping'], result['journeys']['tool']['identity_mapping'])
        self.assertEqual('user-8', result['journeys']['tool']['after']['effects'][0]['recipient'])
        self.assertIn('wrong_recipient', [f['kind'] for f in result['findings']])

    def test_false_success_is_detected_from_empty_saved_state(self):
        result = run_pair('CD-007')
        self.assertTrue(result['parity'])
        self.assertEqual([], result['journeys']['human']['after']['effects'])
        self.assertIn('Shared successfully', [r['message'] for r in result['journeys']['human']['responses']])
        self.assertEqual('FAIL', result['status'])

    def test_missing_observer_never_becomes_pass_even_after_repair(self):
        for mode in ('seeded', 'repaired'):
            result = run_pair('CD-008', mode)
            self.assertEqual('INCONCLUSIVE', result['status'])
            self.assertIsNone(result['parity'])
            self.assertIsNone(result['journeys']['human']['after']['effects'])

    def test_cancellation_and_stale_confirmation(self):
        for sid, kind in [('CD-004', 'cancellation_violation'), ('CD-005', 'stale_confirmation')]:
            result = run_pair(sid)
            self.assertIn(kind, [f['kind'] for f in result['findings']])
            self.assertEqual([], result['journeys']['human']['after']['effects'])
            repaired = run_pair(sid, 'repaired')
            self.assertEqual('PASS', repaired['status'])
            self.assertEqual([], repaired['journeys']['tool']['after']['effects'])

    def test_duplicate_retry_and_safe_idempotency(self):
        seeded, safe = run_pair('CD-009'), run_pair('CD-009', 'repaired')
        self.assertEqual(2, len(seeded['journeys']['tool']['after']['effects']))
        self.assertEqual(1, len(safe['journeys']['tool']['after']['effects']))
        self.assertEqual('PASS', safe['status'])

    def test_unknown_or_inconsistent_repeated_state_is_inconclusive(self):
        first = run_pair('CD-002')
        different = copy.deepcopy(first)
        different['journeys']['tool']['after']['effects'][0]['role'] = 'viewer'
        with patch('consentdiff.core.run_pair', side_effect=[first, different]):
            result = run_scenario('CD-002')
        self.assertEqual('INCONCLUSIVE', result['status'])
        self.assertFalse(result['repeat_consistent'])

    def test_real_sqlite_observer_detects_independent_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Application(Path(temp) / 'app.sqlite', 'human')
            for step in ('stage', 'confirm', 'commit'):
                app.action(step)
            self.assertEqual('viewer', observe(app.path, identity_mapping=app.mapping)['effects'][0]['role'])
            with closing(sqlite3.connect(app.path)) as db:
                db.execute("UPDATE effects SET role='editor'")
                db.commit()
            self.assertEqual('editor', observe(app.path, identity_mapping=app.mapping)['effects'][0]['role'])
            with closing(sqlite3.connect(app.path)) as db:
                db.execute('UPDATE effects SET recipient=9999')
                db.commit()
            self.assertEqual('partial', observe(app.path, identity_mapping=app.mapping)['status'])

    def test_mutable_user_table_cannot_relabel_the_wrong_recipient(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Application(Path(temp) / 'app.sqlite', 'human')
            frozen = copy.deepcopy(app.mapping)
            for step in ('stage', 'confirm', 'commit'):
                app.action(step)
            with closing(sqlite3.connect(app.path)) as db:
                db.execute("UPDATE users SET logical_id='temporary' WHERE logical_id='user-7'")
                db.execute("UPDATE users SET logical_id='user-7' WHERE logical_id='user-8'")
                db.execute("UPDATE users SET logical_id='user-8' WHERE logical_id='temporary'")
                db.execute('UPDATE grants SET recipient=?', (frozen['user-8'],))
                db.execute('UPDATE effects SET recipient=?', (frozen['user-8'],))
                db.commit()
            observed = observe(app.path, identity_mapping=frozen)
            self.assertEqual('partial', observed['status'])
            self.assertIsNone(observed['effects'])
            self.assertIn('frozen setup', observed['reason'])

    def test_missing_setup_mapping_or_database_is_not_complete_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Application(Path(temp) / 'app.sqlite', 'human')
            self.assertEqual('partial', observe(app.path)['status'])
            self.assertEqual('unavailable', observe(Path(temp) / 'missing.sqlite', identity_mapping=app.mapping)['status'])

    def test_incomplete_or_nonempty_baseline_cannot_pass(self):
        for mutation in ('unavailable', 'partial', 'missing-digest', 'preexisting-grant'):
            result = run_pair('CD-001')
            before = result['journeys']['human']['before']
            if mutation in ('unavailable', 'partial'):
                before['status'] = mutation
            elif mutation == 'missing-digest':
                before['state_digest'] = None
            else:
                before['grants'] = copy.deepcopy(result['journeys']['human']['after']['grants'])
            with self.subTest(mutation=mutation):
                compared = compare(result['intent'], result['journeys'])
                self.assertEqual('INCONCLUSIVE', compared['status'])
                self.assertFalse(compared['intent_satisfied'])
                self.assertIsNone(compared['parity'])

    def test_incomplete_other_observer_does_not_erase_conclusive_violation(self):
        result = run_pair('CD-002')
        result['journeys']['human']['before']['status'] = 'unavailable'
        compared = compare(result['intent'], result['journeys'])
        self.assertEqual('FAIL', compared['status'])
        self.assertFalse(compared['observer_complete'])
        self.assertIn('overbroad_permission', [f['kind'] for f in compared['findings']])

    def test_expired_confirmation_and_missing_confirmation_block_commit(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Application(Path(temp) / 'app.sqlite', 'tool')
            app.action('stage')
            self.assertFalse(app.action('commit')['committed'])
            app.action('confirm')
            app.clock = 201
            self.assertFalse(app.action('commit')['committed'])
            self.assertEqual([], observe(app.path, identity_mapping=app.mapping)['effects'])

    def test_pair_export_real_databases_and_distinct_initial_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'output'
            result = run_pair(output_dir=root)
            self.assertTrue(result['baseline_equal'])
            self.assertEqual(2, len(list(root.rglob('*.sqlite'))))
            self.assertEqual(9, len([p for p in root.rglob('*') if p.is_file()]))
            self.assertEqual(result['intent'], json.loads((root / 'intent.json').read_text()))
            with self.assertRaises(ValueError):
                run_pair(output_dir=root)


class ReductionTests(unittest.TestCase):
    def test_minimal_role_failure_retains_consent_preconditions(self):
        result = minimize()
        self.assertEqual(['stage', 'confirm', 'commit'], result['minimized_steps'])
        self.assertTrue(result['one_minimal'])
        self.assertEqual({'kind': 'overbroad_permission', 'journey': 'tool'}, result['signature'])
        self.assertEqual('FAIL', run_pair(trace=result['minimized_steps'])['status'])

    def test_retry_is_not_removed_if_it_is_necessary_for_the_finding(self):
        result = minimize('CD-009')
        self.assertIn('retry', result['minimized_steps'])
        self.assertEqual(4, result['minimized_count'])
        self.assertTrue(result['one_minimal'])

    def test_budget_and_nonfailures_do_not_claim_minimality(self):
        low = minimize(max_evaluations=2)
        self.assertFalse(low['one_minimal'])
        self.assertTrue(low['budget_exhausted'])
        self.assertEqual(2, low['evaluations'])
        for sid in ('CD-001', 'CD-008', 'CD-010'):
            self.assertFalse(minimize(sid)['one_minimal'])

    def test_rejects_invalid_inputs_and_actions(self):
        for fn, kwargs in [(run_pair, {'scenario_id': '../x'}), (run_pair, {'mode': 'x'}), (run_pair, {'trace': ['commit']}),
                           (run_scenario, {'repeats': True}), (minimize, {'max_evaluations': 0}), (minimize, {'max_evaluations': 99999})]:
            with self.assertRaises(ValueError):
                fn(**kwargs)


class SandboxTests(unittest.TestCase):
    def test_real_control_sessions_are_isolated_bounded_and_disposable(self):
        sandbox = Sandbox()
        self.addCleanup(sandbox.close)
        session = sandbox.start()
        for driver in ('human', 'tool'):
            for action in ('stage', 'confirm', 'commit'):
                result = sandbox.action(session['session_id'], driver, action)
            self.assertEqual('viewer' if driver == 'human' else 'editor', result['observation']['effects'][0]['role'])
        for _ in range(8):
            sandbox.start('CD-001')
        self.assertEqual(8, len(sandbox.sessions))
        with self.assertRaises(ValueError):
            sandbox.action(session['session_id'], 'human', 'stage')


if __name__ == '__main__':
    unittest.main()
