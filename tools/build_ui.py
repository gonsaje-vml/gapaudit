"""Build the guide, starter kits, reviewed fictional audit and repaired-copy retest."""

from pathlib import Path
import shutil
import zipfile
import worked_example
import retest_example

ROOT = Path(__file__).resolve().parents[1]

# Keep the publish boundary explicit. Never copy an audit run or whole docs tree.
DOWNLOADS = {
    'gap_audit.py': 'tools/gap_audit.py',
    'config.example.json': 'docs/gap-audit/config.example.json',
    'urls.example.txt': 'docs/gap-audit/urls.example.txt',
    'reproduce-audit.md': 'docs/reproduce-audit.md',
    'review-checklist.md': 'docs/gap-audit/review-checklist.md',
    'SKILL.md': 'skills/pdf-gap-audit/SKILL.md',
    'review-protocol.md': 'skills/pdf-gap-audit/references/review-protocol.md',
    'audit-methods.md': 'docs/audit-methods.md',
}
KIT_FILES = {
    'README.md': 'docs/reproduce-audit.md',
    'tools/gap_audit.py': 'tools/gap_audit.py',
    'config.example.json': 'docs/gap-audit/config.example.json',
    'urls.example.txt': 'docs/gap-audit/urls.example.txt',
    'docs/reproduce-audit.md': 'docs/reproduce-audit.md',
    'docs/audit-methods.md': 'docs/audit-methods.md',
    'docs/gap-audit/review-checklist.md': 'docs/gap-audit/review-checklist.md',
    'skills/pdf-gap-audit/SKILL.md': 'skills/pdf-gap-audit/SKILL.md',
}


SKILL_RESOURCES = (
    'SKILL.md', 'requirements.txt', 'scripts/build_pdf.py', 'scripts/build_readiness_pdf.py', 'scripts/verify_pdf.py',
    'references/review-protocol.md', 'references/browser-review-schema.md', 'references/readiness-report-schema.md',
    'assets/browser-review.example.json', 'assets/audit-checklist.md',
)
KIT_FILES.update({f'skills/pdf-gap-audit/{name}': f'skills/pdf-gap-audit/{name}' for name in SKILL_RESOURCES})
SKILL_FILES = {f'pdf-gap-audit/{name}': f'skills/pdf-gap-audit/{name}' for name in SKILL_RESOURCES}
SKILL_FILES.update({
    'pdf-gap-audit/scripts/gap_audit.py': 'tools/gap_audit.py',
    'pdf-gap-audit/assets/config.example.json': 'docs/gap-audit/config.example.json',
    'pdf-gap-audit/assets/urls.example.txt': 'docs/gap-audit/urls.example.txt',
    'pdf-gap-audit/assets/review-checklist.md': 'docs/gap-audit/review-checklist.md',
})

DIAGRAMS = ('audit-journey.svg', 'evidence-files.svg', 'skill-map.svg',
            'expected-results.svg', 'chart-units.svg')
PRACTICE_FILES = {
    **KIT_FILES,
    'README.md': 'practice/README.md',
    **{f'practice/{name}': f'practice/{name}' for name in
       ('README.md', 'run_demo.py', 'scope.md', 'expected-results.md', 'agent-prompt.txt')},
    **{name: f'site/{name}' for name in ('guide.css', 'favicon.svg', 'mind-the-gap.png')},
    **{f'diagrams/{name}': f'site/diagrams/{name}' for name in DIAGRAMS},
}
for side, guide in (('source', 'guide'), ('target', 'help')):
    for name in ('index.html', 'resources/index.html', 'contact/index.html',
                 f'{guide}/index.html', 'style.css'):
        path = f'practice/sites/{side}/{name}'
        PRACTICE_FILES[path] = path
PRACTICE_FILES['practice/sites/source/downloads/checklist.txt'] = 'practice/sites/source/downloads/checklist.txt'
for side, guide in (('source', 'guide'), ('target', 'help')):
    for name in ('index.html', 'resources/index.html', 'contact/index.html',
                 f'{guide}/index.html', 'style.css', 'downloads/checklist.txt'):
        path = f'practice/sites-repaired/{side}/{name}'
        PRACTICE_FILES[path] = path


def build(output=None):
    output = Path(output or ROOT / 'dist').resolve()
    if output != ROOT / 'dist':
        raise ValueError('Site output must be this project’s dist directory')
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    for name in ('index.html', 'practice.html', 'guide.css', 'favicon.svg', 'mind-the-gap.png'):
        shutil.copy2(ROOT / 'site' / name, output / name)
    (output / 'diagrams').mkdir()
    for name in DIAGRAMS:
        shutil.copy2(ROOT / 'site/diagrams' / name, output / 'diagrams' / name)
    downloads = output / 'downloads'
    downloads.mkdir()
    for name, source in DOWNLOADS.items():
        shutil.copy2(ROOT / source, downloads / name)
    with zipfile.ZipFile(downloads / 'gap-audit-kit.zip', 'w', zipfile.ZIP_DEFLATED) as kit:
        for name, source in KIT_FILES.items():
            kit.write(ROOT / source, name)
    with zipfile.ZipFile(downloads / 'pdf-gap-audit-skill.zip', 'w', zipfile.ZIP_DEFLATED) as package:
        for name, source in SKILL_FILES.items():
            package.write(ROOT / source, name)
    with zipfile.ZipFile(downloads / 'gap-audit-practice-kit.zip', 'w', zipfile.ZIP_DEFLATED) as practice:
        for name, source in PRACTICE_FILES.items():
            practice.write(ROOT / source, name)
        # Keep every teaching visual local. Only optional links back to the
        # published guide/download need a connection in the extracted package.
        walkthrough = (ROOT / 'site/practice.html').read_text(encoding='utf-8')
        walkthrough = walkthrough.replace('href="./index.html"',
                                          'href="https://gonsaje-vml.github.io/gapaudit/"')
        walkthrough = walkthrough.replace('href="./downloads/gap-audit-practice-kit.zip"',
                                          'href="https://gonsaje-vml.github.io/gapaudit/downloads/gap-audit-practice-kit.zip"')
        walkthrough = walkthrough.replace('href="./worked-example.html',
                                          'href="https://gonsaje-vml.github.io/gapaudit/worked-example.html')
        walkthrough = walkthrough.replace('href="./retest.html',
                                          'href="https://gonsaje-vml.github.io/gapaudit/retest.html')
        walkthrough = walkthrough.replace('href="./downloads/audit-methods.md"',
                                          'href="./docs/audit-methods.md"')
        practice.writestr('START-HERE.html', walkthrough)
    worked_example.build(output)
    retest_example.build(output)
    (output / '.nojekyll').write_text('', encoding='utf-8')
    print(f'Built {output}: visual practice lab, local demo, Python toolkit and PDF audit skill')
    return {'downloads': [*DOWNLOADS, 'gap-audit-kit.zip', 'pdf-gap-audit-skill.zip', 'gap-audit-practice-kit.zip', 'gap-audit-worked-example.zip', 'gap-audit-retest-example.zip']}


if __name__ == '__main__':
    build()
