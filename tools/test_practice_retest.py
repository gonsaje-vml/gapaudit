"""Exercise the repaired copy without changing the deliberately broken lesson."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class PracticeRetestTests(unittest.TestCase):
    def test_repaired_run_removes_static_regressions(self):
        with tempfile.TemporaryDirectory(prefix='practice retest ') as temp:
            result = subprocess.run([sys.executable, str(ROOT / 'practice/run_demo.py'),
                                     'start', '--sites', 'repaired', '--once',
                                     '--source-port', '0', '--target-port', '0', '--out', temp + '/run'],
                                    cwd=temp, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads((Path(temp) / 'run/analysis.json').read_text())
            self.assertEqual(data['summary']['comparablePages'], 4)
            self.assertEqual(data['summary']['unavailableLinks'], 0)
            self.assertEqual(data['summary']['affectedPages'], 0)
            self.assertTrue(all(p['content'] == 'Good' for p in data['rows']))

    def test_repaired_tree_changes_only_the_three_target_files(self):
        original = ROOT / 'practice/sites'
        repaired = ROOT / 'practice/sites-repaired'
        original_files = {p.relative_to(original).as_posix() for p in original.rglob('*') if p.is_file()}
        fixed_files = {p.relative_to(repaired).as_posix() for p in repaired.rglob('*') if p.is_file()}
        self.assertEqual(fixed_files - original_files, {'target/downloads/checklist.txt'})
        self.assertFalse(original_files - fixed_files)
        changed = {p for p in original_files if (original / p).read_bytes() != (repaired / p).read_bytes()}
        self.assertEqual(changed, {'target/resources/index.html', 'target/style.css'})
        self.assertEqual((repaired / 'target/downloads/checklist.txt').read_bytes(),
                         (original / 'source/downloads/checklist.txt').read_bytes())

    def test_original_sites_still_match_the_issued_baseline(self):
        with zipfile.ZipFile(ROOT / 'practice/finished/2026-11-08/capture-archive.zip') as packet:
            for name in packet.namelist():
                if name.startswith('fixtures/'):
                    path = ROOT / 'practice/sites' / name.removeprefix('fixtures/')
                    self.assertEqual(path.read_bytes(), packet.read(name), name)


if __name__ == '__main__':
    unittest.main()
