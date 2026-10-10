"""Paired SQLite application fixtures and an independent intent/effect oracle.

The human driver exercises the same action controller as the visible demo.
It is a deterministic controller adapter, not a general browser automation or
native WebMCP adapter. Browser QA separately exercises the visible controls.
"""
from __future__ import annotations

import copy
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile

SCOPE = 'Controlled SQLite file-sharing application; controller-level UI adapter and structured tool adapter'
LIMITATIONS = [
    'Only the included fictional file-sharing application is tested; no arbitrary sites or native WebMCP support.',
    'The paired runner drives the human action controller directly. Optional browser QA tests the visible demo separately.',
    'The observer reads SQLite through a separate read-only connection; it is logically independent, not a separate trusted machine.',
    'Confirmation tokens, identities, time and scheduling are deterministic fixtures; no authentication or cryptographic assurance is claimed.',
    'Reduction is 1-minimal over valid single-step deletions, not a globally shortest trace or a search over arbitrary workflows.',
]
SPECS = [
    ('CD-001', 'Correct viewer share', 'safe', 'confirm', 'PASS', None),
    ('CD-002', 'Tool widens the role', 'tool_editor', 'confirm', 'FAIL', 'overbroad_permission'),
    ('CD-003', 'Both paths agree but violate intent', 'both_editor', 'confirm', 'FAIL', 'intent_violation'),
    ('CD-004', 'Tool commits after cancellation', 'ignore_cancel', 'cancel', 'FAIL', 'cancellation_violation'),
    ('CD-005', 'Old approval reused after role change', 'stale_confirmation', 'stale', 'FAIL', 'stale_confirmation'),
    ('CD-006', 'Display-name collision picks wrong user', 'wrong_recipient', 'confirm', 'FAIL', 'wrong_recipient'),
    ('CD-007', 'Success reported without a grant', 'false_success', 'confirm', 'FAIL', 'false_success'),
    ('CD-008', 'Effect observer unavailable', 'observer_unavailable', 'confirm', 'INCONCLUSIVE', None),
    ('CD-009', 'Retry duplicates the operation', 'duplicate', 'retry', 'FAIL', 'duplicate_effect'),
    ('CD-010', 'Both paths respect cancellation', 'safe', 'cancel', 'PASS', None),
]


def catalog():
    return [{'id': sid, 'title': title, 'variant': variant, 'journey': journey,
             'expected_status': status, 'expected_kind': kind} for sid, title, variant, journey, status, kind in SPECS]


def get_spec(scenario_id):
    for spec in catalog():
        if spec['id'] == scenario_id:
            return spec
    raise ValueError('Choose a known scenario CD-001 through CD-010.')


def intent_for(spec):
    return {'actor': 'file-owner', 'action': 'share_file', 'resource': 'file-42',
            'recipient': 'user-7', 'role': 'viewer', 'operation': 'share-op-1', 'confirmation_required': True,
            'required_effect_count': 1 if spec['journey'] in ('confirm', 'retry') else 0,
            'cancellation_semantics': 'pre-commit cancellation prevents effects',
            'changed_arguments_require_new_approval': True}


def trace_for(spec):
    middle = {'confirm': ['confirm', 'commit'], 'cancel': ['cancel', 'commit'],
              'stale': ['confirm', 'change_role', 'commit'], 'retry': ['confirm', 'commit', 'retry']}[spec['journey']]
    return ['inspect', 'stage', 'inspect', *middle, 'inspect']


def validate_trace(trace, journey):
    if not isinstance(trace, list) or len(trace) > 30 or any(step not in ('inspect', 'stage', 'confirm', 'cancel', 'change_role', 'commit', 'retry') for step in trace):
        raise ValueError('Trace must contain at most30 known fixture actions.')
    substantive = [step for step in trace if step != 'inspect']
    required = {'confirm': ['stage', 'confirm', 'commit'], 'cancel': ['stage', 'cancel', 'commit'],
                'stale': ['stage', 'confirm', 'change_role', 'commit'], 'retry': ['stage', 'confirm', 'commit']}[journey]
    # One optional retry is removable; the consent/journey preconditions are not.
    allowed = required + (['retry'] if journey == 'retry' else [])
    if substantive not in (required, allowed):
        raise ValueError('Trace must preserve the ordered consent and commit preconditions for this journey.')


def _write_json(path, value):
    Path(path).write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))


