# Gap audit

A repeatable way to compare a source website with its migrated version: Python collects evidence, browser review verifies differences, and a reusable AI skill produces a PDF audit.

## Try the practice audit

The guide includes a downloadable practice kit with two fictional local websites,
four scoped routes, deliberate migration defects and an offline visual walkthrough.
After extracting `gap-audit-practice-kit.zip`, open `START-HERE.html`, then run:

```bash
python3 practice/run_demo.py start --out runs/practice-01
```

Leave the terminal open for browser review. The same command works from this
checkout. See [the practice instructions](practice/README.md) and
[answer key](practice/expected-results.md). The illustrated guide explains every
input/output and skill file, evidence flow, chart units, browser review, optional
readiness PDF generation, retesting and switching to your own sites.

In a second terminal, run `python3 practice/run_demo.py prepare-review --run runs/practice-01`
to create blank review records and a screenshot folder without overwriting notes.
Collection and review setup do not create `readiness.json`; a reviewer or capable
agent prepares that assessment before PDF generation.

## The GitHub Pages guide

The site explains the method, Python outputs, reproduction commands and PDF workflow. It publishes neutral starter kits, the finished fictional practice audit and a before-and-after retest of a separately repaired copy. Both issued PDFs, original screenshots, annotated outputs and reproducible downloads are available. Historical client audit data remains excluded.

Build and preview from this project directory:

```bash
python3 tools/build_ui.py
python3 -m http.server 8847 --bind 127.0.0.1 --directory dist
```

Open [the local guide](http://127.0.0.1:8847/). The static page works without JavaScript. See [GitHub Pages deployment](docs/github-pages.md) for publishing and validation.

## Reproduce an audit

- [Reproduction guide](docs/reproduce-audit.md): configuration, collection, review and offline rendering.
- [Python collector and renderer](tools/gap_audit.py): Python 3.10+, standard library, no API key.
- [Neutral configuration](docs/gap-audit/config.example.json) and [URL list](docs/gap-audit/urls.example.txt): replace the placeholder domains and routes.
- [Browser review checklist](docs/gap-audit/review-checklist.md): record real coverage and evidence.
- [PDF audit AI skill](skills/pdf-gap-audit/SKILL.md): versioned review protocol, evidence schema, fixed PDF builder, pinned dependencies and visual verification. The build includes both a standalone skill ZIP and the complete audit kit.

From a repository checkout:

```bash
cp docs/gap-audit/config.example.json config.json
cp docs/gap-audit/urls.example.txt urls.txt
# Edit the origins, URLs, exclusions and mappings before collection.
python3 tools/gap_audit.py collect --config config.json --out audit-run-01
```

Review the baseline, verify the browser behavior, record findings in the run's `reviews.json`, then regenerate:

```bash
python3 tools/gap_audit.py render \
  --evidence audit-run-01/evidence.json \
  --reviews audit-run-01/reviews.json \
  --out audit-run-01
```

Python writes JSON and Markdown. Any capable agent with file, Python and browser access can follow the packaged skill to perform the review and run its supplied PDF builder. Preserve all inputs and the issued PDF. Static similarity and HTTP availability are review signals; they do not establish functional equivalence or launch readiness.

## Validation

```bash
python3 -m unittest discover -s tools -p 'test_gap_audit.py' -v
python3 -m unittest discover -s tools -p 'test_build_ui.py' -v
python3 -m unittest discover -s tools -p 'test_practice_kit.py' -v
python3 tools/build_ui.py
```

The checks cover toolkit decisions, offline reproducibility and the published build's exclusion of prior audit data. Historical packages remain under `migration-work/` and `output/` for provenance; the Pages builder does not read or publish them.
