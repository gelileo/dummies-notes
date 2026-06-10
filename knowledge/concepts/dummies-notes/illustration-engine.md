---
title: Illustration engine
type: concept
area: dummies-notes
updated: 2026-06-10
status: mature
affects:
  - ".claude/skills/concept-illustrator/**"
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

Every figure directory pairs its SVG frames with a `figure.json` manifest. Required fields: `concept_slug`, `archetype`, `playback` (`static` | `slideshow`), `frames` (ordered list of `{ file, caption }` objects).

**Frame-consistency rule:** all frames in a slideshow must share the same `viewBox`, so the sequence reads as smooth evolution rather than jump-cuts.

The `validate_figure(dir_path, style_path)` function in `render.py` enforces this contract — it checks required fields, resolves each frame file, runs `lint_svg` on each, and reports an ERROR if `viewBox` values diverge across frames. Reference: `.claude/skills/concept-illustrator/references/figure-json.md`.

## SVG linter (`render.py`)

`lint_svg` / `lint_file` run a suite of checks: correct `viewBox` width (680), text-class presence, no inline `font-size`, no placeholder tokens, palette-only colors, no filters/emoji, sentence-case text, rect bounds, connector fill rules. All checks return `(level, message)` pairs so callers can filter by severity.

### CLI guards (final-review hardening)

The `main()` CLI dispatch now validates path shape before calling backend functions, so wrong-kind paths fail cleanly instead of producing raw tracebacks:

- `--viewer` requires a directory; passing a file path prints `ERROR … --viewer needs a figure directory` and exits 1.
- `--png` requires a single `.svg` file; passing a directory prints `ERROR … --png needs a single .svg file` and exits 1.

Five `TestCli` tests cover these guards plus the happy-path lint and viewer cases. Suite total: 51 tests, 1 skip.

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

Each figure is reviewed with a blind-reader test (give only the rendered figure to a fresh reader, check comprehension) and a fidelity critic (give concept definition + figure, check correctness). Details in `references/review-protocol.md`. The automated review loop is planned for Phase 3; during Phase 1 both checks are run manually or as a subagent.

## Color-role scope

Color-role conventions (teal = active, gray = eliminated, coral = target/goal) apply only to **illustrative** and **sequence** figures, where elements carry state. **Structural, flowchart, and chart** figures use ramps for pure category differentiation — prefer purple / blue / pink for neutral categories there to avoid misreading a category as a state. Full rule in `references/design-system.md § Color-role conventions`.

The **graph-node** primitive follows the same convention: `c-teal` for the start/active node, `c-coral` for the goal/target node, `c-gray` for visited/done nodes. See `references/visual-vocabulary.md § Graph node`.

## Golden quicksort example — color-model (revised)

The golden quicksort figure at `examples/quicksort/` uses a clarified, unambiguous color model:

- **`c-coral`** — the pivot cell, every frame. It is the fixed reference value; one consistent color throughout the partition pass.
- **`c-teal`** — the cell currently being scanned/compared. Exactly one cell is teal per frame; the pivot is never teal.
- **`c-gray`** — cells already settled into the left "< pivot" zone.
- **`box` (default)** — cells not yet scanned.

In the final frame the pivot lands at its resting slot (`c-coral`); everything else becomes `c-gray`. Captions explicitly narrate every swap so no array rearrangement is silent.
