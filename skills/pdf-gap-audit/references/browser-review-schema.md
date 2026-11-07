# Browser review manifest, schema version 1

This observation/check contract remains unchanged. New main reports add the separate [readiness contract](readiness-report-schema.md). Reassessment preserves original check/finding evidence bindings and records current supplemental observations separately; it does not relabel old checks as freshly retested.

Copy `assets/browser-review.example.json` from this skill into the run as `browser-review.json`. Set `evidenceSha256` to the value in the current `analysis.json`. Populate arrays with actual observations. Keep `limitations` accurate; remove the initial "not performed" note only when checks have been performed.

IDs within each array must be unique. `pageIds` must be a nonempty list of IDs from `evidence.json`. Text fields describe the observed state, not assumptions disguised as results.

## checks

Each entry contains:

| Field | Value |
|---|---|
| `id`, `name` | Stable check ID and descriptive name |
| `pageIds` | Actual affected page IDs |
| `viewport` | Actual dimensions, e.g. `1440x900` |
| `outcome` | `pass`, `fail` or `unverified` |
| `actions` | Ordered list of performed actions; empty only for unverified checks |
| `expected` | Scoped expectation or clearly labeled assumption |
| `actualSource`, `actualTarget` | Actual observations, or why unavailable |
| `evidence` | Screenshot IDs/paths, response pointers or other evidence; nonempty for pass/fail |
| `browser` | Browser and version; required for pass/fail |
| `reviewer`, `reviewedAt` | Actual reviewer and ISO time; required for pass/fail |

An unverified record can leave `browser`, `reviewer` and `reviewedAt` empty, but must state what could not be checked.

## components

Each entry contains `id`, `name`, `pageIds`, `source`, `target`, `status`, `evidence` and `recommendation`. Source/target are descriptions of the observed component. Status is `retained`, `changed`, `missing` or `unverified`. Observed states require evidence references; unverified states explain the missing evidence.

## screenshotPairs

Each entry contains `id`, `title`, `pageIds`, `caption`, `source` and `target`. The two panels use this structure:

```json
{
  "path": "browser/actual-capture.png",
  "url": "https://your-site.example/actual-route",
  "sha256": "actual SHA-256 of the original screenshot bytes",
  "capturedAt": "actual ISO capture time",
  "viewport": "actual width x height",
  "state": "actual scroll position and interaction state",
  "crop": [0, 0, 800, 400]
}
```

The values above illustrate the fields; they are not observations or a ready-to-use record. The path resolves inside the run folder. Preserve the original image and hash it before any crop. `crop` is optional; if present, it is `[left, top, right, bottom]` in original-image pixels. Without it, the whole original image is shown. The PDF builder verifies file hashes and crop bounds and labels the panels Source and Target.

Choose tight, comparable component crops for legibility. Full-page captures can be too tall to read at report scale. Do not alter pixels, composite states or write captions that exceed the captured evidence.

## limitations

A list of nonempty strings explaining outstanding checks, inaccessible states, missing screenshots, missing business decisions or unverified source behavior. The builder also states explicitly when no browser checks are recorded.

The browser manifest records coverage/components/screenshots. `reviews.json` remains the authoritative finding register; add actionable findings there and regenerate the measured report before PDF generation.
