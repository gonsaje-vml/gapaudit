# Answer key — deliberate practice differences

These are expectations derived from fictional fixture files, not recorded browser
observations. Confirm the browser exercises yourself and cite your own captures.

| Measurement | Expected | Unit / denominator |
|---|---:|---|
| Inventory | 4 | Source routes |
| Comparable source/target pairs | 4 / 4 | Inventoried routes |
| Unique unavailable internal targets | 1 | Distinct target URLs returning 404/410 |
| Pages linking to that unavailable target | 2 / 4 | Inventoried routes |
| Initially confirmed findings | 0 | Findings are added after review |

| Source route | Target route | Expected static result | Browser exercise |
|---|---|---|---|
| `/` | `/` | Good content; failed checklist link | Open download on both sides |
| `/resources/` | `/resources/` | Review; missing H1/guidance; same failed download | Compare context and repeat download |
| `/contact/` | `/contact/` | Good static content | At 390x844, target panel overflows |
| `/guide/` | `/help/` | Good content through explicit mapping | Toggle both disclosures with mouse and keyboard |

The one broken URL is `/downloads/checklist.txt`, linked by home and resources.
Do not report two unique broken downloads. Good is a content-signal classification,
not a visual, functional, accessibility or readiness verdict.

## Where the differences come from

- Source `resources/index.html` contains an H1 and preparation paragraph that the
  target deliberately omits.
- Source has `downloads/checklist.txt`. Target deliberately has no such file.
- Target `style.css` sets `.contact-panel` to 760px below a 600px viewport, causing
  narrow-screen overflow. The HTML content remains the same as source.
- Source's `guide/index.html` becomes target's `help/index.html`. This is an
  intentional route move, handled by `routeMap`, rather than a missing page.

## Optional retest exercise

Work on a copy of the extracted kit. Restore the resources heading/guidance, add
the approved sample checklist at the missing target path, and remove the 760px
mobile rule. Keep the source/target fixture changes together with a note of what
you edited. Restart the local servers and collect into a new run such as
`runs/practice-fixed-01`. Repeat the same browser actions, viewports and acceptance
checks. Compare saved runs; do not overwrite the first audit or rewrite its
evidence/reviews as though the fixes existed then.

After those repairs, expect zero unavailable internal targets and no resources
content regression. Browser layout and disclosure behavior still need retesting.
