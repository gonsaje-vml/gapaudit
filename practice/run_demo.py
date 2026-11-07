"""Serve fictional migration sites and collect a real, local practice audit.

Python 3.10+; standard library only. Run from the extracted kit's top level.
"""

import argparse
from contextlib import contextmanager, ExitStack
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import gap_audit  # noqa: E402


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


@contextmanager
def local_sites(source_port, target_port):
    """Serve only the two fixture trees; release every port on all exit paths."""
    with ExitStack() as cleanup:
        servers = []
        for side, port in (('source', source_port), ('target', target_port)):
            handler = partial(QuietHandler, directory=str(ROOT / 'practice/sites' / side))
            try:
                server = ThreadingHTTPServer(('127.0.0.1', port), handler)
            except OSError as error:
                raise OSError(f'Cannot open {side} port {port}: {error}. '
                              'Choose unused --source-port and --target-port values.') from error
            cleanup.callback(server.server_close)
            servers.append(server)
        for server in servers:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            cleanup.callback(worker.join)
            cleanup.callback(server.shutdown)
        yield tuple(f'http://127.0.0.1:{server.server_port}' for server in servers)


def collect_practice(source, target, output):
    config = {
        'name': 'Northstar practice migration — fictional local sites',
        'sourceOrigin': source, 'targetOrigin': target,
        'inventories': [{'kind': 'urls', 'location': 'urls.txt'}],
        'includePrefixes': ['/'], 'excludePrefixes': [],
        'routeMap': {'/guide/': '/help/'}, 'documentPrefixes': ['/downloads/'],
        'maxPages': 10, 'maxLinks': 30, 'maxSitemaps': 5,
        'timeoutSeconds': 5, 'requestDelaySeconds': 0,
    }
    with tempfile.TemporaryDirectory(prefix='gap-practice-inputs-') as temp:
        inputs = Path(temp)
        (inputs / 'config.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
        (inputs / 'urls.txt').write_text(''.join(source + route + '\n' for route in
                                               ('/', '/resources/', '/contact/', '/guide/')), encoding='utf-8')
        gap_audit.collect(inputs / 'config.json', output)
        shutil.copytree(inputs, output / 'demo-inputs')
    shutil.copy2(ROOT / 'practice/scope.md', output / 'scope.md')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    start = commands.add_parser('start', help='Collect a new practice audit, then keep sites open')
    start.add_argument('--out', default='runs/practice-01', help='New output directory')
    start.add_argument('--once', action='store_true', help='Collect then stop both sites')
    serve = commands.add_parser('serve', help='Open sample sites without collecting')
    for command in (start, serve):
        command.add_argument('--source-port', type=int, default=8851)
        command.add_argument('--target-port', type=int, default=8852)
    args = parser.parse_args()
    for port in (args.source_port, args.target_port):
        if not 0 <= port <= 65535:
            parser.error('Ports must be between 0 and 65535 (0 chooses an available port).')
    output = Path(args.out).resolve() if args.command == 'start' else None
    if output is not None and output.exists():
        parser.exit(1, f'Practice demo failed: output already exists: {output}. '
                       'Use a new --out name, or use serve to reopen the sites.\n')
    try:
        with local_sites(args.source_port, args.target_port) as (source, target):
            print(f'Source: {source}/\nTarget: {target}/', flush=True)
            if output is not None:
                collect_practice(source, target, output)
                print(f'\nOpen report: {output / "report.md"}\n'
                      'Next: compare the sites using practice/README.md.\n'
                      'This is fictional practice data; browser checks are not performed automatically.', flush=True)
                if args.once:
                    print('One-shot collection finished; sample sites are stopping.', flush=True)
                    return 0
            print('Keep this terminal open for browser review. Press Ctrl+C to stop.', flush=True)
            threading.Event().wait()
    except KeyboardInterrupt:
        print('\nSample sites stopped. Your saved audit is unchanged.')
    except (OSError, ValueError) as error:
        parser.exit(1, f'Practice demo failed: {error}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
