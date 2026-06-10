---
title: Illustration engine
type: concept
area: dummies-notes
updated: 2026-06-09
status: thin
affects:
  - "src/illustration/**"
references:
  - "concepts/dummies-notes/concept-decomposition.md"
  - "concepts/dummies-notes/atomic-illustration-catalog.md"
---

# Illustration engine

Renders one concept node (from [[concept-decomposition]]) as a clean,
self-contained SVG figure plus a caption. The design reference is
`example/concept-illustrator-SKILL.md`; treat its conventions as the target
spec.

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

## Open design questions

- How is the per-figure caption generated and tied to the concept node?
- When does `validate_figure` gate the output pipeline (pre-commit, CI, or inline during generation)?

> Status: implementation in progress. Updated when `render.py` linter and figure.json validation landed (Task 6 of concept-illustrator Phase 1).
