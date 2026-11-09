# Reproduce a website migration gap audit

The process is Python evidence collection, browser verification, reviewed findings, then an AI-assisted PDF report. Python 3.10+ and its standard library are sufficient for collection and Markdown/JSON rendering. Collection needs network access; offline rendering uses saved evidence. PDF rendering uses pinned Python packages; a capable AI assistant can help perform the review and prepare the assessment. New browser checks need browser tools.

## Practice first

The separate practice kit includes this entire toolkit plus fictional local sites,
an answer key and an illustrated `START-HERE.html` guide. Run
`python3 practice/run_demo.py start --out runs/practice-01` from its extracted
folder, then follow `practice/README.md`. The initial exercise needs only Python
and a browser. The practice runner always uses its local fixtures; use the direct
collector commands below for your own sites.

Keep the sample servers running. In a second terminal in the practice-kit folder,
run `python3 practice/run_demo.py prepare-review --run runs/practice-01` to prepare
blank review records and the screenshot folder. Existing notes remain unchanged.
The current practice kit provides this helper; frozen worked-example toolkits
retain their original files for reproduction.

## 1. Prepare the scope and configuration

Extract the downloadable kit and run commands from its top-level folder. In a repository checkout, the example configuration and URLs are under `docs/gap-audit/`; copy those files to the root instead.

```bash
cp config.example.json config.json
cp urls.example.txt urls.txt
```

Replace the example source and target origins in `config.json` and the source URLs in `urls.txt`. Origins must be HTTP(S), without paths, queries or credentials. The example domains are placeholders, not sites to audit.

The default inventory is `[{"kind":"urls","location":"urls.txt"}]`. For sitemap discovery, use `[{"kind":"sitemap","location":"https://your-source.example/sitemap.xml"}]`. Multiple URL-list and sitemap inputs can be combined. Local paths resolve beside the configuration. Sitemap indexes and gzip files are supported.

Use `includePrefixes` and `excludePrefixes` to define path scope. The target uses the same path/query unless an exact `routeMap` entry changes it, for example `"/old-page": "/new-page"`. Fragments are removed, while queries, case and trailing slashes are retained. Limits stop collection rather than silently sampling. Linked destinations are checked on the configured origins; external hosts require separate scoped review.

Record environments, exclusions, route mappings, required journeys and acceptance criteria in `scope.md`. Confirm that the inventory represents the scope you promise to review.

## 2. Collect a new run

```bash
python3 tools/gap_audit.py collect --config config.json --out audit-run-01
```

The output directory must not exist. Use a new directory for each collection. Retain partial failed runs as incomplete; fix the issue and restart into another directory.

The script collects source/target static HTML, metadata, headings, main text, links and image-alt signals. It checks deduplicated target internal destinations and records status, redirects and collection provenance.

| Output | Purpose |
|---|---|
| `evidence.json` | Captured observations, effective configuration, inventory and responses |
| `snapshots/` | Raw response bodies and inventory inputs, named by SHA-256 |
| `analysis.json` | Metrics, denominators, flags, findings and evidence/review hashes |
| `reviews.json` | Initially empty finding register tied to this evidence |
| `report.md` | Generated report from the evidence and reviewed findings |

## 3. Interpret and verify the baseline

Text similarity uses token-frequency cosine similarity. Heading/link-label coverage measures retained distinct normalized labels. Scores below 90%/90%/95% respectively trigger review; missing comparison data is not a pass.

404/410 means unavailable at capture time. Access failures, timeouts, blocked redirects, rate limits and other unsuccessful responses stay unverified. HTTP 200 can still be a wrong page or soft error. Count unique failed destinations separately from the pages that link to them.

Content fidelity is independent of resource availability and shared experience defects:

- Good: no automated content flags; browser review is still required.
- Review: content/structure differences or comparison limitations need checking.
- Critical: explicit override from a confirmed P0 content/functional finding.
- Unverified: the source/target HTML pair could not be compared.

