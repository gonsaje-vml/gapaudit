# Practice Kit Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task by task.

**Goal:** Publish a self-contained practice audit and a detailed visual guide on the existing GitHub Pages site.

**Architecture:** Local fictional fixtures feed the unchanged collector. An explicit package manifest adds the runner, teaching material and portable visual guide to a separate ZIP. The existing static page links to both the ZIP and the new walkthrough.

**Tech Stack:** Python 3.10+ standard library, static HTML/CSS, accessible SVG, unittest, GitHub Actions Pages.

**Spec:** docs/superpowers/specs/2026-11-07-practice-kit-design.md

## Global Constraints

- No credentials, API key or Node installation for the initial exercise.
- Serve on loopback only; keep ports configurable; never overwrite existing runs.
- Explicit publish allowlist; no historical client data.
- Static measurements do not establish browser behavior or readiness.
- Optional PDF extension uses the existing pinned audit skill.

## Review Focus

- Extracted ZIP works in a path with spaces, independent of this checkout.
- Busy ports report an actionable error and clean up the other server.
- Existing output remains untouched.
- Navigation, SVG alternatives and charts work on narrow screens without scripts.
- All skill/version/command explanations match the shipped files.

### Task 1: Runnable fixtures

**Files:** practice/run_demo.py, practice/sites/{source,target}/, tools/test_practice_kit.py

**Interfaces:** start/serve CLI; start --once exits after collection; configurable --source-port/--target-port; --out identifies a new run.

- [x] Add integration tests for four comparable pairs, route mapping, expected defects, offline reproduction, output refusal and port collision cleanup.
- [x] Run tests and observe missing runner failure.
- [x] Implement local fixtures and standard-library runner with saved inputs.
- [x] Run integration tests to green.

### Task 2: Visual teaching and downloads

**Files:** site/practice.html, site/diagrams/*.svg, site/guide.css, practice/{README.md,expected-results.md,agent-prompt.txt}, tools/build_ui.py, tools/test_build_ui.py

**Interfaces:** dist/practice.html and dist/downloads/gap-audit-practice-kit.zip; START-HERE.html plus local diagrams in the extracted ZIP.

- [x] Add extracted-package and multi-page/diagram link checks; observe failure.
- [x] Write the walkthrough, per-file/skill references, charts, expected results and browser/PDF exercises.
- [x] Extend explicit build manifests and link the kit from the main guide; refresh stale skill/PDF instructions.
- [x] Validate package portability, local links, privacy boundary and fixture behavior.

### Task 3: Verify and publish

**Files:** README.md, docs/github-pages.md, .github/workflows/pages.yml

- [x] Run appropriate Python checks, build, browser QA at desktop/mobile and a fresh reviewer pass.
- [ ] Commit only required guide/toolkit/skill/practice dependencies, preserving unrelated files.
- [ ] Push main and verify the Pages workflow and published practice download; if authentication prevents publication, report the exact remaining action.

## Execution evidence

47 Python checks passed in the pinned temporary PDF runtime, including extracted-ZIP portability and byte reproduction. Browser QA inspected the diagrams and checked a 390px embedded viewport; the browser viewport-override API did not change its host viewport, so a temporary preview frame supplied the actual narrow content viewport. The guide fit; the planted target panel overflowed as expected. A fresh reviewer found Bash continuations incompatible with Windows; all public guide/reproduction commands now use single lines. Clarified the explicit Critical content-fidelity override. GitHub Pages was enabled with build_type=workflow. Publication verification follows.
