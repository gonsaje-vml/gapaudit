# Example provider migration — Migration Gap Audit

Evidence collected: 2026-09-28T12:00:00+00:00

Source: https://source.example  
Target: https://preview.example

Method: 1.0.0 · Evidence SHA-256: `baaa841dd4b4458cf2fe59e9cf00110b6bbd61e23d98d216f644aa02c01f61ed`

**SYNTHETIC EXAMPLE — demonstrates the format; these are not live site findings.**

## Executive summary

3/4 target routes returned usable static HTML. 3/4 source/target pairs could be compared.

1/2 unique internal targets returned 404/410, with document targets accounting for 1. Unverified targets: 1. 2/4 pages link to an unavailable target.

2 findings have a recorded reviewer confirmation. This report does not certify launch readiness; browser and functional review must be recorded separately.

## Scope and method

Inventory: 4 unique source URLs; 0 inventory entries excluded. Only routes in this inventory are assessed; sitemap completeness is not assumed.

Static HTTP GET collection, exact route mapping, main-content extraction, text/heading/link-label comparison, and unique internal target checks. Fragments are removed; queries, path case and trailing slashes are retained. Linked files are checked for HTTP availability, not file integrity or content parity.

404/410 = unavailable at collection time. Timeouts, blocked requests, rate limits and other non-2xx responses = unverified. HTTP 200 may still be a soft error or login page.

Text similarity uses token-frequency cosine similarity. Heading and link-label coverage compare distinct normalized labels. Signals below 90%, 90% and 95% respectively trigger review. Empty denominators are not treated as passes.

Static HTML does not execute JavaScript or establish visual, interaction, keyboard, contrast or accessibility conformance. CSS-hidden content may be included. Canonical presence does not establish canonical correctness.

Good = no automated content flags; Review = content/structure signal; Critical = reviewer-confirmed P0 content/functional gap; Unverified = comparison unavailable. Resource failures and shared experience defects are independent of content fidelity.

Evidence: `evidence.json` and `analysis.json`; capture paths are recorded in the evidence file when present. Identical evidence, reviews and method version produce byte-identical report content.

## What is working

- Matching nonempty titles: 3/3 comparable pairs.
- Descriptions present: 3/3 usable target pages.
- Canonicals present: 3/3 usable target pages.
- Mean text similarity: 79.5% across 3 measurable pairs. These checks are limited to static HTML.

## Critical functional gaps

### F-001 — Required form document unavailable

P0 · confirmed · Owner: TBD

Observation: Synthetic scenario: the required form target returns 404 from both affected pages.

Impact: The assumed launch requirement includes downloading this form; no alternative is accepted in this example.

Required: Publish the approved form or update both links to the approved destination.

Acceptance: Open the form from both pages and confirm a successful response and the correct approved document.

Pages: PAGE-example-home, PAGE-example-forms. Evidence: evidence.json: linkChecks for https://preview.example/docs/form.pdf; review-notes.md: scenario F-001. Reviewed by Synthetic reviewer (example only), 2026-09-28T12:15:00+00:00.

## High-risk content gaps

### F-002 — Lookup guidance omitted

P1 · confirmed · Owner: TBD

Observation: Synthetic scenario: the target lookup page omits the source H1 and the instruction to read eligibility guidance.

Impact: Users lose context before using the tool. Functional service behavior has not been tested in this example.

Required: Restore the heading and approved eligibility guidance.

Acceptance: Confirm a meaningful H1 and the approved guidance appear before the lookup input at all required viewports.

Pages: PAGE-example-lookup. Evidence: evidence.json: PAGE-example-lookup source.html and target.html; review-notes.md: scenario F-002. Reviewed by Synthetic reviewer (example only), 2026-09-28T12:15:00+00:00.

## Visual gaps

No reviewed findings recorded. Review remains unverified; this is not a passing result.

## SEO gaps

Static signals: 0 missing descriptions; 0 missing canonicals among 3 usable target pages. Canonical correctness, production robots, sitemap coverage and search indexing require separate review.

No reviewed findings recorded. Review remains unverified; this is not a passing result.

## Accessibility gaps

Static signals across 3 usable target pages — missing document language: 1; pages without H1: 1; pages with heading jumps: 0; images missing alt: 0; images with empty alt: 1. Empty alt may be appropriate for decoration. These signals are review candidates, not a conformance verdict.

No reviewed findings recorded. Review remains unverified; this is not a passing result.

## Broken-document concentration

Unique unavailable document targets: 1; unavailable internal targets total: 1. Per-page counts below include documents and page links; the same target can appear on multiple pages. Do not sum rows to get unique totals.

| Route | Unavailable internal targets | Unverified targets |
|---|---:|---:|
| /forms | 1 | 1 |
| /home | 1 | 0 |

## Page-by-page matrix

| ID / Route | Content fidelity | Source / target HTTP | Text similarity | Unavailable / unverified links | Main flags |
|---|---|---|---:|---:|---|
| PAGE-example-contact / /contact | Unverified | 200 / 0 | Not measurable | 0 / 0 | Source or target HTML unavailable; inspect response evidence |
| PAGE-example-forms / /forms | Good | 200 / 200 | 91.3% | 1 / 1 | F-001: Required form document unavailable (confirmed) |
| PAGE-example-home / /home | Good | 200 / 200 | 100.0% | 1 / 0 | Document language missing; 1 empty-alt images to review; F-001: Required form document unavailable (confirmed) |
| PAGE-example-lookup / /lookup | Review | 200 / 200 | 47.1% | 0 / 0 | Content/structure difference; Missing H1: regression; F-002: Lookup guidance omitted (confirmed) |

## Recommended remediation order

Priority rubric: P0 blocks a required user journey or required resource at launch; P1 is a material quality issue with an available workaround; P2 is minor polish. A reviewer assigns priority using agreed launch criteria; similarity alone cannot establish P0.

### P0

- F-001: Publish the approved form or update both links to the approved destination. Owner: TBD.

### P1

- F-002: Restore the heading and approved eligibility guidance. Owner: TBD.

### P2

No confirmed items recorded.

## Conclusion

This evidence establishes the observed route, metadata, content-signal and resource-availability results for the listed inventory. Resolve or accept confirmed findings, complete browser/journey review and obtain content-owner approval before a launch decision. Unverified observations remain open; content similarity and HTTP success do not prove functional equivalence.
