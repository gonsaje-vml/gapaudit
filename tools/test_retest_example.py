"""The retest lesson keeps both issued runs and proves repaired-kit portability."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

import retest_example
import worked_example


class RetestExampleTests(unittest.TestCase):
    def test_comparison_uses_fresh_evidence_and_stable_finding_ids(self):
        data = retest_example.comparison()
        self.assertNotEqual(data['baselineEvidenceSha256'], data['retestEvidenceSha256'])
        self.assertEqual(data['counts'], {'fixed': 3, 'stillOpen': 0, 'new': 0, 'unverified': 0})
        self.assertEqual([r['findingId'] for r in data['findings']], ['F-001', 'F-002', 'F-003'])
        before = worked_example.read('browser-review.json')
        after = worked_example.read('browser-review.json', retest_example.RUN)
        self.assertEqual([c['id'] for c in before['checks']], [c['id'] for c in after['checks']])
        self.assertEqual(len(after['checks']), 17)
        self.assertTrue(all(c['outcome'] == 'pass' for c in after['checks']))
        reviews = worked_example.read('reviews.json', retest_example.RUN)
        self.assertEqual(reviews['evidenceSha256'], data['retestEvidenceSha256'])
        self.assertEqual(reviews['findings'], [])

    def test_download_contains_both_frozen_runs_and_runnable_repaired_copy(self):
        with tempfile.TemporaryDirectory(prefix='retest packet ') as temp:
            output = Path(temp) / 'published'
            (output / 'downloads').mkdir(parents=True)
            retest_example.build(output)
            self.assertNotIn('{{', (output / 'retest.html').read_text())
            root = Path(temp) / 'extracted'
            with zipfile.ZipFile(output / 'downloads/gap-audit-retest-example.zip') as packet:
                self.assertEqual(len(packet.namelist()), len(set(packet.namelist())))
                self.assertIn('START-HERE.html', packet.namelist())
                packet.extractall(root)
                for prefix, run in [('before', worked_example.RUN), ('after', retest_example.RUN)]:
                    manifest = worked_example.read('public-example.json', run)
                    for relative, expected in manifest['files'].items():
                        self.assertEqual(hashlib.sha256(packet.read(prefix + '/' + relative)).hexdigest(), expected)
            result = subprocess.run([sys.executable, 'practice/run_demo.py', 'start', '--sites', 'repaired',
                                     '--once', '--source-port', '0', '--target-port', '0', '--out', 'my retest'],
                                    cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads((root / 'my retest/analysis.json').read_text())
            self.assertEqual(data['summary']['unavailableLinks'], 0)


if __name__ == '__main__':
    unittest.main()
