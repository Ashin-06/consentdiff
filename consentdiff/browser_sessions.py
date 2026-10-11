"""Browser capture boundary: clients provide UI evidence, never verdicts/state.

The observer reopens backend-owned SQLite read-only using frozen setup mappings.
Driver tokens cannot access the observer or finalize a case. This is local test
isolation, not attestation against a hostile administrator or runner.
"""
import base64
import copy
import json
from pathlib import Path
import secrets
import tempfile
import time

from .config import strict_object
from .core import Application, compare, get_spec, intent_for, observe, trace_for, validate_trace

BROWSER_LIMITATIONS = [
    'Only the owned fictional local file-sharing application is tested; external websites and production identity providers are not supported.',
    'Playwright clicks rendered controls in headless Chrome. This proves browser execution in this run, not that a person or an autonomous AI chose the actions.',
    'Native WebMCP is claimed only for runs with successful native registration, discovery and invocation. Structured HTTP fallback is labelled separately.',
    'The independent observer uses a separate read-only SQLite connection and frozen setup mappings, on the same machine as the application.',
    'UI captures are runner-supplied and correlated with server action receipts; they are not cryptographic proof against a compromised runner.',
    'Confirmation and identity fixtures are deterministic; no production authentication or cryptographic consent assurance is claimed.',
]


