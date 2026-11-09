"""The public worked example must retain real records and original captures."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import worked_example


class WorkedExampleTests(unittest.TestCase):
    def test_published_files_are_bound_to_the_frozen_manifest(self):
        files = worked_example.public_files()
        self.assertIn('practice-output/readiness-audit.pdf', files)
        self.assertIn('practice-output/browser/contact-target-mobile.jpg', files)
        manifest = json.loads((worked_example.RUN / 'public-example.json').read_text())
        for source in files.values():
            relative = source.relative_to(worked_example.RUN).as_posix()
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), manifest['files'][relative])
        self.assertFalse(any('migration-work' in str(p) for p in files.values()))

    def test_teaching_snippets_use_actual_baseline_and_reviewed_outputs(self):
        snippets = worked_example.snippets()
        baseline = json.loads((worked_example.RUN / 'baseline-analysis.json').read_text())
        reviewed = json.loads((worked_example.RUN / 'analysis.json').read_text())
        self.assertEqual(json.loads(snippets['BASELINE_SUMMARY']), baseline['summary'])
        self.assertEqual(json.loads(snippets['REVIEWED_SUMMARY']), reviewed['summary'])
        self.assertEqual(json.loads(snippets['FINDING'])['id'], 'F-001')
        self.assertEqual(baseline['summary']['confirmedFindings'], 0)
        self.assertEqual(reviewed['summary']['confirmedFindings'], 3)

    def test_example_download_preserves_all_approved_original_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output / 'downloads').mkdir()
            worked_example.build(output)
            self.assertTrue((output / 'worked-example.html').is_file())
            self.assertNotIn('{{', (output / 'worked-example.html').read_text())
            with zipfile.ZipFile(output / 'downloads/gap-audit-worked-example.zip') as packet:
                self.assertEqual(len(packet.namelist()), len(set(packet.namelist())))
                self.assertIn('run/readiness-audit.pdf', packet.namelist())
                self.assertIn('tools/gap_audit.py', packet.namelist())
                self.assertIn('skills/pdf-gap-audit/scripts/build_readiness_pdf.py', packet.namelist())
                manifest = json.loads((worked_example.RUN / 'public-example.json').read_text())
                for relative, expected in manifest['files'].items():
                    self.assertEqual(hashlib.sha256(packet.read('run/' + relative)).hexdigest(), expected)
                self.assertFalse(any('migration-work' in n or '__pycache__' in n for n in packet.namelist()))


if __name__ == '__main__':
    unittest.main()
