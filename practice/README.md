# Your first migration audit

This kit contains two fictional Northstar Learning Hub websites, the real Python
collector, and the complete PDF audit skill. No client evidence is included.

Open **START-HERE.html** for the illustrated walkthrough. In a repository
checkout, the same walkthrough is `site/practice.html` (build the guide first).

## 1. Start the exercise

Extract the entire ZIP. Open a terminal **in the extracted folder**. Check:

```bash
python3 --version
```

Use Python 3.10 or later. On Windows, use `py -3` in place of `python3` throughout
this exercise if that is your Python launcher. Do not type the commands into the
Python `>>>` prompt. You need no Node installation, API key or Python packages for
the first four steps.

```bash
python3 practice/run_demo.py start --out runs/practice-01
```

The runner starts two loopback-only servers, collects four source/target page
pairs, saves the inputs and report, and stays open. Leave this terminal running.

- Source: http://127.0.0.1:8851/
- Target: http://127.0.0.1:8852/
- Report: `runs/practice-01/report.md` (open with a text editor/Markdown viewer).
- Measurements: `runs/practice-01/analysis.json`.

Use the addresses actually printed if you choose other ports. The guide route is
`/guide/` on source and `/help/` on target; the runner supplies that mapping.

## 2. Check your results

See `practice/expected-results.md`. Expect four comparable page pairs, one unique
unavailable download, and two pages linking to it. Resources should be flagged for
review because its target heading and guidance are missing. Contact can have a
Good static content label while its narrow-screen layout is broken.

The initial findings list is empty. The script has collected observations; it
has not performed browser checks or confirmed findings for you.

## 3. Compare in the browser

Keep the first terminal running. Open a **second terminal in the extracted kit
folder** and prepare the review records:

```bash
python3 practice/run_demo.py prepare-review --run runs/practice-01
```

This creates `runs/practice-01/browser/`, a blank `browser-review.json` with this
run's evidence reference, and `audit-checklist.md`. It preserves existing review
notes and stops if a manifest belongs to different evidence. It does not perform
checks or add findings. Open the generated checklist and manifest in your editor
and fill them as you follow the exercises.

Open source and target in separate tabs. Use matching viewports: 1440x900, then
390x844. If your browser supports responsive device controls, enter those exact
dimensions; otherwise record the actual window dimensions you used.

1. Home: follow the checklist download on both sides. Record the target's 404.
2. Resources: compare H1 and preparation guidance; repeat the download journey.
3. Contact: compare at both sizes. At 390 pixels, the target contact panel extends
   past the viewport. Test horizontal scrolling; record the actual result.
4. Guide/help: open each disclosure, then focus the summary with Tab and toggle
   with Enter/Space. Check each side. Do not assume success without doing it.
5. Check shared navigation and record any remaining limits.

Use the generated `runs/practice-01/audit-checklist.md`; the additional journey
worksheet is `docs/gap-audit/review-checklist.md`. The original checklist template
is `skills/pdf-gap-audit/assets/audit-checklist.md`. Save matched screenshots under the run's `browser/`
folder, preserving originals. The fictional contact address has no service behind
it; this exercise never asks you to send messages.

### Review in passes

Before issuing your report, make a verification pass through suspected findings
and the coverage checklist. Revisit missed pages, mobile and keyboard states,
downloads and inconsistent results. Add the observed actions, times and captures
to the current unissued run. If the site or collection conditions changed, or
captured evidence is incomplete, collect into a new folder.

After repairs, collect a fresh retest and repeat the acceptance tests, including
affected shared components and nearby journeys. Preserve both runs. Repeating an
identical scan can repeat the same blind spots; there is no fixed number of runs
that guarantees accuracy. Required checks that remain Unverified make the audit
partial. Rebuilding a report from saved files does not retest the site.

## 4. Record and reproduce

Follow the illustrated guide's finding example and the skill's review protocol.
Use actual page IDs and the `evidenceSha256` from your own `analysis.json`.
Do not copy a hash or reviewer observation from another run.

