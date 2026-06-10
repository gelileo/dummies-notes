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

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.join(os.path.dirname(_HERE), "registry")


class RegistryError(ValueError):
    """Caller error: bad slug, blank fields, or a definition collision."""


def _entry_path(root, slug):
    return os.path.join(root, slug, "entry.json")


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


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
