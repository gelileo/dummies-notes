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

## [2026-06-09] docs | concept-illustrator: author five reference docs

- Authored five canonical reference docs under `.claude/skills/concept-illustrator/references/`: `design-system.md` (palette, color-role conventions, type, canvas geometry, banned decorations), `archetypes.md` (flowchart / structural / illustrative / chart / sequence routing), `visual-vocabulary.md` (lint-clean primitive SVG snippets for list cell, pointer, node, edge, container, stack frame, function box, state styles — the one place literal SVG reuse lives), `voice-and-metaphor.md` (caption voice + metaphor bank), and `review-protocol.md` (blind-reader + fidelity-critic fresh-eyes review, automated in Phase 3).
- All visual-vocabulary SVG snippets verified lint-clean against `render.py` linter rules.
- Added `TestReferenceDocs` suite to `scripts/tests/test_render.py`; full suite now runs 44 tests, all passing.
- Updated `knowledge/concepts/dummies-notes/illustration-engine.md` with a `## Reference docs` section listing all five files.

## [2026-06-09] fix | concept-illustrator: documentation-consistency fixes (Task 9)

- `design-system.md § Color-role conventions`: added clarifying paragraph scoping teal/coral/gray state-roles to illustrative and sequence figures only; structural/flowchart/chart figures should use purple/blue/pink for neutral categories.
- `design-system.md § Canvas & geometry`: replaced informal "~40 px" with precise formula `H = y_max + 40`.
- `archetypes.md § Structural` worked example: changed category bands from `c-coral`/`c-teal` to `c-purple`/`c-blue` to avoid state-color misuse in a pure-category context.
- `visual-vocabulary.md § Graph node`: corrected prose — start/active node uses `c-teal`; `c-coral` is reserved for goal/target node.
- `review-protocol.md § Repair loop`: tightened "approximately two" to "exactly two retries"; added explicit instruction to register flagged and stop retrying after two failures.
- `voice-and-metaphor.md § Voice`: added bullet requiring one caption per frame in sequence figures, stating what is happening and why rather than restating the image.
- Updated `knowledge/concepts/dummies-notes/illustration-engine.md` with `## Color-role scope` section capturing the illustrative/sequence vs structural/flowchart/chart distinction.

## [2026-06-09] compile | Phase 1 — concept-illustrator made real

- Built `.claude/skills/concept-illustrator/`: real SKILL.md, _style.css + template.svg, reference docs (design-system, archetypes, visual-vocabulary, voice-and-metaphor, review-protocol, figure-json), and `scripts/render.py` (lint + figure validation + slideshow viewer + optional PNG), all unit-tested with stdlib unittest (46 tests).
- Added multi-frame figures with the frame-consistency rule; golden quicksort example.
- Matured `illustration-engine.md`; scoped its affects to the skill directory.

## [2026-06-10] fix | concept-illustrator: final-review hardening (CLI guards + doc accuracy + resource leak)

- `scripts/render.py main()`: added path-shape guards for `--viewer` (requires directory) and `--png` (requires `.svg` file); wrong-kind inputs now print a clean ERROR line and return 1 instead of crashing with a traceback.
- `SKILL.md`: corrected false claim that `--theme dark` "forces the dark palette"; replaced with accurate statement that PNG export rasterizes the document's default (light) rendering and `--theme` is reserved for a future enhancement.
- `scripts/check_skill_refs.py`: closed the `open(...).read()` file handle with a `with` block to eliminate ResourceWarning.
- `scripts/tests/test_render.py`: added `TestCli` (5 tests) covering both error-path guards and happy-path lint/viewer cases; suite total is now 51 tests, 1 skip.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-09] doc | narrow illustration-engine drift mapping to SKILL.md + render.py (Phase 1.5)

- Scoped `illustration-engine.md` `affects:` from the broad `concept-illustrator/**` glob to exactly `SKILL.md` and `scripts/render.py`; reference docs and assets no longer trigger article drift checks.
- Updated CLAUDE.md article-mapping table to two specific rows matching the new globs.

## [2026-06-09] docs | concept-illustrator: runbook-first workflow + runbook/commentary in output contract

- `SKILL.md § Workflow step 2`: added explicit runbook-first per-frame order — write runbook (what/why/how, honoring frame-consistency) → draw SVG → write caption + commentary. Noted runbook is persisted in `figure.json` and human-editable for re-runs.
- `SKILL.md § Output contract`: expanded `frames` entry description to list all four required per-frame fields (`file`, `caption`, `runbook`, `commentary`); noted `caption` is the only text shown in the HTML viewer; `commentary` is narration-only for slides/video.
- `knowledge/concepts/dummies-notes/illustration-engine.md`: updated `## figure.json contract` to reflect `{ file, caption, runbook, commentary }` and added runbook-first sentence.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-09] fix | quicksort figure: color-semantics + silent-swap review

