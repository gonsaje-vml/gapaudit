# Northstar repaired practice retest — fictional local sites — Migration Gap Audit

Evidence collected: 2026-11-09T02:50:01.312261+00:00

Source: http://127.0.0.1:8861  
Target: http://127.0.0.1:8862

Method: 1.0.0 · Evidence SHA-256: `d17e5dff0f762699c4cf8ddb18cdf62e2b81570db2f6179a3370cb470fad7788`

## Executive summary

4/4 target routes returned usable static HTML. 4/4 source/target pairs could be compared.

0/2 unique internal targets returned 404/410, with document targets accounting for 0. Unverified targets: 0. 0/4 pages link to an unavailable target.

0 findings have a recorded reviewer confirmation. This report does not certify launch readiness; browser and functional review must be recorded separately.

## Scope and method

Inventory: 4 unique source URLs; 0 inventory entries excluded. Only routes in this inventory are assessed; sitemap completeness is not assumed.

Static HTTP GET collection, exact route mapping, main-content extraction, text/heading/link-label comparison, and unique internal target checks. Fragments are removed; queries, path case and trailing slashes are retained. Linked files are checked for HTTP availability, not file integrity or content parity.

404/410 = unavailable at collection time. Timeouts, blocked requests, rate limits and other non-2xx responses = unverified. HTTP 200 may still be a soft error or login page.

Text similarity uses token-frequency cosine similarity. Heading and link-label coverage compare distinct normalized labels. Signals below 90%, 90% and 95% respectively trigger review. Empty denominators are not treated as passes.

Static HTML does not execute JavaScript or establish visual, interaction, keyboard, contrast or accessibility conformance. CSS-hidden content may be included. Canonical presence does not establish canonical correctness.

Good = no automated content flags; Review = content/structure signal; Critical = reviewer-confirmed P0 content/functional gap; Unverified = comparison unavailable. Resource failures and shared experience defects are independent of content fidelity.

Evidence: `evidence.json` and `analysis.json`; capture paths are recorded in the evidence file when present. Identical evidence, reviews and method version produce byte-identical report content.

## What is working

- Matching nonempty titles: 4/4 comparable pairs.
- Descriptions present: 4/4 usable target pages.
- Canonicals present: 4/4 usable target pages.
- Mean text similarity: 100.0% across 4 measurable pairs. These checks are limited to static HTML.

## Critical functional gaps

No reviewed findings recorded. Review remains unverified; this is not a passing result.

## High-risk content gaps

No reviewed findings recorded. Review remains unverified; this is not a passing result.

## Visual gaps

No reviewed findings recorded. Review remains unverified; this is not a passing result.

## SEO gaps

Static signals: 0 missing descriptions; 0 missing canonicals among 4 usable target pages. Canonical correctness, production robots, sitemap coverage and search indexing require separate review.

No reviewed findings recorded. Review remains unverified; this is not a passing result.

## Accessibility gaps

Static signals across 4 usable target pages — missing document language: 0; pages without H1: 0; pages with heading jumps: 0; images missing alt: 0; images with empty alt: 0. Empty alt may be appropriate for decoration. These signals are review candidates, not a conformance verdict.

No reviewed findings recorded. Review remains unverified; this is not a passing result.

## Broken-document concentration

Unique unavailable document targets: 0; unavailable internal targets total: 0. Per-page counts below include documents and page links; the same target can appear on multiple pages. Do not sum rows to get unique totals.

| Route | Unavailable internal targets | Unverified targets |
|---|---:|---:|


## Page-by-page matrix

| ID / Route | Content fidelity | Source / target HTTP | Text similarity | Unavailable / unverified links | Main flags |
|---|---|---|---:|---:|---|
| PAGE-97936578beed / / | Good | 200 / 200 | 100.0% | 0 / 0 | No automated flags; browser review still required |
| PAGE-0d789dec6881 / /contact/ | Good | 200 / 200 | 100.0% | 0 / 0 | No automated flags; browser review still required |
| PAGE-bd88fd8fbd64 / /guide/ | Good | 200 / 200 | 100.0% | 0 / 0 | No automated flags; browser review still required |
| PAGE-6571b0f11fa5 / /resources/ | Good | 200 / 200 | 100.0% | 0 / 0 | No automated flags; browser review still required |

## Recommended remediation order

Priority rubric: P0 blocks a required user journey or required resource at launch; P1 is a material quality issue with an available workaround; P2 is minor polish. A reviewer assigns priority using agreed launch criteria; similarity alone cannot establish P0.

### P0

No confirmed items recorded.

### P1

No confirmed items recorded.

### P2

No confirmed items recorded.

## Conclusion

This evidence establishes the observed route, metadata, content-signal and resource-availability results for the listed inventory. Resolve or accept confirmed findings, complete browser/journey review and obtain content-owner approval before a launch decision. Unverified observations remain open; content similarity and HTTP success do not prove functional equivalence.
