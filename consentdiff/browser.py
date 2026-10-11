"""Bounded Playwright worker launcher. No arbitrary executable/URL from HTTP."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import uuid

from .config import validate_config


def run_browser(origin, config):
    config = validate_config(config)
    node = shutil.which('node')
    if not node:
        raise ValueError('Browser integration needs Node.js and Playwright. See BROWSER_INTEGRATION.md.')
    env = os.environ.copy()
    bundled = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
    if not env.get('NODE_PATH') and bundled.is_dir():
        env['NODE_PATH'] = str(bundled)
    args = [node, str(Path(__file__).with_name('browser_runner.cjs'))]
    options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    try:
        result = subprocess.run(args, input=json.dumps({'origin': origin, 'config': config}), text=True,
            capture_output=True, timeout=300, env=env, **options)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('Browser integration exceeded the 5 minute run limit; no PASS is inferred.') from exc
    try:
        output = json.loads(result.stdout)
    except ValueError as exc:
        raise ValueError('Browser worker could not start. Install Playwright and Chrome; check local runtime configuration.') from exc
    if result.returncode != 0 or output.get('status') == 'ERROR':
        raise ValueError(output.get('error', 'Browser worker failed.'))
    return output


class BrowserJobs:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()

    def start(self, origin, config):
        config = validate_config(config)
        with self.lock:
            if any(j['state'] == 'running' for j in self.jobs.values()):
                raise ValueError('A browser run is already active.')
            if len(self.jobs) >= 10:
                self.jobs.pop(next(iter(self.jobs)))
            job_id = uuid.uuid4().hex
            self.jobs[job_id] = {'job_id': job_id, 'state': 'running', 'config': config}
        def work():
            try:
                result = run_browser(origin, config)
                update = {'state': 'complete', 'result': result}
            except (ValueError, OSError) as exc:
                update = {'state': 'error', 'error': str(exc)}
            with self.lock:
                self.jobs[job_id].update(update)
        threading.Thread(target=work, daemon=True).start()
        return self.get(job_id)

    def get(self, job_id):
        with self.lock:
            if job_id not in self.jobs:
                raise ValueError('Browser job is unknown.')
            return dict(self.jobs[job_id])
