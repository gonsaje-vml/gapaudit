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

Use `docs/gap-audit/review-checklist.md` and the skill's
`assets/audit-checklist.md`. Save matched screenshots under the run's `browser/`
folder, preserving originals. The fictional contact address has no service behind
it; this exercise never asks you to send messages.

## 4. Record and reproduce

Follow the illustrated guide's finding example and the skill's review protocol.
Use actual page IDs and the `evidenceSha256` from your own `analysis.json`.
Do not copy a hash or reviewer observation from another run.

In a **second terminal in the kit folder**, regenerate after review:

```bash
python3 tools/gap_audit.py render --evidence runs/practice-01/evidence.json --reviews runs/practice-01/reviews.json --out runs/practice-01
```

That command needs no servers. Same saved inputs and toolkit version produce the
same report. Collection is a new observation; it gets a new output folder.

## 5. Optional: review and PDF with an agent

Give an agent this folder and `practice/agent-prompt.txt`, while the servers are
running. The agent must have file/Python access and browser/screenshot tools.
It follows the one bundled `pdf-gap-audit` skill, records actual review evidence,
prepares `readiness.json`, and builds the readiness PDF. PDF dependencies are in
`skills/pdf-gap-audit/requirements.txt`; page-image verification also needs Poppler.
The initial practice run does not require those tools or dependencies.

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

The repaired copy defaults to source port 8861 and target port 8862. Repeat the
same browser actions and viewports, keeping the first run. To reopen those sites,
use `python3 practice/run_demo.py serve --sites repaired`.

The published retest lesson compares actual before/after captures and explains
the separate finding-ID closure record. A new evidence hash must not be substituted
into the old reviews. The complete retest example download includes both frozen
audits and an offline START-HERE.html retest lesson.

## Move to your own sites

Use `config.example.json`, `urls.example.txt` and `docs/reproduce-audit.md`. Set
your real origins, source inventory, route mappings and scope; run the collector
directly into a new folder. The practice runner always audits the fictional local
sites. It is not the command for collecting your real project.
