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


class PracticeReviewSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='learner review ')
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name) / 'my first run'
        result = subprocess.run([sys.executable, str(RUNNER), 'start', '--once',
                                 '--source-port', '0', '--target-port', '0',
                                 '--out', str(self.run)], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def prepare(self, run=None):
        return subprocess.run([sys.executable, str(RUNNER), 'prepare-review',
                               '--run', str(run or self.run)], cwd=self.temp.name,
                              capture_output=True, text=True, timeout=10)

    def test_creates_blank_review_files_bound_to_actual_evidence(self):
        before = {name: (self.run / name).read_bytes() for name in
                  ('evidence.json', 'analysis.json', 'reviews.json', 'report.md')}
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((self.run / 'browser-review.json').read_text())
        self.assertEqual(manifest['evidenceSha256'], json.loads(before['analysis.json'])['evidenceSha256'])
        for key in ('checks', 'components', 'screenshotPairs'):
            self.assertEqual(manifest[key], [])
        self.assertTrue(manifest['limitations'])
        self.assertTrue((self.run / 'browser').is_dir())
        self.assertEqual((self.run / 'audit-checklist.md').read_text(encoding='utf-8'),
                         (ROOT / 'skills/pdf-gap-audit/assets/audit-checklist.md').read_text(encoding='utf-8'))
        for name, content in before.items():
            self.assertEqual((self.run / name).read_bytes(), content)

    def test_repeated_setup_preserves_learner_notes_and_checks(self):
        first = self.prepare()
        self.assertEqual(first.returncode, 0, first.stderr)
        manifest = self.run / 'browser-review.json'
        data = json.loads(manifest.read_text())
        data['learnerNotes'] = 'Keep this in-progress review.'
        data['checks'] = [{'id': 'LEARNER-01', 'outcome': 'unverified'}]
        manifest.write_text(json.dumps(data))
        checklist = self.run / 'audit-checklist.md'
        checklist.write_text(checklist.read_text() + '\nMy recorded observation.\n')
        originals = {p: p.read_bytes() for p in (manifest, checklist)}
        second = self.prepare()
        self.assertEqual(second.returncode, 0, second.stderr)
        for path, content in originals.items():
            self.assertEqual(path.read_bytes(), content)

    def test_foreign_review_evidence_is_rejected_without_rebinding(self):
        manifest = self.run / 'browser-review.json'
        content = json.dumps({'evidenceSha256': 'b' * 64, 'checks': [{'id': 'keep'}]})
        manifest.write_text(content)
        result = self.prepare()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('evidence', result.stderr.lower())
        self.assertEqual(manifest.read_text(), content)
        self.assertFalse((self.run / 'audit-checklist.md').exists())
        self.assertFalse((self.run / 'browser').exists())

    def test_changed_collection_evidence_is_rejected_before_setup(self):
        evidence = self.run / 'evidence.json'
        evidence.write_bytes(evidence.read_bytes() + b'\n')
        result = self.prepare()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('evidence', result.stderr.lower())
        self.assertFalse((self.run / 'browser-review.json').exists())
        self.assertFalse((self.run / 'audit-checklist.md').exists())

    def test_windows_line_endings_keep_the_collected_evidence_binding(self):
        evidence = self.run / 'evidence.json'
        windows_bytes = evidence.read_text(encoding='utf-8').replace('\n', '\r\n').encode('utf-8')
        evidence.write_bytes(windows_bytes)
        expected = json.loads((self.run / 'analysis.json').read_text())['evidenceSha256']
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((self.run / 'browser-review.json').read_text())
        self.assertEqual(manifest['evidenceSha256'], expected)
        self.assertEqual(evidence.read_bytes(), windows_bytes)

    def test_missing_run_is_not_created_by_review_setup(self):
        missing = Path(self.temp.name) / 'not collected'
        result = self.prepare(missing)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('collect', result.stderr.lower())
        self.assertFalse(missing.exists())


if __name__ == '__main__':
    unittest.main()