Use the actual denominator for each measurement: inventoried pages, usable target pages, comparable pairs or measurable pairs. Static HTML does not execute JavaScript or establish visual, functional or accessibility equivalence. File availability checks do not verify document content or integrity.

Copy `docs/gap-audit/review-checklist.md` into the run. Compare source/target at matching viewports; review shared navigation, each template family, automated outliers and required journeys. Record actions, expected/actual results, screenshots, reviewer and time. Keep inaccessible or untested behavior unverified. Preserve screenshot originals and cite them in findings.

### When to make another pass

Use an initial audit, a verification pass before issuing the report, and a retest
after repairs. These stages do not require three identical collections.

- **Initial audit:** collect the scoped pages and perform the planned browser checks.
- **Verification pass:** confirm suspected findings and check the coverage record
  for missed routes, viewports, states and journeys. Recheck inconsistent behavior.
  Add actions, capture times and evidence to the current unissued run. Collect into
  a new folder if the site or collection conditions changed, or evidence is incomplete.
- **Retest:** after fixes, collect a new run, repeat the original acceptance tests
  and check affected shared components and nearby journeys for regressions.

Repeat checks for intermittent behavior, late-loading content or earlier access
failures. Record changes to browser, viewport, session and test data. An identical
scan can repeat the same blind spots; no fixed run count guarantees accuracy.
Required checks without evidence remain Unverified and make the audit partial.
Preserve issued runs. Rebuilding a saved report verifies reproduction, not current
website behavior.

## 4. Record findings and render offline

Add supported findings to `audit-run-01/reviews.json`, preserving its root `evidenceSha256`. Use actual page IDs, evidence references and reviewer information. The AI skill contains the finding schema, categories and priority rubric. Every finding needs an observation, impact, corrective action, owner or TBD and observable acceptance test.

```bash
python3 tools/gap_audit.py render --evidence audit-run-01/evidence.json --reviews audit-run-01/reviews.json --out audit-run-01
```

This recalculates `analysis.json` and `report.md` without network requests. A mismatched review evidence hash is rejected. The same saved evidence, reviews and toolkit version produce the same report bytes. Keep the measured evidence unchanged and archive the inputs with the issued report.

## 5. Use the complete AI skill

The custom `pdf-gap-audit` skill, version 1.4.2, includes instructions, an eleven-area audit checklist, a review protocol, browser-manifest schema, fixed PDF builder, verification helper, blank templates and pinned dependencies. It is supplied under `skills/pdf-gap-audit/` in the full kit and as a standalone skill ZIP. It uses portable Python and files and can be read by any capable agent; no particular vendor's skill loader is required. New main reports use readiness contract 2 and the readiness builder; the legacy measured builder remains available for supporting records and frozen reproduction.

For an agent to perform the whole fresh audit, give it the extracted kit and this request with actual inputs:

```text
Read skills/pdf-gap-audit/SKILL.md and its referenced protocol/schema.
Run a complete fresh migration gap audit.
Source: [source origin]
Target: [target origin and environment]
Inventory: [source sitemap or approved source URL list]
Copy the skill's assets/audit-checklist.md into the run and maintain it
with evidence-backed outcomes and justified exclusions throughout review.
Record scope, assumptions and critical journeys. Configure and collect
into a new run. Perform the protocol's browser/component checks using
matched viewports/states. Save screenshots, reviewed findings and the
browser manifest. Regenerate the measured report. Prepare readiness.json from actual
page/block/variant/use counts and reviewed visual/function/readiness judgments
using references/readiness-report-schema.md. Use the bundled readiness PDF
builder and pinned dependencies, then render and inspect every page.
Deliver the PDF, measured JSON/Markdown, audit checklist, screenshots, review records
and build record. Keep unavailable checks unverified. Use only this
run's evidence and supported findings.
```

Add known critical journeys and acceptance criteria when available. The agent needs file access, Python execution, network access and browser/screenshot tools. Without browser tools it must label visual/journey coverage unverified; that is a partial audit.