- Revised all four frames in `examples/quicksort/` to use an unambiguous color model: `c-coral` = pivot (constant throughout), `c-teal` = current scan target (one cell, never the pivot), `c-gray` = settled left-zone cells, `box` = not-yet-scanned.
- Eliminated the "c-teal means two things" ambiguity (pivot was teal in frames 1–3 and so was the scan target in frame 2).
- Rewrote all four captions to explicitly narrate every swap; no array rearrangement is silent.
- Updated `CLAUDE.md § Current state` to reflect reality: git repo on `main`, pre-commit hook + GitHub Action installed, Phase 1 shipped, correct command references, phases 2–4 not yet built.
- Updated `illustration-engine.md` with `## Golden quicksort example — color-model (revised)` section.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-09] feat | concept-illustrator: enforce runbook + commentary per frame in validate_figure

- `scripts/render.py validate_figure`: added per-frame check — reports ERROR if `runbook` or `commentary` is absent or blank for any frame (including single-frame static figures).
- `scripts/tests/test_render.py`: updated `_write_figure` helper to include `runbook`/`commentary` on every generated frame; added `TestRunbookCommentary` (3 tests). Suite total: 55 tests, 1 skip.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-09] fix | concept-illustrator: workflow-clarity fixes (runbook scope + coordinate planning)

- `SKILL.md § Workflow step 2`: changed "For each frame, work in this order" to "For each frame — including a single static frame — work in this order:" so the runbook-first sub-sequence unambiguously applies to static figures, not just sequences.
- `SKILL.md § Workflow step 2 runbook sub-step`: folded coordinate/layout planning into the runbook sub-step (archetype layout, box positions/coordinates, colour roles, what changes from the previous frame); the box-width formula now appears there, before any SVG.
- `SKILL.md § Workflow`: replaced the separate "Plan coordinates before writing SVG" step with a blockquote note clarifying that coordinate planning happens inside the runbook step, not after drawing. Renumbered subsequent steps (old 4–9 → new 3–8).
- `references/figure-json.md`: trimmed the `runbook` row's Notes cell to just the definition; the standalone bold **runbook-first** paragraph below the table continues to carry the ordering rule.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-10] fix | concept-illustrator: harden per-frame runbook/commentary check in validate_figure

- `scripts/render.py validate_figure`: replaced the `(frame.get(field) or "").strip()` pattern with `isinstance(val, str) and val.strip()`, so non-string values (e.g. `123`) are caught as missing rather than raising `AttributeError`. Added an `else` branch for bare-string frames (e.g. `"frame-01.svg"`) so they now report ERROR ("frame must be an object …") instead of silently bypassing the runbook/commentary check.
- `scripts/tests/test_render.py`: added `test_non_string_runbook_errors` and `test_bare_string_frame_errors` to `TestRunbookCommentary`. Suite total: 57 tests, 1 skip.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-10] doc | scope Phase 2 drift mapping (decompose skill, registry)

- Narrowed `concept-decomposition.md` `affects:` from `src/decomposition/**` to the two concrete Phase 2 paths: `.claude/skills/concept-decompose/SKILL.md` and `.claude/skills/concept-decompose/scripts/validate_decomposition.py`.
- Narrowed `atomic-illustration-catalog.md` `affects:` from `src/catalog/**` to `scripts/concept_registry.py` and `registry/**`.
- Updated CLAUDE.md article-mapping table: replaced two broad rows with four specific rows matching the new globs. Illustration-engine rows unchanged.

## [2026-06-10] feat | concept-illustrator: closure rule — process figures end with the result

- `SKILL.md § Workflow step 2`: added the **End with the result** rule — a process/sequence figure must close with a frame showing the end state; for recursive or iterative algorithms a final fast-forward frame may collapse the remaining iterations and show the finished result, so the reader sees the mechanism AND that it worked.
- `references/archetypes.md § Sequence`: added the same closure rule citing the quicksort example (four frames show one partition pass; a final frame fast-forwards to the fully sorted array).
- Golden quicksort example extended from 4 to 5 frames: added `frame-05.svg` (runbook-first), the fast-forward closure showing the fully sorted `[1, 2, 3, 5, 8, 9]`. The pivot 3 stays coral at index 2 (placed pivots never move — pays off the dividing-wall metaphor); every other cell is gray and sorted. Appended the matching `frame-05` entry (file/caption/runbook/commentary) to `examples/quicksort/figure.json` and rebuilt `figure.html` (now 5 SVGs). Frames 1–4 untouched.
- Validation: figure lints clean, viewer rebuilt with 5 frames, 57 tests / 1 skip, `check_skill_refs.py` exit 0, articles valid.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.