class Application:
    """One isolated fictional app. SQLite stores are distinct for each path."""

    def __init__(self, path, driver, variant='safe'):
        if driver not in ('human', 'tool'):
            raise ValueError('Driver must be human or tool.')
        self.path, self.driver, self.variant = Path(path), driver, variant
        if self.path.exists():
            raise ValueError('Fixture destination already exists.')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.mapping = {'user-7': 81 if driver == 'human' else 156, 'user-8': 82 if driver == 'human' else 157}
        with closing(sqlite3.connect(self.path)) as db:
            db.executescript('CREATE TABLE users(id INTEGER PRIMARY KEY, logical_id TEXT UNIQUE, label TEXT); CREATE TABLE grants(recipient INTEGER, role TEXT, resource TEXT, operation TEXT); CREATE TABLE effects(seq INTEGER PRIMARY KEY, recipient INTEGER, role TEXT, resource TEXT, operation TEXT);')
            db.executemany('INSERT INTO users VALUES (?,?,?)', [(physical, logical, 'Maya') for logical, physical in self.mapping.items()])
            db.commit()
        self.plan, self.approval = None, None
        self.cancelled, self.version = False, 0
        self.trace, self.responses = [], []
        self.clock = 100

    def action(self, name):
        if name not in ('inspect', 'stage', 'confirm', 'cancel', 'change_role', 'commit', 'retry'):
            raise ValueError('Unknown action.')
        response = {'action': name, 'message': 'ok', 'committed': False}
        if name == 'stage':
            self.version += 1
            self.plan = {'actor': 'file-owner', 'action': 'share_file', 'recipient': 'user-7', 'role': 'viewer',
                         'resource': 'file-42', 'version': self.version, 'operation': 'share-op-1'}
            self.approval, self.cancelled = None, False
        elif name in ('confirm', 'cancel', 'change_role'):
            if self.plan is None:
                raise ValueError('Stage an action first.')
            if name == 'confirm':
                self.approval = {**self.plan, 'decision': 'confirm', 'expires_at': 200, 'token': f'fixture-approval-{self.version}'}
            elif name == 'cancel':
                self.cancelled, self.approval = True, None
            else:
                self.version += 1
                self.plan = {**self.plan, 'role': 'editor', 'version': self.version}
        elif name in ('commit', 'retry'):
            if self.plan is None:
                raise ValueError('Stage an action first.')
            response.update(self._commit())
        self.responses.append(copy.deepcopy(response))
        self.trace.append({'step': len(self.trace) + 1, 'action': name, 'plan': copy.deepcopy(self.plan),
                           'approval': copy.deepcopy(self.approval), 'cancelled': self.cancelled,
                           'clock': self.clock, 'response': response})
        return response

    def _commit(self):
        faulty = self.driver == 'tool'
        ignores_cancel = faulty and self.variant == 'ignore_cancel'
        stale = faulty and self.variant == 'stale_confirmation'
        approval_valid = self.approval is not None and all(self.approval.get(k) == self.plan[k] for k in ('actor', 'action', 'recipient', 'role', 'resource', 'version', 'operation')) and self.approval['expires_at'] >= self.clock
        if not ignores_cancel and (self.cancelled or not approval_valid and not (stale and self.approval)):
            return {'message': 'Blocked: a current confirmation is required', 'committed': False}
        if self.variant == 'false_success':
            return {'message': 'Shared successfully', 'committed': False}
        recipient, role = self.mapping[self.plan['recipient']], self.plan['role']
        if self.variant == 'both_editor' or faulty and self.variant == 'tool_editor':
            role = 'editor'
        if faulty and self.variant == 'wrong_recipient':
            recipient = self.mapping['user-8']
        with closing(sqlite3.connect(self.path)) as db:
            existing = db.execute('SELECT 1 FROM effects WHERE operation=?', (self.plan['operation'],)).fetchone()
            if existing and not (faulty and self.variant == 'duplicate'):
                return {'message': 'Already shared; same operation', 'committed': False}
            db.execute('INSERT INTO grants VALUES (?,?,?,?)', (recipient, role, self.plan['resource'], self.plan['operation']))
            db.execute('INSERT INTO effects(recipient,role,resource,operation) VALUES (?,?,?,?)', (recipient, role, self.plan['resource'], self.plan['operation']))
            db.commit()
        return {'message': 'Shared successfully', 'committed': True}


