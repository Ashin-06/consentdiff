import argparse
import json
from pathlib import Path
import sys

from .core import catalog, minimize, run_suite
from .evidence import bundle_case, run_case, verify_case


def main(argv=None):
    parser = argparse.ArgumentParser(description='ConsentDiff local human/tool consistency reference lab')
    commands = parser.add_subparsers(dest='command', required=True)
    serve = commands.add_parser('serve')
    serve.add_argument('--port', type=int, default=8767)
    serve.add_argument('--runs-dir', default='runs')
    commands.add_parser('catalog')
    for name in ('run', 'minimize', 'suite'):
        sub = commands.add_parser(name)
        sub.add_argument('--mode', choices=['seeded', 'repaired'], default='seeded')
        if name != 'suite':
            sub.add_argument('--scenario', default='CD-002')
        if name == 'run':
            sub.add_argument('--repeats', type=int, default=2)
            sub.add_argument('--output-dir', default='runs')
        if name == 'minimize':
            sub.add_argument('--budget', type=int, default=100)
    verify = commands.add_parser('verify')
    verify.add_argument('directory')
    bundle = commands.add_parser('bundle')
    bundle.add_argument('directory')
    bundle.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'serve':
            from .server import serve
            serve(args.port, args.runs_dir)
            return 0
        if args.command == 'catalog':
            output, status = catalog(), 'PASS'
        elif args.command == 'run':
            output = run_case(args.output_dir, args.scenario, args.mode, args.repeats)
            status = output['result']['status']
        elif args.command == 'minimize':
            output = minimize(args.scenario, args.mode, args.budget)
            status = output['status']
        elif args.command == 'suite':
            output = run_suite(args.mode)
            status = output['status']
        elif args.command == 'verify':
            output = verify_case(args.directory)
            status = output['status']
        else:
            directory, destination = Path(args.directory).resolve(), Path(args.output).resolve()
            if destination.is_relative_to(directory):
                raise ValueError('Save the bundle outside the evidence directory.')
            payload = bundle_case(directory.parent, directory.name)
            with destination.open('xb') as stream:
                stream.write(payload)
            output, status = {'status': 'PASS', 'bundle': str(destination)}, 'PASS'
        print(json.dumps(output, indent=2, ensure_ascii=True))
        return {'PASS': 0, 'FAIL': 1, 'INCONCLUSIVE': 2}.get(status, 2)
    except (ValueError, TypeError, OSError) as exc:
        print(f'ConsentDiff: {exc}', file=sys.stderr)
        return 2
