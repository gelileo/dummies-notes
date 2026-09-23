---
title: Drill-down essentials skill
type: concept
area: dummies-notes
updated: 2026-09-23
status: thin
affects:
  - ".claude/skills/drill-down-essentials/SKILL.md"
  - ".claude/skills/drill-down-essentials/scripts/verify_essentials.py"
references:
  - "concepts/dummies-notes/concept-decomposition.md"
---

# Drill-down essentials skill

`drill-down-essentials` is a repo skill for **study material** rather than for the illustration
pipeline: given a technical chapter, find the concepts it *uses* but never *teaches* — the maths,
statistics or theory that would stop a capable high-school graduate — and expand each into a
self-contained article plus a runnable script under `<chapter>/essentials/<concept>/`
(`README.md` + `demo.py`). It was extracted from building `subjects/LLM/`, where every chapter
now carries such a folder (38 essentials across 15 chapters).

## Why it exists

The `subjects/LLM/` curriculum is written for a programmer who is not a data scientist. Chapter
prose kept leaning on ideas — the dot product, softmax, `√d_head`, the chain rule — that are
obvious to the author and a hard stop for the reader. The fix that worked was one article per
concept, **with the demo script written before the article** so every claim is measured rather
than asserted; three times in one chapter the measurement contradicted the intended prose.

## Constraints and decisions

- **Folder per concept**, article always `README.md`, script always `demo.py`: links point at a
  bare folder and git hosts render the article on navigation.
- **Standard library only for chapters 01–03, numpy from 04**, deterministic, runnable from the
  folder. No install step in a prerequisite explainer.
- **Ownership**: whichever chapter first needs a concept owns the article; later chapters link.
- **Index is a lookup table** keyed by the sentence that stopped making sense, not a reading list.
- `scripts/verify_essentials.py <chapter>` checks structure, runs every demo, resolves links
  (inside-chapter links fail; outside-chapter links warn), validates mermaid via `npx`.

Ruled out: bulk pre-writing essentials for chapters before their questions arrive (the useful
ones came from real reader questions), and re-explaining concepts another chapter owns.

## Relationship to the product

Independent of the illustration workflow. It shares [[concept-decomposition]]'s instinct — find
the prerequisites — but stops at prose and a script rather than a figure. Study material under
`subjects/` does not trigger the living-doc rule; the skill itself does, hence this article.