To display this run's evidence reference and page IDs:

```bash
python3 -c "import json,pathlib; a=json.loads(pathlib.Path('runs/practice-01/analysis.json').read_text()); print('Evidence SHA-256:',a['evidenceSha256']); [print(r['id'],r['route']) for r in a['rows']]"
```

In a **second terminal in the kit folder**, regenerate after review:

```bash
python3 tools/gap_audit.py render --evidence runs/practice-01/evidence.json --reviews runs/practice-01/reviews.json --out runs/practice-01
```

That command needs no servers. Same saved inputs and toolkit version produce the
same report. Collection is a new observation; it gets a new output folder.

## 5. Optional: review and PDF with an agent

Open an agent session with access to the extracted folder and paste the contents
of `practice/agent-prompt.txt`, while the servers are running. The agent must have
file/Python access and browser/screenshot tools. If you chose a different run
folder, replace `runs/practice-01` in the prompt and subsequent commands.
It follows the one bundled `pdf-gap-audit` skill, records actual review evidence,
prepares `readiness.json`, and builds the readiness PDF. PDF dependencies are in
`skills/pdf-gap-audit/requirements.txt`; page-image verification also needs Poppler.
The initial practice run does not require those tools or dependencies.

Wait for the reviewed `runs/practice-01/readiness.json` before running the PDF
commands. The collector and review-setup command do not create this assessment.
Without the assessment, keep the JSON/Markdown report and continue browser review
or ask a capable agent to prepare it. The PDF builder validates a completed
assessment; it does not supply the missing judgments.

Without browser tools, keep visual and journey coverage Unverified and deliver
the measured partial audit. Do not turn the deliberate-defect answer key into
fictional browser observations.

## Stop, reopen and troubleshoot

- Press Ctrl+C in the first terminal to stop both sample servers. Files remain.
- Reopen fixtures without changing the audit: `python3 practice/run_demo.py serve`.
- Output exists: choose `--out runs/practice-02`, or use `serve` to review an old run.
- Busy port: add `--source-port 8861 --target-port 8862` to `start` or `serve`, then
  use the printed URLs. Reopening a saved run should use its original ports.
- Collect without leaving servers open: add `--once` to `start`. Browser review
  then needs `serve` with the same ports. Port `0` automatically chooses an unused
  port and is useful for a one-shot smoke test.
- A folder with spaces is fine: quote output paths, e.g. `--out "runs/my first run"`.
- Connection refused: the fixture server has stopped; run `serve` again.
- Do not serve the whole checkout or point the collector at `.example` domains.

## Retest the separate repaired copy

The kit also contains `practice/sites-repaired/`, with exactly the three target
repairs. Original fixtures remain under `practice/sites/` and retain their defects.

```bash
python3 practice/run_demo.py start --sites repaired --out runs/practice-fixed-01
```

In the second terminal, prepare that run's separate review records:

```bash
python3 practice/run_demo.py prepare-review --run runs/practice-fixed-01
```

The repaired copy defaults to source port 8861 and target port 8862. Repeat the
same browser actions and viewports, keeping the first run. To reopen those sites,
use `python3 practice/run_demo.py serve --sites repaired`.

Use `runs/practice-fixed-01` in the review/render/PDF commands for this retest.
Expect zero unavailable target URLs and no resources content flag. Confirm the
restored content, download identity and mobile layout in the browser. An empty
new finding list alone does not establish that the repairs passed.

The published retest lesson compares actual before/after captures and explains
the separate finding-ID closure record. A new evidence hash must not be substituted
into the old reviews. The complete retest example download includes both frozen
audits and an offline START-HERE.html retest lesson.

## Move to your own sites

Use `config.example.json`, `urls.example.txt` and `docs/reproduce-audit.md`. Set
your real origins, source inventory, route mappings and scope; run the collector
directly into a new folder. The practice runner always audits the fictional local
sites. It is not the command for collecting your real project.
