# Readiness report contract 2

Use this contract for new page/component readiness reports. It supplements the unchanged collector evidence and check/finding contracts. A new assessment is not a retest of old checks; state the lineage and distinguish retained evidence from fresh observations.

Run `scripts/build_readiness_pdf.py --assessment readiness.json --validate-only` before rendering. Relative paths resolve beside the assessment file; absolute paths are accepted and recorded. Screenshot crops use **original-image pixels**, not CSS viewport coordinates. Preserve each original screenshot and its full-file SHA-256.

## Required object shape

```text
schemaVersion: 2
meta:
  title, date, baseline, method, sourceEvidenceSha256: strings
  summary, limitations: string arrays
  readinessSummary: optional string
  reportRevisionDate: optional nonempty string
  openingVisual: optional {pageId, pairIndex, title, takeaway}
  summaryChartStyle: optional "flat" (default) or "isometric"
pages[]:
  id, name, route, sourceUrl, targetUrl: strings
  visualStatus, functionalStatus, readiness: enums below
  retained, gaps: string arrays
  components[]: {family, variant, count, visualStatus, functionalStatus, readiness, note}
  screenshotPairs[]: capture pairs below
  qualityNotes: optional string array
components[] and sharedComponents[]:
  id, family, expected: strings
  variants: exact original class-attribute strings
  sourceLabels: optional observed production data-component labels/classes (may be nested)
  usage: {actualPageId: positive use count}
  visualStatus, functionalStatus, readiness: enums below
  retained, visualGaps, functionalGaps, remainingWork, acceptance, evidence, limitations: string arrays
  variantAssessments[]:
    variant: exact original class attribute
    usage: {actualPageId: positive use count}
    visualStatus, functionalStatus, readiness: enums below
    note: specific scope, observation or unverified boundary
  screenshotPairs: optional capture pairs
capabilities[]:
  id, name, retained, missing, action: strings
  pageIds: actual page IDs
  status: check outcome enum below
  evidence: string array
qualityAreas[]:
  name: string
  outcome: check outcome enum below
  observations, remainingWork, evidence: string arrays
  screenshotPairs: optional capture pairs
workItems[]:
  id, title, priority, action, doneWhen, owner: strings
  status: check outcome enum below
  componentIds, pageIds: actual IDs
  evidence: string array
records[]:
  path, label: strings
  archiveName: optional unique flat filename
```

Reader-facing terms are **block type**, **variant** and **use**. For example, hero is a block type, hero video is a variant, and each authored placement is one use. Existing `family`, `usage` and other field names remain unchanged for compatibility, as do actual class names, filenames and historical record bytes.

Keep rows for **every** actual body block type, exact variant and scoped page occurrence. Counts in `pages[].components`, block-type `usage` and variant `usage` must reconcile. A block type present twice on one page has one affected page and two uses. A block containing six cards is one use. Shared header/footer uses are reported separately and never added to body totals. Retain per-variant and per-page exceptions; do not average a broken variant into a working block type.

Use each page occurrence's functional status and note to identify actual action ownership and exceptions. One exact variant may have no action on one page, a download on another and a gate elsewhere. These specific records take precedence over aggregate prose. Establish media purpose from production; a decorative video/background does not establish an expected play-modal capability.

The renderer checks structural consistency and image integrity. It cannot establish that an authored name, observation or evidence reference is true: the reviewer must verify names against original HTML/repository evidence and claims against the actual capture/state.

When `sourceLabels` is supplied, the report prints a compact source-to-block mapping table. Populate it from observed production identifiers, retaining spelling and classes. Nested labels are contextual matches rather than automatically distinct components or established one-to-one aliases.

## Assessment enums and gates

| Dimension | Values | Meaning |
| --- | --- | --- |
| `visualStatus` | `Close`, `Partial`, `Far off`, `Unverified` | Rendered comparison of layout, typography, spacing, color, imagery, crop and alignment at named states/viewports. Explain remaining visual work. HTTP status and text similarity cannot determine this value. |
| `functionalStatus` | `Complete`, `Partial`, `Missing`, `Unverified`, `Not applicable` | Retained versus missing capabilities and states. A sampled pass establishes only the sampled capability. `Missing` requires observed absence; access/tool failures remain `Unverified`. |
| `readiness` | `Ready`, `Minor work`, `Substantial work`, `Capability missing`, `Unverified` | Remaining delivery work, distinct from priority and audit-check outcome. Do not manufacture completion percentages. |
| Check outcome | `Pass`, `Fail`, `Unverified`, `Not applicable` | Use for capabilities, quality topics and work items. Keep original individual check outcomes unchanged; an aggregate topic can fail while other states remain unverified. |

Every record rated `Complete` must supply nonempty `requiredStates` and `verifiedStates`, with every required state verified. Define those states from production and agreed requirements before assigning the rating.

Every record rated `Ready` must supply:

- `visualStatus: Close` and `functionalStatus: Complete` or a justified `Not applicable`;
- every stated required state verified;
- nonempty `requiredViewports` and `verifiedViewports`, covering every required size;
- `qualityComplete: true`, establishing required content, accessibility, responsive and SEO checks where applicable;
- no open `limitations`.

