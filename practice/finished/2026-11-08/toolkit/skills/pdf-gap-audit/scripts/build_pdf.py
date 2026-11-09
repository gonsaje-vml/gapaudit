#!/usr/bin/env python3
"""Render a verified gap-audit run and optional browser evidence to a fixed PDF."""

import argparse
from functools import partial
import hashlib
import html
import importlib.metadata
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import zlib
from urllib.parse import urlsplit

import reportlab
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Image, LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, TableStyle

VERSION = '1.0.0'
ROOT = Path(__file__).resolve().parents[3]
PACKAGED_TOOLKIT = Path(__file__).with_name('gap_audit.py')
DEFAULT_TOOLKIT = PACKAGED_TOOLKIT if PACKAGED_TOOLKIT.is_file() else ROOT / 'tools/gap_audit.py'
NAVY = colors.HexColor('#0d2264')
INK = colors.HexColor('#253047')
MUTED = colors.HexColor('#536077')
LINE = colors.HexColor('#dce1e9')
PALE = colors.HexColor('#f7f8fa')
WIDTH = 528


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_toolkit(path):
    spec = importlib.util.spec_from_file_location('pdf_audit_toolkit', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def nonempty(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} must be a nonempty string')


def page_ids(value, known):
    if not isinstance(value, list) or not value or not set(value) <= known:
        raise ValueError('Browser review must reference actual pageIds from this evidence')


def validate_browser(value, evidence, audit, run):
    run = Path(run).resolve()
    if value.get('schemaVersion') != 1 or value.get('evidenceSha256') != audit.digest(evidence):
        raise ValueError('Browser manifest must use schemaVersion 1 and this evidenceSha256')
    ids = {page['id'] for page in evidence['pages']}
    for field in ('checks', 'components', 'screenshotPairs', 'limitations'):
        if not isinstance(value.get(field), list):
            raise ValueError(f'Browser manifest requires a {field} array')
    for field in ('checks', 'components', 'screenshotPairs'):
        records = value[field]
        if len({record['id'] for record in records}) != len(records):
            raise ValueError(f'Duplicate IDs in {field}')
        for record in records:
            nonempty(record.get('id'), field + '.id')
            page_ids(record.get('pageIds'), ids)
    for check in value['checks']:
        nonempty(check.get('name'), 'check.name')
        if check.get('outcome') not in ('pass', 'fail', 'unverified'):
            raise ValueError('Check outcome must be pass, fail or unverified')
        for field in ('actions', 'evidence'):
            if not isinstance(check.get(field), list):
                raise ValueError(f'Check requires an {field} array')
        for field in ('viewport', 'expected', 'actualSource', 'actualTarget'):
            nonempty(check.get(field), 'check.' + field)
        if check['outcome'] != 'unverified':
            for field in ('reviewer', 'reviewedAt', 'browser'):
                nonempty(check.get(field), 'check.' + field)
            if not check['actions'] or not check['evidence']:
                raise ValueError('Passing/failing checks need actions and evidence')
    for component in value['components']:
        if component.get('status') not in ('retained', 'changed', 'missing', 'unverified'):
            raise ValueError('Component status must be retained, changed, missing or unverified')
        for field in ('name', 'source', 'target', 'recommendation'):
            nonempty(component.get(field), 'component.' + field)
        if not isinstance(component.get('evidence'), list) or (component['status'] != 'unverified' and not component['evidence']):
            raise ValueError('Observed components need evidence references')
    for pair in value['screenshotPairs']:
        for field in ('title', 'caption'):
            nonempty(pair.get(field), 'pair.' + field)
        for side in ('source', 'target'):
            panel = pair[side]
            for field in ('path', 'url', 'sha256', 'capturedAt', 'viewport', 'state'):
                nonempty(panel.get(field), 'panel.' + field)
            if urlsplit(panel['url']).scheme not in ('http', 'https'):
                raise ValueError('Capture URLs must use HTTP(S)')
            path = (run / panel['path']).resolve()
            if not path.is_relative_to(run) or not path.is_file():
                raise ValueError('Capture paths must point to files inside this run')
            if file_hash(path) != panel['sha256']:
                raise ValueError(f'Screenshot hash mismatch: {panel["path"]}')
            with PILImage.open(path) as image:
                box = panel.get('crop', [0, 0, image.width, image.height])
                if not isinstance(box, list) or len(box) != 4 or any(type(x) is not int for x in box):
                    raise ValueError('Crop must be four integer pixel bounds')
                left, top, right, bottom = box
                if not 0 <= left < right <= image.width or not 0 <= top < bottom <= image.height:
                    raise ValueError('Crop exceeds original screenshot bounds')
    for limitation in value['limitations']:
        nonempty(limitation, 'limitation')
    return value


def inline(value):
    text = html.escape(html.unescape(str(value)), quote=False).replace('\n', '<br/>')
    text = re.sub(r'`([^`]+)`', r'<font name="Audit">\1</font>', text)
    return re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)


