---
title: Orchestration workflow
type: concept
area: dummies-notes
updated: 2026-06-10
status: thin
affects:
  - ".claude/workflows/**"
  - "scripts/graph_check.py"
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

## graph_check

`scripts/graph_check.py` (zero-dep; imports `concept_registry.lookup`) is the
deterministic gate: every graph file parses with slug+atomic, the prerequisite
graph is acyclic, every graph node is registered, and (with
`--require-illustrated`) every atomic node has a figure. Frontier prerequisites
(no graph file, not registered) are WARNs.

> Status: thin / capture-first — written before the code lands in this phase.
