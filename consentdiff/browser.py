"""Bounded Playwright worker launcher. No arbitrary executable/URL from HTTP."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import uuid
from urllib.parse import urlsplit

from .config import validate_config
from .processes import ProcessTree, WorkerControl


def node_environment():
    """Also resolve cwd/node_modules when this worker is installed in a wheel."""
    env = os.environ.copy()
    candidates = [str(Path.cwd() / 'node_modules')]
    if env.get('NODE_PATH'):
        candidates.append(env['NODE_PATH'])
    bundled = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
    if bundled.is_dir():
        candidates.append(str(bundled))
    env['NODE_PATH'] = os.pathsep.join(candidates)
    return env


def run_browser(origin, config, control=None, timeout=300):
    config = validate_config(config)
    url = urlsplit(origin)
    if url.scheme != 'http' or url.hostname != '127.0.0.1' or not url.port or url.username or url.password or url.path not in ('', '/') or url.query or url.fragment:
        raise ValueError('Only the owned loopback server is permitted.')
    control = control or WorkerControl()
    node = shutil.which('node')
    if not node:
        raise ValueError('Browser integration needs Node.js and Playwright. See BROWSER_INTEGRATION.md.')
    env = node_environment()
    args = [node, str(Path(__file__).with_name('browser_runner.cjs'))]
    tree = ProcessTree(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    control.attach(tree)
    try:
        stdout, _ = tree.process.communicate(input=json.dumps({'origin': origin, 'config': config}), timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        tree.close()
        tree.process.communicate(timeout=5)
        raise ValueError(f'Browser integration exceeded its {timeout:g} second run limit; no PASS is inferred.') from exc
    finally:
        tree.close()
        control.detach()
        tree.process.wait(timeout=5)
    if control.cancelled.is_set():
        raise ValueError('Browser run cancelled; completed cases remain saved.')
    try:
        output = json.loads(stdout)
    except ValueError as exc:
        raise ValueError('Browser worker could not start. Install Playwright and Chrome; check local runtime configuration.') from exc
    if not isinstance(output, dict):
        raise ValueError('Browser worker returned an invalid result.')
    if tree.process.returncode != 0 or output.get('status') not in ('PASS', 'FAIL'):
        raise ValueError(str(output.get('error', 'Browser worker failed.')))
    return output


class BrowserJobs:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()
        self.closed = False
        self.controls = {}
        self.threads = {}

    def start(self, origin, config):
        config = validate_config(config)
        with self.lock:
            if self.closed:
                raise ValueError('The browser job service is shutting down.')
            if any(j['state'] in ('running', 'cancelling') for j in self.jobs.values()):
                raise ValueError('A browser run is already active.')
            if len(self.jobs) >= 10:
                self.jobs.pop(next(iter(self.jobs)))
            job_id = uuid.uuid4().hex
            self.jobs[job_id] = {'job_id': job_id, 'state': 'running', 'config': config}
            control = self.controls[job_id] = WorkerControl()
        def work():
            try:
                result = run_browser(origin, config, control=control)
                update = {'state': 'complete', 'result': result}
            except Exception as exc:
                update = {'state': 'cancelled' if control.cancelled.is_set() else 'error', 'error': str(exc)}
            with self.lock:
                self.jobs[job_id].update(update)
                self.controls.pop(job_id, None)
                self.threads.pop(job_id, None)
        thread = threading.Thread(target=work, daemon=True)
        with self.lock:
            if self.closed:
                self.jobs[job_id].update(state='cancelled', error='Browser service closed before the worker started.')
                self.controls.pop(job_id, None)
            else:
                self.threads[job_id] = thread
                thread.start()
        return self.get(job_id)

    def get(self, job_id):
        with self.lock:
            if not isinstance(job_id, str) or job_id not in self.jobs:
                raise ValueError('Browser job is unknown.')
            return dict(self.jobs[job_id])

    def cancel(self, job_id):
        with self.lock:
            if not isinstance(job_id, str) or job_id not in self.jobs:
                raise ValueError('Browser job is unknown.')
            control = self.controls.get(job_id)
            if control:
                self.jobs[job_id]['state'] = 'cancelling'
        if control:
            control.cancel()
        return self.get(job_id)

    def close(self):
        with self.lock:
            self.closed = True
            controls, threads = list(self.controls.values()), list(self.threads.values())
        for control in controls:
            control.cancel()
        for thread in threads:
            thread.join(timeout=5)
