# Fresh-download practice walkthrough — November 9, 2026

Downloaded the published practice ZIP into a new temporary folder outside the
repository, with spaces in its path. Followed the downloaded instructions and
matching published walkthrough using macOS, Python 3.14.5 and Chrome 156.0.8078.81.

Original download: 653,790 bytes. SHA-256:
`48b462c9e4fcda3b045390a217f62ab212cc2d866218da810ee881f794d7520a`.

## Exercises performed

- Started the original sites with the documented command and collected all four page pairs.
- Read the saved report and measurements. Confirmed one unavailable target URL referenced by two pages, missing resources context, and unchanged contact text.
- Compared all four pages at 1440×900 and 390×844. Followed both checklist entry points on both sites, exercised both disclosures with mouse/Enter/Space, checked navigation and observed Tab focus.
- Recorded 17 checks: 12 passed and five failed, grouped into the three expected findings. The mobile target contact panel measured 760px; the source measured 335px.
- Recorded findings against the fresh run, regenerated its measured report, and confirmed that offline rendering works with both sample servers stopped.
- Repeated `start` against the existing output. It refused the operation and preserved the saved evidence, analysis, reviews and report.
- Reopened the original fixtures with `serve` and confirmed both sites responded without collecting again.
- Started the included repaired copy in a new run. Repeated desktop/mobile content, layout, download, navigation and disclosure exercises. The approved checklist returned from both entry points; resources context was restored; both mobile panels measured 335px and both desktop panels measured 944px.
- Created a fresh Python environment and installed the pinned PDF dependencies. Prepared a reviewed assessment, validated and built the PDF, rendered all 29 pages and inspected them. The saved-input rebuild was byte-identical. Broader quality checks remained explicitly Unverified; this test report is a partial readiness assessment.
- Extracted the revised ZIP into another clean folder and checked collection, blank review setup and repeated setup without overwriting notes.

## Problems corrected

| Problem | Correction |
|---|---|
| The agent prompt referred to a configuration path outside the run. | Uses `runs/practice-01/demo-inputs/config.json` and explains replacing the run folder when needed. |
| Beginners had to locate templates and edit the evidence reference manually. | Added `prepare-review --run` to create blank review records and a screenshot folder. Existing notes remain unchanged; mismatched evidence is rejected. |
| The checklist path was shortened and page IDs were left for learners to locate. | Uses full kit paths and provides a command that prints the current evidence reference and page IDs. |
| The PDF commands could be reached before the assessment existed. | Explains the agent handoff and the required reviewed `readiness.json`. The CLI now identifies the missing step and points to the installed contract. |
| The main walkthrough emphasized manual repairs while the kit already contained a repaired copy. | Gives the repaired-copy command first and keeps manual repair as a separate exercise. Explains new ports, run folders and fresh acceptance checks. |
| The new setup initially compared raw file bytes with the collector's LF-based hash. | Normalizes platform newlines in memory. A regression test covers CRLF input, correct binding and unchanged source bytes. |

## Verification and limits

All 59 Pages-workflow tests passed, including the new setup, preservation,
CRLF and missing-assessment cases. The new regression cases were observed failing before their
corresponding implementation changes. All 263 payload files in the two issued
example manifests retain their original hashes; original fixtures and reports
were preserved.

Applied the installed Unslop documentation rules to the revised instructions.
Kept commands, evidence rules, measurements and scope distinctions explicit.

The browser controls could not open `file://` pages. Read the extracted
`START-HERE.html`, checked its packaged assets, and used the matching published
page for browser navigation; direct offline-page rendering was not tested.
Windows launcher instructions were reviewed and CRLF handling was tested, but
the complete exercise was not executed on Windows. Production services, launch
approval, formal accessibility conformance and unperformed broader quality checks
remain outside this walkthrough's verified results.
