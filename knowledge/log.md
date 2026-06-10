# Build Log

Append-only chronological log of significant changes to this project. Each entry records what changed, why, and which articles were touched. Read sequentially, this log tells the story of the project's decisions.

## [2026-06-09] compile | adopt living-doc + seed vision articles

- Adopted the living-documentation methodology (https://github.com/mpklu/living-doc) on this greenfield repo: installed `knowledge/`, `schemas/`, `scripts/` (drift-check, validate-articles), and `actions/drift-check/`.
- Merged the living-doc same-task rule into `CLAUDE.md` alongside the existing project vision.
- Wrote three thin foundational articles capturing the design before code exists: `concept-decomposition`, `illustration-engine`, `atomic-illustration-catalog`.
- Pre-commit hook and GitHub Action deferred until `git init` (repo is not yet under git).

## [2026-06-09] feat | concept-illustrator: figure.json validation + frame-consistency

- Added `validate_figure(dir_path, style_path)` to `scripts/render.py`: validates required fields, resolves frame files, runs `lint_svg` per frame, enforces frame-consistency (all frames must share identical `viewBox`).
- Added constants `FIGURE_REQUIRED` and `FIGURE_PLAYBACK` to encode the schema.
- Created `references/figure-json.md` (field table + rules + example).
- Added `TestValidateFigure` suite (4 tests) to `scripts/tests/test_render.py`; suite now runs 39 tests total.
- Updated `knowledge/concepts/dummies-notes/illustration-engine.md` with figure.json contract and linter summary.

## [2026-06-09] design | dummies_notes architecture spec

- Brainstormed and wrote the architecture design: `docs/superpowers/specs/2026-06-09-dummies-notes-design.md`.
- Decisions: Claude Code skills + a Workflow (no standalone app); autonomous recursive decomposition; output is both a bottom-up explainer doc and an interactive concept map over a shared registry.
- Reframed "reusable" as **referencing** (link covered concepts, don't re-illustrate); the registry is a reference graph, not a dedup cache.
- Style consistency is engineered (shared stylesheet/template + primitive visual-vocabulary + color-role conventions + linter gate), not inherited from reuse.
- Voice: vivid metaphor + plain language, restrained visuals; simplicity wins.
- Added fresh-eyes verification (separate-agent blind-reader + fidelity critic) at two altitudes (per-figure gate, end-to-end chain review) with a bounded repair loop.
- Build phased 1–4; Phase 1 (`concept-illustrator` made real) to be planned next. The three seed concept articles will be refined/renamed as those phases land.