These fields apply to page, component, variant and page-occurrence assessments. Missing coverage remains visible rather than becoming Ready by default. Business release approval and accepted differences still require the actual decision reference; a Ready component is not release approval.

## Capture pair

```text
title, caption: strings
source, target:
  path, sha256, url, viewport, state, capturedAt: strings
  crop: optional [left, top, right, bottom] original-pixel integers
```

Match source/target browser dimensions, session, content and interaction state when comparing visuals. Explain non-identical journey stages in the caption. A top-of-page capture does not verify lower-page components. Preserve mobile and requested ultrawide evidence, including inner content widths/margins, separately from the desktop assessment.

## Main report and supporting records

The main report leads with the chart overview below, then page breakdowns, block-type and exact-variant frequency matrices, block assessments, missing capabilities, quality requirements and the final work board. Each block assessment states expected behavior, what already works, visual/function gaps, remaining work, acceptance tests and evidence limits. Shared explanations appear once and are linked from occurrences.

### Visual opening

The **first physical page** presents the title/date, a short scope-wide verdict and readiness charts before optional screenshot examples and dense prose. The overview explains current evidenced readiness and remaining work across the scope. A time-progress claim requires comparable dated observations; this snapshot supplies neither an invented completion score nor elapsed-work measure. Detailed baseline/method prose follows the opening.

Place the global readiness chart beside its exact-count table. Both derive from **the same `components[]` records**, partitioned by readiness, with distinct body block types as the unit and their total as the denominator. Include all five rows—Ready, Minor work, Substantial work, Capability missing and Unverified—even at zero. Shared components, variant totals, uses and page counts remain separate scope facts. These overlapping units cannot form slices of one whole. An empty `components[]` inventory displays “Block-type inventory unrecorded”; it establishes no completion result.

Per-page stacked readiness bars use the existing `pages[].components` records: sum each record's `count` into its `readiness` category. Each row labels its **total body uses** and the separate page `visualStatus`. A repeated block type contributes multiple uses; page bars do not count distinct block types or determine visual similarity. Per-page totals reconcile to the usage inventory and stay separate from the distinct global block-type denominator. The opening includes up to five page rows; label a bounded subset for larger scopes and retain every page in the detailed breakdowns. No additional assessment field is required for these bars.

`meta.openingVisual`, when supplied, adds a supporting source/target comparison **after the chart overview**. It contains a real `pageId`, a zero-based integer `pairIndex` into that page's `screenshotPairs`, and nonempty `title` and `takeaway` strings. The page/pair must exist; existing capture hash/crop validation applies. Choose a relevant evidenced example, label its viewport/date and bound its takeaway to that state. Omit it when no supporting example is needed or no suitable matched pair exists. Charts remain the opening in either case; unverified comparison coverage stays explicit. An invalid reference is a validation error.

Use exact count labels and a stable category-color key shared by chart and table. `meta.summaryChartStyle` selects `flat` (default) or `isometric`; shallow depth is decorative and keeps the category areas, labels and Unverified category readable. Counts express recorded readiness judgments, not measured similarity or a completion percentage.

`meta.date` remains the audit/evidence date. A presentation-only revision uses `meta.reportRevisionDate` for its actual layout revision date and labels that revision without changing observations, capture timestamps or evidence bindings. Explanations for a page's condition remain hypotheses until supported by audit evidence. Preserve the original issued assessment/PDF separately. The assessment `schemaVersion` remains **2**.

Both frequency matrices show per-page counts, total uses and separate **Visual**, **Function** and **Readiness** columns. Block-type rows use the block-type assessment; exact-variant rows use their own assessments. Keep detail links and explain that page-specific exceptions can differ from an aggregate row. A reader should be able to see where a block is used, how often and how close it is in one view.

Every supplied `records` file is embedded byte for byte in `audit-records.zip`, alongside the assessment and a checksum manifest. Use `--records additional.zip` to include a pre-existing evidence archive without changing it; relative paths resolve beside the assessment. Manifest paths preserve the supplied relative form rather than embedding the current machine's resolved directory. Verification resolves them beside the assessment too. A packet with relative assessment/image/record paths, identical fonts and the same runtime libraries can therefore be moved without changing its PDF bytes. Absolute paths remain supported.

The renderer never implies that screenshots/HTTP bodies are embedded unless they were supplied as record files. Keep complete original check outcomes and technical metrics in these supporting records; static text scores are triage signals, not visual-readiness scores.

## Commands

```bash
python3 skills/pdf-gap-audit/scripts/build_readiness_pdf.py \
  --assessment run/readiness.json --validate-only
python3 skills/pdf-gap-audit/scripts/build_readiness_pdf.py \
  --assessment run/readiness.json --out run/readiness-audit.pdf
python3 skills/pdf-gap-audit/scripts/verify_pdf.py \
  --pdf run/readiness-audit.pdf --assessment run/readiness.json --out run/pdf-qa
```

Optional `--font-regular`, `--font-bold` and `--records` paths are supported. The build writes a `.build.json` with assessment/evidence hashes, counts, original-record hashes, outline destinations, font hashes and PDF hash. Render and inspect every final page before delivery; validate duplicate pages, clipping, navigation and a frozen rebuild separately.
