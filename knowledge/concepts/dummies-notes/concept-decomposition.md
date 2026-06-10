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

- **Atomicity test**: what signal stops the recursion? Candidate: "one
  archetype figure (see [[illustration-engine]]) can express it without
  needing a sub-figure." Needs a concrete, checkable definition.
- **Dependency discovery**: LLM-proposed prerequisites vs. a curated graph vs.
  hybrid. How are cycles detected and broken?
- **Identity**: when are two concepts "the same" node (so the figure is
  reused)? Drives the catalog's addressing scheme.

> Status: thin / capture-first. No implementation exists yet; this records the
> intended design so it isn't lost. Update in the same task as the first
> `src/decomposition/` code.