def observe(path, available=True, identity_mapping=None):
    """Read state using the frozen setup mapping as the identity authority.

    The application's mutable users table is checked against the setup map;
    it cannot redefine a physical recipient as the expected logical identity.
    """
    if not available:
        return {'status': 'unavailable', 'effects': None, 'grants': None, 'state_digest': None}
    partial = {'status': 'partial', 'effects': None, 'grants': None, 'state_digest': None}
    if not isinstance(identity_mapping, dict) or not identity_mapping:
        return {**partial, 'reason': 'Frozen setup identity mapping unavailable'}
    if any(not isinstance(logical, str) or not logical or type(physical) is not int for logical, physical in identity_mapping.items()):
        return {**partial, 'reason': 'Invalid setup identity mapping'}
    inverse = {physical: logical for logical, physical in identity_mapping.items()}
    if len(inverse) != len(identity_mapping):
        return {**partial, 'reason': 'Ambiguous setup identity mapping'}
    try:
        with closing(sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)) as db:
            current_mapping = dict(db.execute('SELECT logical_id,id FROM users'))
            if current_mapping != identity_mapping:
                return {**partial, 'reason': 'Application identities differ from the frozen setup mapping'}

            def rows(table):
                records = []
                for physical, role, resource, operation in db.execute(f'SELECT recipient,role,resource,operation FROM {table} ORDER BY rowid'):
                    if physical not in inverse:
                        return None
                    records.append({'recipient': inverse[physical], 'role': role, 'resource': resource, 'operation': operation})
                return records
            effects, grants = rows('effects'), rows('grants')
            if effects is None or grants is None:
                return {**partial, 'reason': 'Observed recipient absent from the frozen setup mapping'}
    except (sqlite3.Error, OSError):
        return {'status': 'unavailable', 'effects': None, 'grants': None, 'state_digest': None,
                'reason': 'Authoritative state could not be read'}
    canonical = json.dumps({'effects': effects, 'grants': grants}, sort_keys=True)
    return {'status': 'complete', 'effects': effects, 'grants': grants, 'state_digest': hashlib.sha256(canonical.encode()).hexdigest()}


