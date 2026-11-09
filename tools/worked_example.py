"""Publish only the approved, hash-bound fictional practice audit."""

from html import escape
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'practice/finished/2026-11-08'


def read(name, run=None):
    return json.loads(((run or RUN) / name).read_text(encoding='utf-8'))


def approved_files(run=None):
    run = run or RUN
    manifest = read('public-example.json', run)
    files = {}
    for relative, expected in manifest['files'].items():
        source = (run / relative).resolve()
        if not source.is_relative_to(run.resolve()) or not source.is_file():
            raise ValueError('Worked-example file escapes or is missing: ' + relative)
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen worked-example hash mismatch: ' + relative)
        files[relative] = source
    return files


def public_files(run=None, prefix='practice-output/'):
    run = run or RUN
    files = approved_files(run)
    return {prefix + relative: files[relative]
            for relative in read('public-example.json', run)['publicFiles']}


def snippets():
    baseline, reviewed = read('baseline-analysis.json'), read('analysis.json')
    evidence, review, browser = read('evidence.json'), read('reviews.json'), read('browser-review.json')
    assessment, build, qa = read('readiness.json'), read('readiness-audit.build.json'), read('pdf-qa/visual-review.json')
    resource = next(p for p in evidence['pages'] if p['route'] == '/resources/')
    contact = next(c for c in browser['checks'] if c['id'] == 'V03-mobile')
    captured = {'id': resource['id'], 'route': resource['route']}
    for side in ('source', 'target'):
        response = resource[side]
        captured[side] = {key: response[key] for key in ('status', 'snapshot', 'sha256')}
        captured[side]['h1s'] = response['html']['h1s']
    values = {
        'CONFIG': read('demo-inputs/config.json'),
        'EVIDENCE': captured,
        'BASELINE_SUMMARY': baseline['summary'],
        'BROWSER_CHECK': contact,
        'FINDING': review['findings'][0],
        'REVIEWED_SUMMARY': reviewed['summary'],
        'READINESS': {'countBasis': read('census.json')['basis'],
                      'counts': build['counts'], 'globalChart': build['openingSummary']['counts'],
                      'page': {k: assessment['pages'][2][k] for k in
                               ('name', 'visualStatus', 'functionalStatus', 'readiness', 'gaps')}},
        'BUILD_RECORD': {k: build[k] for k in ('rendererVersion', 'pageCount', 'counts', 'pdfSha256', 'assessmentSha256', 'dependencies')},
        'QA': {k: qa[k] for k in ('pageCount', 'visualInspection', 'frozenRebuild', 'scopeConclusion')},
    }
    rendered = {key: json.dumps(value, indent=2, ensure_ascii=False) for key, value in values.items()}
    rendered.update({
        'URLS': (RUN / 'demo-inputs/urls.txt').read_text().strip(),
        'COLLECT_LOG': (RUN / 'collection-console.txt').read_text().strip(),
        'PDF_PAGES': str(build['pageCount']),
        'CAPTURE_COUNT': str(len(read('browser-observations.json')['captures'])),
        'CHECK_COUNT': str(len(browser['checks'])),
        'PASS_COUNT': str(sum(c['outcome'] == 'pass' for c in browser['checks'])),
        'FAIL_COUNT': str(sum(c['outcome'] == 'fail' for c in browser['checks'])),
        'PDF_SHA256': build['pdfSha256'],
    })
    return rendered


def build(output):
    output = Path(output)
    approved = approved_files()
    for relative, source in public_files().items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    values = snippets()
    template = (ROOT / 'site/worked-example.html').read_text(encoding='utf-8')
    page = re.sub(r'\{\{([A-Z_0-9]+)\}\}', lambda m: escape(values[m[1]]), template)
    (output / 'worked-example.html').write_text(page, encoding='utf-8')
    with zipfile.ZipFile(output / 'downloads/gap-audit-worked-example.zip', 'w', zipfile.ZIP_DEFLATED) as packet:
        for relative, source in approved.items():
            packet.write(source, 'run/' + relative)
            if relative.startswith('toolkit/') and relative != 'toolkit/README.md':
                packet.write(source, relative.removeprefix('toolkit/'))
        packet.write(RUN / 'public-example.json', 'run/public-example.json')
        packet.write(RUN / 'README.md', 'README.md')
