# Northstar practice migration — fictional local sites — Migration Gap Audit

Evidence collected: 2026-11-09T02:12:05.296611+00:00

Source: http://127.0.0.1:8851  
Target: http://127.0.0.1:8852

Method: 1.0.0 · Evidence SHA-256: `dab6e380fb5bc7e0b4686429fed8547ac71a1be503ea4f61f15716ccef077c78`

## Executive summary

4/4 target routes returned usable static HTML. 4/4 source/target pairs could be compared.

1/2 unique internal targets returned 404/410, with document targets accounting for 1. Unverified targets: 0. 2/4 pages link to an unavailable target.

3 findings have a recorded reviewer confirmation. This report does not certify launch readiness; browser and functional review must be recorded separately.

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
- Mean text similarity: 96.5% across 4 measurable pairs. These checks are limited to static HTML.

## Critical functional gaps

### F-001 — Required checklist download returns 404

P0 · confirmed · Owner: TBD

Observation: At 1440x900 and 390x844, following the checklist link from home and resources opened the approved text on source and the same 404 URL on target. HTTP capture and byte checks agree.

Impact: The practice scope requires this preparation download without an accepted alternative. Two pages are affected by one unique unavailable URL.

Required: Publish the approved sample checklist at /downloads/checklist.txt or update both entry points to an approved destination.

Acceptance: From both pages at both viewports, open the approved checklist and verify its content, not just an HTTP 200.

Pages: PAGE-94d251729fdb, PAGE-8d7d68e3faf1. Evidence: D-desktop; D-mobile; download-mobile; asset-checks.json; evidence.json: linkChecks. Reviewed by Codex, 2026-11-09T02:22:12.341566+00:00.

## High-risk content gaps

### F-002 — Resources heading and preparation guidance omitted

P1 · confirmed · Owner: TBD

Observation: The source resources page displays Learning resources as H1 and the preparation paragraph. The target starts with Your preparation kit (H2) and omits both source elements at both viewports.

Impact: Learners lose preparation instructions and the main page heading; heading structure also regresses.

Required: Restore the approved H1 and introductory preparation paragraph before the kit.

Acceptance: At desktop and mobile sizes, verify the H1, exact approved guidance and order; retain the kit and download link.

Pages: PAGE-8d7d68e3faf1. Evidence: V02-desktop; V02-mobile; resources-mobile; quality-observations.json. Reviewed by Codex, 2026-11-09T02:22:12.341566+00:00.

## Visual gaps

### F-003 — Contact panel overflows the mobile viewport

P1 · confirmed · Owner: TBD

Observation: At 390x844, target .contact-panel is 760 CSS pixels wide and the document spans 780 pixels, clipping text and requiring horizontal scrolling. Source panel is 335 pixels wide and fits. Desktop content matches.

Impact: Mobile learners cannot read the panel naturally without horizontal scrolling. Matching static text does not establish responsive parity.

Required: Remove the target-only fixed mobile width and allow the panel to fit its container.

Acceptance: At 390x844 and 1440x900, all panel copy fits without horizontal scrolling and remains matched to source.

Pages: PAGE-3c32be8e5d4f. Evidence: V03-mobile; contact-mobile; browser-observations.json; asset-checks.json. Reviewed by Codex, 2026-11-09T02:22:12.341566+00:00.

## SEO gaps

Static signals: 0 missing descriptions; 0 missing canonicals among 4 usable target pages. Canonical correctness, production robots, sitemap coverage and search indexing require separate review.

No reviewed findings recorded. Review remains unverified; this is not a passing result.

## Accessibility gaps

Static signals across 4 usable target pages — missing document language: 0; pages without H1: 1; pages with heading jumps: 0; images missing alt: 0; images with empty alt: 0. Empty alt may be appropriate for decoration. These signals are review candidates, not a conformance verdict.

No reviewed findings recorded. Review remains unverified; this is not a passing result.

## Broken-document concentration

Unique unavailable document targets: 1; unavailable internal targets total: 1. Per-page counts below include documents and page links; the same target can appear on multiple pages. Do not sum rows to get unique totals.

| Route | Unavailable internal targets | Unverified targets |
|---|---:|---:|
| / | 1 | 0 |
| /resources/ | 1 | 0 |

## Page-by-page matrix

| ID / Route | Content fidelity | Source / target HTTP | Text similarity | Unavailable / unverified links | Main flags |
|---|---|---|---:|---:|---|
| PAGE-94d251729fdb / / | Good | 200 / 200 | 100.0% | 1 / 0 | F-001: Required checklist download returns 404 (confirmed) |
| PAGE-3c32be8e5d4f / /contact/ | Good | 200 / 200 | 100.0% | 0 / 0 | F-003: Contact panel overflows the mobile viewport (confirmed) |
| PAGE-eedf4cc7bddc / /guide/ | Good | 200 / 200 | 100.0% | 0 / 0 | No automated flags; browser review still required |
| PAGE-8d7d68e3faf1 / /resources/ | Review | 200 / 200 | 86.1% | 1 / 0 | Content/structure difference; Missing H1: regression; F-001: Required checklist download returns 404 (confirmed); F-002: Resources heading and preparation guidance omitted (confirmed) |

## Recommended remediation order

Priority rubric: P0 blocks a required user journey or required resource at launch; P1 is a material quality issue with an available workaround; P2 is minor polish. A reviewer assigns priority using agreed launch criteria; similarity alone cannot establish P0.

### P0

- F-001: Publish the approved sample checklist at /downloads/checklist.txt or update both entry points to an approved destination. Owner: TBD.

### P1

- F-002: Restore the approved H1 and introductory preparation paragraph before the kit. Owner: TBD.
- F-003: Remove the target-only fixed mobile width and allow the panel to fit its container. Owner: TBD.

### P2

No confirmed items recorded.

## Conclusion

This evidence establishes the observed route, metadata, content-signal and resource-availability results for the listed inventory. Resolve or accept confirmed findings, complete browser/journey review and obtain content-owner approval before a launch decision. Unverified observations remain open; content similarity and HTTP success do not prove functional equivalence.