def make_styles():
    body = ParagraphStyle('body', fontName='Audit', fontSize=9.5, leading=14, textColor=INK, spaceAfter=8, splitLongWords=1)
    return {
        'body': body,
        'title': ParagraphStyle('title', parent=body, fontName='Audit-Bold', fontSize=24, leading=29, textColor=NAVY, spaceAfter=18),
        'h2': ParagraphStyle('h2', parent=body, fontName='Audit-Bold', fontSize=15, leading=19, textColor=NAVY, spaceBefore=17, spaceAfter=10, keepWithNext=True),
        'h3': ParagraphStyle('h3', parent=body, fontName='Audit-Bold', fontSize=11, leading=15, textColor=NAVY, spaceBefore=9, keepWithNext=True),
        'cell': ParagraphStyle('cell', parent=body, fontSize=7.5, leading=10, spaceAfter=0),
        'small': ParagraphStyle('small', parent=body, fontSize=7.5, leading=11, textColor=MUTED),
    }


def paragraph(value, style):
    return Paragraph(inline(value), style)


def table(rows, styles, widths=None):
    cells = [[paragraph(value, styles['cell']) for value in row] for row in rows]
    count = len(rows[0])
    widths = widths or [WIDTH / count] * count
    result = LongTable(cells, colWidths=widths, repeatRows=1, splitInRow=1, hAlign='LEFT', spaceAfter=12)
    result.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PALE), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -1), .4, LINE),
        ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    return result


def markdown_story(text, styles):
    lines = text.splitlines()
    story = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.startswith('# '):
            index += 1
            continue
        if line.startswith('|'):
            rows = []
            while index < len(lines) and lines[index].startswith('|'):
                row = [cell.strip() for cell in lines[index].strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', cell) for cell in row):
                    rows.append(row)
                index += 1
            if rows:
                widths = [110, 53, 60, 65, 80, 160] if len(rows[0]) == 6 else None
                story.append(table(rows, styles, widths))
            continue
        if line.startswith('## '):
            story.append(paragraph(line[3:], styles['h2']))
        elif line.startswith('### '):
            story.append(paragraph(line[4:], styles['h3']))
        elif line.startswith('- '):
            story.append(paragraph('• ' + line[2:], styles['body']))
        else:
            story.append(paragraph(line, styles['body']))
        index += 1
    return story


def capture_image(run, panel):
    with PILImage.open(run / panel['path']) as source:
        box = panel.get('crop', [0, 0, source.width, source.height])
        capture = source.crop(box).convert('RGB')
        content = io.BytesIO()
        capture.save(content, format='PNG')
        content.seek(0)
        ratio = min(250 / capture.width, 225 / capture.height)
        return Image(content, width=capture.width * ratio, height=capture.height * ratio)


def browser_story(browser, run, styles):
    story = [paragraph('Browser and component review', styles['h2'])]
    if not browser or not browser['checks']:
        story.append(paragraph('No browser checks recorded. Visual, mobile, keyboard and journey behavior remain unverified.', styles['body']))
    if not browser:
        return story
    if browser['checks']:
        rows = [['Check / affected pages', 'Viewport / outcome', 'Evidence']]
        for check in browser['checks']:
            rows.append([f'{check["id"]}: {check["name"]}\n' + ', '.join(check['pageIds']), f'{check["viewport"]}: {check["outcome"]}', '; '.join(check['evidence'])])
        story.append(table(rows, styles))
        for check in browser['checks']:
            story.append(paragraph(f'{check["id"]} - {check["name"]}', styles['h3']))
            for label, value in [('Actions', ' → '.join(check['actions'])), ('Expected', check['expected']), ('Source', check['actualSource']), ('Target', check['actualTarget'])]:
                story.append(paragraph(label + ': ' + value, styles['body']))
            story.append(paragraph(f'Reviewer: {check.get("reviewer") or "Unverified"}; {check.get("reviewedAt") or "time not recorded"}; {check.get("browser") or "browser not recorded"}', styles['small']))
    if browser['components']:
        story.append(paragraph('Component matrix', styles['h2']))
        rows = [['Component / pages', 'Source / target', 'Status / evidence', 'Required action']]
        for component in browser['components']:
            rows.append([component['id'] + ': ' + component['name'] + '; ' + ', '.join(component['pageIds']), 'Source: ' + component['source'] + '\nTarget: ' + component['target'], component['status'] + '; ' + '; '.join(component['evidence']), component['recommendation']])
        story.append(table(rows, styles, [110, 180, 92, 146]))
    for pair in browser['screenshotPairs']:
        story.extend([PageBreak(), paragraph(pair['id'] + ' - ' + pair['title'], styles['h2']), paragraph(pair['caption'], styles['body'])])
        labels = [paragraph('Source', styles['h3']), paragraph('Target', styles['h3'])]
        images = [capture_image(run, pair[side]) for side in ('source', 'target')]
        details = []
        for side in ('source', 'target'):
            panel = pair[side]
            details.append(paragraph(f'{panel["url"]}\n{panel["viewport"]}; {panel["state"]}\n{panel["capturedAt"]}; {panel["path"]}', styles['small']))
        panels = LongTable([labels, images, details], colWidths=[264, 264], splitInRow=1, hAlign='LEFT')
        panels.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 14)]))
        story.append(panels)
        story.append(paragraph('Affected pages: ' + ', '.join(pair['pageIds']) + '. Original captures and crop bounds are retained in the browser manifest.', styles['small']))
    if browser['limitations']:
        story.append(paragraph('Remaining review limits', styles['h2']))
        story.extend(paragraph('• ' + item, styles['body']) for item in browser['limitations'])
    return story


