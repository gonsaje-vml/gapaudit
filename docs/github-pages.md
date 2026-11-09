# GitHub Pages method guide

GitHub Pages serves a static method guide, visual practice lab and completed worked-example page. The starter practice download contains fictional sample sites and expectations. A separate completed-example download contains the actual reviewed practice run, PDF and original screenshots. All three pages work without JavaScript; no client audits are published.

## Preview locally

From the repository root, with Python 3.10+:

```bash
python3 tools/build_ui.py
python3 -m http.server 8847 --bind 127.0.0.1 --directory dist
```

Open [the local guide](http://127.0.0.1:8847/). The build is also available as `npm run build`. Node dependencies are needed for the retained development checks, not to build or view the static guide.

## Published files

`tools/build_ui.py` clears `dist/` and copies an explicit file allowlist:

- `index.html`, `practice.html`, generated `worked-example.html`, `guide.css`, five accessible SVG diagrams, the favicon and the Mind the Gap logo.
- Downloads for the current Python script, neutral configuration/URL examples, reproduction guide, blank review checklist and PDF audit skill.
- A full audit-kit ZIP and a standalone skill ZIP containing the collector, PDF builder, verification helper, review protocol/schema, blank templates and pinned dependencies.
- A separate `gap-audit-practice-kit.zip` with the full toolkit, two local sample sites, standard-library runner, scope, answer key, agent prompt and a portable offline `START-HERE.html` walkthrough.
- `practice-output/` with an explicit list of approved PDF, preview, screenshot and record assets from `practice/finished/2026-11-08/public-example.json`.
- `gap-audit-worked-example.zip` with that complete frozen practice run and its exact toolkit copy. Starter kits remain blank.
- `.nojekyll` for static hosting.

The build excludes historical client reports/configurations, unrelated findings/screenshots/PDFs/captures, local browser storage and repository metadata. It reads only the explicitly approved fictional run under `practice/finished/2026-11-08/`; every approved file is bound to its recorded SHA-256 and changed bytes fail the build. `tools/worked_example.py` derives the teaching snippets from those actual records. Clearing the output removes stale files left by a previous build.

The page describes the actual division of work: Python writes JSON and Markdown; browser review validates behavior; an AI assistant with PDF tools uses the skill to produce the PDF. GitHub Pages serves these instructions and downloads.

The practice runner starts local-only servers on ports 8851/8852 (configurable),
collects a real baseline from the fictional HTML and leaves the servers open for
review. Generated runs stay on the learner's machine. The static build uses an
explicit practice-file allowlist and never copies generated evidence into the ZIP.

## Deployment

The Python-only workflow is `.github/workflows/pages.yml`, targeting [gonsaje-vml/gapaudit](https://github.com/gonsaje-vml/gapaudit).

1. Push the guide, builder, toolkit, generic starter files and skill to `main`.
2. In [Settings → Pages](https://github.com/gonsaje-vml/gapaudit/settings/pages), use GitHub Actions as the source.
3. The Pages workflow validates and builds the project, then uploads only `dist/`. Pull requests validate without deployment. A manual workflow run is also available.
4. Check the completed deployment for its URL. The configured project address is [the GitHub Pages site](https://gonsaje-vml.github.io/gapaudit/).

No historical run package is needed to build this guide. Repository visibility is independent of the Pages asset allowlist; excluding files from the site does not change repository access.

## Validation

```bash
python3 -m unittest discover -s tools -p 'test_gap_audit.py' -v
python3 -m unittest discover -s tools -p 'test_build_ui.py' -v
python3 -m unittest discover -s tools -p 'test_practice_kit.py' -v
python3 tools/build_ui.py
```

Build tests verify local links and both download packages, exclusion of previous results, stale-asset removal and collection/offline rendering against temporary test sites. PDF tests validate fixed-input byte reproduction, page/finding coverage, rejection of stale measurements and changed screenshots, and execution from the standalone skill package.

The workflow installs the pinned PDF packages and runs `test_pdf_skill.py` and the readiness/chart checks in `test_readiness_pdf.py` as well. Those chart checks also need pdfplumber as a test-only dependency. To run PDF checks locally, use a Python environment with `skills/pdf-gap-audit/requirements.txt` installed and pdfplumber for the readiness suite. The guide build itself still uses only the standard library.
