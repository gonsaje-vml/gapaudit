"""Verify PDF content, frozen-input reproduction and rejection of stale evidence."""

from copy import deepcopy
import hashlib
import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path
import tempfile
import unittest

import gap_audit as audit
import build_ui
from test_gap_audit import example_evidence

try:
    from PIL import Image
    from pypdf import PdfReader
    import reportlab
except ImportError as error:
    raise unittest.SkipTest('Install skills/pdf-gap-audit/requirements.txt for PDF tests') from error

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('pdf_builder', ROOT / 'skills/pdf-gap-audit/scripts/build_pdf.py')
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def prepare_run(root):
    evidence = example_evidence()
    evidence['config']['name'] = 'Synthetic migration café & QA'
    evidence['configHash'] = audit.digest(evidence['config'])
    reviews = {'evidenceSha256': audit.digest(evidence), 'findings': [{
        'id': 'F-001', 'category': 'content', 'title': 'Synthetic omitted guidance',
        'priority': 'P1', 'disposition': 'confirmed', 'contentFidelity': 'Review',
        'pageIds': ['PAGE-example-lookup'], 'observation': 'Synthetic recorded observation. ' * 180,
        'impact': 'Synthetic test of long-text pagination.', 'recommendation': 'Restore approved guidance.',
        'acceptance': 'Verify guidance in the test fixture.', 'owner': 'TBD',
        'evidence': ['Synthetic fixture: PAGE-example-lookup'],
        'reviewer': 'Synthetic test reviewer', 'reviewedAt': '2026-10-01T12:00:00Z',
    }]}
    audit.write_json(root / 'evidence.json', evidence)
    audit.write_json(root / 'reviews.json', reviews)
    audit.render(root / 'evidence.json', root, root / 'reviews.json')
    return evidence, reviews


def browser_manifest(root, evidence):
    pair = {'id': 'E01', 'title': 'Synthetic component pair', 'pageIds': ['PAGE-example-lookup'],
            'caption': 'Synthetic images are test-only fixtures, not browser observations.'}
    for side, color, url in [('source', 'white', 'https://source.example/lookup'), ('target', 'navy', 'https://preview.example/lookup')]:
        path = root / (side + '.png')
        Image.new('RGB', (800, 600), color).save(path)
        pair[side] = {'path': path.name, 'url': url, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                      'capturedAt': '2026-10-01T12:00:00Z', 'viewport': '1440x900',
                      'state': 'Synthetic fixture', 'crop': [0, 0, 800, 400]}
    return {'schemaVersion': 1, 'evidenceSha256': audit.digest(evidence),
            'checks': [{'id': 'J01', 'name': 'Synthetic lookup check', 'pageIds': ['PAGE-example-lookup'],
                        'viewport': '1440x900', 'outcome': 'fail', 'actions': ['Read the synthetic fixture'],
                        'expected': 'Synthetic guidance present', 'actualSource': 'Synthetic guidance present',
                        'actualTarget': 'Synthetic guidance omitted', 'evidence': ['E01'],
                        'browser': 'Synthetic fixture; no real browser', 'reviewer': 'Synthetic test reviewer',
                        'reviewedAt': '2026-10-01T12:00:00Z'}],
            'components': [{'id': 'C01', 'name': 'Synthetic guidance', 'pageIds': ['PAGE-example-lookup'],
                            'source': 'Present', 'target': 'Omitted', 'status': 'missing',
                            'evidence': ['E01'], 'recommendation': 'Restore approved guidance'}],
            'screenshotPairs': [pair], 'limitations': ['Test-only fixtures; no live site review performed.']}


