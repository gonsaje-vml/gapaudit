# Gap audit

Reusable website migration audits: Python evidence collection, a fixed SOP and prompt, browser verification, and consistent report generation.

## Start here

- [Python output walkthrough — completed provider audit](migration-work/gap-audits/2026-09-28/python-output-walkthrough.md)
- [Reviewed provider audit — Adobe develop](migration-work/gap-audits/2026-09-28/client-report.md)
- [Untouched Python report](migration-work/gap-audits/2026-09-28/audit/report-automated.md)
- [Exact prompt used for the provider run](migration-work/gap-audits/2026-09-28/audit-prompt.md)

## Reuse the method

- [Toolkit instructions and commands](docs/gap-audit/README.md)
- [SOP](docs/gap-audit/SOP.md)
- [Reusable prompt](docs/gap-audit/prompt.md)
- [Browser review checklist](docs/gap-audit/review-checklist.md)
- [Python collector and renderer](tools/gap_audit.py)
- [Synthetic example report](docs/gap-audit/examples/report.md)

Run commands from this directory (`/Users/jaesong/src/vml/gapaudit`). The Python toolkit uses Python 3.10 or later and the standard library; no API key or third-party Python packages are required.

To verify the completed run offline:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 migration-work/gap-audits/2026-09-28/validate-deliverables.py
```

To verify the toolkit:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools -p 'test_gap_audit.py' -v
```

## Package layout

| Folder | Contents |
|---|---|
| `docs/gap-audit/` | SOP, prompt, checklist, configuration, inventory and synthetic example |
| `tools/` | Current Python toolkit/tests and the original Node audit reference |
| `migration-work/gap-audits/2026-09-28/` | Complete develop audit, reports, configuration, review records, scripts, raw evidence and browser captures |

The [original September 16 report](docs/adobe-nc-provider-gap-report.md) and [original Node audit script](tools/audit-nc-migration.mjs) are historical references. The original Node script retains its old defaults, including its temporary inventory path and main-branch target; use the Python toolkit and the completed run's develop configuration for new work.

## Relocation and evidence provenance

This package was moved from `/Users/jaesong/src/vml/elevance` on September 28, 2026. The internal layout is preserved so relative paths and commands still work. Presentation links were regenerated for this directory.

Frozen evidence, snapshots, the original Python output and recorded review decisions are preserved. `audit/evidence.json` intentionally retains the original absolute inventory location as a historical collection record; its saved inventory snapshot and the relocated `urls.txt` are available here. Do not rewrite that provenance field to update links: it would change the evidence hash. Repository commit references describe the original collection environment.

See [relocation manifest](relocation-manifest.json) for file hashes at the move and [run validation](migration-work/gap-audits/2026-09-28/validation.json) for current integrity and reproducibility results.
