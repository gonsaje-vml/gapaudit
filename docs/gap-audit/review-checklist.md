# Browser and journey review record

Copy this file into a run directory. Complete it with actual observations; blank cells mean unverified. Use the bundled review protocol and audit coverage checklist. Every check ends as Pass, Fail, Unverified or Not applicable, with evidence or a reason. Not applicable is not a pass.

Run ID:  
Evidence SHA-256:  
Reviewer:  
Review date/time:  
Source/target environments:  
Browser/version and zoom:  
Agreed launch criteria/decision reference:

## Coverage

| Template or shared experience | Source/target routes | Viewport(s) | Pass / Fail / Unverified / Not applicable | Evidence reference or reason | Notes |
|---|---|---|---|---|---|
| Homepage and shared header/footer | | | Unverified | | |
| Landing page | | | Unverified | | |
| Article page | | | Unverified | | |
| Document list | | | Unverified | | |
| Accordion/modal | | | Unverified | | |
| Archive/table | | | Unverified | | |
| Tool/form | | | Unverified | | |
| Automated outliers | | | Unverified | | |

Record justified exclusions where a template does not exist. Add rows for every additional template and high-risk page.

## Mandatory area register

Split these areas into individual checks in the run ledger. Preserve success, empty, error, opening, closing and switching states separately where relevant. Record actual viewport sizes, including requested ultrawide views.

| Area | Outcome | Evidence or explicit reason | Remaining action / owner |
|---|---|---|---|
| Scope, page inventory, mappings and acceptance criteria | Unverified | | |
| Content, instructions, images, captions and section order | Unverified | | |
| Actual components, variants and implementation loading | Unverified | | |
| Shared header/footer, menus, breadcrumbs, product navigation, search and language | Unverified | | |
| Buttons, tabs, accordions, carousels, modals, video and sticky states | Unverified | | |
| Journeys, forms, services and authorized success/empty/error states | Unverified | | |
| Links, redirects, fragments, assets, downloads and document identity | Unverified | | |
| Visual styling, desktop/mobile reflow and requested ultrawide behavior | Unverified | | |
| Keyboard, focus, labels, headings, language, alt purpose, contrast and zoom | Unverified | | |
| Titles, descriptions, canonicals, robots and sitemap/environment behavior | Unverified | | |
| Evidence, priorities, owners, acceptance, retest and accepted differences | Unverified | | |

## Journey observation — duplicate per test

- Journey/test ID:
- Affected page IDs and source/target URLs:
- Viewport:
- Preconditions and approved test data:
- Actions, in order:
- Expected source/target behavior:
- Actual source result:
- Actual target result:
- Outcome: unverified
- Screenshot/trace/response or repository evidence references:
- User/launch impact, if failing:
- Finding ID, if applicable:
- Reviewer and date/time:

## Remaining checks and decisions

| Open check or decision | Why unresolved | Evidence/action needed | Owner/TBD |
|---|---|---|---|
| | | | |

## Verification and retest log

Before issuing the report, confirm suspected findings and check the coverage
record for missed routes, states and journeys. Record additional checks and
inconsistent results here. After fixes, use a new run and repeat acceptance tests
plus affected shared components and nearby journeys. Preserve the original
findings and their evidence references; matching repeated scans alone do not
prove complete coverage.

| Pass / new run ID if collected | Purpose and reason to repeat | Check/finding IDs | Result and evidence | Remaining limits |
|---|---|---|---|---|
| | | | | |

## Release review

- Counts reconcile with generated analysis:
- Confirmed findings have evidence and acceptance criteria:
- Inherited/accepted differences are recorded:
- Untested work is explicit:
- Audit lead and review date:
- Report approved for sharing (record actual decision):
