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
