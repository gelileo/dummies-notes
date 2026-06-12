---
title: Illustration engine
type: concept
area: dummies-notes
updated: 2026-06-12
status: mature
affects:
  - ".claude/skills/concept-illustrator/SKILL.md"
  - ".claude/skills/concept-illustrator/scripts/render.py"
references:
  - "concepts/dummies-notes/concept-decomposition.md"
  - "concepts/dummies-notes/atomic-illustration-catalog.md"
---

# Illustration engine

Renders one concept node (from [[concept-decomposition]]) as a clean,
self-contained SVG figure plus a caption. The skill is fully implemented at
`.claude/skills/concept-illustrator/` and includes a linter, a figure validator,
a slideshow viewer generator, and a golden example (quicksort partition pass).

## Archetype routing

Route on the **verb**, not the noun — the same subject becomes a different
figure depending on intent:

- **Flowchart** — steps in sequence, a decision branching, a pipeline.
- **Structural** — containment / architecture / where data lives.
- **Illustrative** — building intuition for a mechanism. The **default** and
  most valuable: invent a spatial metaphor that makes the mechanism *visible*
  (recursion = a stack growing and unwinding; attention = a fan of weighted
  lines). Don't retreat to boxes-and-arrows because it feels safer.
- **Chart** — quantities / distributions / comparisons.

One archetype per figure. If a node needs both intuition and a precise
reference, emit two figures. This one-figure-per-node rule is what makes each
output an atomic, reusable unit for [[atomic-illustration-catalog]].

## Output contract

Self-contained SVG: embedded `<style>` + arrow marker, renders standalone in a
browser/blog/slide, light+dark via `@media (prefers-color-scheme:dark)`.
Restrained system — `viewBox="0 0 680 H"`; two type sizes (`th`/`t` 14px,
`ts` 12px); sentence case; 0.5 strokes; color encodes *category* via named
ramps; no gradients/shadows/emoji.

## figure.json contract

Every figure directory pairs its SVG frames with a `figure.json` manifest. Required fields: `concept_slug`, `archetype`, `playback` (`static` | `slideshow`), `frames` (ordered list of `{ file, caption, runbook, commentary }` objects).

The generation workflow is **runbook-first** and applies to **every frame — including a single static frame**. For each frame: (1) write the `runbook` — the build-spec capturing archetype layout, box positions/coordinates (planned here, before any SVG), colour roles, and what changes from the previous frame; (2) draw the SVG from the runbook; (3) write the `caption` (terse viewer subtitle) and `commentary` (narration for slides/video). Coordinate and layout planning is done inside the runbook step, before emitting SVG. `caption` is the only text shown in the HTML viewer; `commentary` is not rendered there.

**Frame-consistency rule:** all frames in a slideshow must share the same `viewBox`, so the sequence reads as smooth evolution rather than jump-cuts.

**Closure rule:** a process/sequence figure must end with the result — its final frame shows the end state; for recursive or iterative algorithms a fast-forward frame is fine, collapsing the remaining iterations so the reader sees both the mechanism and that it worked.

The `validate_figure(dir_path, style_path)` function in `render.py` enforces this contract — it checks required fields, resolves each frame file, runs `lint_svg` on each, reports an ERROR if `viewBox` values diverge across frames, and reports an ERROR for any frame where `runbook` or `commentary` is absent, blank/whitespace, or a non-string value (e.g. a number from malformed JSON). A bare-string frame entry (e.g. `"frame-01.svg"` instead of an object) is also an ERROR — every frame must be a `{ file, caption, runbook, commentary }` object. Both fields are **required** on every frame, including single-frame static figures. Reference: `.claude/skills/concept-illustrator/references/figure-json.md`.

## Self-sufficient figures (Phase 5)

Every figure teaches its own concept STANDALONE — a reader who lands on it cold should still grasp the mechanism without having seen any prerequisite's figure. A concept with prerequisites is illustrated the same way as a leaf; the only difference is the **commentary**: add a short "go deeper" pointer (e.g. "for the clock-math underneath this, see the modular-arithmetic figure") when the concept builds on fundamentals that have their own figures. The pointer is a reference, not a dependency.

The Phase-4 compose-from-children mode is **retired** in Phase 5: the composition-figure approach mapped structural parts but did not teach the target's own mechanism. Every node — atomic or not, with prerequisites or without — now receives a mechanism figure of its own.

## SVG linter (`render.py`)

`lint_svg` / `lint_file` run a suite of checks: correct `viewBox` width (680), text-class presence, no inline `font-size`, no placeholder tokens, palette-only colors, no filters/emoji, sentence-case text, rect bounds, connector fill rules. All checks return `(level, message)` pairs so callers can filter by severity.

