# Review protocol 1.4.2

This protocol defines the repeatable choices that a capable agent should follow. Use the user's specified scope, viewports and acceptance criteria first; record any departures so another agent can repeat them.

## Inputs and modes

For a fresh audit, require source/target origins and an approved URL inventory or sitemap. Record target environment, includes/excludes, mappings, critical journeys and accepted changes in `scope.md`. If business criteria are missing, record explicit assumptions and provisional impact instead of inventing launch approval.

For a re-render, use the frozen run folder, browser manifest, screenshots and current toolkit. Do not recollect or revise reviews. This reproduces the issued outputs rather than reevaluating the sites.

For a retest, collect into a new folder and repeat the recorded routes, states, actions and acceptance tests. Preserve the original findings and their original evidence hash. Bind only new review records to the new evidence; record each original finding's fixed, still-open or unverified outcome separately, retaining its stable ID and both evidence references. Record newly discovered issues as new findings. Do not substitute a new hash into old reviews.

For a reassessment, preserve the original evidence/check/finding bindings and make new assessments from those observations. Identify current supplemental collection separately, including actual dates, states and dimensions. Unchanged response bodies can support continued applicability, but they do not prove that every original browser check was rerun. Mismatched current viewports are context evidence, not matched visual comparisons.

For a presentation-only revision, retain the original audit/capture dates, judgments and bindings, label the layout revision separately and preserve the issued original. Suggested reasons for a page's condition remain hypotheses until supported by evidence.

## Selection and environment

1. Run the static collector for every in-scope inventory route.
2. Before browser review, group the routes by observed templates/block types and list the selected page IDs in `scope.md`.
3. Include the homepage, shared header/footer, at least one route for every template family, every automated content outlier, and every critical journey. Inspect all routes affected by a proposed shared defect before claiming its full reach.
4. Default viewports: 1440 × 900 desktop and 390 × 844 mobile. Add 768 × 1024 tablet for tablet-specific behavior or when requested. Record any tool constraint that changes the dimensions.
5. Use the same browser/version, zoom, authentication state, test data and consent state for each source/target pair. Record the browser, state and timestamps. Document unavailable source states instead of substituting a convenient target state.

Python scores below the versioned 90% text, 90% heading and 95% link-label thresholds trigger review. High similarity does not remove a route from required journey review.

## Verification passes

Before issuing the initial report, confirm suspected findings and revisit the
coverage checklist for missed routes, viewports, states and journeys. Repeat
inconsistent checks with comparable browser/session settings and record what
changed. Additional browser checks can continue the current unissued run; record
their actions, times and captures. If the site or collection conditions changed,
or captured evidence is incomplete, collect into a new folder.

After repairs, collect a fresh retest and repeat the original acceptance tests.
Check affected shared components and nearby journeys for regressions. Repeated
identical scans can retain the same blind spots; no fixed number guarantees
accuracy. Required checks without evidence remain Unverified and make the audit
partial. Frozen reproduction does not retest website behavior.

## Checks to record

Use [the audit checklist](../assets/audit-checklist.md) as the run's overall coverage record, covering scope, content, components, navigation, interactions, journeys, assets, visual/mobile behavior, accessibility, SEO and closure. Split it into the actual scoped checks; preserve an evidence/reason reference for each outcome. Checklist Not applicable items require a reason and are recorded as exclusions in the browser manifest's `limitations`; the manifest's outcome enum is unchanged.

For each applicable component/journey, record pass, fail or unverified, affected page IDs, viewport, action sequence, expected behavior, actual source and target behavior, evidence reference, actual reviewer and time.

