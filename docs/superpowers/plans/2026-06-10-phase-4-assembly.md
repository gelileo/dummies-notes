# Phase 4 — assembly + map + chain review — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn a completed run (graph + registry figures) into the learner-facing deliverable — `output/<topic>/index.html` (bottom-up explainer) and `output/<topic>/map.html` (concept map) — plus the compose-from-children mode for the target's composition figure and the end-to-end chain review.

**Architecture:** Assembly is **deterministic** — `scripts/assemble.py` (zero-dep, TDD) reads the graph dir + registry and emits both HTML files; no agent writes HTML. Per the spec: topological bottom-up order (prerequisites before dependents, target last); atomic nodes embed their figure frames inline as a slideshow; **intermediate nodes render caption-only** (definition + links up to children) — **except the target**, which gets a single-frame structural **composition figure** authored via the illustrator's new compose-from-children mode; **already-covered prerequisites are linked, not re-inlined** (a short section linking to the registry figure's viewer); frontier prerequisites get an honest stub note. The workflow gains `Assemble` + `ChainReview` phases (compose root figure if non-atomic → run assemble.py → fresh-eyes chain reviewer writes `chain-review.json`; gaps surface as a report, no auto-repair — allowed by the spec).

**Tech Stack:** Python 3 stdlib + unittest; vanilla HTML/CSS/JS (no frameworks); the Workflow JS runtime for the two new phases. `assemble.py` imports `concept_registry` (same dir) and the illustrator's `render` module (for `build_viewer` on covered figures lacking a viewer). Spec: `docs/superpowers/specs/2026-06-09-dummies-notes-design.md` (Data flow steps 5–6; "output/<topic>/" naming; compose-from-children).

**Conventions:**
- assemble.py tests join the scripts suite: `python3 -m unittest discover -s scripts/tests -p 'test_*.py'` (35 now; ~47 after).
- **Drift gate:** Task 1 adds `scripts/assemble.py` to `orchestration-workflow.md`'s `affects` + a CLAUDE.md row. After that: commits touching `assemble.py` or `.claude/workflows/**` need the orchestration article; the illustrator `SKILL.md` needs `illustration-engine.md`. Never `--no-verify`; STOP if blocked unexpectedly.
- **Task 6 invokes the Workflow tool** (the RSA run: multi-node — expect roughly 15–25 subagents). Controller-run; consent obtained at execution handoff.

## Model policy

Implementers **sonnet** (complete code below; judgment done here) — except Task 4 (compose-mode contract wording) which is small enough for sonnet with the exact text provided. Reviews: spec=sonnet, quality/final=opus. Workflow agents inherit the session model.

## File structure

| File | Responsibility | Task |
|------|----------------|------|
| `scripts/assemble.py` | deterministic assembler: graph→index.html+map.html | 1–3 |
| `scripts/tests/test_assemble.py` | its tests | 1–3 |
| `.claude/skills/concept-illustrator/SKILL.md` (+ test) | compose-from-children mode | 4 |
| `.claude/workflows/dummies-notes.js` | Assemble + ChainReview phases | 5 |
| `output/modular-arithmetic/`, `output/rsa-encryption/`, `registry/*` | acceptance artifacts | 6 |
| knowledge + CLAUDE.md | all-phases-shipped finalization | 7 |

---

## Task 1: assemble.py core — graph loading, root, topological order

**Model: sonnet.** **Files:** Create `scripts/assemble.py`, `scripts/tests/test_assemble.py`; Modify `knowledge/concepts/dummies-notes/orchestration-workflow.md` (add `"scripts/assemble.py"` to `affects`, one sentence noting the assembler), `CLAUDE.md` (add row `| `scripts/assemble.py` | `concepts/dummies-notes/orchestration-workflow.md` |`), `knowledge/log.md`.

- [ ] **Step 1: Write the failing tests** — create `scripts/tests/test_assemble.py`:

