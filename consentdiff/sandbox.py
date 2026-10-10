"""Bounded ephemeral demo sessions for the visible human and tool controls."""
from pathlib import Path
import tempfile
import uuid

from .core import Application, get_spec, observe


class Sandbox:
    def __init__(self):
        self.sessions = {}

    def start(self, scenario_id='CD-002', mode='seeded'):
        spec = get_spec(scenario_id)
        if mode not in ('seeded', 'repaired'):
            raise ValueError('Mode must be seeded or repaired.')
        if len(self.sessions) >= 8:
            self.sessions.pop(next(iter(self.sessions)))['temp'].cleanup()
        temp = tempfile.TemporaryDirectory(prefix='consentdiff-visible-')
        variant = spec['variant'] if mode == 'seeded' else 'safe'
        session_id = uuid.uuid4().hex
        self.sessions[session_id] = {'temp': temp, 'spec': spec, 'mode': mode,
            'apps': {driver: Application(Path(temp.name) / (driver + '.sqlite'), driver, variant) for driver in ('human', 'tool')}}
        return {'session_id': session_id, 'scenario': spec, 'mode': mode, 'states': {d: observe(app.path, identity_mapping=app.mapping) for d, app in self.sessions[session_id]['apps'].items()}}

    def action(self, session_id, driver, action):
        if not isinstance(session_id, str) or session_id not in self.sessions:
            raise ValueError('Demo session expired or missing; start a fresh session.')
        session = self.sessions[session_id]
        if driver not in ('human', 'tool'):
            raise ValueError('Driver must be human or tool.')
        app = session['apps'][driver]
        if len(app.trace) >= 100:
            raise ValueError('Demo action limit reached; start a fresh session.')
        response = app.action(action)
        return {'session_id': session_id, 'driver': driver, 'response': response, 'plan': app.plan,
                'approval': app.approval, 'trace': app.trace,
                'observation': observe(app.path, available=session['spec']['variant'] != 'observer_unavailable', identity_mapping=app.mapping)}

    def close(self):
        for session in self.sessions.values():
            session['temp'].cleanup()
        self.sessions.clear()