class PDFSkillTests(unittest.TestCase):
    def test_frozen_inputs_produce_identical_pdf_and_preserve_page_finding_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence, _ = prepare_run(root)
            first = builder.build(root, root / 'first.pdf')
            second = builder.build(root, root / 'second.pdf')
            self.assertEqual((root / 'first.pdf').read_bytes(), (root / 'second.pdf').read_bytes())
            self.assertEqual(first['pdfSha256'], second['pdfSha256'])
            text = '\n'.join(page.extract_text() or '' for page in PdfReader(root / 'first.pdf').pages)
            compact = ''.join(text.split())
            for page in evidence['pages']:
                self.assertIn(page['id'], compact)
            self.assertIn('F-001', text)
            self.assertIn('No browser checks recorded', text)
            for heading in audit.SECTIONS:
                self.assertIn(heading, text)
            self.assertTrue(all(page.extract_text().strip() for page in PdfReader(root / 'first.pdf').pages))

    def test_browser_records_screenshot_labels_and_component_matrix_are_in_pdf(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence, _ = prepare_run(root)
            manifest = browser_manifest(root, evidence)
            audit.write_json(root / 'browser-review.json', manifest)
            record = builder.build(root, root / 'reviewed.pdf', browser_path=root / 'browser-review.json')
            text = '\n'.join(page.extract_text() or '' for page in PdfReader(root / 'reviewed.pdf').pages)
            for value in ('J01', 'C01', 'E01', 'Source', 'Target', 'Component matrix', 'Test-only fixtures'):
                self.assertIn(value, text)
            self.assertNotIn('No browser checks recorded', text)
            self.assertEqual(record['browserManifestSha256'], audit.digest(manifest))

    def test_altered_measurements_and_stale_browser_review_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence, _ = prepare_run(root)
            analysis = json.loads((root / 'analysis.json').read_text())
            altered = deepcopy(analysis)
            altered['summary']['pages'] = 999
            audit.write_json(root / 'analysis.json', altered)
            with self.assertRaisesRegex(ValueError, 'recomputed'):
                builder.build(root, root / 'invalid.pdf')
            self.assertFalse((root / 'invalid.pdf').exists())
            audit.write_json(root / 'analysis.json', analysis)
            manifest = browser_manifest(root, evidence)
            manifest['evidenceSha256'] = 'wrong-run'
            audit.write_json(root / 'browser-review.json', manifest)
            with self.assertRaisesRegex(ValueError, 'evidenceSha256'):
                builder.build(root, root / 'invalid.pdf', browser_path=root / 'browser-review.json')

    def test_standalone_skill_runs_without_repository_paths(self):
        build_ui.build()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with zipfile.ZipFile(ROOT / 'dist/downloads/pdf-gap-audit-skill.zip') as package:
                package.extractall(root)
            run = root / 'run'
            run.mkdir()
            prepare_run(run)
            skill = root / 'pdf-gap-audit'
            subprocess.run([sys.executable, str(skill / 'scripts/build_pdf.py'), '--run', str(run), '--out', str(run / 'portable.pdf')], cwd=root, check=True, capture_output=True, text=True)
            builder.build(run, run / 'reference.pdf')
            self.assertEqual((run / 'portable.pdf').read_bytes(), (run / 'reference.pdf').read_bytes())
            record = json.loads((run / 'portable.build.json').read_text())
            self.assertEqual(record['toolkitSha256'], hashlib.sha256((skill / 'scripts/gap_audit.py').read_bytes()).hexdigest())
            self.assertTrue(PdfReader(run / 'portable.pdf').pages)

    def test_changed_capture_and_invalid_crop_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence, _ = prepare_run(root)
            manifest = browser_manifest(root, evidence)
            manifest['screenshotPairs'][0]['target']['sha256'] = 'changed'
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                builder.validate_browser(manifest, evidence, audit, root)
            manifest = browser_manifest(root, evidence)
            manifest['screenshotPairs'][0]['source']['crop'] = [0, 0, 900, 400]
            with self.assertRaisesRegex(ValueError, 'bounds'):
                builder.validate_browser(manifest, evidence, audit, root)


if __name__ == '__main__':
    unittest.main()
