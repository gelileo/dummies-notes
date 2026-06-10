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