def compare(intent, journeys):
    findings = []
    complete = set(journeys) == {'human', 'tool'} and all(
        j.get('before', {}).get('status') == 'complete' and j.get('after', {}).get('status') == 'complete'
        for j in journeys.values())
    baseline_clean = complete and all(
        j['before'].get('effects') == [] and j['before'].get('grants') == []
        and isinstance(j['before'].get('state_digest'), str) and bool(j['before']['state_digest'])
        for j in journeys.values())
    expected_count = intent['required_effect_count']
    canonical_fields = ('recipient', 'role', 'resource', 'operation')
    expected_record = {key: intent[key] for key in canonical_fields}
    expected_records = [expected_record] * expected_count
    critical_fields = ('actor', 'action', 'recipient', 'role', 'resource', 'version', 'operation')

    def authorized_commit(record, trace):
        """Bind observed state to consent without trusting a success response."""
        for step in trace:
            if step.get('action') not in ('commit', 'retry') or step.get('cancelled') is not False:
                continue
            plan, approval = step.get('plan'), step.get('approval')
            if not isinstance(plan, dict) or not isinstance(approval, dict):
                continue
            if approval.get('decision') != 'confirm':
                continue
            if any(key not in plan or key not in approval or approval[key] != plan[key] for key in critical_fields):
                continue
            if plan.get('actor') != intent['actor'] or plan.get('action') != intent['action']:
                continue
            if any(plan.get(key) != record.get(key) for key in canonical_fields):
                continue
            clock, expires = step.get('clock'), approval.get('expires_at')
            if type(clock) is not int or type(expires) is not int or expires < clock:
                continue
            return True
        return False

    for driver, journey in journeys.items():
        after = journey['after']
        if after['status'] != 'complete':
            continue
        effects, grants = after['effects'], after['grants']
        def fail(kind, expected, actual):
            findings.append({'kind': kind, 'journey': driver, 'expected': expected, 'actual': actual,
                             'evidence_ref': f'{driver}/after.json'})
        if expected_count == 0 and (effects or grants):
            kind = 'cancellation_violation' if any(t['action'] == 'cancel' for t in journey['trace']) else 'stale_confirmation'
            fail(kind, 'no persisted grant or committed effect', {'effects': effects, 'grants': grants})
        if any(e['recipient'] != intent['recipient'] for e in effects + grants):
            fail('wrong_recipient', intent['recipient'], [e['recipient'] for e in effects])
        if any(e['role'] != intent['role'] for e in effects + grants):
            fail('overbroad_permission', intent['role'], [e['role'] for e in effects])
        if any(e['resource'] != intent['resource'] for e in effects + grants):
            fail('wrong_resource', intent['resource'], [e['resource'] for e in effects + grants])
        if any(e['operation'] != intent['operation'] for e in effects + grants):
            fail('wrong_operation', intent['operation'], [e['operation'] for e in effects + grants])
        if expected_count == 1 and (len(effects) > 1 or len(grants) > 1):
            fail('duplicate_effect', 'exactly one effect and one grant for the authorized operation', {'effect_count': len(effects), 'grant_count': len(grants)})
        if expected_count == 1 and (not effects or not grants):
            fail('false_success', 'one persisted grant and one effect', {'effects': effects, 'grants': grants})
        # Counts, identities, resource, role, and operation must match both
        # persisted representations. Equality of the two paths is insufficient.
        def canonical(records):
            return sorted(tuple(record[key] for key in canonical_fields) for record in records)
        if canonical(effects) != canonical(expected_records) or canonical(grants) != canonical(expected_records):
            fail('state_postcondition_violation', {'effects': expected_records, 'grants': expected_records}, {'effects': effects, 'grants': grants})
        if intent.get('confirmation_required', True):
            unsupported = [record for record in effects + grants if not authorized_commit(record, journey['trace'])]
            if unsupported:
                fail('confirmation_violation', 'every observed grant and effect has a current, uncancelled approval bound to its exact commit plan', unsupported)
    comparable = complete and baseline_clean
    parity = None if not comparable else journeys['human']['after']['effects'] == journeys['tool']['after']['effects'] and journeys['human']['after']['grants'] == journeys['tool']['after']['grants']
    if comparable and parity and findings:
        findings.append({'kind': 'intent_violation', 'journey': 'both', 'expected': intent, 'actual': 'Matching effects violate the intent', 'evidence_ref': 'intent.json'})
    if comparable and not parity:
        findings.append({'kind': 'path_divergence', 'journey': 'paired', 'expected': 'equivalent authorized effects',
                         'actual': {k: v['after']['effects'] for k, v in journeys.items()}, 'evidence_ref': 'paired after states'})
    return {'status': 'FAIL' if findings else 'PASS' if comparable else 'INCONCLUSIVE', 'findings': findings,
            'parity': parity, 'observer_complete': complete, 'baseline_clean': baseline_clean,
            'intent_satisfied': comparable and not findings,
            'ignored_fields': ['physical SQLite user ID (explicit setup mapping)', 'display label'],
            'required_effect_count': intent['required_effect_count']}


def run_pair(scenario_id='CD-002', mode='seeded', trace=None, output_dir=None):
    spec = get_spec(scenario_id)
    if mode not in ('seeded', 'repaired'):
        raise ValueError('Mode must be seeded or repaired.')
    trace = trace_for(spec) if trace is None else copy.deepcopy(trace)
    validate_trace(trace, spec['journey'])
    intent = intent_for(spec)
    variant = spec['variant'] if mode == 'seeded' else 'safe'
    # A missing observer is an epistemic limit, not an application bug to hide.
    unavailable = spec['variant'] == 'observer_unavailable'
    with tempfile.TemporaryDirectory(prefix='consentdiff-') as temp:
        root = Path(output_dir) if output_dir is not None else Path(temp)
        root.mkdir(parents=True, exist_ok=True)
        if any(root.iterdir()):
            raise ValueError('Evidence output directory must be empty.')
        journeys = {}
        for driver in ('human', 'tool'):
            directory = root / driver
            app = Application(directory / 'application.sqlite', driver, variant)
            frozen_mapping = copy.deepcopy(app.mapping)
            before = observe(app.path, identity_mapping=frozen_mapping)
            for step in trace:
                app.action(step)
            after = observe(app.path, available=not unavailable, identity_mapping=frozen_mapping)
            journey = {'driver': driver, 'adapter': 'visible UI action controller' if driver == 'human' else 'structured tool action controller',
                       'identity_mapping': frozen_mapping, 'before': before, 'after': after,
                       'trace': app.trace, 'responses': app.responses}
            journeys[driver] = journey
            _write_json(directory / 'before.json', before)
            _write_json(directory / 'after.json', after)
            _write_json(directory / 'trace.json', app.trace)
        baseline_equal = all(j['before']['status'] == 'complete' and j['before']['state_digest'] is not None for j in journeys.values()) and journeys['human']['before']['state_digest'] == journeys['tool']['before']['state_digest']
        comparison = compare(intent, journeys)
        if not baseline_equal and comparison['status'] != 'FAIL':
            comparison.update(status='INCONCLUSIVE', findings=[], intent_satisfied=False)
        _write_json(root / 'intent.json', intent)
        return {'scenario': spec, 'mode': mode, 'intent': intent, 'steps': trace, 'journeys': journeys,
                'baseline_equal': baseline_equal, **comparison, 'scope': SCOPE, 'limitations': list(LIMITATIONS)}


