#!/usr/bin/env python3
"""Fail if SKILL.md references a path that does not exist in the skill dir."""
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Matches inline single-backtick paths only; keep referenced paths in inline code spans (not bare in fenced blocks) so they are checked.
REF = re.compile(r"`((?:assets|references|scripts|examples)/[^`]+)`")


def missing_refs():
    with open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8") as fh:
        text = fh.read()
    out = []
    for rel in sorted(set(REF.findall(text))):
        if not os.path.exists(os.path.join(SKILL_DIR, rel)):
            out.append(rel)
    return out


if __name__ == "__main__":
    missing = missing_refs()
    for m in missing:
        print(f"MISSING: {m}")
    sys.exit(1 if missing else 0)
