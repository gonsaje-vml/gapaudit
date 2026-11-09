# Completed practice audit coverage

Run: 2026-11-08 / fictional Northstar sites. Reviewer: Codex.
Browser: Chrome 156.0.8078.81. Matched CSS viewports: 1440x900 and 390x844.
Evidence hash: dab6e380fb5bc7e0b4686429fed8547ac71a1be503ea4f61f15716ccef077c78

| Area | Outcome | Evidence / boundary |
|---|---|---|
| Scope and page inventory | Pass | Four routes, exact /guide/ -> /help/ mapping; scope.md and evidence.json. |
| Content accuracy | Fail | V02 desktop/mobile and F-002: resources H1/guidance omitted. |
| Components and variants | Pass | census.json, actual HTML/classes, quality-observations.json and stylesheet byte checks. Native groups have no fabricated CSS names. |
| Shared navigation | Pass | N-desktop/N-mobile: all four destinations; A checks preserve keyboard order. |
| Interactions | Pass | I-desktop/I-mobile: both details controls, mouse, Enter, Space, closed/open states. |
| User journeys and integrations | Fail | D-desktop/D-mobile and F-001: required download fails from both pages. No forms/backend/services exist; submission/integration checks Not applicable. |
| Links and assets | Fail | One unique checklist 404 affects two pages; source checklist identity and served CSS bytes verified. |
| Visual and responsive | Fail | Matched captures on all four pages; F-003 mobile overflow, F-002 omitted region. |
| Scoped accessibility | Fail | Visible focus, logical tab order, native disclosure semantics, language, labels and authored color pairs checked. Missing H1/reflow remain. Formal conformance is excluded, not claimed. |
| Local SEO/environment | Pass | Titles, descriptions, canonicals and local CSS recorded. Production robots/sitemap/indexing Not applicable to these fixtures. |
| Evidence and closure | Pass | Findings/census/hashes frozen. All 31 rendered PDF pages inspected; embedded originals verified; same-runtime rebuild is byte-identical. See pdf-qa/visual-review.json. |

No approval of differences, report, or production launch has been requested or recorded.

Coverage conclusion: complete for this scoped practice exercise, with three open findings. No required check remains Unverified; excluded production/formal-conformance areas remain explicitly Not applicable. Report approval: pending/not requested. Launch decision: not assessed.