- Header/footer/navigation: logo, visible entries, destinations, menus, mobile toggles and keyboard focus.
- Content/templates: section order, headings, instructions, copy omissions, card grouping, images and authored component presence.
- Interactive components: accordion open/close state, tabs, modals, carousels, selected state and keyboard controls.
- Hover/focus states: default, pointer hover, keyboard focus, active/selected and disabled states where applicable; include changes to text, underline, border, imagery and click area. Check that hover does not create layout movement or hide essential keyboard/touch access. Record unperformed states as Unverified.
- Component implementation: exact authored block types/variants, use counts, live JS/CSS loading, shared fragment content and runtime errors. Verify deployed-code equality before attributing behavior to a repository revision; a loaded DOM marker alone does not prove the implementation loaded successfully.
- Search/tools/forms: initial, valid-result, no-result and error states when in scope; follow scoped test data and document service limits.
- Links/documents: required destinations and actual file identity where scoped. HTTP-only checks leave file content unverified.
- Visual/mobile: clipping, overlap, layout/reflow, image placement, typography hierarchy, and source/target differences at matching states.
- Accessibility/SEO: record observable keyboard, label, focus, heading and metadata issues; distinguish inherited source issues and preview rules from migration regressions.

Skip a check only with a recorded reason, such as an absent component, excluded external service or inaccessible state. Never turn a blank check into a pass. Screenshot pairs must identify the actual state and show the evidence used by the caption.

## Shared judgments

Use the existing finding categories and priority rubric in SKILL.md. Classify components as retained, changed, missing or unverified. A change is not automatically a defect; record approved intentional changes as accepted, and unresolved intent as needs-review.

Use one stable finding per shared issue and list verified affected page IDs. Keep unique broken targets separate from affected-page counts. Keep content fidelity separate from visual and resource failures.

Another agent can repeat the recorded coverage and acceptance tests. Exact independent judgments or wording are not guaranteed. Frozen evidence, finding records, browser manifests, screenshot originals, script versions, fonts and pinned dependencies support exact output reproduction.

## Page and block readiness synthesis

Use [the readiness report contract](readiness-report-schema.md) for new main reports. First inventory actual authored block types, every exact class combination and per-page use counts. Keep shared chrome, nested source labels and card/item counts distinct. Record real candidate code names as candidates until compatible markup and behavior are verified.

For each page, show matching source/target evidence and explain retained content/capabilities, visual differences, missing behavior, actual block frequency and quality exceptions. For each block type and variant, record visual similarity separately from functional completeness, then explain readiness in terms of remaining work. Preserve occurrence-specific exceptions rather than averaging them into the block-type verdict. Reader labels use block type/variant/use; internal `family`/`usage` keys and historical records remain unchanged.

Lead the first physical page with the scope-wide readiness chart/table and bounded per-page stacked bars. The global unit is distinct body block types from `components[]`; page bars sum `pages[].components[].count` by readiness into body uses and show the separate page visual status. Use at most five page rows in the opening and retain all pages in detailed breakdowns. Explain current readiness and remaining work using exact counts, including zero and Unverified; time-progress claims require comparable dated evidence. An optional `meta.openingVisual` is a bounded supporting example after the overview. Preserve comparison limitations and apply [the visual-opening contract](readiness-report-schema.md#visual-opening).

### Action ownership and per-page exceptions

Build the capability expectation from the actual production placement: identify its anchors, buttons, forms, media purpose and available interaction states. Locate each action in its owning body block or shared navigation region. A nearby shared action does not establish that the introductory block owns it.

The same exact authored variant may be static on one page and contain an action on another. Record the page/use exception in its functional status and note, then qualify the block-type/variant rollup. A placement with no applicable widget/action must not inherit a type-wide CTA failure. Required tests follow the real action: a download, external link, gated form and gallery are different capabilities even if their styling or labels resemble one another.

Class names describe authoring, not proof of behavior. Determine whether media is decorative background, content imagery or an interactive player. A video/background variant does not imply a play modal. Decorative media still needs the relevant visual, motion/reduced-motion and accessibility review. Unknown purpose remains Unverified rather than becoming a missing player defect.

`Close` is a visual observation, not a delivery pass. `Complete` requires all stated required states. `Ready` requires required visual/viewports, functional states and scoped quality checks to be complete. A known missing capability can support `Capability missing`; insufficient evidence supports `Unverified`. Use exact acceptance tests and evidence references instead of a speculative completion percentage.

The page breakdown, frequency matrices, block assessments and work board are connected views. Refer to one shared issue explanation from affected occurrences. Keep full original check outcomes and automated metrics as supporting records so the main report remains readable.
