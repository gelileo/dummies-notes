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

## Run shape

1. **Snapshot** the registry index (one agent) — coverage decisions are made
   in-memory against it.
2. **Decompose** (BFS, one [[concept-decomposition]] skill call per node):
   the root always decomposes; an `illustrated` prerequisite is linked and
   stopped (covered); a `registered`-only prerequisite is decomposed using the
   registry definition verbatim (identity). Caps: `maxDepth` (default 2),
   `maxNodes` (default 12); capped concepts become logged *frontier*, never
   silent truncation. Graph lands at `output/<root-slug>/graph/<slug>.json`.
3. **Illustrate** every **figurable** (`mechanism_figurable: true`) not-yet-illustrated
   node (atomic or non-atomic) via the [[illustration-engine]] skill, runbook-first,
   into `registry/<slug>/figure/`. Each figure is **self-sufficient**: it teaches the
   concept's own mechanism so a reader who has not seen the prerequisites still
   understands it. When a concept has prerequisites, the commentary adds short "go
   deeper" pointers to each prerequisite that has its own figure (reference, not
   re-teach). A figurable root gets its own mechanism figure here — no separate
   compose step is needed.
4. **Review** per figure: a blind reader (sees ONLY the frame SVGs — never
   figure.json) reports what the pictures teach; a fidelity critic checks
   runbook↔SVG drift, compares the blind read against the commentary's intent,
   and writes `review.json` into the figure dir. Bounded: exactly two repairs,
   then flag-and-continue.
5. **Finalize** (one agent): register every new node with its prerequisite
   slugs (the registry persists the graph edges — see
   [[atomic-illustration-catalog]]), attach figures, rebuild the index, and run
   `scripts/graph_check.py` (shape, cross-node cycle detection, coverage).
6. **Assemble**: `scripts/assemble.py` renders `output/<root>/index.html` (bottom-up
   explainer: prerequisites before dependents, target last; atomic nodes embed
   inline slideshows; covered prerequisites are linked to their registry viewer;
   intermediate nodes are caption-only; frontier prerequisites get a stub note)
   and `output/<root>/map.html` (concept map: nodes layered by depth, first-frame
   thumbnails for illustrated nodes, edges for each prerequisite link, click-through
   to the explainer sections).
7. **ChainReview**: a fresh agent reads the assembled explainer bottom-up (as a
   learner would), plus the graph files, and writes
   `output/<root>/chain-review.json` as `{"pass": bool, "summary": "...", "gaps":
   [...]}`. It reports graph-level gaps (leaps, unmet prerequisites, broken arc)
   that per-figure reviews cannot see. Gaps surface as a report; no auto-repair —
   the intent is honest disclosure, not silent patching.

The script accepts `args` either as an object or a JSON-encoded string (some
callers stringify it); it parses and falls back gracefully.

## First run (Phase 3 smoke)

The first end-to-end run ("modular arithmetic", 2026-06-10): 1 node, atomic;
clock-face figure illustrated into `registry/modular-arithmetic/figure/`;
blind-reader + fidelity-critic review passed with no repairs; entry promoted to
`illustrated`; `graph_check --require-illustrated` clean. 6 agents total.

## First full run (Phase 4)

"RSA encryption" with `maxDepth: 1` (2026-06-10): 4 nodes — modular-arithmetic
linked (covered-stop), prime-numbers + asymmetric-cryptography decomposed and
illustrated (reviews passed), a composition figure for the root, prerequisite
edges persisted to the registry, deliverable assembled. 14 agents.

**The chain review failed honestly** (`output/rsa-encryption/chain-review.json`,
4 gaps) — its job working as designed: the per-figure reviews were clean, but
the chain reviewer caught graph-level pedagogy gaps, chiefly that a composition
figure maps how the parts fit without teaching the target's own *mechanism*,
and that the depth-capped run never illustrated factoring-hardness. Recorded
finding for future work: a non-atomic target may need a mechanism figure of its
own in addition to the composition map, and deeper runs surface the missing
nodes. Gaps ship alongside the output as the spec prescribes.

## graph_check

`scripts/graph_check.py` (zero-dep; imports `concept_registry.lookup`) is the
deterministic gate: every graph file parses with slug+atomic, the prerequisite
graph is acyclic, every graph node is registered, and (with
`--require-illustrated`) every **figurable** node (`mechanism_figurable: true`)
has a figure. Non-figurable nodes are exempt from the illustration requirement.
Graph files that predate Phase 5 and lack the `mechanism_figurable` field default
it to the value of `atomic`. Frontier prerequisites
(no graph file, not registered) are WARNs.

`graph_check.py` ships with 14 unit tests. The `load_graph` / `find_cycles` / `check_coverage` API matches this description exactly.

The shipped workflow script parameters: `MAX_DEPTH=2`, `MAX_NODES=12`, `MAX_REPAIRS=2`, `registry-snapshot` agent, BFS loop with frontier logging, `pipeline()` for illustrate/review, and a Finalize agent that calls `--prereqs` on registration and `--require-illustrated` on graph_check.

The Finalize agent registers concepts by writing NODES to a temp JSON file and calling `concept_registry.reg.register` via a python3 heredoc, avoiding shell-quoting hazards that could corrupt definitions or prerequisite slugs containing spaces or special characters.

## Open question

**Figure invalidation and versioning**: when an illustrated concept's definition
changes, the registry does not yet detect staleness or trigger a re-illustration.
This is the one deferred question from Phase 4.
