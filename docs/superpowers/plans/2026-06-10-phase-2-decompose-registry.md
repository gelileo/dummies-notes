# Phase 2 — concept-decompose + concept-registry — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the single-level decomposition primitive (`concept-decompose` skill: one concept → slug, plain definition, atomicity verdict, prerequisites) and the reference graph (`concept-registry` script: "covered already? → link and stop recursing"), each independently testable, so Phase 3's Workflow can wire the recursion.

**Architecture:** Two new units. (1) `scripts/concept_registry.py` — a zero-dependency, importable module + thin `scripts/concept-registry` CLI wrapper (mirroring the drift-check pattern) storing one entry per concept at `registry/<slug>/entry.json` with a rebuildable `registry/index.json`; reuse = referencing, so entries *point* at figure directories, never copy them. (2) `.claude/skills/concept-decompose/` — a skill whose contract is SKILL.md + a machine-checkable `decomposition.json` output schema enforced by a zero-dep validator (the same SKILL+validator pattern as concept-illustrator). Golden examples exercise both atomicity branches, and the registry is seeded with the existing quicksort figure as its first illustrated entry.

**Tech Stack:** Python 3 stdlib + unittest (as Phases 1/1.5). No new dependencies. Spec: `docs/superpowers/specs/2026-06-09-dummies-notes-design.md` (Components, Concept identity, Atomicity, Data model sections).

**Conventions:**
- Test commands (three suites after this phase):
  - illustrator: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
  - registry: `python3 -m unittest discover -s scripts/tests -p 'test_*.py'`
  - decompose: `python3 -m unittest discover -s .claude/skills/concept-decompose/scripts/tests -p 'test_*.py'`
- **Living-doc drift gate.** Task 1 sets the `affects:` globs *narrowly from the start* (Phase 1.5 lesson): `concept-decomposition.md` ← `.claude/skills/concept-decompose/SKILL.md` + `.claude/skills/concept-decompose/scripts/validate_decomposition.py`; `atomic-illustration-catalog.md` ← `scripts/concept_registry.py` + `registry/**`. After Task 1, commits touching those paths MUST update the matching article in the same commit; reference docs, examples, and test files are unmapped. If a commit is unexpectedly blocked, STOP and report — never `--no-verify`.
- Articles keep plain `updated: YYYY-MM-DD` dates (use 2026-06-10).

## Design decisions locked here (from the spec)