```python
import json
import os
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import assemble as asm  # noqa: E402
import concept_registry as reg  # noqa: E402


def write_decomp(graph_dir, slug, atomic, prereqs=()):
    """prereqs: list of slugs; expands to full prerequisite objects."""
    os.makedirs(graph_dir, exist_ok=True)
    data = {
        "concept": {"slug": slug, "name": slug.replace("-", " ").title(),
                    "definition": f"Plain definition of {slug}."},
        "audience": "a curious adult with no domain background",
        "atomic": atomic,
        "atomic_reason": "fixture.",
        "prerequisites": [
            {"slug": p, "name": p.replace("-", " ").title(),
             "definition": f"Plain definition of {p}.", "why": f"{slug} needs {p}."}
            for p in prereqs
        ],
    }
    with open(os.path.join(graph_dir, f"{slug}.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh)


class TestLoadFullGraph(unittest.TestCase):
    def test_loads_names_definitions_and_prereq_objects(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "rsa-encryption", False, ["prime-numbers"])
            nodes, issues = asm.load_full_graph(d)
            self.assertEqual([m for lvl, m in issues if lvl == "ERROR"], [])
            node = nodes["rsa-encryption"]
            self.assertEqual(node["name"], "Rsa Encryption")
            self.assertIn("Plain definition", node["definition"])
            self.assertEqual(node["prerequisites"][0]["slug"], "prime-numbers")
            self.assertIn("why", node["prerequisites"][0])

    def test_missing_dir_errors(self):
        nodes, issues = asm.load_full_graph("/nonexistent")
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in issues))


class TestFindRoot(unittest.TestCase):
    def test_single_root(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "rsa", False, ["primes", "asym"])
            write_decomp(d, "primes", True)
            write_decomp(d, "asym", True)
            nodes, _ = asm.load_full_graph(d)
            self.assertEqual(asm.find_root(nodes), "rsa")

    def test_multiple_roots_raise(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "a", True)
            write_decomp(d, "b", True)
            nodes, _ = asm.load_full_graph(d)
            with self.assertRaises(ValueError):
                asm.find_root(nodes)


class TestTopoOrder(unittest.TestCase):
    def test_prereqs_come_before_dependents_root_last(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "rsa", False, ["primes", "asym"])
            write_decomp(d, "primes", True)
            write_decomp(d, "asym", True)
            nodes, _ = asm.load_full_graph(d)
            order = asm.topo_order(nodes)
            self.assertEqual(order[-1], "rsa")
            self.assertLess(order.index("asym"), order.index("rsa"))
            self.assertLess(order.index("primes"), order.index("rsa"))

    def test_deterministic_alphabetical_ties(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "top", False, ["zeta", "alpha"])
            write_decomp(d, "zeta", True)
            write_decomp(d, "alpha", True)
            nodes, _ = asm.load_full_graph(d)
            self.assertEqual(asm.topo_order(nodes), ["alpha", "zeta", "top"])

    def test_out_of_graph_prereqs_are_ignored_for_ordering(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "solo", True, ["external-thing"])
            nodes, _ = asm.load_full_graph(d)
            self.assertEqual(asm.topo_order(nodes), ["solo"])

    def test_cycle_raises(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "a", False, ["b"])
            write_decomp(d, "b", False, ["a"])
            nodes, _ = asm.load_full_graph(d)
            with self.assertRaises(ValueError):
                asm.topo_order(nodes)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure** — `python3 -m unittest discover -s scripts/tests -p 'test_*.py'` → FAIL: `No module named 'assemble'` (35 existing tests still pass).

- [ ] **Step 3: Create `scripts/assemble.py`** (core only — HTML builders come in Tasks 2–3):

```python
#!/usr/bin/env python3
"""Assemble the learner-facing deliverable for a topic.

Reads a concept graph (output/<topic>/graph/*.json, as produced by the
dummies-notes workflow) plus the registry, and writes:

  output/<topic>/index.html  — the bottom-up explainer: prerequisites before
                               dependents, the target last; atomic nodes embed
                               their figure frames as an inline slideshow;
                               intermediate nodes are caption-only (links up to
                               their children); already-covered prerequisites
                               are LINKED to their registry figure, never
                               re-inlined; frontier prerequisites get a stub.
  output/<topic>/map.html    — the concept map: one node per concept (with a
                               first-frame thumbnail when illustrated), edges
                               are prerequisite links, layered by depth.

Deterministic and zero-dependency: no agent writes HTML."""

import argparse
import html
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from concept_registry import DEFAULT_ROOT, lookup  # noqa: E402

_ILLUSTRATOR = os.path.join(os.path.dirname(_HERE), ".claude", "skills",
                            "concept-illustrator", "scripts")
sys.path.insert(0, _ILLUSTRATOR)
import render  # noqa: E402  (build_viewer for covered figures lacking one)


def load_full_graph(graph_dir):
    """slug -> {name, definition, atomic, prerequisites:[{slug,name,definition,why}]}."""
    nodes, issues = {}, []
    if not os.path.isdir(graph_dir):
        return nodes, [("ERROR", f"graph dir not found: {graph_dir}")]
    for fname in sorted(os.listdir(graph_dir)):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(graph_dir, fname), encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(("ERROR", f"{fname}: unreadable ({exc})"))
            continue
        concept = data.get("concept") if isinstance(data, dict) else None
        slug = concept.get("slug") if isinstance(concept, dict) else None
        if not slug:
            issues.append(("ERROR", f"{fname}: missing concept.slug"))
            continue
        nodes[slug] = {
            "name": concept.get("name", slug),
            "definition": concept.get("definition", ""),
            "atomic": bool(data.get("atomic")),
            "prerequisites": [p for p in (data.get("prerequisites") or [])
                              if isinstance(p, dict) and p.get("slug")],
        }
    return nodes, issues


def find_root(nodes):
    """The root is the one node no other node lists as a prerequisite."""
    referenced = {p["slug"] for n in nodes.values() for p in n["prerequisites"]}
    roots = sorted(set(nodes) - referenced)
    if len(roots) != 1:
        raise ValueError(f"expected exactly one root, found: {roots}")
    return roots[0]


def topo_order(nodes):
    """Prerequisites before dependents (bottom-up); alphabetical ties; root last."""
    emitted, order = set(), []
    remaining = dict(nodes)
    while remaining:
        ready = sorted(
            s for s, n in remaining.items()
            if all(p["slug"] in emitted or p["slug"] not in nodes
                   for p in n["prerequisites"]))
        if not ready:
            raise ValueError("cycle in graph; run graph_check first")
        for s in ready:
            order.append(s)
            emitted.add(s)
            del remaining[s]
    return order