For an existing collected run, follow the review protocol and complete `audit-run-01/browser-review.json` using the blank template and schema in the skill. Set its evidence hash from the current analysis. This records actual checks, components, source/target screenshot pairs, capture hashes, optional crop bounds and remaining limits. Screenshots must be saved inside the run folder. `reviews.json` remains the finding register.

## 6. Generate and verify the readiness PDF

For a new audit, prepare `audit-run-01/readiness.json` following
`skills/pdf-gap-audit/references/readiness-report-schema.md`. This reviewed
assessment supplements the measured evidence: page breakdowns, actual body block
types, exact variants and uses, separate visual/function/readiness judgments,
capabilities, quality, work items and preserved supporting records. Required
coverage must support Complete/Ready ratings. The collector does not generate
these judgments automatically.

Use an existing Python runtime with the pinned packages or create a local environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r skills/pdf-gap-audit/requirements.txt
.venv/bin/python skills/pdf-gap-audit/scripts/build_readiness_pdf.py --assessment audit-run-01/readiness.json --validate-only
.venv/bin/python skills/pdf-gap-audit/scripts/build_readiness_pdf.py --assessment audit-run-01/readiness.json --out audit-run-01/readiness-audit.pdf
```

On Windows use `.venv\Scripts\python.exe`. In the standalone skill folder, use `requirements.txt`, `scripts/gap_audit.py`, `scripts/build_readiness_pdf.py`, `scripts/build_pdf.py`, `scripts/verify_pdf.py` and the starter files under `assets/` instead of the full-kit paths. Agents may read the standalone `SKILL.md` and adapt these documented paths.

The readiness builder validates counts/references and screenshot hashes/crops, then generates readiness charts, page breakdowns, block-type and exact-variant matrices, capabilities, quality and the work board. It embeds supplied supporting records byte for byte. Preserve the measured report unchanged. The legacy `scripts/build_pdf.py --run audit-run-01 --browser-review audit-run-01/browser-review.json --out audit-run-01/gap-audit.pdf` remains available for a measured supporting PDF or frozen reproduction; without a browser manifest that report explicitly retains unverified coverage.

`readiness-audit.build.json` records assessment/evidence hashes, reconciled counts, original-record hashes, builder/font/dependency versions and PDF hash. The legacy measured builder writes its own `gap-audit.build.json`. Default fonts come with ReportLab; if they lack required language characters, use suitable TTF files with `--font-regular` and `--font-bold` and retain those fonts.

For PDF page rendering, install Poppler if needed (`brew install poppler` on macOS; `sudo apt-get install poppler-utils` on Debian/Ubuntu) or use an existing `pdftoppm` executable:

```bash
.venv/bin/python skills/pdf-gap-audit/scripts/verify_pdf.py --pdf audit-run-01/readiness-audit.pdf --assessment audit-run-01/readiness.json --out audit-run-01/pdf-qa
```

The helper checks assessment references, build/PDF hashes and embedded original records, then renders every page to PNG. For the legacy PDF use `--run audit-run-01` instead of `--assessment`. Inspect all page images; text checks alone cannot establish layout quality. Use a clean QA output folder when re-rendering. Repair clipping, overcrowded tables and unreadable screenshots before sharing.

## 7. Reproduce an issued run

Freeze the evidence, reviews, browser manifest, screenshot originals, readiness assessment, scope/review records, fonts, issued PDF, build record and exact toolkit/skill versions. Repeat `render` and the appropriate `build_readiness_pdf.py` or legacy `build_pdf.py` commands with those files and pinned dependencies. The renderer fixes PDF metadata so repeated builds with identical inputs and environment produce identical PDF bytes. Compare the recorded hashes. To reproduce the measured JSON byte-for-byte, use the same render arguments, including whether a review file was provided.

Fresh collection repeats the process, not the original historical state. Live websites, access and independent reviewer judgments can change results. To repeat browser checks, reuse the recorded selected routes, viewport/session settings, test data, states and actions. The package specifies consistent coverage and criteria; it cannot guarantee that independent agents will make identical judgments.