class BrowserSessions:
    def __init__(self):
        self.sessions = {}

    def start(self, data):
        strict_object(data, ('scenario_id', 'mode', 'steps'), ('scenario_id', 'mode'))
        spec = get_spec(data['scenario_id'])
        mode = data['mode']
        if mode not in ('seeded', 'repaired'):
            raise ValueError('Mode must be seeded or repaired.')
        steps = data.get('steps', trace_for(spec))
        validate_trace(steps, spec['journey'])
        self.expire()
        if len(self.sessions) >= 12:
            raise ValueError('Browser session limit reached; finish or close existing sessions.')
        temp = tempfile.TemporaryDirectory(prefix='consentdiff-browser-')
        sid = secrets.token_hex(16)
        variant = spec['variant'] if mode == 'seeded' else 'safe'
        apps = {d: Application(Path(temp.name) / (d + '.sqlite'), d, variant) for d in ('human', 'tool')}
        mappings = {d: copy.deepcopy(app.mapping) for d, app in apps.items()}
        before = {d: observe(app.path, identity_mapping=mappings[d]) for d, app in apps.items()}
        session = {'temp': temp, 'spec': spec, 'mode': mode, 'steps': list(steps), 'apps': apps,
                   'mapping': mappings, 'before': before, 'tokens': {d: secrets.token_hex(24) for d in apps},
                   'evidence_token': secrets.token_hex(24), 'receipts': {d: [] for d in apps}, 'created': time.monotonic()}
        self.sessions[sid] = session
        return {'session_id': sid, 'scenario': spec, 'mode': mode, 'steps': steps, 'intent': intent_for(spec),
                'driver_tokens': session['tokens'], 'evidence_token': session['evidence_token']}

    def _session(self, sid):
        if not isinstance(sid, str) or sid not in self.sessions:
            raise ValueError('Browser session is missing or expired.')
        return self.sessions[sid]

    def _driver(self, data):
        session = self._session(data.get('session_id'))
        driver = data.get('driver')
        token = data.get('token')
        if driver not in ('human', 'tool') or not isinstance(token, str) or not secrets.compare_digest(token, session['tokens'][driver]):
            raise ValueError('Invalid driver capability.')
        return session, driver

    def view(self, data):
        strict_object(data, ('session_id', 'driver', 'token'), ('session_id', 'driver', 'token'))
        session, driver = self._driver(data)
        app = session['apps'][driver]
        return {'scenario': session['spec'], 'mode': session['mode'], 'driver': driver,
                'intent': intent_for(session['spec']), 'plan': copy.deepcopy(app.plan), 'approval': copy.deepcopy(app.approval),
                'cancelled': app.cancelled, 'response': app.responses[-1] if app.responses else None, 'action_count': len(app.trace)}

    def action(self, data):
        strict_object(data, ('session_id', 'driver', 'token', 'action', 'transport'), ('session_id', 'driver', 'token', 'action', 'transport'))
        session, driver = self._driver(data)
        transport = data['transport']
        allowed = ('playwright-visible-control',) if driver == 'human' else ('structured-http', 'native-webmcp')
        if transport not in allowed:
            raise ValueError('Transport does not match the selected driver.')
        app = session['apps'][driver]
        index = len(app.trace)
        if index >= len(session['steps']) or session['steps'][index] != data['action']:
            raise ValueError('Action is out of order for this validated scenario.')
        app.action(data['action'])
        receipt = {'id': secrets.token_hex(12), 'step': index + 1, 'action': data['action'], 'transport': transport}
        session['receipts'][driver].append(receipt)
        return {**self.view({k: data[k] for k in ('session_id', 'driver', 'token')}), 'receipt': receipt}

    def prepare_finish(self, data):
        strict_object(data, ('runs',), ('runs',))
        runs = data['runs']
        if not isinstance(runs, list) or not 1 <= len(runs) <= 3:
            raise ValueError('Finalize requires 1 to 3 independent browser trials.')
        prepared, ids = [], set()
        for run in runs:
            strict_object(run, ('session_id', 'evidence_token', 'captures', 'runtime'), ('session_id', 'evidence_token', 'captures', 'runtime'))
            session = self._session(run['session_id'])
            if run['session_id'] in ids:
                raise ValueError('A repeated trial must use a fresh independent session.')
            ids.add(run['session_id'])
            if not isinstance(run['evidence_token'], str) or not secrets.compare_digest(run['evidence_token'], session['evidence_token']):
                raise ValueError('Invalid evidence capability.')
            strict_object(run['captures'], ('human', 'tool'), ('human', 'tool'))
            runtime = run['runtime']
            strict_object(runtime, ('browser_version', 'tool_adapter', 'webmcp', 'runner', 'headless'), ('browser_version', 'tool_adapter', 'webmcp', 'runner', 'headless'))
            if runtime['runner'] != 'playwright' or runtime['headless'] is not True or runtime['tool_adapter'] not in ('structured-http', 'native-webmcp'):
                raise ValueError('Unsupported browser execution metadata.')
            if not isinstance(runtime['browser_version'], str) or len(runtime['browser_version']) > 80 or not isinstance(runtime['webmcp'], dict):
                raise ValueError('Invalid runtime metadata.')
            native = runtime['webmcp']
            strict_object(native, ('status', 'surface', 'secure_context', 'registered', 'discovered', 'invocations', 'reason', 'testing_flag'),
                          ('status', 'surface', 'secure_context', 'registered', 'discovered', 'invocations', 'reason', 'testing_flag'))
            if type(native['invocations']) is not int or native['invocations'] < 0 or not isinstance(native['reason'], str) or len(native['reason']) > 3000:
                raise ValueError('Invalid native capability report.')
            if runtime['tool_adapter'] == 'native-webmcp' and not (native['status'] == 'available' and native['surface'] == 'document.modelContext'
                    and native['secure_context'] is True and native['registered'] is True and native['discovered'] is True
                    and native['invocations'] == len(session['steps'])):
                raise ValueError('Native execution requires successful registration, discovery and every invocation.')
            if runtime['tool_adapter'] == 'structured-http' and native['invocations'] != 0:
                raise ValueError('HTTP fallback must not claim native invocations.')
            captures, journeys = {}, {}
            for driver in ('human', 'tool'):
                capture = run['captures'][driver]
                strict_object(capture, ('events', 'screenshots'), ('events', 'screenshots'))
                events, screenshots = capture['events'], capture['screenshots']
                app = session['apps'][driver]
                if len(app.trace) != len(session['steps']) or not isinstance(events, list) or len(events) != len(app.trace):
                    raise ValueError('Incomplete browser journey; every action and capture is required.')
                for event, receipt, step in zip(events, session['receipts'][driver], app.trace):
                    strict_object(event, ('action', 'receipt_id', 'transport', 'visible', 'plan', 'approval', 'cancelled', 'response'),
                                  ('action', 'receipt_id', 'transport', 'visible', 'plan', 'approval', 'cancelled', 'response'))
                    expected_transport = 'playwright-visible-control' if driver == 'human' else runtime['tool_adapter']
                    if event['action'] != receipt['action'] or event['receipt_id'] != receipt['id'] or event['transport'] != receipt['transport'] or event['transport'] != expected_transport:
                        raise ValueError('Browser capture does not match the server action receipt.')
                    if any(event[key] != step[key] for key in ('plan', 'approval', 'cancelled', 'response')):
                        raise ValueError('Captured consent state does not match the server record.')
                    if not isinstance(event['visible'], str) or not 1 <= len(event['visible']) <= 12000:
                        raise ValueError('Missing or oversized visible UI capture.')
                strict_object(screenshots, ('before', 'after'), ('before', 'after'))
                decoded = {}
                for name, encoded in screenshots.items():
                    if not isinstance(encoded, str) or len(encoded) > 260000:
                        raise ValueError('Screenshot must be a bounded PNG.')
                    try:
                        image = base64.b64decode(encoded, validate=True)
                    except (ValueError, TypeError) as exc:
                        raise ValueError('Screenshot is not valid base64.') from exc
                    if not image.startswith(b'\x89PNG\r\n\x1a\n') or len(image) < 40:
                        raise ValueError('Screenshot must contain PNG data.')
                    decoded[name] = image
                captures[driver] = {'events': events, 'screenshots': decoded}
                journeys[driver] = {'driver': driver, 'adapter': 'Playwright visible browser controls' if driver == 'human' else runtime['tool_adapter'],
                    'identity_mapping': session['mapping'][driver], 'before': session['before'][driver],
                    'after': observe(app.path, available=session['spec']['variant'] != 'observer_unavailable', identity_mapping=session['mapping'][driver]),
                    'trace': copy.deepcopy(app.trace), 'responses': copy.deepcopy(app.responses)}
            intent = intent_for(session['spec'])
            result = {'scenario': session['spec'], 'mode': session['mode'], 'intent': intent, 'steps': session['steps'], 'journeys': journeys,
                'baseline_equal': journeys['human']['before']['state_digest'] == journeys['tool']['before']['state_digest'],
                **compare(intent, journeys), 'scope': 'Real browser controls paired with ' + runtime['tool_adapter'] + ' on the owned local application',
                'execution': 'browser', 'runtime': copy.deepcopy(runtime), 'limitations': list(BROWSER_LIMITATIONS)}
            prepared.append({'session_id': run['session_id'], 'session': session, 'captures': captures, 'result': result})
        first = prepared[0]['result']
        if any(any(p['result'][k] != first[k] for k in ('scenario', 'mode', 'steps')) for p in prepared):
            raise ValueError('Repeated trials must share the same scenario, mode and steps.')
        return prepared

    def close_ids(self, ids):
        for sid in ids:
            session = self.sessions.pop(sid, None)
            if session:
                session['temp'].cleanup()

    def abort(self, data):
        strict_object(data, ('session_id', 'evidence_token'), ('session_id', 'evidence_token'))
        session = self._session(data['session_id'])
        token = data['evidence_token']
        if not isinstance(token, str) or not secrets.compare_digest(token, session['evidence_token']):
            raise ValueError('Invalid evidence capability.')
        self.close_ids([data['session_id']])
        return {'status': 'closed'}

    def expire(self):
        self.close_ids([sid for sid, s in self.sessions.items() if time.monotonic() - s['created'] > 900])

    def close(self):
        self.close_ids(list(self.sessions))
