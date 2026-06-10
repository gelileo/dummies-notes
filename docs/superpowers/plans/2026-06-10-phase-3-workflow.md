# Phase 3 — dummies-notes Workflow — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the recursion: a named Workflow that takes a topic, decomposes it registry-aware down to atomic concepts (with depth/node caps), illustrates each atomic concept runbook-first, runs the fresh-eyes review loop (blind reader + fidelity critic, ≤2 repairs), registers everything, and validates the graph.

**Architecture:** Three units. (1) `scripts/graph_check.py` — zero-dep, unit-tested validator for a graph directory of `decomposition.json` files: shape, **cross-node cycle detection** (the Phase 2 open question), and registry coverage (`--require-illustrated` for atomic nodes). It imports `concept_registry.lookup` (same dir — no duplication). (2) `.claude/workflows/dummies-notes.js` — the orchestrator: one registry-snapshot agent, a BFS decompose loop calling the `concept-decompose` skill per node (illustrated-covered prerequisites link-and-stop; registered ones reuse the registry definition), then a `pipeline()` of illustrate → review-with-repair per atomic node, then one Finalize agent that registers nodes (with prerequisite slugs — persisting the graph into the registry), attaches figures, and runs `graph_check.py`. (3) A real smoke run on the single-node topic "modular arithmetic" (already `registered`, awaiting its figure) as the end-to-end acceptance, with artifacts committed.

**Tech Stack:** Python 3 stdlib + unittest for graph_check; the Workflow tool's JS runtime (`agent`/`pipeline`/`phase`/`log`, JSON-schema structured outputs) for orchestration. No new dependencies. Spec: `docs/superpowers/specs/2026-06-09-dummies-notes-design.md` (Data flow steps 1–4 + 7; Verification).

**Conventions:**
- Test commands: graph_check joins the registry suite — `python3 -m unittest discover -s scripts/tests -p 'test_*.py'`. The other two suites must stay green.
- **Living-doc drift gate.** Task 1 creates a thin article `knowledge/concepts/dummies-notes/orchestration-workflow.md` with `affects: [".claude/workflows/**", "scripts/graph_check.py"]` and matching CLAUDE.md rows. After Task 1, commits touching those paths MUST update that article in the same commit. If a commit is unexpectedly blocked, STOP and report — never `--no-verify`.
- **The smoke run (Task 4) invokes the Workflow tool** (multi-agent orchestration: roughly 5–7 subagents for a single-node topic). The CONTROLLER runs it directly — subagents must not invoke Workflow. User consent for this run is obtained at execution handoff.
- Workflow-script constraints (runtime rules): plain JS, no `Date.now()`/`Math.random()`/argless `new Date()`, no filesystem access from the script — all file I/O happens inside agents.

## Design decisions locked here

- **Where figures go:** `registry/<slug>/figure/` (entry and figure co-located; `attach_figure` stores the relpath `<slug>/figure`). `build_index` is unaffected (it only looks for `entry.json`).
- **Where the graph goes:** `output/<root-slug>/graph/<slug>.json` — one decomposition per node; Phase 4 assembles `output/<root-slug>/index.html` + `map.html` next to it. Run artifacts are committed (the registry is committed by design; the graph is the durable record Phase 4 consumes).
- **Coverage semantics (spec: "covered → link & stop"):** a prerequisite whose registry status is `illustrated` is linked and NOT decomposed or re-illustrated. A `registered`-only prerequisite is processed (decomposed using the registry definition verbatim — identity), since it was never finished. The ROOT topic is always decomposed (it is the subject of the run).
- **Caps:** `maxDepth` default 2, `maxNodes` default 12 (overridable via args). Cap hits are `log()`ged and capped concepts become "frontier" (reported, registered if known, left for a later run) — no silent truncation.
- **Repair bound:** ≤ 2 repairs per figure (per review-protocol.md "exactly two retries"); still-failing figures are attached but flagged in `review.json` + the run report.
- **Registry graph persistence:** Finalize registers every new node with `--prereqs <slugs>` — resolving the Phase 2 open question (the registry carries the persistent graph edges).
- **Blind-reader blindness:** the blind reader is instructed to read ONLY the `frame-*.svg` files (never `figure.json`, which contains runbook/commentary). Reading SVG source approximates "viewing" (no rasterizer installed); noted in the article.

## Model policy

