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

## Open design questions

- Adopt the reference skill's tooling (`template.svg`, `render.py` linter)
  as-is, or build our own generator? The helper files aren't present yet —
  only the SKILL.md and sample outputs are in `example/`.
- How is the per-figure caption generated and tied to the node?

> Status: thin / capture-first. No implementation yet. Update in the same task
> as the first `src/illustration/` code.