**Reveal-consistency lint** (`_lint_reveal`): `validate_figure` also checks that `data-reveal` groups in a frame's SVG are consistent with the `beats` array in `figure.json`. Rules: (1) if a frame has `data-reveal` groups but no `beats`, that is an ERROR; (2) if a frame has `beats` but no `data-reveal` groups, that is an ERROR; (3) `data-reveal` indices must form a gap-free `1..N` sequence (missing indices are an ERROR); (4) the count of `beats` must equal the max `data-reveal` value (mismatch is an ERROR); (5) `data-reveal` values must be integers (a non-integer like `"abc"` is an ERROR). Frames with neither `data-reveal` nor `beats` are silently skipped — existing figures without progressive reveal validate clean.

### CLI guards (final-review hardening)

The `main()` CLI dispatch now validates path shape before calling backend functions, so wrong-kind paths fail cleanly instead of producing raw tracebacks:

- `--viewer` requires a directory; passing a file path prints `ERROR … --viewer needs a figure directory` and exits 1.
- `--png` requires a single `.svg` file; passing a directory prints `ERROR … --png needs a single .svg file` and exits 1.

Five `TestCli` tests cover these guards plus the happy-path lint and viewer cases. Suite total: 63 tests, 1 skip.

### PNG export and `--theme`

`export_png` currently rasterizes the document's default (light) rendering; `--theme` is reserved for a future forced dark-theme pass. Static rasterizers (rsvg-convert, cairosvg) don't evaluate the `@media (prefers-color-scheme:dark)` query, so dark-theme rasterization is a future enhancement. The `SKILL.md` wording has been corrected to match.

## Reference docs

Canonical reference files live in `.claude/skills/concept-illustrator/references/`:

- `references/design-system.md` — palette, color-role conventions, type, canvas geometry, banned decorations.
- `references/archetypes.md` — flowchart / structural / illustrative / chart / sequence routing.
- `references/visual-vocabulary.md` — lint-clean primitive snippets (list cell, pointer, node, edge, container, stack frame, function box, state styles) — the one place literal SVG reuse lives.
- `references/voice-and-metaphor.md` — caption voice + metaphor bank.
- `references/review-protocol.md` — blind-reader + fidelity-critic fresh-eyes review (automated in Phase 3).

## Slideshow viewer

For multi-frame figures, `render.py --viewer out.html` inlines all frame SVGs and captions into a browsable HTML slideshow using `assets/slideshow.template.html`. The generated `figure.html` is included in the figure directory alongside the SVG frames.

## Per-figure review protocol

Each figure goes through three checks (details in `references/review-protocol.md`):

1. **Blind-reader test** — give only the rendered figure and caption to a fresh reader; their description is compared against the frame's `commentary` intent. Divergence is a comprehension gap that must be fixed in the figure, not papered over with a longer caption.
2. **Fidelity critic** — give the concept definition + figure to a fresh reader; any wrong, misleading, or silently assumed claims are fidelity gaps.
3. **Runbook↔SVG drift reconciliation** — the fidelity critic diffs each frame's rendered SVG against its `runbook` (cell count, colour roles, pointer positions, what changed from the previous frame). A mismatch is drift; repair by regenerating the SVG from the runbook (SVG wrong) or updating the runbook first (concept changed).

The automated review loop is planned for Phase 3; during Phase 1 all three checks are run manually or as a subagent.

## Color-role scope

Color-role conventions (teal = active, gray = eliminated, coral = target/goal) apply only to **illustrative** and **sequence** figures, where elements carry state. **Structural, flowchart, and chart** figures use ramps for pure category differentiation — prefer purple / blue / pink for neutral categories there to avoid misreading a category as a state. Full rule in `references/design-system.md § Color-role conventions`.

The **graph-node** primitive follows the same convention: `c-teal` for the start/active node, `c-coral` for the goal/target node, `c-gray` for visited/done nodes. See `references/visual-vocabulary.md § Graph node`.

## Golden quicksort example — color-model (revised)

The golden quicksort figure at `examples/quicksort/` uses a clarified, unambiguous color model:

- **`c-coral`** — the pivot cell, every frame. It is the fixed reference value; one consistent color throughout the partition pass.
- **`c-teal`** — the cell currently being scanned/compared. Exactly one cell is teal per frame; the pivot is never teal.
- **`c-gray`** — cells already settled into the left "< pivot" zone.
- **`box` (default)** — cells not yet scanned.

Frame 4 lands the pivot at its resting slot (`c-coral`); everything else becomes `c-gray`. A fifth fast-forward frame closes the figure on the fully sorted array `[1, 2, 3, 5, 8, 9]` — the recursion on both halves collapses, the pivot 3 stays put at index 2 (placed pivots never move), and the coral pays off the dividing-wall metaphor. Captions explicitly narrate every swap so no array rearrangement is silent.
