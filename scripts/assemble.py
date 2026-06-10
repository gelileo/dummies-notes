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


def build_map(order, nodes, covered, frontier, registry_root, root):
    return "<!doctype html><title>map stub (replaced in Task 3)</title>"
