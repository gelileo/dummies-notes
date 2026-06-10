---
title: Concept decomposition engine
type: concept
area: dummies-notes
updated: 2026-06-10
status: thin
affects:
  - ".claude/skills/concept-decompose/SKILL.md"
  - ".claude/skills/concept-decompose/scripts/validate_decomposition.py"
references:
  - "concepts/dummies-notes/illustration-engine.md"
  - "concepts/dummies-notes/atomic-illustration-catalog.md"
---

# Concept decomposition engine

Given a target concept, the decomposition engine recursively/iteratively
discovers the **dependency concepts** required to understand it — the
prerequisites on the reasoning toolchain — and keeps decomposing until each
leaf is **atomic**: small enough that a single figure explains it clearly.

The output is a **directed dependency graph** (a concept points to the
concepts it depends on), not a tree — concepts are shared, so the same atomic
node is reached from many parents. This sharing is the whole point: it is what
makes [[atomic-illustration-catalog]] reuse possible.

## Why divide-and-conquer

Explaining a hard concept end-to-end produces a wall of prose nobody absorbs.
Instead we explain the smallest understandable pieces and compose them. The
learner walks the graph bottom-up; each step adds exactly one new idea on top
of already-illustrated foundations.

## Open design questions (resolve as code lands)

- **Atomicity test**: a concept is atomic when (a) one figure of ≤ ~6 frames
  explains its mechanism without needing a sub-figure, and (b) its remaining
  prerequisites are common knowledge for the audience. Non-atomic ⇒ at least
  one prerequisite. **Jargon is a decomposition signal**: a term the audience
  wouldn't know must become a prerequisite, never an aside. Output shape is
  enforced by `validate_decomposition.py`.
- **Dependency discovery**: LLM-proposed prerequisites vs. a curated graph vs.
  hybrid. How are cycles detected and broken?
- **Identity**: when are two concepts "the same" node (so the figure is
  reused)? Drives the catalog's addressing scheme.

## Skill (Phase 2)

The decomposition primitive now exists as a Claude Code skill at
`.claude/skills/concept-decompose/`. Its contract is **single-level**: ONE
concept in → a canonical slug + plain definition + atomicity verdict + direct
prerequisites out, emitted as a `decomposition.json` (schema in
`references/decomposition-json.md`, enforced by
`scripts/validate_decomposition.py`). The skill never recurses — walking
prerequisites, registry deduplication, and cross-node cycle detection are the
`dummies-notes` Workflow's job (Phase 3). The jargon rule is operationalized in
the SKILL.md: any term in a definition the audience wouldn't know becomes its own
prerequisite. Two golden decompositions under
`.claude/skills/concept-decompose/examples/` cover both atomicity branches —
`rsa-encryption` (non-atomic, with load-bearing prerequisites) and
`modular-arithmetic` (atomic, the clock metaphor) — and share the
`modular-arithmetic` identity to demonstrate slug-plus-definition reuse.

> Status: thin. The single-level decomposition contract (SKILL.md + schema +
> validator) has shipped; the recursive graph walk that composes these
> single-level results lands with the Workflow in Phase 3.