Workflow `agent()` calls omit `model` (inherit the session model) per the Workflow tool's guidance. For the plan's implementer subagents: all tasks are **sonnet** (complete code provided below; the judgment was done in this plan), reviews per the established policy (spec=sonnet, quality/final=opus).

## File structure

| File | Responsibility | Task |
|------|----------------|------|
| `knowledge/concepts/dummies-notes/orchestration-workflow.md` (new, thin) + `CLAUDE.md` rows | drift mapping + capture the design | 1 |
| `scripts/graph_check.py` | graph shape + cycle + coverage validator (CLI + importable) | 2 |
| `scripts/tests/test_graph_check.py` | its unit tests | 2 |
| `.claude/workflows/dummies-notes.js` | the orchestrator | 3 |
| `output/modular-arithmetic/graph/`, `registry/modular-arithmetic/` | smoke-run artifacts (figure, review.json, entry illustrated) | 4 |
| knowledge articles + `index.md` + `log.md` + `CLAUDE.md` | matured / refreshed | 5 |

---

## Task 1: Drift mapping + thin orchestration article

**Model: sonnet.** **Files:** Create `knowledge/concepts/dummies-notes/orchestration-workflow.md`; Modify `CLAUDE.md` (mapping table), `knowledge/index.md`, `knowledge/log.md`.

- [ ] **Step 1: Write the thin article**

Create `knowledge/concepts/dummies-notes/orchestration-workflow.md`:

```markdown
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
```

- [ ] **Step 2: Add CLAUDE.md mapping rows**

In `CLAUDE.md`'s article-mapping table, add two rows (keep all existing rows):