```

- [ ] **Step 4: Run to verify pass** — 43 tests (35 + 8). 

- [ ] **Step 5: Mapping + commit** — add `- "scripts/assemble.py"` to `orchestration-workflow.md`'s `affects` list and one sentence in its body ("Assembly is deterministic: `scripts/assemble.py` renders index.html + map.html from the graph + registry — no agent writes HTML."); add the CLAUDE.md row; append a log line. `python3 scripts/validate-articles` → valid.

```bash
git add scripts/ knowledge/ CLAUDE.md
git commit -m "feat(assemble): graph loading, root detection, bottom-up topological order"
```

---

## Task 2: assemble.py — the explainer (index.html)

**Model: sonnet.** **Files:** Modify `scripts/assemble.py`, `scripts/tests/test_assemble.py`; Modify `knowledge/concepts/dummies-notes/orchestration-workflow.md` + `knowledge/log.md` (assemble.py mapped).

- [ ] **Step 1: Write the failing tests** — append to `test_assemble.py` (before `if __name__`):

```python
TINY_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 100">'
            '<text class="t">Tiny figure</text></svg>')


def make_figure(figure_dir, slug, n_frames=2):
    os.makedirs(figure_dir, exist_ok=True)
    frames = []
    for i in range(1, n_frames + 1):
        name = f"frame-{i:02d}.svg"
        with open(os.path.join(figure_dir, name), "w", encoding="utf-8") as fh:
            fh.write(TINY_SVG)
        frames.append({"file": name, "caption": f"Step {i}.",
                       "runbook": f"Frame {i}.", "commentary": f"Step {i}. Simple."})
    with open(os.path.join(figure_dir, "figure.json"), "w", encoding="utf-8") as fh:
        json.dump({"concept_slug": slug, "archetype": "illustrative",
                   "playback": "slideshow" if n_frames > 1 else "static",
                   "frames": frames}, fh)
    return figure_dir


def make_world(base):
    """graph: rsa -> [modular-arithmetic(covered), primes(atomic), asym(atomic)];
    registry: mod covered+illustrated; primes/asym illustrated; rsa registered."""
    graph = os.path.join(base, "out", "graph")
    registry = os.path.join(base, "registry")
    write_decomp(graph, "rsa", False, ["modular-arithmetic", "primes", "asym"])
    write_decomp(graph, "primes", True)
    write_decomp(graph, "asym", True)
    for slug in ("modular-arithmetic", "primes", "asym"):
        reg.register(registry, slug, slug.title(), f"Plain definition of {slug}.")
        reg.attach_figure(registry, slug,
                          make_figure(os.path.join(registry, slug, "figure"), slug))
    reg.register(registry, "rsa", "Rsa", "Plain definition of rsa.")
    return graph, registry, os.path.join(base, "out")


