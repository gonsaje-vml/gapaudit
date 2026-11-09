#!/usr/bin/env python3
"""Extract PDF text, check page/finding coverage, and render every page for inspection."""

import argparse
import hashlib
import importlib.util
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

from pypdf import PdfReader


def verify_readiness(reader, assessment, pdf=None):
    """Verify the new report against its assessment, build hash and exact record bytes."""
    assessment=Path(assessment).resolve();data=json.loads(assessment.read_text())
    spec=importlib.util.spec_from_file_location('readiness_contract',Path(__file__).with_name('build_readiness_pdf.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    counts=module.validate_assessment(data,assessment.parent)
    text=''.join(''.join((page.extract_text() or '').split()) for page in reader.pages)
    values=[p['id'] for p in data['pages']]
    for component in data['components']+data['sharedComponents']:
        values.extend([component['id'],component['family'],*component['variants']])
    values.extend(w['id'] for w in data['workItems'])
    missing=[value for value in values if ''.join(value.split()) not in text]
    if missing:raise ValueError('Readiness PDF omits page/component/variant/work references: '+', '.join(missing))
    if 'audit-records.zip' not in reader.attachments:
        raise ValueError('Readiness PDF lacks its original-record attachment')
    with zipfile.ZipFile(BytesIO(reader.attachments['audit-records.zip'][0])) as archive:
        if archive.testzip() is not None:raise ValueError('Embedded original-record archive is corrupt')
        if archive.read('readiness.json')!=assessment.read_bytes():raise ValueError('Embedded assessment differs from the current source assessment')
        manifest=json.loads(archive.read('record-manifest.json'))
        for name,record in manifest['files'].items():
            content=archive.read(name)
            if hashlib.sha256(content).hexdigest()!=record['sha256'] or content!=module.path_at(assessment.parent,record['path']).read_bytes():
                raise ValueError('Embedded original record differs from its source/hash: '+name)
    if pdf:
        pdf=Path(pdf).resolve();build=json.loads(pdf.with_suffix('.build.json').read_text())
        if hashlib.sha256(pdf.read_bytes()).hexdigest()!=build['pdfSha256']:
            raise ValueError('Readiness PDF differs from its build hash')
        if hashlib.sha256(assessment.read_bytes()).hexdigest()!=build['assessmentSha256'] or counts!=build['counts'] or len(reader.pages)!=build['pageCount']:
            raise ValueError('Readiness build counts/assessment hash/page count differ from source')
    return counts


def verify(pdf, output, run=None, renderer=None, assessment=None):
    pdf, output = Path(pdf).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(pdf)
    readiness_counts=verify_readiness(reader,assessment,pdf) if assessment else None
    text_by_page = [page.extract_text() or '' for page in reader.pages]
    if not text_by_page or any(not text.strip() for text in text_by_page):
        raise ValueError('PDF contains no pages or a blank text page; inspect before delivery')
    text = '\n\n'.join(f'--- Page {index + 1} ---\n{content}' for index, content in enumerate(text_by_page))
    (output / 'text.txt').write_text(text, encoding='utf-8')
    if run:
        analysis = json.loads((Path(run) / 'analysis.json').read_text(encoding='utf-8'))
        compact = ''.join(text.split())
        missing = [record['id'] for record in analysis['rows'] + analysis['findings'] if ''.join(record['id'].split()) not in compact]
        if missing:
            raise ValueError('PDF omits page/finding IDs: ' + ', '.join(missing))
    renderer = renderer or shutil.which('pdftoppm')
    if not renderer:
        raise ValueError('Install Poppler or pass --renderer /path/to/pdftoppm for visual verification')
    subprocess.run([renderer, '-r', '110', '-png', str(pdf), str(output / 'page')], check=True)
    images = sorted(output.glob('page-*.png'))
    if len(images) != len(reader.pages):
        raise ValueError('Rendered page count does not match PDF; use a clean QA output directory')
    result = {'pageCount': len(reader.pages), 'renderedPages': [path.name for path in images], 'visualInspection': 'pending; an agent must inspect every page image'}
    if readiness_counts is not None:result['readinessCounts']=readiness_counts
    (output / 'checks.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--run')
    parser.add_argument('--renderer')
    parser.add_argument('--assessment',help='readiness.json for page/component, count, build and original-record verification')
    args = parser.parse_args()
    try:
        result = verify(args.pdf, args.out, args.run, args.renderer, args.assessment)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'PDF verification failed: {error}\n')
    print(f'Rendered {result["pageCount"]} pages. Inspect every image in {args.out}.')


if __name__ == '__main__':
    main()