```markdown
| `.claude/workflows/**` | `concepts/dummies-notes/orchestration-workflow.md` |
| `scripts/graph_check.py` | `concepts/dummies-notes/orchestration-workflow.md` |
```

- [ ] **Step 3: Index + log**

Add an `orchestration-workflow.md` row to `knowledge/index.md` (dummies_notes table, 2026-06-10). Append a `knowledge/log.md` line: `## [2026-06-10] doc | scope Phase 3 drift mapping + thin orchestration-workflow article`.

- [ ] **Step 4: Verify + commit**

```bash
python3 scripts/validate-articles
git add knowledge/ CLAUDE.md
git commit -m "docs: thin orchestration-workflow article + Phase 3 drift mapping"
```
Expected: 4 articles valid; commit passes the hook (the new article is in the commit).

---

## Task 2: `graph_check.py` (TDD)

**Model: sonnet.** **Files:** Create `scripts/graph_check.py`, `scripts/tests/test_graph_check.py`; Modify `knowledge/concepts/dummies-notes/orchestration-workflow.md` + `knowledge/log.md` (graph_check.py is mapped → same-commit article touch).

- [ ] **Step 1: Write the failing tests**

Create `scripts/tests/test_graph_check.py`:

```python
import json
import os
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import concept_registry as reg  # noqa: E402
import graph_check as gc  # noqa: E402


def write_decomp(graph_dir, slug, atomic, prereqs=()):
    os.makedirs(graph_dir, exist_ok=True)
    data = {
        "concept": {"slug": slug, "name": slug, "definition": f"{slug} def."},
        "audience": "a curious adult with no domain background",
        "atomic": atomic,
        "atomic_reason": "test fixture.",
        "prerequisites": [
            {"slug": p, "name": p, "definition": f"{p} def.", "why": "needed."}
            for p in prereqs
        ],
    }
    with open(os.path.join(graph_dir, f"{slug}.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def errors(issues):
    return [m for lvl, m in issues if lvl == "ERROR"]


class TestLoadGraph(unittest.TestCase):
    def test_loads_nodes_and_edges(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "rsa", False, ["mod", "primes"])
            write_decomp(d, "mod", True)
            nodes, issues = gc.load_graph(d)
            self.assertEqual(errors(issues), [])
            self.assertEqual(nodes["rsa"]["prerequisites"], ["mod", "primes"])
            self.assertTrue(nodes["mod"]["atomic"])

    def test_unreadable_file_errors(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "bad.json"), "w") as fh:
                fh.write("{not json")
            nodes, issues = gc.load_graph(d)
            self.assertTrue(errors(issues))

    def test_missing_dir_errors(self):
        nodes, issues = gc.load_graph("/nonexistent/graph")
        self.assertTrue(errors(issues))


class TestCycles(unittest.TestCase):
    def test_acyclic_graph_is_clean(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "a", False, ["b"])
            write_decomp(d, "b", True)
            nodes, _ = gc.load_graph(d)
            self.assertEqual(gc.find_cycles(nodes), [])

    def test_cycle_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "a", False, ["b"])
            write_decomp(d, "b", False, ["a"])
            nodes, _ = gc.load_graph(d)
            issues = gc.find_cycles(nodes)
            self.assertTrue(any("cycle" in m for _, m in issues))


class TestCoverage(unittest.TestCase):
    def test_atomic_unregistered_errors(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "mod", True)
            nodes, _ = gc.load_graph(graph)
            issues = gc.check_coverage(nodes, registry)
            self.assertTrue(any("not registered" in m for m in errors(issues)))

    def test_registered_atomic_passes_without_flag(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "mod", True)
            reg.register(registry, "mod", "Mod", "mod def.")
            nodes, _ = gc.load_graph(graph)
            self.assertEqual(errors(gc.check_coverage(nodes, registry)), [])

    def test_require_illustrated_errors_on_registered_only(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "mod", True)
            reg.register(registry, "mod", "Mod", "mod def.")
            nodes, _ = gc.load_graph(graph)
            issues = gc.check_coverage(nodes, registry, require_illustrated=True)
            self.assertTrue(any("not illustrated" in m for m in errors(issues)))

    def test_frontier_prereq_warns(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "rsa", False, ["mystery"])
            reg.register(registry, "rsa", "RSA", "rsa def.")
            nodes, _ = gc.load_graph(graph)
            issues = gc.check_coverage(nodes, registry)
            warns = [m for lvl, m in issues if lvl == "WARN"]
            self.assertTrue(any("frontier" in m for m in warns))


class TestCliExit(unittest.TestCase):
    def test_clean_graph_exits_0(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "mod", True)
            reg.register(registry, "mod", "Mod", "mod def.")
            self.assertEqual(gc.main([graph, "--registry", registry]), 0)

    def test_cycle_exits_1(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "a", False, ["b"])
            write_decomp(graph, "b", False, ["a"])
            reg.register(registry, "a", "A", "a def.")
            reg.register(registry, "b", "B", "b def.")
            self.assertEqual(gc.main([graph, "--registry", registry]), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s scripts/tests -p 'test_*.py'`
Expected: FAIL — `ModuleNotFoundError: No module named 'graph_check'` (the 22 registry tests still pass).

- [ ] **Step 3: Create `scripts/graph_check.py`**

```python
#!/usr/bin/env python3
"""Check a dummies-notes concept graph (a directory of decomposition.json files).

Checks: every file parses with the required shape; the prerequisite graph is
acyclic (the cross-node cycle check the per-file validator can't do); every
graph node has a registry entry; and, with --require-illustrated, every atomic
node has an attached figure. Prerequisites with no graph file and no registry
entry are *frontier* WARNs — depth-capped runs leave them for a later pass.

Importable (functions return (level, message) tuples, matching render.py and
validate_decomposition.py) and runnable as a CLI (exit 1 on any ERROR)."""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concept_registry import DEFAULT_ROOT, lookup  # noqa: E402


def load_graph(graph_dir):
    """Return (nodes, issues): slug -> {"atomic": bool, "prerequisites": [slug]}."""
    nodes, issues = {}, []
    if not os.path.isdir(graph_dir):
        return nodes, [("ERROR", f"graph dir not found: {graph_dir}")]
    for name in sorted(os.listdir(graph_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(graph_dir, name)
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(("ERROR", f"{name}: unreadable ({exc})"))
            continue
        concept = data.get("concept") if isinstance(data, dict) else None
        slug = concept.get("slug") if isinstance(concept, dict) else None
        if not slug or not isinstance(data.get("atomic"), bool):
            issues.append(("ERROR", f"{name}: not a decomposition (missing slug/atomic)"))
            continue
        prereqs = [p.get("slug") for p in (data.get("prerequisites") or [])
                   if isinstance(p, dict) and p.get("slug")]
        nodes[slug] = {"atomic": data["atomic"], "prerequisites": prereqs}
    return nodes, issues


def find_cycles(nodes):
    """DFS cycle detection over prerequisite edges (within the graph)."""
    issues, state = [], {}

    def visit(slug, path):
        state[slug] = "in"
        for nxt in nodes.get(slug, {}).get("prerequisites", []):
            if nxt not in nodes:
                continue  # frontier/covered — no edge to follow inside the graph
            if state.get(nxt) == "in":
                cycle = path[path.index(nxt):] + [nxt] if nxt in path else [slug, nxt]
                issues.append(("ERROR", "cycle: " + " -> ".join(cycle)))
            elif state.get(nxt) != "done":
                visit(nxt, path + [nxt])
        state[slug] = "done"

    for slug in nodes:
        if state.get(slug) != "done":
            visit(slug, [slug])
    return issues


def check_coverage(nodes, registry_root, require_illustrated=False):
    """Every graph node registered; atomic nodes illustrated (when required);
    unknown prerequisites reported as frontier WARNs."""
    issues = []
    for slug, node in nodes.items():
        entry = lookup(registry_root, slug)
        if entry is None:
            issues.append(("ERROR", f"{slug}: in graph but not registered"))
            continue
        if node["atomic"] and require_illustrated and entry["status"] != "illustrated":
            issues.append(("ERROR", f"{slug}: atomic but not illustrated"))
    seen_prereqs = {p for n in nodes.values() for p in n["prerequisites"]}
    for prereq in sorted(seen_prereqs - set(nodes)):
        if lookup(registry_root, prereq) is None:
            issues.append(("WARN", f"{prereq}: frontier prerequisite "
                                   "(no graph file, not registered)"))
    return issues


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="graph_check",
        description="validate a dummies-notes concept graph directory")
    parser.add_argument("graph_dir", help="directory of decomposition .json files")
    parser.add_argument("--registry", default=DEFAULT_ROOT,
                        help=f"registry root (default: {DEFAULT_ROOT})")
    parser.add_argument("--require-illustrated", action="store_true",
                        help="atomic nodes must have an attached figure")
    args = parser.parse_args(argv)

    nodes, issues = load_graph(args.graph_dir)
    issues += find_cycles(nodes)
    issues += check_coverage(nodes, args.registry, args.require_illustrated)
    for level, message in issues:
        print(f"{level:<6} {message}")
    errors = sum(1 for lvl, _ in issues if lvl == "ERROR")
    if not issues:
        print(f"OK     {len(nodes)} node(s), acyclic, covered")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s scripts/tests -p 'test_*.py'`
Expected: PASS (33 tests = 22 registry + 11 new).

- [ ] **Step 5: Update the article + commit**

In `orchestration-workflow.md`, the `## graph_check` section already describes this — confirm it matches what shipped (adjust wording if needed; e.g. confirm the frontier-WARN semantics). Append a `knowledge/log.md` line.

```bash
git add scripts/ knowledge/
git commit -m "feat(workflow): graph_check — shape, cross-node cycles, registry coverage"
```

---

## Task 3: The `dummies-notes` Workflow script

**Model: sonnet** (full code below; verify it matches exactly). **Files:** Create `.claude/workflows/dummies-notes.js`; Modify `knowledge/concepts/dummies-notes/orchestration-workflow.md` + `knowledge/log.md` (`.claude/workflows/**` is mapped → same-commit article touch).

- [ ] **Step 1: Create `.claude/workflows/dummies-notes.js`** with exactly:

```javascript
export const meta = {
  name: 'dummies-notes',
  description: 'Decompose a topic into a concept graph, illustrate atomic concepts, review with fresh eyes, and register figures',
  whenToUse: 'args: {topic: string, definition?: string, maxDepth?: number, maxNodes?: number}. Phase 3 scope: graph + figures + registry; assembly is Phase 4.',
  phases: [
    { title: 'Decompose', detail: 'registry-aware BFS, one skill call per node' },
    { title: 'Illustrate', detail: 'runbook-first figure per atomic concept' },
    { title: 'Review', detail: 'blind reader + fidelity critic, two repairs max' },
    { title: 'Finalize', detail: 'register, attach figures, graph check' },
  ],
}

const topic = args && args.topic
if (!topic) throw new Error('args.topic is required (e.g. {topic: "modular arithmetic"})')
const MAX_DEPTH = (args && args.maxDepth) || 2
const MAX_NODES = (args && args.maxNodes) || 12
const MAX_REPAIRS = 2
const AUDIENCE = 'a curious adult with no domain background'

const CONCEPT_PROPS = {
  slug: { type: 'string' },
  name: { type: 'string' },
  definition: { type: 'string' },
}
const INDEX_SCHEMA = {
  type: 'object',
  properties: {
    concepts: {
      type: 'array',
      items: {
        type: 'object',
        properties: { ...CONCEPT_PROPS, status: { type: 'string' } },
        required: ['slug', 'status', 'definition'],
      },
    },
  },
  required: ['concepts'],
}
const DECOMP_SCHEMA = {
  type: 'object',
  properties: {
    concept: { type: 'object', properties: CONCEPT_PROPS, required: ['slug', 'name', 'definition'] },
    atomic: { type: 'boolean' },
    atomic_reason: { type: 'string' },
    prerequisites: {
      type: 'array',
      items: {
        type: 'object',
        properties: { ...CONCEPT_PROPS, why: { type: 'string' } },
        required: ['slug', 'name', 'definition', 'why'],
      },
    },
    file: { type: 'string' },
    validator_clean: { type: 'boolean' },
  },
  required: ['concept', 'atomic', 'atomic_reason', 'prerequisites', 'file', 'validator_clean'],
}
const FIGURE_SCHEMA = {
  type: 'object',
  properties: {
    figure_dir: { type: 'string' },
    lint_clean: { type: 'boolean' },
    frames: { type: 'number' },
  },
  required: ['figure_dir', 'lint_clean', 'frames'],
}
const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    pass: { type: 'boolean' },
    summary: { type: 'string' },
    gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['pass', 'summary', 'gaps'],
}
const REPORT_SCHEMA = {
  type: 'object',
  properties: {
    registered: { type: 'array', items: { type: 'string' } },
    attached: { type: 'array', items: { type: 'string' } },
    collisions: { type: 'array', items: { type: 'string' } },
    graph_check_clean: { type: 'boolean' },
    graph_check_output: { type: 'string' },
  },
  required: ['registered', 'attached', 'collisions', 'graph_check_clean', 'graph_check_output'],
}

// ---- Phase 1: registry snapshot + BFS decomposition -------------------------
phase('Decompose')

const snapshot = await agent(
  'Run `scripts/concept-registry index` from the repo root, then read registry/index.json. ' +
  'Return every concept as {slug, name, definition, status}. If the registry is empty, return an empty list.',
  { label: 'registry-snapshot', phase: 'Decompose', schema: INDEX_SCHEMA })
const covered = {}
for (const c of (snapshot && snapshot.concepts) || []) covered[c.slug] = c

const nodes = {}      // slug -> {name, definition, atomic, prerequisites:[slug], covered}
const frontier = []   // concepts left undone by caps
let rootSlug = null
let graphDir = null
let queue = [{ slug: null, name: topic, definition: (args && args.definition) || null, depth: 0 }]

while (queue.length) {
  const item = queue.shift()
  if (item.slug && nodes[item.slug]) continue
  const isRoot = rootSlug === null

  // Covered → link & stop (spec). Illustrated prerequisites are done; the root always proceeds.
  if (!isRoot && item.slug && covered[item.slug] && covered[item.slug].status === 'illustrated') {
    nodes[item.slug] = { name: item.name, definition: covered[item.slug].definition, atomic: null, prerequisites: [], covered: true }
    log(`${item.slug}: already illustrated — linked, not re-explained`)
    continue
  }
  // Identity: a registered concept keeps its registry definition verbatim.
  if (item.slug && covered[item.slug]) item.definition = covered[item.slug].definition

  if (!isRoot && item.depth > MAX_DEPTH) {
    frontier.push(item.slug || item.name)
    log(`depth cap ${MAX_DEPTH}: '${item.slug || item.name}' left as frontier`)
    continue
  }
  if (Object.keys(nodes).length >= MAX_NODES) {
    frontier.push(item.slug || item.name, ...queue.map(q => q.slug || q.name))
    log(`node cap ${MAX_NODES}: ${frontier.length} concept(s) left as frontier`)
    break
  }

  const d = await agent(
    'Follow the skill at .claude/skills/concept-decompose/SKILL.md exactly. Decompose ONE concept, one level only.\n' +
    `Concept name: ${item.name}\n` +
    (item.slug ? `Use this slug verbatim: ${item.slug}\n` : '') +
    (item.definition ? `Use this definition verbatim (identity rule): ${item.definition}\n` : '') +
    `Audience: ${AUDIENCE}\n` +
    'Reuse covered identities: read registry/index.json — if this concept or any prerequisite matches a covered slug, reuse its slug AND definition exactly.\n' +
    `Write the decomposition to ${graphDir ? graphDir + '/' : 'output/<your-canonical-slug>/graph/'}<slug>.json (create directories as needed).\n` +
    'Then run: python3 .claude/skills/concept-decompose/scripts/validate_decomposition.py <that file> — fix every ERROR until it prints "OK     clean".\n' +
    'Return the decomposition object plus the file path and validator_clean.',
    { label: `decompose:${item.slug || item.name}`, phase: 'Decompose', schema: DECOMP_SCHEMA })
  if (!d) { frontier.push(item.slug || item.name); log(`decompose agent for '${item.name}' returned nothing — frontier`); continue }
  if (!d.validator_clean) throw new Error(`decomposition for '${item.name}' did not pass its validator`)

  const slug = d.concept.slug
  if (isRoot) { rootSlug = slug; graphDir = `output/${slug}/graph` }
  nodes[slug] = {
    name: d.concept.name,
    definition: d.concept.definition,
    atomic: d.atomic,
    prerequisites: d.prerequisites.map(p => p.slug),
    covered: false,
  }
  for (const p of d.prerequisites) {
    if (!nodes[p.slug]) queue.push({ slug: p.slug, name: p.name, definition: p.definition, depth: item.depth + 1 })
  }
}
log(`graph: ${Object.keys(nodes).length} node(s) under output/${rootSlug}/graph; frontier: ${frontier.length}`)

// ---- Phases 2+3: illustrate + review, pipelined per atomic concept ----------
phase('Illustrate')

const toIllustrate = Object.entries(nodes)
  .filter(([slug, n]) => !n.covered && n.atomic === true &&
    !(covered[slug] && covered[slug].status === 'illustrated'))
  .map(([slug, n]) => ({ slug, name: n.name, definition: n.definition }))
log(`${toIllustrate.length} atomic concept(s) to illustrate`)

function illustrate(c, critique) {
  return agent(
    'Follow the skill at .claude/skills/concept-illustrator/SKILL.md exactly — runbook-first; read its references (design-system, visual-vocabulary, voice-and-metaphor, figure-json).\n' +
    `Concept slug: ${c.slug}\nName: ${c.name}\nDefinition: ${c.definition}\n` +
    `Write the figure directory to registry/${c.slug}/figure (create it; figure.json + frame-NN.svg).\n` +
    (critique ? 'A fresh-eyes review found gaps in the previous attempt. Revise the runbook FIRST, then redraw from it. The gaps:\n' + critique + '\n' : '') +
    `The figure must validate clean: python3 .claude/skills/concept-illustrator/scripts/render.py registry/${c.slug}/figure\n` +
    'Return figure_dir, lint_clean (true only if the validator printed OK/clean), and the frame count.',
    { label: `illustrate:${c.slug}`, phase: 'Illustrate', schema: FIGURE_SCHEMA })
}

async function review(c) {
  const blind = await agent(
    `You are a blind reader. Read ONLY the frame-*.svg files in registry/${c.slug}/figure — ` +
    'do NOT open figure.json or any other file (it contains answer keys that would unblind you).\n' +
    'In plain words: what does this sequence of pictures teach, step by step? What is confusing or unclear? ' +
    'You have no other context — judge the pictures alone. pass = the pictures alone teach a coherent idea.',
    { label: `blind:${c.slug}`, phase: 'Review', schema: VERDICT_SCHEMA })
  const blindSummary = blind ? blind.summary : 'blind reader unavailable'
  const critic = await agent(
    `You are the fidelity critic for the figure in registry/${c.slug}/figure.\n` +
    `The concept: ${c.name} — ${c.definition}\n` +
    'Follow .claude/skills/concept-illustrator/references/review-protocol.md. Read figure.json (runbook, captions, commentary) and every frame SVG. Check:\n' +
    '1. Runbook drift: does each frame match its runbook exactly (values, colours, pointers, what-changed)?\n' +
    `2. Comprehension: a blind reader (who saw only the SVGs) reported: "${blindSummary}". Does that match the commentary's intent? Divergence is a gap.\n` +
    '3. Commentary quality: simple sentences, faithful to the frames, vivid metaphor.\n' +
    '4. Closure: the final frame shows the end state.\n' +
    `Write your verdict to registry/${c.slug}/figure/review.json as {"pass": <bool>, "summary": "<str>", "gaps": ["..."]} and return the same verdict. pass = no real gaps.`,
    { label: `critic:${c.slug}`, phase: 'Review', schema: VERDICT_SCHEMA })
  return critic || { pass: false, summary: 'critic unavailable', gaps: ['review agent failed'] }
}

const reviewed = await pipeline(
  toIllustrate,
  c => illustrate(c, null).then(f => ({ c, f })),
  async (r) => {
    if (!r || !r.f) return { slug: r ? r.c.slug : 'unknown', pass: false, gaps: ['illustrator failed'] }
    const { c } = r
    let verdict = await review(c)
    let repairs = 0
    while (!verdict.pass && repairs < MAX_REPAIRS) {
      repairs += 1
      log(`${c.slug}: review found ${verdict.gaps.length} gap(s) — repair ${repairs}/${MAX_REPAIRS}`)
      await illustrate(c, verdict.gaps.join('\n'))
      verdict = await review(c)
    }
    if (!verdict.pass) log(`${c.slug}: still failing after ${MAX_REPAIRS} repairs — flagged`)
    return { slug: c.slug, pass: verdict.pass, gaps: verdict.gaps, repairs }
  })

// ---- Phase 4: register everything, attach figures, validate the graph -------
phase('Finalize')

const newNodes = Object.entries(nodes)
  .filter(([, n]) => !n.covered)
  .map(([slug, n]) => ({ slug, name: n.name, definition: n.definition, prerequisites: n.prerequisites }))
const figures = (reviewed || []).filter(Boolean)

const report = await agent(
  `Finalize a dummies-notes run from the repo root. Data:\n` +
  `NODES = ${JSON.stringify(newNodes)}\n` +
  `FIGURES = ${JSON.stringify(figures.map(f => f.slug))}\n` +
  `GRAPH_DIR = output/${rootSlug}/graph\n` +
  'Steps, in order:\n' +
  '1. For each node in NODES: scripts/concept-registry register --slug <slug> --name <name> --definition <definition> ' +
  '(quote arguments carefully) plus --prereqs <comma-joined prerequisites> when non-empty. ' +
  'Idempotent re-registration is fine; if one fails with a slug-collision ERROR, record it in collisions and continue.\n' +
  '2. For each slug in FIGURES: python3 .claude/skills/concept-illustrator/scripts/render.py registry/<slug>/figure ' +
  '(must be clean), then scripts/concept-registry attach-figure <slug> registry/<slug>/figure.\n' +
  '3. scripts/concept-registry index\n' +
  '4. python3 scripts/graph_check.py output/' + rootSlug + '/graph --require-illustrated — capture its full output.\n' +
  'Return registered (slugs), attached (slugs), collisions, graph_check_clean (exit 0), graph_check_output.',
  { label: 'finalize', phase: 'Finalize', schema: REPORT_SCHEMA })

const flagged = figures.filter(f => !f.pass).map(f => f.slug)
log(`done: ${report && report.registered ? report.registered.length : 0} registered, ` +
  `${report && report.attached ? report.attached.length : 0} attached, ${flagged.length} flagged, ` +
  `graph check ${report && report.graph_check_clean ? 'clean' : 'FAILED'}`)

return {
  root: rootSlug,
  graph_dir: `output/${rootSlug}/graph`,
  nodes: Object.keys(nodes).length,
  illustrated: figures.filter(f => f.pass).map(f => f.slug),
  flagged,
  frontier,
  collisions: (report && report.collisions) || [],
  graph_check_clean: !!(report && report.graph_check_clean),
}
```

- [ ] **Step 2: Sanity-check the file**

```bash
node --check .claude/workflows/dummies-notes.js 2>/dev/null || python3 - <<'EOF'
# node may not be installed; minimal sanity: file exists, has meta + phases
text = open('.claude/workflows/dummies-notes.js', encoding='utf-8').read()
for token in ("export const meta", "phase('Decompose')", "phase('Illustrate')",
              "phase('Finalize')", "MAX_REPAIRS", "graph_check.py"):
    assert token in text, f"missing {token}"
print("workflow script sanity ok")
EOF
```
Expected: `workflow script sanity ok` (or a clean `node --check`). Note: `export const meta` is ESM — plain `node --check` may reject it; the Python token check is the fallback acceptance.

- [ ] **Step 3: Update the article + commit**

In `orchestration-workflow.md`, confirm the "Run shape" section matches the implemented script (snapshot → BFS with caps → pipeline illustrate/review with 2 repairs → finalize with `--prereqs` + `--require-illustrated` graph check); adjust wording where it differs. Append a `knowledge/log.md` line.

```bash
git add .claude/workflows/ knowledge/
git commit -m "feat(workflow): dummies-notes orchestrator — decompose, illustrate, review, finalize"
```

---

## Task 4: Smoke run (end-to-end acceptance) — CONTROLLER-RUN

**This task is executed by the controller (main session), not a subagent**, because it invokes the Workflow tool. **Files touched by the run:** `output/modular-arithmetic/graph/modular-arithmetic.json`, `registry/modular-arithmetic/` (figure/ + entry → illustrated), `registry/index.json`.

- [ ] **Step 1: Run the workflow** (controller): `Workflow {name: "dummies-notes", args: {topic: "modular arithmetic"}}`. Expected shape: root `modular-arithmetic`; 1 node; decomposes atomic (reusing the registered definition verbatim); 1 figure illustrated into `registry/modular-arithmetic/figure/` (clock metaphor, closure frame); review passes (≤2 repairs); finalize attaches + graph check clean. If the run returns flagged figures or a failed graph check, READ the run artifacts and `review.json`, diagnose, and re-run after fixing (the workflow is idempotent for this topic).

- [ ] **Step 2: Verify the artifacts** (controller):

```bash
python3 .claude/skills/concept-illustrator/scripts/render.py registry/modular-arithmetic/figure
python3 scripts/graph_check.py output/modular-arithmetic/graph --require-illustrated
scripts/concept-registry lookup modular-arithmetic
test -f registry/modular-arithmetic/figure/review.json && python3 -c "import json;d=json.load(open('registry/modular-arithmetic/figure/review.json'));print('review pass:',d['pass'])"
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 scripts/validate-articles
```
Expected: figure clean; graph check `OK 1 node(s)`; entry `illustrated` with figure `modular-arithmetic/figure`; review pass True; 33 tests; articles valid. ALSO verify identity held: the graph file's definition is byte-identical to the registry entry's.

- [ ] **Step 3: Commit the run artifacts** (registry/** is mapped → article touch; note the run in `atomic-illustration-catalog.md`'s seeded-entries section: modular-arithmetic is now illustrated, produced by the first workflow run; append a `knowledge/log.md` entry):

```bash
git add output/ registry/ knowledge/
git commit -m "feat(workflow): first dummies-notes run — modular-arithmetic illustrated end-to-end"
```

---

## Task 5: Finalize the knowledge base

**Model: sonnet.** **Files:** Modify `knowledge/concepts/dummies-notes/orchestration-workflow.md` (mature), `knowledge/index.md`, `knowledge/log.md`, `CLAUDE.md` (Current state).

- [ ] **Step 1:** Mature `orchestration-workflow.md`: `status: mature`, accurate to the shipped script + the smoke run (note the run record: modular-arithmetic, 1 node, review passed). Note remaining Phase 4 scope (assembly, map, chain review) and the open question now carried forward: figure invalidation/versioning.
- [ ] **Step 2:** `CLAUDE.md` Current state: Phase 3 shipped (the `dummies-notes` Workflow + graph_check; run via the Workflow tool with `{topic}`); only Phase 4 remains. Add the graph_check command to the commands block.
- [ ] **Step 3:** `knowledge/index.md` row refreshed; `knowledge/log.md` compile entry for Phase 3.
- [ ] **Step 4:** Verify + commit:

```bash
python3 scripts/validate-articles
git add knowledge/ CLAUDE.md
git commit -m "docs: mature orchestration-workflow; Phase 3 shipped"
```

---

## Definition of done (Phase 3)

- `scripts/graph_check.py`: 11 tests green (33 total in the scripts suite); detects cross-node cycles; coverage + frontier semantics as specified.
- `.claude/workflows/dummies-notes.js` ships with the exact orchestration above (caps logged, ≤2 repairs, blind reader sees only SVGs, finalize persists `--prereqs`).
- The smoke run completed: `modular-arithmetic` is `illustrated` in the registry with a lint-clean, review-passed figure at `registry/modular-arithmetic/figure/`, graph at `output/modular-arithmetic/graph/`, `graph_check --require-illustrated` exits 0.
- All three suites green; `validate-articles` valid; `orchestration-workflow.md` mature; CLAUDE.md current.
