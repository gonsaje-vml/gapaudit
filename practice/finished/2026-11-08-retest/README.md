# Before and after: the Northstar practice retest

Open START-HERE.html for the illustrated offline lesson. The ZIP includes both
issued audits, original screenshots, the flawed sites and a separately repaired
copy. Only three copied target files change. The original issued baseline remains
unchanged and hash-verified.

## Fresh retest you can run

From this extracted top-level folder:

```bash
python3 practice/run_demo.py start --sites repaired --out runs/practice-fixed-01
```

Repaired source: http://127.0.0.1:8861/; target: http://127.0.0.1:8862/ by default.
Leave the terminal open for browser review. Original sites still use 8851/8852 and
remain deliberately flawed when run without --sites repaired. Windows may use
py -3 in place of python3. Use a new output folder for each collection.

Repeat the original routes, viewport sizes, states and acceptance tests. Do not
reuse these historical review decisions on your new evidence. The supplied fresh
retest passed all 17 browser checks and closed F-001/F-002/F-003. No new scoped
finding was observed. Formal accessibility conformance, production indexing and
release approval are outside this fictional exercise.

## Inspect the two issued runs

- before/readiness-audit.pdf: original flawed-site audit, 3 findings open then.
- after/readiness-audit.pdf: fresh repaired-copy retest, all 3 verified fixed.
- after/retest-results.json: stable finding IDs, original acceptance criteria,
  both evidence hashes and explicit old/new page-ID mapping by route.
- after/repairs.json: the 3 changes, actual unified diffs and file hashes.
- before/ and after/: separately preserved evidence, reviews, observations,
  original screenshots, measured reports, readiness assessments and PDF QA.
- after/prior-findings.json: byte-identical old reviews with their original hash.
- after/reviews.json: new evidence binding and no remaining open findings.

Do not overwrite before/. The source copy is identical; the ports differ, so
page IDs differ. Comparison joins the same logical routes and criteria rather
than silently substituting new page IDs or hashes into old reviews.

## Rebuild the supplied retest PDF without recollecting

Use the bundled pinned requirements and the supplied after/ records:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r skills/pdf-gap-audit/requirements.txt
.venv/bin/python tools/gap_audit.py render --evidence after/evidence.json --reviews after/reviews.json --out after
.venv/bin/python skills/pdf-gap-audit/scripts/build_readiness_pdf.py --assessment after/readiness.json --validate-only
.venv/bin/python skills/pdf-gap-audit/scripts/build_readiness_pdf.py --assessment after/readiness.json --out after/rebuilt-readiness.pdf
.venv/bin/python skills/pdf-gap-audit/scripts/verify_pdf.py --pdf after/rebuilt-readiness.pdf --assessment after/readiness.json --out after/rebuilt-pdf-qa
```

Windows: use py -3 to create the environment and .venv\Scripts\python.exe for the
remaining commands. Verification needs Poppler's pdftoppm. Byte identity was
verified in the original pinned runtime; other platforms/runtime versions may
differ. Preserve the issued PDF and build record.

All report dates use America/New_York. Original capture timestamps remain UTC.
