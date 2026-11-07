"""Exercise the learner's CLI against the actual local practice websites."""

import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / 'practice/run_demo.py'


class PracticeRunnerTests(unittest.TestCase):
    def test_practice_collection_and_offline_reproduction(self):
        with tempfile.TemporaryDirectory(prefix='gap practice ') as temp:
            run = Path(temp) / 'my first run'
            result = subprocess.run(
                [sys.executable, str(RUNNER), 'start', '--once', '--source-port', '0',
                 '--target-port', '0', '--out', str(run)],
                cwd=temp, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            analysis = json.loads((run / 'analysis.json').read_text())
            self.assertEqual(analysis['summary']['pages'], 4)
            self.assertEqual(analysis['summary']['comparablePages'], 4)
            self.assertEqual(analysis['summary']['unavailableLinks'], 1)
            self.assertEqual(analysis['summary']['affectedPages'], 2)
            self.assertEqual(analysis['findings'], [])
            rows = {row['route']: row for row in analysis['rows']}
            self.assertEqual(rows['/resources/']['content'], 'Review')
            self.assertIn('Missing H1: regression', rows['/resources/']['flags'])
            self.assertEqual(rows['/contact/']['content'], 'Good')
            evidence = json.loads((run / 'evidence.json').read_text())
            guide = next(p for p in evidence['pages'] if p['route'] == '/guide/')
            self.assertTrue(guide['target']['url'].endswith('/help/'))
            config = json.loads((run / 'demo-inputs/config.json').read_text())
            self.assertEqual(config['routeMap'], {'/guide/': '/help/'})
            self.assertTrue((run / 'demo-inputs/urls.txt').is_file())
            self.assertTrue((run / 'scope.md').is_file())
            initial = (run / 'report.md').read_bytes()
            subprocess.run([sys.executable, str(ROOT / 'tools/gap_audit.py'),
                            'render', '--evidence', str(run / 'evidence.json'),
                            '--reviews', str(run / 'reviews.json'), '--out', str(run)],
                           check=True, capture_output=True, timeout=20)
            self.assertEqual(initial, (run / 'report.md').read_bytes())

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / 'keep.txt'
            marker.write_text('keep this run')
            result = subprocess.run([sys.executable, str(RUNNER), 'start', '--once',
                                     '--out', temp], capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('already exists', result.stderr)
            self.assertEqual(marker.read_text(), 'keep this run')
            self.assertEqual(list(Path(temp).iterdir()), [marker])

    def test_busy_target_port_releases_source_port(self):
        with socket.socket() as occupied, socket.socket() as available:
            occupied.bind(('127.0.0.1', 0))
            occupied.listen()
            target_port = occupied.getsockname()[1]
            available.bind(('127.0.0.1', 0))
            source_port = available.getsockname()[1]
            available.close()
            result = subprocess.run([sys.executable, str(RUNNER), 'serve',
                                     '--source-port', str(source_port),
                                     '--target-port', str(target_port)],
                                    capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('port', result.stderr.lower())
            with socket.socket() as released:
                released.bind(('127.0.0.1', source_port))


if __name__ == '__main__':
    unittest.main()
