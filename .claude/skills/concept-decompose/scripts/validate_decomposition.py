#!/usr/bin/env python3
"""Validate a decomposition.json produced by the concept-decompose skill.

Importable: validate(data) returns a list of (level, message) tuples
("ERROR" | "WARN"), matching the render.py convention. CLI: exits 1 on
any ERROR."""

import json
import re
import sys

# Keep in sync with the identical SLUG_RE in scripts/concept_registry.py
# (duplicated on purpose: both tools stay zero-dependency and self-contained).
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CONCEPT_KEYS = ("slug", "name", "definition")
DEFINITION_WARN_CHARS = 400


def _check_concept(concept, where):
    if not isinstance(concept, dict):
        return [("ERROR", f"{where}: must be an object")]
    issues = []
    for key in CONCEPT_KEYS:
        value = concept.get(key)
        if not isinstance(value, str) or not value.strip():
            issues.append(("ERROR", f"{where}: missing '{key}'"))
    slug = concept.get("slug")
    if isinstance(slug, str) and slug.strip() and not SLUG_RE.fullmatch(slug):
        issues.append(("ERROR", f"{where}: slug '{slug}' is not kebab-case"))
    definition = concept.get("definition")
    if isinstance(definition, str) and len(definition) > DEFINITION_WARN_CHARS:
        issues.append(("WARN", f"{where}: definition over "
                               f"{DEFINITION_WARN_CHARS} chars; keep it short and plain"))
    return issues


def validate(data):
    if not isinstance(data, dict):
        return [("ERROR", "decomposition must be a JSON object")]
    issues = _check_concept(data.get("concept"), "concept")
    audience = data.get("audience")
    if not isinstance(audience, str) or not audience.strip():
        issues.append(("ERROR", "missing 'audience'"))
    if not isinstance(data.get("atomic"), bool):
        issues.append(("ERROR", "'atomic' must be true or false (a JSON bool)"))
    if not isinstance(data.get("mechanism_figurable"), bool):
        issues.append(("ERROR", "'mechanism_figurable' must be true or false (a JSON bool)"))
    reason = data.get("atomic_reason")
    if not isinstance(reason, str) or not reason.strip():
        issues.append(("ERROR", "missing 'atomic_reason'"))
    prereqs = data.get("prerequisites")
    if not isinstance(prereqs, list):
        issues.append(("ERROR", "'prerequisites' must be a list"))
        prereqs = []
    seen = set()
    concept_slug = (data.get("concept") or {}).get("slug") \
        if isinstance(data.get("concept"), dict) else None
    for i, prereq in enumerate(prereqs):
        where = f"prerequisites[{i}]"
        issues += _check_concept(prereq, where)
        if isinstance(prereq, dict):
            why = prereq.get("why")
            if not isinstance(why, str) or not why.strip():
                issues.append(("ERROR", f"{where}: missing 'why'"))
            slug = prereq.get("slug")
            if isinstance(slug, str):
                if slug in seen:
                    issues.append(("ERROR", f"duplicate prerequisite slug '{slug}'"))
                seen.add(slug)
                if slug == concept_slug:
                    issues.append(("ERROR", "concept cannot be its own prerequisite"))
    if data.get("atomic") is False and not prereqs:
        issues.append(("ERROR", "non-atomic concept must list at least one prerequisite"))
    if data.get("atomic") is True and prereqs:
        issues.append(("WARN", "atomic concept lists prerequisites; are they "
                               "really not common knowledge?"))
    return issues


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: validate_decomposition.py <decomposition.json>")
        return 2
    try:
        with open(args[0], encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR  {exc}")
        return 1
    issues = validate(data)
    for level, message in issues:
        print(f"{level:<6} {message}")
    if not issues:
        print("OK     clean")
    return 1 if any(lvl == "ERROR" for lvl, _ in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