def build(run, output, toolkit=DEFAULT_TOOLKIT, browser_path=None, font_regular=None, font_bold=None):
    run = Path(run).resolve()
    output = Path(output).resolve()
    audit = load_toolkit(toolkit)
    evidence = load_json(run / 'evidence.json')
    reviews = load_json(run / 'reviews.json')
    analysis = audit.analyze(evidence, reviews)
    if load_json(run / 'analysis.json') != analysis:
        raise ValueError('analysis.json differs from the recomputed evidence/reviews; run render first')
    report = audit.report(evidence, analysis)
    if (run / 'report.md').read_text(encoding='utf-8') != report:
        raise ValueError('report.md differs from the measured report; run render first')
    browser = validate_browser(load_json(browser_path), evidence, audit, run) if browser_path else None
    fontdir = Path(reportlab.__file__).parent / 'fonts'
    regular = Path(font_regular or fontdir / 'Vera.ttf')
    bold = Path(font_bold or fontdir / 'VeraBd.ttf')
    pdfmetrics.registerFont(TTFont('Audit', str(regular)))
    pdfmetrics.registerFont(TTFont('Audit-Bold', str(bold)))
    pdfmetrics.registerFontFamily('Audit', normal='Audit', bold='Audit-Bold', italic='Audit', boldItalic='Audit-Bold')
    text = html.unescape(report + (json.dumps(browser, ensure_ascii=False) if browser else ''))
    available = set(pdfmetrics.getFont('Audit').face.charToGlyph) & set(pdfmetrics.getFont('Audit-Bold').face.charToGlyph)
    missing = sorted({character for character in text if ord(character) > 32 and ord(character) not in available})
    if missing:
        raise ValueError('Fonts lack characters ' + repr(''.join(missing)) + '; provide matching --font-regular and --font-bold TTF files')
    styles = make_styles()
    story = [paragraph(evidence['config']['name'] + ' - Migration Gap Audit', styles['title'])]
    story.extend(markdown_story(report, styles))
    story.extend([PageBreak(), *browser_story(browser, run, styles)])
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output), pagesize=(612, 792), invariant=1, leftMargin=42, rightMargin=42, topMargin=46, bottomMargin=46, title=evidence['config']['name'] + ' - Migration Gap Audit', author='Gap audit toolkit')

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.line(42, 34, 570, 34)
        canvas.setFont('Audit', 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(42, 23, f'Method {audit.VERSION} / PDF {VERSION} / evidence-backed migration audit')
        canvas.drawRightString(570, 23, str(document.page))
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer, canvasmaker=partial(Canvas, invariant=1))
    record = {
        'pdfRendererVersion': VERSION, 'toolkitVersion': audit.VERSION,
        'evidenceSha256': analysis['evidenceSha256'], 'reviewsSha256': analysis['reviewsSha256'],
        'browserManifestSha256': audit.digest(browser) if browser else None,
        'builderSha256': file_hash(__file__), 'toolkitSha256': file_hash(toolkit),
        'fontSha256': {'regular': file_hash(regular), 'bold': file_hash(bold)},
        'pythonVersion': sys.version.split()[0], 'platform': sys.platform, 'zlibVersion': zlib.ZLIB_RUNTIME_VERSION,
        'dependencies': {name: importlib.metadata.version(name) for name in ('reportlab', 'Pillow')},
        'pdfSha256': file_hash(output),
    }
    output.with_suffix('.build.json').write_text(audit.json_text(record), encoding='utf-8')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--browser-review', help='browser-review.json using the supplied schema')
    parser.add_argument('--toolkit', default=str(DEFAULT_TOOLKIT))
    parser.add_argument('--font-regular')
    parser.add_argument('--font-bold')
    args = parser.parse_args()
    try:
        build(args.run, args.out, args.toolkit, args.browser_review, args.font_regular, args.font_bold)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'PDF build failed: {error}\n')
    print(f'Wrote {args.out}')


if __name__ == '__main__':
    main()
