---
title: Orchestration workflow
type: concept
area: dummies-notes
updated: 2026-06-10
status: mature
affects:
  - ".claude/workflows/**"
  - "scripts/graph_check.py"
  - "scripts/assemble.py"
references:
  - "concepts/dummies-notes/concept-decomposition.md"
  - "concepts/dummies-notes/illustration-engine.md"
  - "concepts/dummies-notes/atomic-illustration-catalog.md"
---

# Orchestration workflow

The `dummies-notes` Workflow (`.claude/workflows/dummies-notes.js`) is the only
recursive, stateful piece of the system. It wires the Phase 1–2 primitives into
one run: take a topic, build its concept graph, illustrate the atomic nodes,
review them with fresh eyes, and register everything.

## Run shape (Phase 3)

1. **Snapshot** the registry index (one agent) — coverage decisions are made
   in-memory against it.
2. **Decompose** (BFS, one [[concept-decomposition]] skill call per node):
   the root always decomposes; an `illustrated` prerequisite is linked and
   stopped (covered); a `registered`-only prerequisite is decomposed using the
   registry definition verbatim (identity). Caps: `maxDepth` (default 2),
   `maxNodes` (default 12); capped concepts become logged *frontier*, never
   silent truncation. Graph lands at `output/<root-slug>/graph/<slug>.json`.
3. **Illustrate** atomic, not-yet-illustrated nodes via the
   [[illustration-engine]] skill, runbook-first, into `registry/<slug>/figure/`.
4. **Review** per figure: a blind reader (sees ONLY the frame SVGs — never
   figure.json) reports what the pictures teach; a fidelity critic checks
   runbook↔SVG drift, compares the blind read against the commentary's intent,
   and writes `review.json` into the figure dir. Bounded: exactly two repairs,
   then flag-and-continue.
5. **Finalize** (one agent): register every new node with its prerequisite
   slugs (the registry persists the graph edges — see
   [[atomic-illustration-catalog]]), attach figures, rebuild the index, and run
   `scripts/graph_check.py` (shape, cross-node cycle detection, coverage).

The script accepts `args` either as an object or a JSON-encoded string (some
callers stringify it); it parses and falls back gracefully.

## First run (Phase 3 smoke)

The first end-to-end run ("modular arithmetic", 2026-06-10): 1 node, atomic;
clock-face figure illustrated into `registry/modular-arithmetic/figure/`;
blind-reader + fidelity-critic review passed with no repairs; entry promoted to
`illustrated`; `graph_check --require-illustrated` clean. 6 agents total.

## graph_check

`scripts/graph_check.py` (zero-dep; imports `concept_registry.lookup`) is the
deterministic gate: every graph file parses with slug+atomic, the prerequisite
graph is acyclic, every graph node is registered, and (with
`--require-illustrated`) every atomic node has a figure. Frontier prerequisites
(no graph file, not registered) are WARNs.

`graph_check.py` ships with 12 unit tests (35 total across the suite). The `load_graph` / `find_cycles` / `check_coverage` API matches this description exactly.

The shipped workflow script parameters: `MAX_DEPTH=2`, `MAX_NODES=12`, `MAX_REPAIRS=2`, `registry-snapshot` agent, BFS loop with frontier logging, `pipeline()` for illustrate/review, and a Finalize agent that calls `--prereqs` on registration and `--require-illustrated` on graph_check.

The Finalize agent registers concepts by writing NODES to a temp JSON file and calling `concept_registry.reg.register` via a python3 heredoc, avoiding shell-quoting hazards that could corrupt definitions or prerequisite slugs containing spaces or special characters.

## Phase 4 next

Phase 4 scope (not yet built):

- **Assembly**: render `output/<topic>/index.html` (bottom-up explainer) and `output/<topic>/map.html` (interactive concept map) from the graph + registry figures.
- **End-to-end chain review**: a cross-node fresh-eyes pass over the full assembled output, not just per-figure review.
- **Open question carried forward**: figure invalidation and versioning — when an illustrated concept's definition changes, how does the registry detect staleness and trigger a re-illustration?

Assembly is deterministic: `scripts/assemble.py` renders index.html + map.html from the graph + registry — no agent writes HTML. The explainer (`index.html`) is built bottom-up (prerequisites before dependents, target last): atomic nodes embed their figure frames as inline slideshows; already-covered prerequisites (in the registry but not in this run's graph) are linked to their registry viewer, never re-inlined; intermediate nodes render caption-only with links to their children; frontier prerequisites (not in graph or registry) get an honest stub note. The concept map (`map.html`) places nodes in layers by depth from the root (root at top, leaves below), illustrated nodes carry first-frame thumbnails, and every node links through to the corresponding section in the explainer.

`load_full_graph` emits a clean `ERROR: no decomposition files found in <dir>` when the graph directory exists but contains no `*.json` files (empty-graph diagnostic), so `main` prints the issue and exits 1 rather than crashing inside `find_root`.
