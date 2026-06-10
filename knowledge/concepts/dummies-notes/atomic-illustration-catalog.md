---
title: Atomic illustration catalog
type: concept
area: dummies-notes
updated: 2026-06-10
status: mature
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

## Storage layout

The registry is implemented as the zero-dependency `scripts/concept_registry.py`
module. One directory per concept under `registry/`:

```
registry/
  <slug>/
    entry.json      # single concept entry
  index.json        # rebuildable summary of all entries
```

`registry/index.json` is rebuilt via `scripts/concept-registry index` and is
byte-identical after a rebuild (no diff after the test suite calls `build_index`).

## Entry schema and status lifecycle

Each `entry.json` carries: `slug`, `name`, `definition`, `status`, `prerequisites`,
and `figure`.

| Status | Meaning |
|---|---|
| `registered` | identity established; no figure yet |
| `illustrated` | `figure` path is set; concept is fully catalogued |

The `figure` field stores the path to the figure directory **relative to the
registry root**. This keeps entries portable: they point at self-contained figure
directories (each with `figure.json` + SVG frames), and the relative path
round-trips correctly through `lookup` regardless of where the repo is checked out.

## Addressing: slug + definition

A concept is keyed by its **slug and definition together** — the same rule as the
decomposition engine. Same slug + same definition → idempotent registration (no-op).
Same slug + different definition → `RegistryError`; the caller must qualify the slug
(e.g. `mean-average` vs `mean-unkind`). This is consistent with the identity rule in
[[concept-decomposition]]: a `decomposition.json` prerequisite and its registry entry
are the same concept when slug and definition match exactly. The kebab-case slug
regex is **intentionally duplicated** in `scripts/concept_registry.py` and the
decompose validator (each tool stays zero-dependency and self-contained); the two
copies must be kept in sync.

## CLI

The executable wrapper `scripts/concept-registry` exposes four verbs from the shell
(no `python3 -m` prefix needed):

| Verb | Effect |
|---|---|
| `register` | create a new entry; idempotent on same definition |
| `lookup` | print the entry JSON for a slug |
| `attach-figure` | set the `figure` path and transition status to `illustrated` |
| `index` | rebuild `registry/index.json` from all entries |

Errors from `RegistryError` print a clean `ERROR` line and exit 1.

## Error contract

`_read_json` catches `OSError` / `json.JSONDecodeError` and raises
`RegistryError("corrupt registry entry at …")` instead of a raw traceback.
`build_index` catches `KeyError` / `TypeError` on missing required fields and raises
`RegistryError("malformed entry for '…'")`. Both paths are covered by
`TestRobustness` (4 tests in `scripts/tests/test_concept_registry.py`).

## Seeded entries (Phase 2)

The registry ships with two entries:

- **quicksort** (`status: illustrated`) — linked to the Phase 1 golden figure at
  `.claude/skills/concept-illustrator/examples/quicksort`. The relative `figure` path
  round-trips correctly through `lookup`.
- **modular-arithmetic** (`status: illustrated`) — definition byte-identical to the
  golden decomposition at `.claude/skills/concept-decompose/examples/modular-arithmetic/decomposition.json`.
  Promoted from `registered` by the **first dummies-notes workflow run** (Phase 3
  smoke): the run decomposed it (atomic), illustrated a clock-face figure into
  `registry/modular-arithmetic/figure/` (review passed, `review.json` in the figure
  dir), and attached it — the first figure produced end-to-end by the orchestrator.

## Open question (Phase 3+)

**Versioning/invalidation**: when a concept's understanding changes, how is a cached
figure invalidated without breaking chains that reference it? This is a genuine open
question deferred to Phase 3 or later — it does not block the current shipped state.

Idempotent re-registration now updates prerequisites when explicitly provided, so the workflow can persist graph edges for concepts that were already registered without a definition change.
