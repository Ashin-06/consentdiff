"""Strict, executable configuration for the owned local browser integration."""
import json
from pathlib import Path

from .core import catalog, get_spec, trace_for, validate_trace


def strict_object(value, allowed, required=()):
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        raise ValueError('Invalid object fields; expected: ' + ', '.join(sorted(allowed)))


def strict_json(text):
    """Reject ambiguous duplicate keys, non-finite numbers and deep payloads."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError('Non-finite JSON numbers are not accepted: ' + value)
    try:
        value = json.loads(text, object_pairs_hook=unique, parse_constant=constant)
    except RecursionError as exc:
        raise ValueError('JSON nesting is too deep.') from exc
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > 32:
            raise ValueError('JSON nesting is too deep.')
        if isinstance(item, dict):
            pending.extend((v, depth + 1) for v in item.values())
        elif isinstance(item, list):
            pending.extend((v, depth + 1) for v in item)
    return value


def validate_config(value):
    strict_object(value, ('schema_version', 'fixture', 'scenarios', 'modes', 'repeats', 'tool_adapter', 'webmcp_testing'),
                  ('schema_version', 'fixture', 'scenarios'))
    if value['schema_version'] != '1.0' or value['fixture'] != 'consentdiff-owned-local-app':
        raise ValueError('Only schema 1.0 and the owned local ConsentDiff fixture are supported.')
    scenarios = value['scenarios']
    if not isinstance(scenarios, list) or not 1 <= len(scenarios) <= 10:
        raise ValueError('Select 1 to 10 scenarios.')
    normalized, seen = [], set()
    for entry in scenarios:
        strict_object(entry, ('id', 'steps'), ('id',))
        spec = get_spec(entry['id'])
        if spec['id'] in seen:
            raise ValueError('Duplicate scenario identifier.')
        seen.add(spec['id'])
        steps = entry.get('steps', trace_for(spec))
        validate_trace(steps, spec['journey'])
        normalized.append({'id': spec['id'], 'steps': list(steps)})
    modes = value.get('modes', ['seeded'])
    if not isinstance(modes, list) or not modes or len(modes) > 2 or any(m not in ('seeded', 'repaired') for m in modes) or len(set(modes)) != len(modes):
        raise ValueError('Modes must be a unique list of seeded and/or repaired.')
    repeats = value.get('repeats', 2)
    if type(repeats) is not int or not 1 <= repeats <= 3:
        raise ValueError('Browser repeats must be an integer from 1 to 3.')
    adapter = value.get('tool_adapter', 'auto')
    if adapter not in ('auto', 'http', 'native'):
        raise ValueError('Tool adapter must be auto, http, or native.')
    testing = value.get('webmcp_testing', False)
    if type(testing) is not bool:
        raise ValueError('webmcp_testing must be a boolean.')
    return {'schema_version': '1.0', 'fixture': value['fixture'], 'scenarios': normalized,
            'modes': list(modes), 'repeats': repeats, 'tool_adapter': adapter, 'webmcp_testing': testing}


def load_config(path):
    path = Path(path)
    if path.stat().st_size > 65536:
        raise ValueError('Browser config must be at most 64 KiB.')
    return validate_config(strict_json(path.read_text(encoding='utf-8')))


def default_config(scenario_id=None, mode='seeded', repeats=2, tool_adapter='auto', webmcp_testing=False):
    return validate_config({'schema_version': '1.0', 'fixture': 'consentdiff-owned-local-app',
        'scenarios': [{'id': scenario_id}] if scenario_id else [{'id': s['id']} for s in catalog()],
        'modes': [mode], 'repeats': repeats, 'tool_adapter': tool_adapter, 'webmcp_testing': webmcp_testing})
