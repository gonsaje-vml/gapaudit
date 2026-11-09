"""Check the Pages publish boundary and the downloadable kit's real workflow."""

from contextlib import ExitStack
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.parse import urlsplit
import zipfile

import build_ui
import worked_example

ROOT = Path(__file__).resolve().parents[1]


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])
        if tag == 'script':
            self.scripts.append(attrs)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class GuideBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Simulate an upgrade from the old results dashboard.
        stale = ROOT / 'dist/data'
        stale.mkdir(parents=True, exist_ok=True)
        (stale / 'previous-run.json').write_text('{"previousResults": true}')
        old_downloads = ROOT / 'dist/downloads'
        old_downloads.mkdir(exist_ok=True)
        (old_downloads / 'report-reviewed.md').write_text('Previous client report')
        build_ui.build()

    def test_results_and_stale_dashboard_assets_are_not_published(self):
        output = ROOT / 'dist'
        self.assertFalse((output / 'data').exists())
        self.assertFalse((output / 'downloads/report-reviewed.md').exists())
        self.assertFalse((output / '.git').exists())
        self.assertFalse((output / 'migration-work').exists())
        self.assertFalse((output / 'output').exists())
        forbidden = {'.pdf', '.json', '.js', '.mjs', '.pyc'}
        example_files = worked_example.public_files()
        for path in output.rglob('*'):
            if path.suffix in forbidden and path.relative_to(output).as_posix() not in example_files:
                self.assertIn(path.name, ('config.example.json', 'browser-review.example.json'), str(path))
            if path.suffix in {'.md', '.py', '.json', '.html', '.css', '.txt'}:
                text = path.read_text()
                for private_content in ('/Users/jaesong/', 'Healthy Blue', 'E*TRADE', 'Everything Energy', 'develop--elevance-nc'):
                    self.assertNotIn(private_content, text, str(path))

    def test_guide_links_and_anchors_work_without_javascript(self):
        output = ROOT / 'dist'
        for filename in ('index.html', 'practice.html', 'worked-example.html'):
            page = PageLinks()
            page.feed((output / filename).read_text())
            self.assertEqual(page.scripts, [])
            for reference in page.links:
                parsed = urlsplit(reference)
                if parsed.scheme or parsed.netloc:
                    continue
                if parsed.path:
                    destination = (output / parsed.path).resolve()
                    self.assertTrue(destination.is_relative_to(output), reference)
                    self.assertTrue(destination.is_file(), reference)
                    if parsed.fragment and destination.suffix == '.html':
                        linked_page = PageLinks()
                        linked_page.feed(destination.read_text())
                        self.assertIn(parsed.fragment, linked_page.ids, reference)
                elif parsed.fragment:
                    self.assertIn(parsed.fragment, page.ids, reference)

    def test_practice_zip_runs_after_extraction_and_has_offline_visual_guide(self):
        with tempfile.TemporaryDirectory(prefix='extracted practice ') as temp:
            folder = Path(temp)
            with zipfile.ZipFile(ROOT / 'dist/downloads/gap-audit-practice-kit.zip') as kit:
                kit.extractall(folder)
                self.assertIn('practice/sites/source/downloads/checklist.txt', kit.namelist())
                self.assertNotIn('practice/sites/target/downloads/checklist.txt', kit.namelist())
                for name in kit.namelist():
                    self.assertFalse(any(part in name.split('/') for part in
                                         ('migration-work', 'output', 'snapshots', '__pycache__')))
                    if Path(name).suffix in {'.md', '.py', '.json', '.html', '.css', '.txt', '.svg'}:
                        for secret in ('Healthy Blue', 'E*TRADE', '/Users/jaesong/'):
                            self.assertNotIn(secret, kit.read(name).decode('utf-8'), name)
            guide = PageLinks()
            guide.feed((folder / 'START-HERE.html').read_text())
            self.assertEqual(guide.scripts, [])
            for reference in guide.links:
                parsed = urlsplit(reference)
                if parsed.scheme or parsed.netloc:
                    continue
                if parsed.path:
                    self.assertTrue((folder / parsed.path).is_file(), reference)
                elif parsed.fragment:
                    self.assertIn(parsed.fragment, guide.ids, reference)
            self.assertGreaterEqual(len(list((folder / 'diagrams').glob('*.svg'))), 4)
            result = subprocess.run([sys.executable, 'practice/run_demo.py', 'start', '--once',
                                     '--source-port', '0', '--target-port', '0', '--out', 'my first run'],
                                    cwd=folder, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            analysis = json.loads((folder / 'my first run/analysis.json').read_text())
            self.assertEqual(analysis['summary']['pages'], 4)
            self.assertEqual(analysis['summary']['unavailableLinks'], 1)
            self.assertEqual(analysis['summary']['affectedPages'], 2)

    def test_kit_contains_reusable_inputs_and_no_prior_results(self):
        with zipfile.ZipFile(ROOT / 'dist/downloads/gap-audit-kit.zip') as kit:
            names = set(kit.namelist())
            self.assertIn('tools/gap_audit.py', names)
            self.assertIn('skills/pdf-gap-audit/SKILL.md', names)
            self.assertIn('skills/pdf-gap-audit/scripts/build_pdf.py', names)
            self.assertIn('skills/pdf-gap-audit/scripts/verify_pdf.py', names)
            self.assertIn('skills/pdf-gap-audit/requirements.txt', names)
            self.assertIn('skills/pdf-gap-audit/assets/audit-checklist.md', names)
            self.assertIn('config.example.json', names)
            self.assertIn('urls.example.txt', names)
            self.assertIn('docs/gap-audit/review-checklist.md', names)
            for name in names:
                self.assertFalse(any(part in name.split('/') for part in ('migration-work', 'examples', 'snapshots', 'output')), name)
                self.assertNotIn(Path(name).name, ('evidence.json', 'analysis.json', 'reviews.json', 'report.md', 'client-report.md'))
                self.assertNotEqual(Path(name).suffix, '.pdf')
                text = kit.read(name).decode('utf-8')
                for private_content in ('Healthy Blue', 'E*TRADE', 'Everything Energy', '/Users/jaesong/'):
                    self.assertNotIn(private_content, text, name)
            config = json.loads(kit.read('config.example.json'))
            self.assertEqual(config['sourceOrigin'], 'https://source.example')
            self.assertEqual(config['targetOrigin'], 'https://target.example')

    def test_standalone_skill_has_its_own_collector_and_blank_inputs(self):
        with zipfile.ZipFile(ROOT / 'dist/downloads/pdf-gap-audit-skill.zip') as package:
            names = set(package.namelist())
            for required in ('SKILL.md', 'scripts/gap_audit.py', 'scripts/build_pdf.py', 'scripts/build_readiness_pdf.py', 'scripts/verify_pdf.py', 'requirements.txt', 'references/review-protocol.md', 'references/browser-review-schema.md', 'references/readiness-report-schema.md', 'assets/audit-checklist.md', 'assets/config.example.json', 'assets/urls.example.txt'):
                self.assertIn('pdf-gap-audit/' + required, names)
            manifest = json.loads(package.read('pdf-gap-audit/assets/browser-review.example.json'))
            for field in ('checks', 'components', 'screenshotPairs'):
                self.assertEqual(manifest[field], [])
            for name in names:
                text = package.read(name).decode('utf-8')
                self.assertNotEqual(Path(name).suffix, '.pdf')
                for private_content in ('Healthy Blue', 'E*TRADE', 'Everything Energy', '/Users/jaesong/'):
                    self.assertNotIn(private_content, text, name)

    def test_extracted_kit_collects_and_reproduces_its_report(self):
        with tempfile.TemporaryDirectory() as temp, ExitStack() as cleanup:
            folder = Path(temp)
            toolkit = folder / 'kit'
            with zipfile.ZipFile(ROOT / 'dist/downloads/gap-audit-kit.zip') as kit:
                kit.extractall(toolkit)
            origins = []
            page = '<html lang="en"><head><title>Example</title><meta name="description" content="Example page"><link rel="canonical" href="/"></head><body><main><h1>Example</h1><p>Matching source and target content.</p></main></body></html>'
            for side in ('source', 'target'):
                root = folder / side
                root.mkdir()
                (root / 'index.html').write_text(page)
                server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(root)))
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                cleanup.callback(server.server_close)
                cleanup.callback(thread.join)
                cleanup.callback(server.shutdown)
                origins.append(f'http://127.0.0.1:{server.server_port}')
            config = json.loads((toolkit / 'config.example.json').read_text())
            config.update(sourceOrigin=origins[0], targetOrigin=origins[1], requestDelaySeconds=0)
            (toolkit / 'config.json').write_text(json.dumps(config))
            (toolkit / 'urls.txt').write_text(origins[0] + '/\n')
            command = [sys.executable, 'tools/gap_audit.py']
            subprocess.run(command + ['collect', '--config', 'config.json', '--out', 'audit-run-01'], cwd=toolkit, check=True, capture_output=True, text=True)
            run = toolkit / 'audit-run-01'
            first_report = (run / 'report.md').read_bytes()
            analysis = json.loads((run / 'analysis.json').read_text())
            self.assertEqual(analysis['summary']['pages'], 1)
            self.assertEqual(analysis['summary']['comparablePages'], 1)
            self.assertEqual(analysis['summary']['meanTextSimilarity'], 1)
            self.assertEqual(analysis['findings'], [])
            self.assertTrue(any((run / 'snapshots').iterdir()))
            subprocess.run(command + ['render', '--evidence', 'audit-run-01/evidence.json', '--reviews', 'audit-run-01/reviews.json', '--out', 'audit-run-01'], cwd=toolkit, check=True, capture_output=True, text=True)
            self.assertEqual(first_report, (run / 'report.md').read_bytes())


if __name__ == '__main__':
    unittest.main()
