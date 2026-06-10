#!/usr/bin/env python3
"""Zero-dependency concept registry — the reference graph for dummies_notes.

A concept is *covered* once it has a registry entry; the decomposition
workflow links to covered concepts instead of re-explaining them
(reuse = referencing). Entries live at registry/<slug>/entry.json;
registry/index.json is a rebuildable summary. Entries point at figure
directories — they never copy figure assets.

Identity is canonical slug + one-line definition: registering the same
slug with the same definition is an idempotent no-op; the same slug with
a different definition is an error — the caller must disambiguate with a
qualified slug (e.g. mean-average vs mean-unkind)."""

import argparse
import json
import os
import re
import sys

# Keep in sync with the identical SLUG_RE in .claude/skills/concept-decompose/scripts/validate_decomposition.py
# (duplicated on purpose: both tools stay zero-dependency and self-contained).
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.join(os.path.dirname(_HERE), "registry")


class RegistryError(ValueError):
    """Caller error: bad slug, blank fields, or a definition collision."""


def _entry_path(root, slug):
    return os.path.join(root, slug, "entry.json")


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"corrupt registry entry at {path}: {exc}")


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def lookup(root, slug):
    """Return the entry dict for slug, or None if the concept isn't covered."""
    path = _entry_path(root, slug)
    return _read_json(path) if os.path.exists(path) else None


def register(root, slug, name, definition, prerequisites=()):
    """Create (or idempotently confirm) a registry entry."""
    if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
        raise RegistryError(f"invalid slug '{slug}' (kebab-case required)")
    if not (name or "").strip() or not (definition or "").strip():
        raise RegistryError("name and definition must be non-empty")
    existing = lookup(root, slug)
    if existing is not None:
        if existing["definition"].strip() == definition.strip():
            return existing
        raise RegistryError(
            f"slug collision: '{slug}' is already covered with a different "
            "definition; register under a qualified slug instead "
            "(e.g. mean-average vs mean-unkind)")
    entry = {
        "slug": slug,
        "name": name.strip(),
        "definition": definition.strip(),
        "status": "registered",
        "prerequisites": list(prerequisites),
        "figure": None,
    }
    _write_json(_entry_path(root, slug), entry)
    return entry


def attach_figure(root, slug, figure_dir):
    """Point an entry at its figure directory and mark it illustrated.

    Stores a path relative to the registry root — the registry references
    figures, it never copies them."""
    entry = lookup(root, slug)
    if entry is None:
        raise RegistryError(f"unknown slug '{slug}' (register it first)")
    if not os.path.exists(os.path.join(figure_dir, "figure.json")):
        raise RegistryError(f"no figure.json in {figure_dir}")
    entry["figure"] = os.path.relpath(figure_dir, root)
    entry["status"] = "illustrated"
    _write_json(_entry_path(root, slug), entry)
    return entry


def build_index(root):
    """Rebuild registry/index.json (slug → name/status/definition)."""
    index = {}
    if os.path.isdir(root):
        for slug in sorted(os.listdir(root)):
            path = _entry_path(root, slug)
            if os.path.exists(path):
                entry = _read_json(path)
                try:
                    index[slug] = {"name": entry["name"],
                                   "status": entry["status"],
                                   "definition": entry["definition"]}
                except (KeyError, TypeError) as exc:
                    raise RegistryError(
                        f"malformed entry for '{slug}' (missing {exc})")
    _write_json(os.path.join(root, "index.json"), index)
    return index


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="concept-registry",
        description="slug-based reference graph of covered concepts")
    parser.add_argument("--root", default=DEFAULT_ROOT,
                        help=f"registry directory (default: {DEFAULT_ROOT})")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_reg = sub.add_parser("register", help="add a concept (idempotent)")
    p_reg.add_argument("--slug", required=True)
    p_reg.add_argument("--name", required=True)
    p_reg.add_argument("--definition", required=True)
    p_reg.add_argument("--prereqs", default="", help="comma-separated slugs")
    p_look = sub.add_parser("lookup", help="print an entry; exit 1 if not covered")
    p_look.add_argument("slug")
    p_att = sub.add_parser("attach-figure", help="link a figure dir; mark illustrated")
    p_att.add_argument("slug")
    p_att.add_argument("figure_dir")
    sub.add_parser("index", help="rebuild registry/index.json")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "register":
            prereqs = [s.strip() for s in args.prereqs.split(",") if s.strip()]
            entry = register(args.root, args.slug, args.name,
                             args.definition, prereqs)
            print(json.dumps(entry, indent=2))
        elif args.cmd == "lookup":
            entry = lookup(args.root, args.slug)
            if entry is None:
                print(f"not covered: {args.slug}")
                return 1
            print(json.dumps(entry, indent=2))
        elif args.cmd == "attach-figure":
            print(json.dumps(attach_figure(args.root, args.slug,
                                           args.figure_dir), indent=2))
        elif args.cmd == "index":
            index = build_index(args.root)
            print(f"indexed {len(index)} concept(s) -> "
                  f"{os.path.join(args.root, 'index.json')}")
    except RegistryError as exc:
        print(f"ERROR  {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
