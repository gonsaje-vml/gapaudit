# Migration audit coverage checklist

Copy into each fresh audit or retest run as `audit-checklist.md`. This is the overall coverage record; `browser-review.json` holds individual browser checks, components and screenshots, and `reviews.json` holds findings.

- Run ID and review date:
- Evidence SHA-256:
- Source/target environments:
- Reviewer:
- Scope and acceptance-criteria reference:
- Browser/version, viewports, zoom and session state:

## Record outcomes

Split area rows into individual checks for the scoped pages, variants, states and viewports. Record **Pass**, **Fail**, **Unverified** or **Not applicable** for each check, with evidence or a reason. Pass/fail needs actual observations; an inaccessible state remains Unverified. Not applicable needs an agreed scope exclusion or evidence that the component/feature is absent. Blanks remain Unverified.

In `browser-review.json`, keep check outcomes as `pass`, `fail` or `unverified`; put justified exclusions in `limitations`. Link the coverage rows to browser check IDs, screenshot IDs, response/asset records and finding IDs. Give unresolved checks an owner/TBD and the next action needed.

## Coverage

| Area | Required checks where applicable | Result | Evidence or reason; owner/TBD and next action |
|---|---|---|---|
| Scope and page inventory | Confirm included/excluded routes, source-to-target mappings, critical journeys, document/external-service boundaries and acceptance criteria. Reconcile the promised scope with navigation, sitemap and CMS/importer inventory where available. | Unverified | |
| Content accuracy | Compare copy, headings, section order, instructions, images, captions, downloads and hidden/modal content. Distinguish missing content, inherited issues and approved changes. | Unverified | |
| Components and variants | Inventory actual component families, exact variants, instances and individual items separately. Map authored names to deployed implementations; check live JS/CSS responses, runtime errors and shared content fragments. Match deployed code to the cited repository revision before using it to explain behavior. | Unverified | |
| Shared navigation | Check header, footer, logo, menus, mobile toggles, breadcrumbs, product/sticky navigation, search entry point and language controls, including destinations and keyboard operation. | Unverified | |
| Interactions | Exercise buttons, tabs, accordions, carousels, modals, video and sticky elements. Test opening/closing, switching, selected state, keyboard controls and playback/pause behavior where present. | Unverified | |
| User journeys and integrations | Verify scoped search, resource discovery, forms, lookup tools and service connections. Cover initial, valid-result, empty, validation and error states using approved test data/actions. Record unauthorized or inaccessible submissions/services as Unverified. | Unverified | |
| Links and assets | Check destination intent, redirects, fragment triggers, images, scripts/styles and downloads. Confirm required document identity/content separately from HTTP availability. Count unique failing targets separately from affected pages and link occurrences; identify dependencies outside the audited page scope. | Unverified | |
| Visual and responsive behavior | Compare matched source/target desktop and mobile states for branding, typography, spacing, alignment, content width, image crop, overlap, clipping and reflow. Use the protocol's default viewports unless scope or tool limits specify otherwise; add tablet checks where needed. | Unverified | |
| Accessibility | Check keyboard reachability, focus order/visibility, control labels/semantics, headings, document language, alternative-text purpose, contrast, zoom/reflow and interactive state announcements. Record the tested scope; formal conformance requires separately agreed coverage. | Unverified | |
| SEO and environment | Verify titles, descriptions, canonical destinations, redirects, robots rules, sitemap coverage and indexing requirements for the intended environment. Assess preview restrictions in preview context and verify production separately where in scope. | Unverified | |
| Evidence and closure | Reconcile page/count totals and coverage records; attach evidence, affected pages, impact, priority, owner/TBD and testable acceptance criteria to findings. Retest fixes with fresh evidence and record actual acceptance/approval decisions. | Unverified | |

Successful page responses, retained text, a component's presence or a `loaded` marker establish only those observations. They do not validate interaction, visual quality or a connected service. A missing same-name implementation may indicate an authoring/code mismatch; verify runtime behavior before claiming the component is absent or assigning launch priority.

## Completion and handoff

- [ ] Every in-scope page appears once in the page matrix; measured totals reconcile with analysis, including unavailable versus unverified targets.
- [ ] Every applicable coverage check has an outcome and evidence/reason; exclusions and inaccessible states are explicit.
- [ ] Every required journey, selected template/component variant and planned viewport/state has been reviewed. Remaining required Unverified checks make the audit partial.
- [ ] Findings distinguish confirmed regressions, inherited issues, accepted changes and unresolved intent. Shared issues list only verified affected pages.
- [ ] Each confirmed finding has impact, priority, owner/TBD and observable acceptance criteria. Any release-blocking priority is tied to a required journey/resource and agreed expectations.
- [ ] For retests, stable finding IDs and repeated acceptance tests identify fixed, still-open, new and unverified items using the new run's evidence.
- [ ] The issued PDF has passed the skill's content checks and visual page inspection; scope, checklist, manifests, screenshots, findings and build records are preserved with the report.
- [ ] Report approval and accepted differences cite actual decisions. Launch approval is recorded separately; a complete audit can report open defects.

Coverage conclusion (complete/partial) and remaining gaps:

Report approval decision/reference (or pending):

Launch decision/reference (or not assessed):