- **Registry location:** top-level `registry/` (the spec's directory layout names `registry/<slug>/` and `scripts/concept-registry`).
- **Identity:** canonical kebab slug + one-line definition. Same slug + same definition → idempotent no-op. Same slug + *different* definition → hard error telling the caller to register under a **qualified slug** (e.g. `mean-average` vs `mean-unkind`).
- **Entry states:** `registered` (known concept, no figure yet) → `illustrated` (figure attached). "Covered" = an entry exists; Phase 3 stops recursion on covered slugs and links instead.
- **Audience:** a required `audience` string in `decomposition.json`; default text "a curious adult with no domain background" (single default — selectable audiences are YAGNI until a real need).
- **Atomicity rule (decompose contract):** atomic when (a) one figure of ≤ ~6 frames explains the mechanism without sub-figures AND (b) its remaining prerequisites are common knowledge for the audience. Non-atomic ⇒ at least one prerequisite. Jargon in a definition is a decomposition signal: an unexplained term becomes a prerequisite, never an aside.

## Model policy (controller sets `model` per dispatch)

| Step | Model | Why |
|------|-------|-----|
| `concept-decompose` SKILL.md authoring (Task 5) | **opus** | the contract's judgment rules (atomicity test, jargon rule, plain definitions) are the deliverable |
| Golden decomposition examples (Task 6) | **opus** | writing-quality + judgment exemplar (these are what future decompositions copy) |
| Mechanical implementers (Tasks 1–4, 7, 8) | **sonnet** | exact code/specs |
| Spec-compliance review (every task) | **sonnet** | mechanical compare |
| Code-quality reviews + final whole-phase review | **opus** | proven catch-rate on subtle issues |

## File structure

| File | Responsibility | Task |
|------|----------------|------|
| `knowledge/concepts/dummies-notes/{concept-decomposition,atomic-illustration-catalog}.md` (frontmatter) + `CLAUDE.md` rows | narrow drift mapping for Phase 2 surfaces | 1 |
| `scripts/concept_registry.py` | importable registry module: register / lookup / attach_figure / build_index + CLI `main()` | 2–3 |
| `scripts/concept-registry` | thin executable wrapper | 3 |
| `scripts/tests/test_concept_registry.py` | registry unit tests (tempdir-based) | 2–3 |
| `.claude/skills/concept-decompose/references/decomposition-json.md` | the `decomposition.json` schema reference | 4 |
| `.claude/skills/concept-decompose/scripts/validate_decomposition.py` | zero-dep output validator (the enforceable gate) | 4 |
| `.claude/skills/concept-decompose/scripts/tests/test_validate_decomposition.py` | validator tests | 4 |
| `.claude/skills/concept-decompose/SKILL.md` | the skill contract | 5 |
| `.claude/skills/concept-decompose/examples/{rsa-encryption,modular-arithmetic}/decomposition.json` | golden examples: non-atomic + atomic | 6 |
| `registry/quicksort/entry.json`, `registry/modular-arithmetic/entry.json`, `registry/index.json` | seeded registry (first illustrated entry) | 7 |
| knowledge articles + `index.md` + `log.md` | matured to describe shipped Phase 2 | 1, 8 |

---

## Task 1: Narrow the drift mapping for Phase 2 surfaces

**Model: sonnet.** **Files:** Modify `knowledge/concepts/dummies-notes/concept-decomposition.md`, `knowledge/concepts/dummies-notes/atomic-illustration-catalog.md` (frontmatter), `CLAUDE.md` (mapping rows), `knowledge/log.md`.

- [ ] **Step 1: Set `concept-decomposition.md`'s `affects` globs**

Change its frontmatter `affects:` (currently `- "src/decomposition/**"`) to:

```yaml
affects:
  - ".claude/skills/concept-decompose/SKILL.md"
  - ".claude/skills/concept-decompose/scripts/validate_decomposition.py"
```

Also set `updated: 2026-06-10`. Leave `status: thin` (it matures in Task 8).

- [ ] **Step 2: Set `atomic-illustration-catalog.md`'s `affects` globs**

Change its frontmatter `affects:` (currently `- "src/catalog/**"`) to:

```yaml
affects:
  - "scripts/concept_registry.py"
  - "registry/**"
```

Also set `updated: 2026-06-10`. Leave `status: thin`.

- [ ] **Step 3: Update the CLAUDE.md mapping rows**

In `CLAUDE.md`'s article-mapping table, replace the two rows
`| `.claude/skills/concept-decompose/**` | `concepts/dummies-notes/concept-decomposition.md` |` and
`| `src/catalog/**`, `registry/**` | `concepts/dummies-notes/atomic-illustration-catalog.md` |`
with:

```markdown
| `.claude/skills/concept-decompose/SKILL.md` | `concepts/dummies-notes/concept-decomposition.md` |
| `.claude/skills/concept-decompose/scripts/validate_decomposition.py` | `concepts/dummies-notes/concept-decomposition.md` |
| `scripts/concept_registry.py` | `concepts/dummies-notes/atomic-illustration-catalog.md` |
| `registry/**` | `concepts/dummies-notes/atomic-illustration-catalog.md` |
```

(Keep the two illustration-engine rows unchanged.)

- [ ] **Step 4: Verify**

```bash
python3 scripts/validate-articles
python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'
```
Expected: all 3 articles valid; 57 tests pass / 1 skip (nothing else changed).

- [ ] **Step 5: Commit** (the two articles are themselves in the commit → drift-check satisfied)

Append a `knowledge/log.md` line: `## [2026-06-10] doc | scope Phase 2 drift mapping (decompose skill, registry)`.

```bash
git add knowledge/ CLAUDE.md
git commit -m "docs: scope Phase 2 drift mapping (decompose contract, registry paths)"
```

---

## Task 2: Registry core — `register` + `lookup`

**Model: sonnet.** **Files:** Create `scripts/concept_registry.py`, `scripts/tests/test_concept_registry.py`, `scripts/tests/__init__.py` (empty). Modify `knowledge/concepts/dummies-notes/atomic-illustration-catalog.md` + `knowledge/log.md` (concept_registry.py is mapped after Task 1 → article update in the same commit).

- [ ] **Step 1: Create the test package and write the failing tests**

```bash
mkdir -p scripts/tests
: > scripts/tests/__init__.py
```

Create `scripts/tests/test_concept_registry.py`:

```python
import json
import os
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import concept_registry as reg  # noqa: E402


class TestRegisterLookup(unittest.TestCase):
    def test_register_creates_entry_and_lookup_finds_it(self):
        with tempfile.TemporaryDirectory() as root:
            entry = reg.register(root, "quicksort", "Quicksort",
                                 "A sorting algorithm that partitions around a pivot.")
            self.assertEqual(entry["status"], "registered")
            self.assertIsNone(entry["figure"])
            found = reg.lookup(root, "quicksort")
            self.assertEqual(found, entry)
            on_disk = os.path.join(root, "quicksort", "entry.json")
            self.assertTrue(os.path.exists(on_disk))
            with open(on_disk, encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["slug"], "quicksort")

    def test_lookup_unknown_returns_none(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertIsNone(reg.lookup(root, "nope"))

    def test_register_same_definition_is_idempotent(self):
        with tempfile.TemporaryDirectory() as root:
            a = reg.register(root, "recursion", "Recursion", "A thing defined using itself.")
            b = reg.register(root, "recursion", "Recursion", "A thing defined using itself.")
            self.assertEqual(a, b)

    def test_register_same_slug_different_definition_raises(self):
        with tempfile.TemporaryDirectory() as root:
            reg.register(root, "mean", "Mean", "The average of a set of numbers.")
            with self.assertRaises(reg.RegistryError):
                reg.register(root, "mean", "Mean", "Unkind behaviour.")

    def test_invalid_slug_raises(self):
        with tempfile.TemporaryDirectory() as root:
            for bad in ("Has Space", "CamelCase", "trailing-", "-leading", "под"):
                with self.assertRaises(reg.RegistryError):
                    reg.register(root, bad, "X", "Y.")

    def test_blank_name_or_definition_raises(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(reg.RegistryError):
                reg.register(root, "x", "  ", "def.")
            with self.assertRaises(reg.RegistryError):
                reg.register(root, "x", "X", "")

    def test_register_with_prerequisites(self):
        with tempfile.TemporaryDirectory() as root:
            entry = reg.register(root, "rsa-encryption", "RSA encryption",
                                 "Public-key encryption built on modular arithmetic.",
                                 prerequisites=["modular-arithmetic", "prime-numbers"])
            self.assertEqual(entry["prerequisites"],
                             ["modular-arithmetic", "prime-numbers"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s scripts/tests -p 'test_*.py'`
Expected: FAIL — `ModuleNotFoundError: No module named 'concept_registry'`.

- [ ] **Step 3: Create `scripts/concept_registry.py`**

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s scripts/tests -p 'test_*.py'`
Expected: PASS (7 tests).

- [ ] **Step 5: Update the article + commit**

`scripts/concept_registry.py` is drift-mapped to `atomic-illustration-catalog.md`. In that article, replace the "Storage: … undecided" open question with a sentence: storage is `registry/<slug>/entry.json` + a rebuildable `registry/index.json`, via the zero-dep `scripts/concept_registry.py` (register/lookup; same-slug-same-definition is idempotent, definition collisions demand a qualified slug). Keep `updated: 2026-06-10`. Append a `knowledge/log.md` line.

```bash
git add scripts/ knowledge/
git commit -m "feat(registry): zero-dep concept registry — register + lookup"
```

---

## Task 3: Registry — `attach_figure`, `build_index`, CLI

**Model: sonnet.** **Files:** Modify `scripts/concept_registry.py`, `scripts/tests/test_concept_registry.py`; Create `scripts/concept-registry` (executable wrapper). Modify `knowledge/concepts/dummies-notes/atomic-illustration-catalog.md` + `knowledge/log.md` (mapped path → same-commit article touch).

- [ ] **Step 1: Write the failing tests**

Append to `scripts/tests/test_concept_registry.py` (before `if __name__`):

```python
class TestAttachAndIndex(unittest.TestCase):
    def _figure_dir(self, base):
        fig = os.path.join(base, "fig")
        os.makedirs(fig, exist_ok=True)
        with open(os.path.join(fig, "figure.json"), "w", encoding="utf-8") as fh:
            json.dump({"concept_slug": "quicksort"}, fh)
        return fig

    def test_attach_figure_marks_illustrated(self):
        with tempfile.TemporaryDirectory() as root:
            reg.register(root, "quicksort", "Quicksort", "Partition sort.")
            fig = self._figure_dir(root)
            entry = reg.attach_figure(root, "quicksort", fig)
            self.assertEqual(entry["status"], "illustrated")
            self.assertTrue(entry["figure"])
            self.assertEqual(reg.lookup(root, "quicksort")["status"], "illustrated")

    def test_attach_to_unknown_slug_raises(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(reg.RegistryError):
                reg.attach_figure(root, "ghost", root)

    def test_attach_without_figure_json_raises(self):
        with tempfile.TemporaryDirectory() as root:
            reg.register(root, "x", "X", "def.")
            empty = os.path.join(root, "empty")
            os.makedirs(empty)
            with self.assertRaises(reg.RegistryError):
                reg.attach_figure(root, "x", empty)

    def test_build_index_lists_entries(self):
        with tempfile.TemporaryDirectory() as root:
            reg.register(root, "a-thing", "A thing", "First.")
            reg.register(root, "b-thing", "B thing", "Second.")
            index = reg.build_index(root)
            self.assertEqual(sorted(index), ["a-thing", "b-thing"])
            self.assertEqual(index["a-thing"]["status"], "registered")
            with open(os.path.join(root, "index.json"), encoding="utf-8") as fh:
                self.assertEqual(json.load(fh), index)


class TestCli(unittest.TestCase):
    def test_register_lookup_roundtrip(self):
        with tempfile.TemporaryDirectory() as root:
            rc = reg.main(["--root", root, "register", "--slug", "recursion",
                           "--name", "Recursion",
                           "--definition", "A thing defined using itself."])
            self.assertEqual(rc, 0)
            self.assertEqual(reg.main(["--root", root, "lookup", "recursion"]), 0)

    def test_lookup_missing_exits_1(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(reg.main(["--root", root, "lookup", "ghost"]), 1)

    def test_collision_exits_1(self):
        with tempfile.TemporaryDirectory() as root:
            reg.main(["--root", root, "register", "--slug", "mean",
                      "--name", "Mean", "--definition", "The average."])
            rc = reg.main(["--root", root, "register", "--slug", "mean",
                           "--name", "Mean", "--definition", "Unkind."])
            self.assertEqual(rc, 1)

    def test_index_command(self):
        with tempfile.TemporaryDirectory() as root:
            reg.main(["--root", root, "register", "--slug", "x",
                      "--name", "X", "--definition", "def."])
            self.assertEqual(reg.main(["--root", root, "index"]), 0)
            self.assertTrue(os.path.exists(os.path.join(root, "index.json")))
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s scripts/tests -p 'test_*.py'`
Expected: FAIL — `attach_figure` not defined.

- [ ] **Step 3: Implement `attach_figure`, `build_index`, and `main`**

Append to `scripts/concept_registry.py`:

```python
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
                index[slug] = {"name": entry["name"],
                               "status": entry["status"],
                               "definition": entry["definition"]}
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
```

- [ ] **Step 4: Create the executable wrapper**

Create `scripts/concept-registry`:

```python
#!/usr/bin/env python3
"""Thin wrapper so the registry runs as `scripts/concept-registry` (the
hyphenated name can't be imported; the module logic lives in
concept_registry.py)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concept_registry import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
```

```bash
chmod +x scripts/concept-registry
```

- [ ] **Step 5: Run to verify pass + CLI smoke test**

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
scripts/concept-registry --root /tmp/reg-smoke register --slug demo --name Demo --definition "A demo." && scripts/concept-registry --root /tmp/reg-smoke lookup demo; echo "exit: $?"; rm -rf /tmp/reg-smoke
```
Expected: 15 tests pass; the smoke test prints the entry JSON twice, `exit: 0`.

- [ ] **Step 6: Update the article + commit**

In `atomic-illustration-catalog.md`, extend the storage sentence: entries carry `status` (`registered` → `illustrated`) and a `figure` path relative to the registry root; CLI verbs are `register` / `lookup` / `attach-figure` / `index`. Append a `knowledge/log.md` line.

```bash
git add scripts/ knowledge/
git commit -m "feat(registry): attach-figure, index, CLI wrapper"
```

---

## Task 4: Decomposition schema doc + validator

**Model: sonnet.** **Files:** Create `.claude/skills/concept-decompose/references/decomposition-json.md`, `.claude/skills/concept-decompose/scripts/validate_decomposition.py`, `.claude/skills/concept-decompose/scripts/tests/test_validate_decomposition.py`, `.claude/skills/concept-decompose/scripts/tests/__init__.py` (empty). Modify `knowledge/concepts/dummies-notes/concept-decomposition.md` + `knowledge/log.md` (validate_decomposition.py is mapped → same-commit article touch).

- [ ] **Step 1: Write the schema reference**

Create `.claude/skills/concept-decompose/references/decomposition-json.md`:

```markdown
# decomposition.json

The machine-readable output of one `concept-decompose` run: ONE concept,
one level down. The skill never recurses — recursion belongs to the
dummies-notes Workflow (Phase 3).

## Top-level fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `concept` | object | yes | the concept being decomposed (see Concept object) |
| `audience` | string | yes | who this is for; default: "a curious adult with no domain background" |
| `atomic` | bool | yes | the atomicity verdict (see Atomicity) |
| `atomic_reason` | string | yes | one or two plain sentences justifying the verdict |
| `prerequisites` | array | yes | direct prerequisites, one level only; `[]` when atomic |

## Concept object (used for `concept` and each prerequisite)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `slug` | string | yes | canonical kebab-case identity (registry key) |
| `name` | string | yes | human-readable name |
| `definition` | string | yes | one or two plain sentences; no unexplained jargon |
| `why` | string | prerequisites only | why the parent can't be understood without it |

## Atomicity

A concept is **atomic** when (a) one figure of ≤ ~6 frames explains its
mechanism without needing a sub-figure, and (b) its remaining
prerequisites are common knowledge for the audience. Non-atomic ⇒ at
least one prerequisite. **Jargon is a decomposition signal:** a term the
audience wouldn't know must become a prerequisite, never an aside.

## Slug rules

Kebab-case (`^[a-z0-9]+(-[a-z0-9]+)*$`). On a meaning collision, qualify
the slug (`mean-average` vs `mean-unkind`) — definitions disambiguate.

## Example

​```json
{
  "concept": {
    "slug": "rsa-encryption",
    "name": "RSA encryption",
    "definition": "A way to send secret messages using two keys: a public one anyone can use to lock, and a private one only the owner can use to unlock."
  },
  "audience": "a curious adult with no domain background",
  "atomic": false,
  "atomic_reason": "Understanding RSA needs ideas that each deserve their own picture, like clock-style arithmetic and the two-key idea.",
  "prerequisites": [
    {
      "slug": "modular-arithmetic",
      "name": "Modular arithmetic",
      "definition": "Arithmetic that wraps around at a fixed number, like clock hands wrapping past 12.",
      "why": "RSA's locking and unlocking are both wrap-around calculations."
    }
  ]
}
​```
```

(When writing the actual file, the inner fence is a plain ```json block — no zero-width characters.)

- [ ] **Step 2: Write the failing validator tests**

```bash
mkdir -p .claude/skills/concept-decompose/scripts/tests
: > .claude/skills/concept-decompose/scripts/tests/__init__.py
```

Create `.claude/skills/concept-decompose/scripts/tests/test_validate_decomposition.py`:

```python
import os
import sys
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import validate_decomposition as vd  # noqa: E402


def good():
    return {
        "concept": {"slug": "rsa-encryption", "name": "RSA encryption",
                    "definition": "Two-key secret messaging."},
        "audience": "a curious adult with no domain background",
        "atomic": False,
        "atomic_reason": "Needs clock arithmetic and the two-key idea first.",
        "prerequisites": [
            {"slug": "modular-arithmetic", "name": "Modular arithmetic",
             "definition": "Arithmetic that wraps around, like a clock.",
             "why": "RSA's math is wrap-around math."}
        ],
    }


def errors(data):
    return [m for lvl, m in vd.validate(data) if lvl == "ERROR"]


class TestValidate(unittest.TestCase):
    def test_good_decomposition_is_clean(self):
        self.assertEqual(errors(good()), [])

    def test_missing_concept_fields(self):
        d = good()
        del d["concept"]["definition"]
        self.assertTrue(any("definition" in m for m in errors(d)))

    def test_bad_slug(self):
        d = good()
        d["concept"]["slug"] = "Not A Slug"
        self.assertTrue(any("kebab" in m for m in errors(d)))

    def test_atomic_must_be_bool(self):
        d = good()
        d["atomic"] = "false"
        self.assertTrue(any("atomic" in m for m in errors(d)))

    def test_non_atomic_needs_prerequisites(self):
        d = good()
        d["prerequisites"] = []
        self.assertTrue(any("at least one prerequisite" in m for m in errors(d)))

    def test_atomic_with_empty_prereqs_is_clean(self):
        d = good()
        d["atomic"] = True
        d["atomic_reason"] = "One short clock-face figure explains it."
        d["prerequisites"] = []
        self.assertEqual(errors(d), [])

    def test_prerequisite_missing_why(self):
        d = good()
        del d["prerequisites"][0]["why"]
        self.assertTrue(any("why" in m for m in errors(d)))

    def test_duplicate_prerequisite_slugs(self):
        d = good()
        d["prerequisites"].append(dict(d["prerequisites"][0]))
        self.assertTrue(any("duplicate" in m for m in errors(d)))

    def test_self_prerequisite(self):
        d = good()
        d["prerequisites"][0]["slug"] = "rsa-encryption"
        self.assertTrue(any("own prerequisite" in m for m in errors(d)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run to verify failure**

Run: `python3 -m unittest discover -s .claude/skills/concept-decompose/scripts/tests -p 'test_*.py'`
Expected: FAIL — `ModuleNotFoundError: No module named 'validate_decomposition'`.

- [ ] **Step 4: Create the validator**

Create `.claude/skills/concept-decompose/scripts/validate_decomposition.py`:

```python
#!/usr/bin/env python3
"""Validate a decomposition.json produced by the concept-decompose skill.

Importable: validate(data) returns a list of (level, message) tuples
("ERROR" | "WARN"), matching the render.py convention. CLI: exits 1 on
any ERROR."""

import json
import re
import sys

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
```

- [ ] **Step 5: Run to verify pass**

Run: `python3 -m unittest discover -s .claude/skills/concept-decompose/scripts/tests -p 'test_*.py'`
Expected: PASS (9 tests).

- [ ] **Step 6: Update the article + commit**

`validate_decomposition.py` is drift-mapped to `concept-decomposition.md`. In that article, replace the "Atomicity test … needs a concrete, checkable definition" open question with the shipped rule (≤ ~6-frame figure + common-knowledge prerequisites; jargon ⇒ prerequisite; enforced shape via `validate_decomposition.py`). Keep `updated: 2026-06-10`. Append a `knowledge/log.md` line.

```bash
git add .claude/skills/concept-decompose/ knowledge/
git commit -m "feat(decompose): decomposition.json schema + zero-dep validator"
```

---

## Task 5: `concept-decompose` SKILL.md

**Model: opus** (the contract's judgment rules are the deliverable). **Files:** Create `.claude/skills/concept-decompose/SKILL.md`; Create `.claude/skills/concept-decompose/scripts/check_skill_refs.py`; Modify `.claude/skills/concept-decompose/scripts/tests/test_validate_decomposition.py`; Modify `knowledge/concepts/dummies-notes/concept-decomposition.md` + `knowledge/log.md` (SKILL.md is mapped → same-commit article touch).

- [ ] **Step 1: Write `SKILL.md`**

Frontmatter: `name: concept-decompose`; a description that triggers on "what do I need to know first to understand X", "break down this concept", "find the prerequisites of", "is X atomic enough to illustrate". Body must cover, leanly:

- **Job:** ONE concept in → canonical identity + atomicity verdict + direct prerequisites out, as a `decomposition.json` (point to `references/decomposition-json.md`). One level only — never recurse (the Workflow recurses).
- **Workflow:** (1) canonicalize: kebab slug + plain one-or-two-sentence definition for the audience (default "a curious adult with no domain background"); (2) atomicity test: could ONE figure of ≤ ~6 frames make the mechanism click without a sub-figure, AND are the remaining ideas common knowledge for the audience? Record the verdict + a plain `atomic_reason`; (3) if not atomic, list the DIRECT prerequisites (typically 2–4; each slug + name + plain definition + `why` the parent needs it). The jargon rule: any term in your definitions the audience wouldn't know must itself become a prerequisite — never lean on an unexplained word; (4) registry awareness: if the caller supplies already-covered slugs, reuse those exact slugs for matching concepts (link, don't rename); (5) validate: `python3 scripts/validate_decomposition.py path/to/decomposition.json` must print `OK clean`.
- **Quality bar:** definitions a curious adult could repeat back; prerequisites genuinely load-bearing (drop nice-to-knows — simplicity wins); no cycles (a concept never lists itself).
- Reference only paths that exist (`references/decomposition-json.md`, `scripts/validate_decomposition.py`, and `examples/...` only after Task 6 — so do NOT reference examples yet).

- [ ] **Step 2: Add the reference-integrity checker**

Create `.claude/skills/concept-decompose/scripts/check_skill_refs.py` (same pattern as the illustrator's):

```python
#!/usr/bin/env python3
"""Fail if SKILL.md references a path that does not exist in the skill dir."""
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Matches inline single-backtick paths only; keep referenced paths in inline
# code spans (not bare in fenced blocks) so they are checked.
REF = re.compile(r"`((?:references|scripts|examples)/[^`]+)`")


def missing_refs():
    with open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8") as fh:
        text = fh.read()
    return [rel for rel in sorted(set(REF.findall(text)))
            if not os.path.exists(os.path.join(SKILL_DIR, rel))]


if __name__ == "__main__":
    missing = missing_refs()
    for rel in missing:
        print(f"MISSING: {rel}")
    sys.exit(1 if missing else 0)
```

- [ ] **Step 3: Add tests**

Append to `test_validate_decomposition.py` (before `if __name__`):

```python
class TestSkillContract(unittest.TestCase):
    SKILL_DIR = os.path.dirname(SCRIPTS_DIR)

    def test_skill_md_references_exist(self):
        import check_skill_refs
        self.assertEqual(check_skill_refs.missing_refs(), [])

    def test_skill_md_covers_the_contract(self):
        with open(os.path.join(self.SKILL_DIR, "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        for token in ("decomposition.json", "atomic", "jargon",
                      "one level", "kebab"):
            self.assertIn(token, text, f"SKILL.md missing '{token}'")
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s .claude/skills/concept-decompose/scripts/tests -p 'test_*.py'`
Expected: PASS (11 tests). Also run `python3 .claude/skills/concept-decompose/scripts/check_skill_refs.py; echo "exit: $?"` → exit 0.

- [ ] **Step 5: Update the article + commit**

In `concept-decomposition.md`, note the skill now exists at `.claude/skills/concept-decompose/` (single-level contract; Workflow recursion is Phase 3). Append a `knowledge/log.md` line.

```bash
git add .claude/skills/concept-decompose/ knowledge/
git commit -m "feat(decompose): SKILL.md contract + reference-integrity check"
```

---

## Task 6: Golden decomposition examples (both atomicity branches)

**Model: opus** (judgment exemplar — future decompositions copy these). **Files:** Create `.claude/skills/concept-decompose/examples/rsa-encryption/decomposition.json`, `.claude/skills/concept-decompose/examples/modular-arithmetic/decomposition.json`; Modify `.claude/skills/concept-decompose/scripts/tests/test_validate_decomposition.py`; Modify `.claude/skills/concept-decompose/SKILL.md` (add an `examples/` pointer now that it exists).

- [ ] **Step 1: Author `examples/rsa-encryption/decomposition.json` (non-atomic)**

Following SKILL.md: concept `rsa-encryption`, plain two-key definition; `atomic: false` with a plain reason; 2–4 prerequisites (e.g. `modular-arithmetic`, `prime-numbers`, `asymmetric-cryptography` — each with slug/name/plain definition/why). Definitions must obey the jargon rule (no unexplained terms). Must validate clean.

- [ ] **Step 2: Author `examples/modular-arithmetic/decomposition.json` (atomic)**

Concept `modular-arithmetic` (the clock metaphor), `atomic: true` with a reason referencing the one-figure test (a clock-face figure of a few frames explains wrap-around), `prerequisites: []`. The slug MUST match the one used in the rsa example (identity consistency). Must validate clean.

- [ ] **Step 3: Validate both**

```bash
python3 .claude/skills/concept-decompose/scripts/validate_decomposition.py .claude/skills/concept-decompose/examples/rsa-encryption/decomposition.json
python3 .claude/skills/concept-decompose/scripts/validate_decomposition.py .claude/skills/concept-decompose/examples/modular-arithmetic/decomposition.json
```
Expected: both print `OK     clean`, exit 0.

- [ ] **Step 4: Pin them with a test**

Append to `test_validate_decomposition.py` (before `if __name__`):

```python
class TestGoldenDecompositions(unittest.TestCase):
    EXAMPLES = os.path.join(os.path.dirname(SCRIPTS_DIR), "examples")

    def _load(self, slug):
        import json
        path = os.path.join(self.EXAMPLES, slug, "decomposition.json")
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def test_rsa_is_valid_and_non_atomic(self):
        data = self._load("rsa-encryption")
        self.assertEqual([m for lvl, m in vd.validate(data) if lvl == "ERROR"], [])
        self.assertFalse(data["atomic"])
        self.assertGreaterEqual(len(data["prerequisites"]), 2)

    def test_modular_arithmetic_is_valid_and_atomic(self):
        data = self._load("modular-arithmetic")
        self.assertEqual([m for lvl, m in vd.validate(data) if lvl == "ERROR"], [])
        self.assertTrue(data["atomic"])
        self.assertEqual(data["prerequisites"], [])

    def test_identity_is_consistent_across_examples(self):
        rsa = self._load("rsa-encryption")
        mod = self._load("modular-arithmetic")
        rsa_slugs = {p["slug"] for p in rsa["prerequisites"]}
        self.assertIn(mod["concept"]["slug"], rsa_slugs)
```

- [ ] **Step 5: Update SKILL.md's example pointer; run everything**

Add a one-line pointer in SKILL.md to `examples/rsa-encryption/decomposition.json` and `examples/modular-arithmetic/decomposition.json` (they now exist, so `check_skill_refs` stays green).

```bash
python3 -m unittest discover -s .claude/skills/concept-decompose/scripts/tests -p 'test_*.py'
python3 .claude/skills/concept-decompose/scripts/check_skill_refs.py; echo "exit: $?"
```
Expected: 14 tests pass; exit 0.

- [ ] **Step 6: Commit** (examples + tests + SKILL.md → SKILL.md is mapped, so touch the article: add one sentence that golden examples cover both atomicity branches; append a `knowledge/log.md` line)

```bash
git add .claude/skills/concept-decompose/ knowledge/
git commit -m "feat(decompose): golden decompositions — rsa (non-atomic) + modular-arithmetic (atomic)"
```

---

## Task 7: Seed the registry (first real entries)

**Model: sonnet.** **Files:** Create `registry/quicksort/entry.json`, `registry/modular-arithmetic/entry.json`, `registry/index.json` (all generated via the CLI, then committed); Modify `scripts/tests/test_concept_registry.py`; Modify `knowledge/concepts/dummies-notes/atomic-illustration-catalog.md` + `knowledge/log.md` (`registry/**` is mapped → same-commit article touch).

- [ ] **Step 1: Seed via the CLI (not hand-written JSON)**

```bash
scripts/concept-registry register --slug quicksort --name "Quicksort" \
  --definition "A sorting algorithm that repeatedly partitions an array around a pivot until every piece is sorted."
scripts/concept-registry attach-figure quicksort .claude/skills/concept-illustrator/examples/quicksort
scripts/concept-registry register --slug modular-arithmetic --name "Modular arithmetic" \
  --definition "Arithmetic that wraps around at a fixed number, like clock hands wrapping past 12."
scripts/concept-registry index
scripts/concept-registry lookup quicksort
```
Expected: quicksort ends `"status": "illustrated"` with a `figure` path pointing (relative) at the illustrator example; modular-arithmetic is `registered`; `index` reports 2 concepts.

NOTE: the modular-arithmetic definition MUST be exactly the same text used in Task 6's examples (identity = slug + definition; keep them in sync — copy from the example file).

- [ ] **Step 2: Pin the committed registry with a test**

Append to `scripts/tests/test_concept_registry.py` (before `if __name__`):

```python
class TestSeededRegistry(unittest.TestCase):
    ROOT = os.path.join(SCRIPTS_DIR, os.pardir, "registry")

    def test_quicksort_is_illustrated_and_figure_exists(self):
        entry = reg.lookup(self.ROOT, "quicksort")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["status"], "illustrated")
        figure_dir = os.path.normpath(os.path.join(self.ROOT, entry["figure"]))
        self.assertTrue(os.path.exists(os.path.join(figure_dir, "figure.json")))

    def test_modular_arithmetic_is_registered(self):
        entry = reg.lookup(self.ROOT, "modular-arithmetic")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["status"], "registered")

    def test_index_matches_entries(self):
        index = reg.build_index(self.ROOT)
        self.assertIn("quicksort", index)
        self.assertIn("modular-arithmetic", index)
```

(Note: `test_index_matches_entries` rebuilds `index.json`; run `git status` after tests and commit the rebuilt file if it changed — it should be byte-identical.)

- [ ] **Step 3: Run all three suites**

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 -m unittest discover -s .claude/skills/concept-decompose/scripts/tests -p 'test_*.py'
python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'
```
Expected: 18 / 14 / 57(1 skip) — all green.

- [ ] **Step 4: Update the article + commit**

In `atomic-illustration-catalog.md`: the registry is live with its first entries (quicksort illustrated → pointing at the Phase 1 figure; modular-arithmetic registered, awaiting its figure). Set `status: mature` if the article now accurately describes the shipped registry. Append a `knowledge/log.md` line.

```bash
git add registry/ scripts/tests/ knowledge/
git commit -m "feat(registry): seed first entries — quicksort (illustrated) + modular-arithmetic"
```

---

## Task 8: Finalize the knowledge base

**Model: sonnet.** **Files:** Modify `knowledge/concepts/dummies-notes/concept-decomposition.md`, `knowledge/concepts/dummies-notes/atomic-illustration-catalog.md`, `knowledge/index.md`, `knowledge/log.md`.

- [ ] **Step 1: Mature `concept-decomposition.md`**

The article should now describe the SHIPPED single-level primitive: the skill location, the `decomposition.json` contract (concept/audience/atomic/atomic_reason/prerequisites + the `why` field), the atomicity rule, the jargon rule, slug identity + qualified-slug collisions, the validator gate, golden examples — and state plainly that recursion/graph assembly is Phase 3 (Workflow). Resolve remaining open questions that Phase 2 answered (identity ✓, atomicity ✓; cycle detection stays open for Phase 3 — say so). Set `status: mature`, `updated: 2026-06-10`. Keep the `[[illustration-engine]]` / `[[atomic-illustration-catalog]]` links.

- [ ] **Step 2: Mature `atomic-illustration-catalog.md`**

Confirm it describes the shipped registry (storage layout, entry states, CLI verbs, reference-not-copy, collision policy) with `status: mature`, `updated: 2026-06-10`; resolve its open questions (addressing ✓ slug+definition; portability ✓ entries point at self-contained figure dirs; versioning/invalidation → still open, note it for Phase 3+).

- [ ] **Step 3: Refresh `knowledge/index.md` rows** for both articles (one-liners reflecting shipped state + 2026-06-10 dates).

- [ ] **Step 4: Validate, test, commit**

```bash
python3 scripts/validate-articles
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
git add knowledge/
git commit -m "docs: mature concept-decomposition + atomic-illustration-catalog for Phase 2"
```

(If earlier tasks already matured everything, verify and skip the commit — don't invent a no-op.)

---

## Definition of done (Phase 2)

- `scripts/concept_registry.py` + `scripts/concept-registry`: register / lookup / attach-figure / index, zero-dep, 18 tests green; collision policy enforced (qualified slugs).
- `.claude/skills/concept-decompose/`: SKILL.md contract (single-level, atomicity rule, jargon rule), `decomposition-json.md` schema, validator (14 tests green), golden examples covering both atomicity branches, `check_skill_refs.py` exit 0.
- `registry/` seeded: quicksort `illustrated` (pointing at the Phase 1 figure), modular-arithmetic `registered`; committed and pinned by tests.
- All three suites green; `validate-articles` valid; both Phase 2 articles `mature` and truthful; drift mapping narrow and accurate.
