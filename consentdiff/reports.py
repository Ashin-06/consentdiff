"""Escaped, portable offline evidence report."""
from html import escape
import json


def render_report(case):
    r = case['result']
    def block(title, value):
        return '<section><h2>' + escape(title) + '</h2><pre>' + escape(json.dumps(value, indent=2, ensure_ascii=False)) + '</pre></section>'
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ConsentDiff evidence report</title><style>body{background:#101522;color:#e8eef7;font:16px/1.6 system-ui;max-width:1100px;margin:40px auto;padding:0 20px}h1{font-size:36px;color:#c8b9ff}section{background:#192031;padding:24px;border-radius:12px;margin:18px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:700px){.pair{display:block}}</style>' + \
        '<p>CONSENTDIFF / LOCAL INTENT & EFFECT LAB</p><h1>' + escape(r['status'] + ' · ' + r['scenario']['title']) + '</h1><p>' + escape(case['case_id'] + ' · ' + case['created_at']) + '</p>' + \
        '<p>' + escape(r.get('scope', 'Controller-level paired workflow test.')) + '</p>' + \
        (block('Browser runtime and native capability', r['runtime']) if r.get('execution') == 'browser' else '<p>The human adapter shares the visible demo controller. This controller run does not claim browser or native WebMCP execution.</p>') + \
        block('Frozen intent', r['intent']) + block('Findings', r['findings']) + '<div class="pair">' + \
        ''.join(block(driver.title() + ' · observed effects', r['journeys'][driver]['after']) for driver in ('human', 'tool')) + '</div>' + \
        ''.join(block(driver.title() + ' · action and confirmation record', r['journeys'][driver]['trace']) for driver in ('human', 'tool')) + \
        block('Scope and limitations', r['limitations']) + '<p>The unsigned SHA-256 manifest checks integrity relative to its hashes, not authenticity or proof of execution.</p></html>'