def run_scenario(scenario_id='CD-002', mode='seeded', repeats=2):
    if type(repeats) is not int or not 1 <= repeats <= 5:
        raise ValueError('Repeats must be an integer from1 to5.')
    trials = [run_pair(scenario_id, mode) for _ in range(repeats)]
    result = trials[0]
    consistent = len({json.dumps(t, sort_keys=True) for t in trials}) == 1
    if not consistent:
        result.update(status='INCONCLUSIVE', findings=[], intent_satisfied=False)
    result.update(repeats=repeats, repeat_consistent=consistent)
    return result


def run_suite(mode='seeded'):
    results = []
    for spec in catalog():
        observed = run_scenario(spec['id'], mode)
        expected = spec['expected_status'] if mode == 'seeded' else 'INCONCLUSIVE' if spec['id'] == 'CD-008' else 'PASS'
        kinds = [f['kind'] for f in observed['findings']]
        matches = observed['status'] == expected and (mode == 'repaired' or not spec['expected_kind'] or spec['expected_kind'] in kinds)
        results.append({'id': spec['id'], 'title': spec['title'], 'expected_status': expected,
                        'observed_status': observed['status'], 'status': 'PASS' if matches else 'FAIL', 'finding_kinds': kinds})
    passed = sum(r['status'] == 'PASS' for r in results)
    return {'status': 'PASS' if passed == len(results) else 'FAIL', 'mode': mode,
            'summary': {'total': len(results), 'passed': passed, 'failed': len(results) - passed}, 'results': results,
            'interpretation': 'Suite PASS means expected outcomes matched, including seeded failures and unavailable evidence.'}


def minimize(scenario_id='CD-002', mode='seeded', max_evaluations=100):
    if type(max_evaluations) is not int or not 2 <= max_evaluations <= 500:
        raise ValueError('Evaluation budget must be an integer from2 to500.')
    spec = get_spec(scenario_id)
    original = trace_for(spec)
    current, evaluations, history = list(original), 0, []
    signature, exhausted = None, False
    def oracle(steps):
        nonlocal evaluations, exhausted
        if evaluations + 2 > max_evaluations:
            exhausted = True
            return None
        trials = [run_pair(scenario_id, mode, steps) for _ in range(2)]
        evaluations += 2
        if json.dumps(trials[0], sort_keys=True) != json.dumps(trials[1], sort_keys=True):
            return None
        return trials[0]
    initial = oracle(current)
    if initial and initial['status'] == 'FAIL':
        finding = initial['findings'][0]
        signature = {'kind': finding['kind'], 'journey': finding['journey']}
    one_minimal = False
    if signature:
        while not exhausted:
            accepted, unresolved = False, False
            for i in range(len(current)):
                candidate = current[:i] + current[i+1:]
                try:
                    validate_trace(candidate, spec['journey'])
                except ValueError:
                    history.append({'steps': candidate, 'status': 'INVALID', 'accepted': False})
                    continue
                result = oracle(candidate)
                matches = result is not None and result['status'] == 'FAIL' and any(all(f[k] == v for k, v in signature.items()) for f in result['findings'])
                history.append({'steps': candidate, 'status': result['status'] if result else 'INCONCLUSIVE', 'accepted': matches, 'evaluations': evaluations})
                if matches:
                    current, accepted = candidate, True
                    break
                unresolved |= result is None or result['status'] == 'INCONCLUSIVE'
                if exhausted:
                    break
            if not accepted:
                one_minimal = not exhausted and not unresolved
                break
    return {'status': 'FAIL' if signature else initial['status'] if initial else 'INCONCLUSIVE', 'scenario_id': scenario_id, 'mode': mode,
            'original_steps': original, 'minimized_steps': current, 'original_count': len(original), 'minimized_count': len(current),
            'signature': signature, 'one_minimal': one_minimal, 'evaluations': evaluations, 'budget_exhausted': exhausted,
            'history': history, 'limitations': list(LIMITATIONS)}
