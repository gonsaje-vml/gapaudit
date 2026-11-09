# Finished Northstar practice audit

This is a real browser review of fictional, deliberately flawed local websites.
Report date: 2026-11-08 in America/New_York. Capture timestamps are preserved in
UTC; late-evening November 8 captures therefore display November 9 in UTC.

Start with readiness-audit.pdf. It contains 31 pages, six logical body block types,
nine source-required uses, and three confirmed findings. Target currently renders
eight body uses because the resources intro is absent. The audit is complete for
its local teaching scope; the migration still has open defects. This is not a
client report, production test or release approval.

## What is preserved

- evidence.json and snapshots/: original static HTTP capture.
- baseline-analysis.json, baseline-report.md, baseline-reviews.json: before review.
- analysis.json, report.md, reviews.json: recomputed supporting report and findings.
- browser/: 30 original JPEG captures at matched 1440x900 and 390x844 CSS viewports.
- browser-review.json, browser-actions.json, browser-observations.json: actual checks,
  interactions, screenshot hashes and DOM observations.
- quality-observations.json, asset-checks.json, census.json, scope.md and
  audit-checklist.md: quality, inventory, criteria and coverage.
- readiness.json: the reviewed assessment used by the bundled PDF renderer.
- readiness-audit.build.json: build/input/output hashes and exact runtime versions.
- pdf-qa/: rendered page images, structural checks and actual final visual review.
- capture-archive.zip: original screenshots/HTTP bodies and matching fixture code,
  also embedded with supporting records in the PDF attachment.
- public-example.json: explicit file hashes and the bounded set published on the guide.

Some mobile JPEGs are 375x812 pixels despite a measured 390x844 CSS viewport.
Original pixels/hashes are preserved; crops use original pixels, not CSS units.
The fixture has only two authored body classes (hero, contact-panel). Other
variant identifiers describe observed native HTML groups, not invented CSS names.

## Rebuild from the completed-example ZIP

Run these commands from the extracted packet's top level (beside run/, tools/
and skills/). No recollection or running websites is required.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r skills/pdf-gap-audit/requirements.txt
.venv/bin/python tools/gap_audit.py render --evidence run/evidence.json --reviews run/reviews.json --out run
.venv/bin/python skills/pdf-gap-audit/scripts/build_readiness_pdf.py --assessment run/readiness.json --validate-only
.venv/bin/python skills/pdf-gap-audit/scripts/build_readiness_pdf.py --assessment run/readiness.json --out run/rebuilt-readiness-audit.pdf
.venv/bin/python skills/pdf-gap-audit/scripts/verify_pdf.py --pdf run/rebuilt-readiness-audit.pdf --assessment run/readiness.json --out run/rebuilt-pdf-qa
```

Windows: use py -3 for environment creation and .venv\Scripts\python.exe for the
remaining commands. PDF page rendering needs Poppler's pdftoppm on PATH.
Byte identity is demonstrated in the recorded original runtime; other platforms,
Python/zlib or renderer versions may differ. Preserve the issued PDF and build
record rather than overwriting them during experimentation.

For a fresh run, use the separate starter practice kit. A fresh crawl produces
new timestamps/evidence; do not bind these old findings to a new hash.
