"""Build the before/after lesson from two separately frozen practice audits."""

from html import escape
import json
from pathlib import Path
import re
import shutil
import zipfile

import worked_example as frozen

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'practice/finished/2026-11-08-retest'


def comparison():
    data = frozen.read('retest-results.json', RUN)
    metrics = {}
    for label, run in [('before', frozen.RUN), ('after', RUN)]:
        summary = frozen.read('analysis.json', run)['summary']
        checks = frozen.read('browser-review.json', run)['checks']
        build = frozen.read('readiness-audit.build.json', run)
        metrics[label] = {
            'unavailableLinks': summary['unavailableLinks'],
            'affectedPages': summary['affectedPages'],
            'passingChecks': sum(c['outcome'] == 'pass' for c in checks),
            'failingChecks': sum(c['outcome'] == 'fail' for c in checks),
            'totalChecks': len(checks),
            'readyTypes': build['openingSummary']['counts']['Ready'],
            'bodyTypes': build['openingSummary']['total'],
            'renderedTargetUses': frozen.read('census.json', run)['targetBodyUses'],
        }
    data['metrics'] = metrics
    return data


def check_grid(checks):
    return ''.join('<span class="check-dot ' + ('check-pass' if c['outcome'] == 'pass' else 'check-fail') +
                   '" title="' + escape(c['id'] + ': ' + c['name'] + ' / ' + c['outcome'], quote=True) +
                   '" aria-label="' + escape(c['id'] + ' ' + c['outcome'], quote=True) + '"></span>' for c in checks)


def snippets():
    data = comparison()
    repairs = frozen.read('repairs.json', RUN)['changes']
    values = {
        'BEFORE_SUMMARY': json.dumps(frozen.read('analysis.json')['summary'], indent=2),
        'AFTER_SUMMARY': json.dumps(frozen.read('analysis.json', RUN)['summary'], indent=2),
        'LINEAGE': json.dumps({k: data[k] for k in ('baselineEvidenceSha256', 'retestEvidenceSha256', 'comparisonBasis', 'pageMapping')}, indent=2),
        'CLOSURE': json.dumps([{'findingId': f['findingId'], 'status': f['status'], 'result': f['result']} for f in data['findings']], indent=2),
        'NEW_REVIEWS': json.dumps(frozen.read('reviews.json', RUN), indent=2),
        'BEFORE_CHECK_GRID': check_grid(frozen.read('browser-review.json')['checks']),
        'AFTER_CHECK_GRID': check_grid(frozen.read('browser-review.json', RUN)['checks']),
        'DOWNLOAD_DIFF': repairs[0]['diff'],
        'CONTENT_DIFF': repairs[1]['diff'],
        'LAYOUT_DIFF': repairs[2]['diff'],
    }
    for label, metrics in data['metrics'].items():
        for key, value in metrics.items():
            values[label.upper() + '_' + re.sub(r'([a-z])([A-Z])', r'\1_\2', key).upper()] = str(value)
    return values


def build(output):
    output = Path(output)
    for relative, source in frozen.public_files(RUN, prefix='retest-output/').items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    values = snippets()
    raw = {'BEFORE_CHECK_GRID', 'AFTER_CHECK_GRID'}
    template = (ROOT / 'site/retest.html').read_text(encoding='utf-8')
    page = re.sub(r'\{\{([A-Z_0-9]+)\}\}', lambda m: values[m[1]] if m[1] in raw else escape(values[m[1]]), template)
    (output / 'retest.html').write_text(page, encoding='utf-8')
    with zipfile.ZipFile(output / 'downloads/gap-audit-retest-example.zip', 'w', zipfile.ZIP_DEFLATED) as packet:
        for prefix, run in [('before', frozen.RUN), ('after', RUN)]:
            for relative, source in frozen.approved_files(run).items():
                packet.write(source, prefix + '/' + relative)
                if prefix == 'after' and relative.startswith('kit/') and relative not in ('kit/README.md', 'kit/guide.css'):
                    packet.write(source, relative.removeprefix('kit/'))
            packet.write(run / 'public-example.json', prefix + '/public-example.json')
        packet.write(RUN / 'README.md', 'README.md')
        # Style the current teaching page; archived kits keep their original CSS.
        packet.write(ROOT / 'site/guide.css', 'guide.css')
        offline = page.replace('href="./index.html"', 'href="https://gonsaje-vml.github.io/gapaudit/"')
        offline = offline.replace('href="./practice.html"', 'href="https://gonsaje-vml.github.io/gapaudit/practice.html"')
        offline = offline.replace('href="./retest.html"', 'href="./START-HERE.html"')
        offline = offline.replace('href="./worked-example.html"', 'href="https://gonsaje-vml.github.io/gapaudit/worked-example.html"')
        offline = offline.replace('./practice-output/', './before/').replace('./retest-output/', './after/')
        offline = offline.replace('href="./downloads/gap-audit-retest-example.zip"', 'href="https://gonsaje-vml.github.io/gapaudit/downloads/gap-audit-retest-example.zip"')
        packet.writestr('START-HERE.html', offline)
