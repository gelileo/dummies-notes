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
- **Storage**: resolved — `registry/<slug>/entry.json` per concept, plus a rebuildable `registry/index.json` summary. Implemented as the zero-dependency `scripts/concept_registry.py` module. Entries carry a `status` field (`registered` → `illustrated`) and a `figure` path relative to the registry root (set via `attach_figure`; `None` until a figure is linked). CLI verbs: `register` / `lookup` / `attach-figure` / `index`. Same-slug + same-definition calls are idempotent; same-slug + different-definition raises `RegistryError` and the caller must use a qualified slug (e.g. `mean-average` vs `mean-unkind`). The executable wrapper at `scripts/concept-registry` exposes all verbs from the shell.
- **Error contract hardening**: `_read_json` now catches `OSError`/`json.JSONDecodeError` and converts them to `RegistryError` ("corrupt registry entry at …") instead of a raw traceback. `build_index` catches `KeyError`/`TypeError` on missing required fields and raises `RegistryError` ("malformed entry for '…'"). Both paths are covered by `TestRobustness` (4 tests).

## First real entries (Phase 2 Task 7)

The registry is now seeded with two concepts, registered via `scripts/concept-registry`:

- **quicksort** (`status: illustrated`) — linked to the Phase 1 golden figure at
  `.claude/skills/concept-illustrator/examples/quicksort`; the relative `figure`
  path round-trips correctly through `lookup`.
- **modular-arithmetic** (`status: registered`) — identity anchored to the golden
  decomposition (`concept-decompose/examples/modular-arithmetic/decomposition.json`);
  its definition is byte-identical to that file's `concept.definition`; awaiting its
  own figure (Phase 3 or later).

`registry/index.json` is rebuildable at any time via `scripts/concept-registry index`
and is byte-identical after a rebuild (verified: `git status` shows no diff after the
test suite calls `build_index`).

> Status: thin. Versioning/invalidation and the content-hash vs. slug-only addressing
> questions remain open; update to mature once those are resolved.
