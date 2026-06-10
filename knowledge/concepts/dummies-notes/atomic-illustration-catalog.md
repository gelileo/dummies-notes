---
title: Atomic illustration catalog
type: concept
area: dummies-notes
updated: 2026-06-10
status: thin
affects:
  - "scripts/concept_registry.py"
  - "registry/**"
references:
  - "concepts/dummies-notes/concept-decomposition.md"
  - "concepts/dummies-notes/illustration-engine.md"
---

# Atomic illustration catalog

Stores the figures produced by the [[illustration-engine]] so that an atomic
concept appearing in many reasoning chains is **drawn once and referenced
everywhere**. This is what turns one-off figures into reusable, portable
building blocks.

## Why a catalog

The decomposition graph ([[concept-decomposition]]) shares nodes: "logarithm"
underpins binary search, entropy, and pH. Regenerating its figure each time is
wasteful and inconsistent. The catalog gives each atomic concept a stable
identity and a single canonical figure that every chain links to.

## Open design questions (resolve as code lands)

- **Addressing**: how is a figure keyed — by a normalized concept identity, by
  content hash, by both? This is the same identity question raised in
  [[concept-decomposition]] and must be answered consistently.
- **Portability**: figures are self-contained SVGs (per the
  [[illustration-engine]] output contract), so a catalog entry is portable by
  construction. What metadata travels with it (caption, archetype, the
  concept it depends on)?
- **Versioning/invalidation**: when a concept's understanding changes, how is
  the cached figure invalidated without breaking chains that reference it?
- **Storage**: resolved — `registry/<slug>/entry.json` per concept, plus a rebuildable `registry/index.json` summary. Implemented as the zero-dependency `scripts/concept_registry.py` module (verbs: `register` / `lookup`). Same-slug + same-definition calls are idempotent; same-slug + different-definition raises `RegistryError` and the caller must use a qualified slug (e.g. `mean-average` vs `mean-unkind`).

> Status: thin / capture-first. No implementation yet. Update in the same task
> as the first `src/catalog/` code.