class TestExplainer(unittest.TestCase):
    def test_sections_in_bottom_up_order_root_last(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry, out = make_world(base)
            result, issues = asm.assemble(graph, registry, out)
            text = open(os.path.join(out, "index.html"), encoding="utf-8").read()
            for s in ("asym", "primes", "rsa"):
                self.assertIn(f'<section id="{s}"', text)
            self.assertLess(text.index('<section id="asym"'), text.index('<section id="rsa"'))
            self.assertLess(text.index('<section id="primes"'), text.index('<section id="rsa"'))

    def test_atomic_nodes_embed_frames_inline(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry, out = make_world(base)
            asm.assemble(graph, registry, out)
            text = open(os.path.join(out, "index.html"), encoding="utf-8").read()
            # primes + asym: 2 frames each, inline
            self.assertGreaterEqual(text.count("<svg"), 4)

    def test_covered_prereq_is_linked_not_inlined(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry, out = make_world(base)
            asm.assemble(graph, registry, out)
            text = open(os.path.join(out, "index.html"), encoding="utf-8").read()
            self.assertIn('id="modular-arithmetic"', text)
            self.assertIn("Already covered", text)
            self.assertIn("figure.html", text)  # link target
            # the covered figure's frames are NOT inlined: its viewer link exists
            viewer = os.path.join(registry, "modular-arithmetic", "figure", "figure.html")
            self.assertTrue(os.path.exists(viewer))

    def test_intermediate_root_is_caption_only_with_child_links(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry, out = make_world(base)
            asm.assemble(graph, registry, out)
            text = open(os.path.join(out, "index.html"), encoding="utf-8").read()
            rsa = text[text.index('<section id="rsa"'):]
            self.assertIn('href="#primes"', rsa)
            self.assertIn("rsa needs primes", rsa)

    def test_frontier_prereq_gets_stub(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "out", "graph")
            registry = os.path.join(base, "registry")
            write_decomp(graph, "solo", True, ["mystery-idea"])
            reg.register(registry, "solo", "Solo", "Plain definition of solo.")
            reg.attach_figure(registry, "solo",
                              make_figure(os.path.join(registry, "solo", "figure"), "solo"))
            asm.assemble(graph, registry, os.path.join(base, "out"))
            text = open(os.path.join(base, "out", "index.html"), encoding="utf-8").read()
            self.assertIn("not yet covered", text)
            self.assertIn("mystery-idea", text)
```

- [ ] **Step 2: Run to verify failure** — `assemble` has no `assemble` attribute yet.

- [ ] **Step 3: Implement** — append to `scripts/assemble.py`:

```python
PAGE_CSS = """
:root{color-scheme:light dark}
body{margin:0;font-family:-apple-system,"Segoe UI",Roboto,system-ui,sans-serif;
     max-width:760px;margin:0 auto;padding:2rem 1rem;line-height:1.55}
header h1{margin-bottom:.2rem} .definition{opacity:.85}
section{margin:2.5rem 0;border-top:1px solid rgba(127,127,127,.25);padding-top:1.2rem}
.figure .frame{display:none} .figure .frame.active{display:block}
.figure svg{max-width:100%;height:auto}
.figure .caption{text-align:center;opacity:.85;min-height:1.4em}
.figure .bar{display:flex;gap:.5rem;justify-content:center;align-items:center}
.figure button{font:inherit;padding:.2rem .7rem;cursor:pointer}
.covered,.frontier{opacity:.92} .meta{font-size:.85em;opacity:.7}
ul.children li{margin:.3rem 0}
"""

SLIDESHOW_JS = """
document.querySelectorAll('.figure').forEach(function(fig){
  var frames=fig.querySelectorAll('.frame'),i=0,
      cap=fig.querySelector('.caption'),count=fig.querySelector('.count');
  function show(n){i=(n+frames.length)%frames.length;
    frames.forEach(function(f,j){f.classList.toggle('active',j===i)});
    if(cap)cap.textContent=frames[i].getAttribute('data-caption')||'';
    if(count)count.textContent=(i+1)+' / '+frames.length;}
  var p=fig.querySelector('.prev'),n=fig.querySelector('.next');
  if(p)p.onclick=function(){show(i-1)}; if(n)n.onclick=function(){show(i+1)};
  show(0);});
"""


def load_figure(figure_dir):
    """[(svg_text, caption)] for a figure dir, or None when absent/incomplete."""
    figure_json = os.path.join(figure_dir, "figure.json")
    if not os.path.exists(figure_json):
        return None
    try:
        with open(figure_json, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    frames = []
    for frame in data.get("frames") or []:
        name = frame.get("file") if isinstance(frame, dict) else frame
        path = os.path.join(figure_dir, name or "")
        if not name or not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as fh:
            caption = frame.get("caption", "") if isinstance(frame, dict) else ""
            frames.append((fh.read(), caption))
    return frames or None


def figure_html(frames):
    parts = ['<div class="figure">', '<div class="stage">']
    for i, (svg, caption) in enumerate(frames):
        cls = "frame active" if i == 0 else "frame"
        parts.append(f'<div class="{cls}" data-caption="{html.escape(caption, quote=True)}">{svg}</div>')
    parts.append("</div>")
    parts.append('<p class="caption"></p>')
    if len(frames) > 1:
        parts.append('<div class="bar"><button class="prev">&larr;</button>'
                     '<span class="count"></span><button class="next">&rarr;</button></div>')
    parts.append("</div>")
    return "\n".join(parts)


def _children_list(node, known_ids):
    items = []
    for p in node["prerequisites"]:
        label = html.escape(p.get("name", p["slug"]))
        why = html.escape(p.get("why", ""))
        if p["slug"] in known_ids:
            items.append(f'<li><a href="#{p["slug"]}">{label}</a>'
                         f'{" — " + why if why else ""}</li>')
        else:
            items.append(f'<li>{label} <span class="meta">({p["slug"]}: not yet '
                         f'covered — left for a later run)</span></li>')
    return '<ul class="children">' + "".join(items) + "</ul>" if items else ""


def _figure_dir_for(entry, registry_root):
    return os.path.normpath(os.path.join(registry_root, entry["figure"])) \
        if entry and entry.get("figure") else None


def _ensure_viewer(figure_dir):
    """Generate the figure's standalone viewer if missing; return its path."""
    out = os.path.join(figure_dir, "figure.html")
    if not os.path.exists(out):
        render.build_viewer(figure_dir, render.DEFAULT_TEMPLATE, out)
    return out


def build_explainer(order, nodes, covered, frontier, registry_root, out_dir, root):
    known_ids = set(nodes) | set(covered)
    parts = ["<!doctype html>", '<html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             f"<title>{html.escape(nodes[root]['name'])} — dummies notes</title>",
             f"<style>{PAGE_CSS}</style></head><body>",
             f"<header><h1>{html.escape(nodes[root]['name'])}</h1>",
             f'<p class="definition">{html.escape(nodes[root]["definition"])}</p>',
             f'<p class="meta">Built bottom-up from {len(order)} concept(s)'
             f'{" + " + str(len(covered)) + " already covered" if covered else ""}.'
             "</p></header><main>"]

    # Already-covered prerequisites first (linked, never re-inlined).
    for slug in sorted(covered):
        entry = covered[slug]
        figure_dir = _figure_dir_for(entry, registry_root)
        href = ""
        if figure_dir and os.path.isdir(figure_dir):
            viewer = _ensure_viewer(figure_dir)
            href = os.path.relpath(viewer, out_dir)
        parts.append(f'<section id="{html.escape(slug)}" class="covered">'
                     f"<h2>{html.escape(entry['name'])}</h2>"
                     f'<p class="definition">{html.escape(entry["definition"])}</p>'
                     f'<p>Already covered — '
                     + (f'<a href="{html.escape(href)}">see its figure</a>.' if href
                        else "figure pending.") + "</p></section>")

    for slug in order:
        node = nodes[slug]
        entry = lookup(registry_root, slug)
        figure_dir = _figure_dir_for(entry, registry_root)
        frames = load_figure(figure_dir) if figure_dir else None
        parts.append(f'<section id="{html.escape(slug)}">'
                     f"<h2>{html.escape(node['name'])}</h2>"
                     f'<p class="definition">{html.escape(node["definition"])}</p>')
        if frames:
            parts.append(figure_html(frames))
        elif node["atomic"]:
            parts.append('<p class="meta">Figure pending for this concept.</p>')
        if node["prerequisites"]:
            parts.append("<p>Builds on:</p>" + _children_list(node, known_ids))
        parts.append("</section>")

    if frontier:
        parts.append('<section class="frontier"><h2>Frontier</h2>'
                     "<p>These prerequisites were not yet covered in this run "
                     "(depth or node caps):</p><ul>"
                     + "".join(f"<li>{html.escape(s)}</li>" for s in sorted(frontier))
                     + "</ul></section>")

    parts.append(f"</main><script>{SLIDESHOW_JS}</script></body></html>")
    return "\n".join(parts)


def classify_prereqs(nodes, registry_root):
    """Prereq slugs not in the graph: covered (registry entry) vs frontier."""
    covered, frontier = {}, set()
    for node in nodes.values():
        for p in node["prerequisites"]:
            slug = p["slug"]
            if slug in nodes or slug in covered or slug in frontier:
                continue
            entry = lookup(registry_root, slug)
            if entry is not None:
                covered[slug] = entry
            else:
                frontier.add(slug)
    return covered, frontier


def assemble(graph_dir, registry_root, out_dir):
    nodes, issues = load_full_graph(graph_dir)
    if any(lvl == "ERROR" for lvl, _ in issues):
        return None, issues
    root = find_root(nodes)
    order = topo_order(nodes)
    covered, frontier = classify_prereqs(nodes, registry_root)
    os.makedirs(out_dir, exist_ok=True)
    index = build_explainer(order, nodes, covered, frontier,
                            registry_root, out_dir, root)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(index)
    map_html = build_map(order, nodes, covered, frontier, registry_root, root)
    with open(os.path.join(out_dir, "map.html"), "w", encoding="utf-8") as fh:
        fh.write(map_html)
    return {"root": root, "sections": len(order) + len(covered),
            "covered": sorted(covered), "frontier": sorted(frontier)}, issues
```

NOTE: `build_map` is implemented in Task 3. For THIS task's tests to run before Task 3, add a temporary stub at the very end of the file — it will be REPLACED in Task 3:

```python
def build_map(order, nodes, covered, frontier, registry_root, root):
    return "<!doctype html><title>map stub (replaced in Task 3)</title>"
```

- [ ] **Step 4: Run to verify pass** — 48 tests (43 + 5).
- [ ] **Step 5: Article sentence (explainer semantics: covered linked, intermediates caption-only, frontier stubs) + log; commit:**

```bash
git add scripts/ knowledge/
git commit -m "feat(assemble): bottom-up explainer — inline slideshows, covered links, frontier stubs"
```

---

## Task 3: assemble.py — the concept map + CLI

**Model: sonnet.** **Files:** Modify `scripts/assemble.py`, `scripts/tests/test_assemble.py`; Modify `knowledge/concepts/dummies-notes/orchestration-workflow.md` + `knowledge/log.md`.

- [ ] **Step 1: Write the failing tests** — append:

```python
class TestMap(unittest.TestCase):
    def test_map_has_node_per_concept_and_edges(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry, out = make_world(base)
            asm.assemble(graph, registry, out)
            text = open(os.path.join(out, "map.html"), encoding="utf-8").read()
            for slug in ("rsa", "primes", "asym", "modular-arithmetic"):
                self.assertIn(f'data-node="{slug}"', text)
            self.assertEqual(text.count("<line"), 3)  # rsa -> its 3 prereqs

    def test_map_nodes_link_to_explainer_sections(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry, out = make_world(base)
            asm.assemble(graph, registry, out)
            text = open(os.path.join(out, "map.html"), encoding="utf-8").read()
            self.assertIn('href="index.html#primes"', text)

    def test_illustrated_nodes_carry_thumbnails(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry, out = make_world(base)
            asm.assemble(graph, registry, out)
            text = open(os.path.join(out, "map.html"), encoding="utf-8").read()
            self.assertGreaterEqual(text.count("<svg"), 3)  # primes, asym, mod thumbs


class TestCli(unittest.TestCase):
    def test_cli_assembles_and_exits_0(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry, out = make_world(base)
            rc = asm.main([graph, "--registry", registry, "--out", out])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(os.path.join(out, "index.html")))
            self.assertTrue(os.path.exists(os.path.join(out, "map.html")))

    def test_cli_missing_graph_exits_1(self):
        with tempfile.TemporaryDirectory() as base:
            rc = asm.main(["/nonexistent", "--registry", base,
                           "--out", os.path.join(base, "o")])
            self.assertEqual(rc, 1)
```

- [ ] **Step 2: Run to verify failure** — `data-node` not present (stub map), `main` missing.

- [ ] **Step 3: REPLACE the Task 2 stub `build_map`** with the real implementation, and add `main`:

```python
MAP_CSS = """
:root{color-scheme:light dark}
body{margin:0;font-family:-apple-system,"Segoe UI",Roboto,system-ui,sans-serif;padding:1.5rem}
.canvas{position:relative;margin:0 auto}
.edges{position:absolute;inset:0;z-index:0}
.edges line{stroke:rgba(127,127,127,.55);stroke-width:1.5}
.node{position:absolute;z-index:1;width:200px;border:1px solid rgba(127,127,127,.5);
      border-radius:8px;padding:.5rem;background:Canvas;text-align:center}
.node .thumb svg{max-width:170px;height:auto;display:block;margin:0 auto}
.node .badge{font-size:.72em;opacity:.7;display:block;margin-top:.2rem}
.node.covered{border-style:dashed} .node.frontier{border-style:dotted;opacity:.75}
h1{text-align:center}
"""

_NODE_W, _NODE_H, _COL_W, _ROW_H = 200, 150, 230, 240


def _depths(order, nodes, covered, frontier, root):
    """Layer per node: root at 0, prerequisites below their dependents."""
    depth = {root: 0}
    changed = True
    while changed:
        changed = False
        for slug, node in nodes.items():
            if slug not in depth:
                continue
            for p in node["prerequisites"]:
                target = depth[slug] + 1
                if depth.get(p["slug"], -1) < target:
                    depth[p["slug"]] = target
                    changed = True
    for slug in list(nodes) + list(covered) + list(frontier):
        depth.setdefault(slug, 1)
    return depth


def _thumb(slug, registry_root):
    entry = lookup(registry_root, slug)
    figure_dir = _figure_dir_for(entry, registry_root)
    frames = load_figure(figure_dir) if figure_dir else None
    return f'<div class="thumb">{frames[0][0]}</div>' if frames else ""


def build_map(order, nodes, covered, frontier, registry_root, root):
    depth = _depths(order, nodes, covered, frontier, root)
    layers = {}
    for slug, d in depth.items():
        layers.setdefault(d, []).append(slug)
    for d in layers:
        layers[d].sort()
    width = max(len(v) for v in layers.values()) * _COL_W + 40
    height = (max(layers) + 1) * _ROW_H + 40
    pos = {}
    for d, slugs in layers.items():
        offset = (width - len(slugs) * _COL_W) / 2
        for i, slug in enumerate(slugs):
            pos[slug] = (offset + i * _COL_W + (_COL_W - _NODE_W) / 2, 20 + d * _ROW_H)

    edges = []
    for slug, node in nodes.items():
        for p in node["prerequisites"]:
            if p["slug"] in pos:
                x1, y1 = pos[slug][0] + _NODE_W / 2, pos[slug][1] + _NODE_H
                x2, y2 = pos[p["slug"]][0] + _NODE_W / 2, pos[p["slug"]][1]
                edges.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" '
                             f'x2="{x2:.0f}" y2="{y2:.0f}"/>')

    node_divs = []
    for slug, (x, y) in pos.items():
        if slug in nodes:
            name, badge, cls = nodes[slug]["name"], \
                ("atomic" if nodes[slug]["atomic"] else "composite"), ""
        elif slug in covered:
            name, badge, cls = covered[slug]["name"], "already covered", " covered"
        else:
            name, badge, cls = slug, "frontier — not yet covered", " frontier"
        thumb = _thumb(slug, registry_root) if cls != " frontier" else ""
        node_divs.append(
            f'<div class="node{cls}" data-node="{html.escape(slug)}" '
            f'style="left:{x:.0f}px;top:{y:.0f}px">'
            f'<a href="index.html#{html.escape(slug)}"><strong>'
            f"{html.escape(name)}</strong></a>{thumb}"
            f'<span class="badge">{badge}</span></div>')

    title = html.escape(nodes[root]["name"])
    return "\n".join([
        "<!doctype html>", '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{title} — concept map</title>",
        f"<style>{MAP_CSS}</style></head><body>",
        f"<h1>{title} — concept map</h1>",
        f'<div class="canvas" style="width:{width:.0f}px;height:{height:.0f}px">',
        f'<svg class="edges" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}">', *edges, "</svg>",
        *node_divs, "</div></body></html>"])


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="assemble",
        description="assemble output/<topic>/index.html + map.html from a graph")
    parser.add_argument("graph_dir")
    parser.add_argument("--registry", default=DEFAULT_ROOT)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        result, issues = assemble(args.graph_dir, args.registry, args.out)
    except ValueError as exc:
        print(f"ERROR  {exc}")
        return 1
    for level, message in issues:
        print(f"{level:<6} {message}")
    if result is None:
        return 1
    print(f"OK     assembled {result['sections']} section(s) -> "
          f"{os.path.join(args.out, 'index.html')} + map.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify pass** — 53 tests (48 + 5). Also smoke the CLI on the real Phase 3 run:

```bash
python3 scripts/assemble.py output/modular-arithmetic/graph --out /tmp/ma-smoke
python3 - <<'EOF'
t=open('/tmp/ma-smoke/index.html').read(); assert '<section id="modular-arithmetic"' in t and t.count('<svg')>=3
print('explainer ok:', t.count('<svg'), 'svgs')
EOF
rm -rf /tmp/ma-smoke
```

- [ ] **Step 5: Article sentence (map semantics: layered by depth, thumbnails, click-through) + log; commit:**

```bash
git add scripts/ knowledge/
git commit -m "feat(assemble): concept map with thumbnails + CLI"
```

---

## Task 4: compose-from-children mode in the illustrator contract

**Model: sonnet.** **Files:** Modify `.claude/skills/concept-illustrator/SKILL.md`; Modify `.claude/skills/concept-illustrator/scripts/tests/test_render.py`; Modify `knowledge/concepts/dummies-notes/illustration-engine.md` + `knowledge/log.md` (SKILL.md mapped).

- [ ] **Step 1: Extend the contract test** — in `test_render.py`, `class TestSkillRefs`, add a method:

```python
    def test_skill_md_documents_composition_mode(self):
        with open(os.path.join(os.path.dirname(SCRIPTS_DIR), "SKILL.md"),
                  encoding="utf-8") as fh:
            text = fh.read()
        for token in ("Composition figures", "compose-from-children"):
            self.assertIn(token, text)
```

- [ ] **Step 2: Run to verify it fails.**

- [ ] **Step 3: Add the section to SKILL.md** (place after the output-contract section):

```markdown
## Composition figures (compose-from-children)

Used by the assembly phase for a NON-ATOMIC parent whose children are already
illustrated. Input: the parent concept (slug, name, definition) and its children
(slug, name, definition, why). Output: a normal figure directory — a single
frame, `archetype: "structural"`, `playback: "static"` — showing how the
children snap together into the parent:

- One box per child (compose from `references/visual-vocabulary.md` primitives;
  neutral category ramps — purple/blue/pink per `references/design-system.md`),
  labelled with the child's name and a 2–6 word essence of its `why`.
- The parent is the destination the children converge into (enclosing container
  or convergence point); give it the visual emphasis.
- Do NOT redraw the children's own figures — this is a map of how the parts
  fit, not a re-teaching (reuse = referencing).
- Same contract as every figure: runbook-first, caption + commentary, must
  validate clean via `scripts/render.py`. Closure is inherent — the composition
  IS the end-state picture.
```

- [ ] **Step 4: Run to verify pass** (illustrator suite: 58, 1 skip) and `python3 .claude/skills/concept-illustrator/scripts/check_skill_refs.py; echo $?` → 0.
- [ ] **Step 5: Article sentence in `illustration-engine.md` (compose-from-children mode shipped, used by assembly for the target's composition figure) + log; commit:**

```bash
git add .claude/skills/concept-illustrator/ knowledge/
git commit -m "feat(illustrator): compose-from-children mode for composition figures"
```

---

## Task 5: workflow extension — Assemble + ChainReview phases

**Model: sonnet.** **Files:** Modify `.claude/workflows/dummies-notes.js`; Modify `knowledge/concepts/dummies-notes/orchestration-workflow.md` + `knowledge/log.md` (mapped).

- [ ] **Step 1: Update `meta.phases`** — append two entries after `{ title: 'Finalize', ... }`:

```javascript
    { title: 'Assemble', detail: 'compose root figure if needed; render index.html + map.html' },
    { title: 'ChainReview', detail: 'fresh-eyes pass over the assembled explainer' },
```

Also update `meta.whenToUse` to drop "assembly is Phase 4" (now built in).

- [ ] **Step 2: Append the two phases** at the END of the script — replace the existing final `return {...}` block with:

```javascript
// ---- Phase 5: assemble the deliverable ---------------------------------------
phase('Assemble')

const ASSEMBLE_SCHEMA = {
  type: 'object',
  properties: {
    index_html: { type: 'string' },
    map_html: { type: 'string' },
    sections: { type: 'number' },
    assemble_clean: { type: 'boolean' },
  },
  required: ['index_html', 'map_html', 'sections', 'assemble_clean'],
}

const rootNode = nodes[rootSlug]
if (rootNode && rootNode.atomic === false) {
  const kids = rootNode.prerequisites.map(s => ({
    slug: s,
    name: (nodes[s] && nodes[s].name) || s,
    definition: (nodes[s] && nodes[s].definition) || '',
  }))
  await agent(
    'Follow .claude/skills/concept-illustrator/SKILL.md — the "Composition figures (compose-from-children)" mode.\n' +
    `Parent concept: ${rootSlug} (${rootNode.name}) — ${rootNode.definition}\n` +
    `Children: ${JSON.stringify(kids)}\n` +
    `Write a single-frame structural composition figure to registry/${rootSlug}/figure (runbook-first; caption + commentary required).\n` +
    `It must validate clean: python3 .claude/skills/concept-illustrator/scripts/render.py registry/${rootSlug}/figure\n` +
    `Then attach it: scripts/concept-registry attach-figure ${rootSlug} registry/${rootSlug}/figure\n` +
    'Return figure_dir, lint_clean, frames.',
    { label: `compose:${rootSlug}`, phase: 'Assemble', schema: FIGURE_SCHEMA })
}

const assembled = await agent(
  `Run from the repo root: python3 scripts/assemble.py output/${rootSlug}/graph --out output/${rootSlug}\n` +
  'It must exit 0 (prints "OK assembled N section(s) ..."). Return index_html and map_html as the generated file paths, ' +
  'sections = N from the OK line, assemble_clean = (exit code was 0).',
  { label: 'assemble', phase: 'Assemble', schema: ASSEMBLE_SCHEMA })
if (!assembled || !assembled.assemble_clean) throw new Error('assembly failed')

// ---- Phase 6: end-to-end chain review (fresh eyes over the whole artifact) ----
phase('ChainReview')

const chain = await agent(
  `You are the chain reviewer for output/${rootSlug}/index.html. Read it top to bottom ` +
  `as a learner would (it is ordered bottom-up: prerequisites first, the target last), ` +
  `plus the graph files in output/${rootSlug}/graph/.\n` +
  'Report graph-level gaps that per-figure reviews cannot see:\n' +
  '1. Leaps: a section assumes an idea no earlier section taught or linked.\n' +
  '2. Unmet prerequisites: a concept referenced but never illustrated, linked, or honestly stubbed.\n' +
  '3. Broken arc: the chain never actually builds up to the target concept.\n' +
  `Write your verdict to output/${rootSlug}/chain-review.json as {"pass": <bool>, "summary": "<str>", "gaps": ["..."]} and return the same verdict. ` +
  'pass = a curious adult could read this start to finish and understand the target.',
  { label: 'chain-review', phase: 'ChainReview', schema: VERDICT_SCHEMA })
if (chain && !chain.pass) log(`chain review found ${chain.gaps.length} gap(s) — see output/${rootSlug}/chain-review.json`)

return {
  root: rootSlug,
  graph_dir: `output/${rootSlug}/graph`,
  nodes: Object.keys(nodes).length,
  illustrated: figures.filter(f => f.pass).map(f => f.slug),
  flagged,
  frontier,
  collisions: (report && report.collisions) || [],
  graph_check_clean: !!(report && report.graph_check_clean),
  index_html: assembled.index_html,
  map_html: assembled.map_html,
  chain_review_pass: !!(chain && chain.pass),
  chain_gaps: (chain && chain.gaps) || [],
}
```

- [ ] **Step 3: Verify** — `node --check .claude/workflows/dummies-notes.js` → ok; token sanity (`Assemble`, `ChainReview`, `chain-review.json`, `compose-from-children` present; braces/parens balanced).
- [ ] **Step 4: Article — update the Run shape (add steps 6–7: assemble via assemble.py; chain review writes chain-review.json; gaps surface as a report, no auto-repair) + log; commit:**

```bash
git add .claude/workflows/ knowledge/
git commit -m "feat(workflow): Assemble + ChainReview phases — the full pipeline"
```

---

## Task 6: Acceptance — assemble modular-arithmetic, then the full RSA run (CONTROLLER)

**Controller-run.** Part (a) is deterministic (no agents); part (b) invokes the Workflow tool (multi-node run, ~15–25 subagents — consented at handoff).

- [ ] **Step (a): assemble the existing modular-arithmetic run and verify:**

```bash
python3 scripts/assemble.py output/modular-arithmetic/graph --out output/modular-arithmetic
python3 - <<'EOF'
t = open('output/modular-arithmetic/index.html').read()
assert '<section id="modular-arithmetic"' in t and t.count('<svg') >= 3
m = open('output/modular-arithmetic/map.html').read()
assert 'data-node="modular-arithmetic"' in m
print('modular-arithmetic deliverable ok')
EOF
```

Commit: `git add output/ && git commit -m "feat(assemble): modular-arithmetic deliverable (index.html + map.html)"` (output/ isn't drift-mapped... registry untouched here).

- [ ] **Step (b): the full run** — controller invokes `Workflow {scriptPath: ".claude/workflows/dummies-notes.js", args: {topic: "RSA encryption"}}`. Expected: root `rsa-encryption` (non-atomic) → prerequisites incl. `modular-arithmetic` (illustrated → **link & stop**, exercising covered semantics) + `prime-numbers` + `asymmetric-cryptography` (decomposed/illustrated; their prereqs hit the depth cap → frontier); composition figure for the root; assembly + chain review. Verify after:

```bash
python3 scripts/graph_check.py output/rsa-encryption/graph --require-illustrated
python3 .claude/skills/concept-illustrator/scripts/render.py registry/rsa-encryption/figure
python3 - <<'EOF'
import json
e = json.load(open('registry/rsa-encryption/entry.json'))
assert e['status'] == 'illustrated' and e['prerequisites'], 'edges must persist'
c = json.load(open('output/rsa-encryption/chain-review.json'))
print('rsa edges:', e['prerequisites'], '| chain pass:', c['pass'])
EOF
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 scripts/validate-articles
```

Verify the explainer: covered modular-arithmetic section LINKS (not re-inlines); root section embeds the composition figure + child links; frontier section lists capped prereqs. Update `atomic-illustration-catalog.md` (new entries incl. edges persisted — first real non-empty `prerequisites`) + `orchestration-workflow.md` (first full run record) + log, then commit everything (`output/ registry/ knowledge/`). If the run returns flagged figures or `chain_review_pass: false`, READ the artifacts, diagnose, and fix-and-rerun or document the gap honestly — do NOT paper over.

---

## Task 7: Finalize the knowledge base — all phases shipped

**Model: sonnet.** **Files:** Modify `knowledge/concepts/dummies-notes/orchestration-workflow.md`, `knowledge/index.md`, `knowledge/log.md`, `CLAUDE.md`.

- [ ] **Step 1:** `orchestration-workflow.md`: full pipeline description (7 steps incl. Assemble + ChainReview), both run records, remaining open question (figure invalidation/versioning) — keep `status: mature`.
- [ ] **Step 2:** `CLAUDE.md` Current state: **all four phases shipped — the system is complete**: skills (illustrator, decompose), registry, workflow (full pipeline to `output/<topic>/index.html` + `map.html`), assembler + graph_check commands listed. Remove "Phase 4 ... not yet built".
- [ ] **Step 3:** index rows + a Phase 4 compile log entry.
- [ ] **Step 4:** `python3 scripts/validate-articles`; commit `docs: Phase 4 shipped — the dummies-notes system is complete`.

---

## Definition of done (Phase 4)

- `scripts/assemble.py`: ~18 tests green (53 in the scripts suite); deterministic explainer (bottom-up, inline slideshows, covered-linked, intermediate caption-only, frontier stubs) + map (layers, thumbnails, edges, click-through) + CLI.
- Illustrator SKILL.md documents compose-from-children; workflow runs Assemble + ChainReview.
- `output/modular-arithmetic/` and `output/rsa-encryption/` deliverables exist and verify; RSA registry entry is `illustrated` with non-empty `prerequisites` (edges persisted); `chain-review.json` present.
- All suites green; articles valid + mature; CLAUDE.md declares the system complete.
