# Phase 1 — concept-illustrator, made real — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the draft `concept-illustrator` skill into a working, self-contained Claude Code skill that renders one concept into a lint-clean, multi-frame SVG figure with a viewable slideshow.

**Architecture:** A skill directory at `.claude/skills/concept-illustrator/` holding `SKILL.md`, authored `assets/` and `references/`, and one dependency-free Python tool `scripts/render.py` that (a) lints a single SVG against the design system, (b) validates a multi-frame figure directory (`figure.json` + frames), (c) generates a self-contained slideshow HTML, and (d) optionally exports PNG. The tool is the enforceable quality gate; the docs/assets are gated by it. Per-figure fresh-eyes review is authored as a documented protocol (its automated loop is Phase 3).

**Tech Stack:** Python 3 standard library only (`xml.etree.ElementTree`, `argparse`, `json`, `re`, `unittest`) — no external dependencies, matching the repo's zero-dep tooling. Optional `rsvg-convert` or `cairosvg` for PNG export (gracefully optional). Vanilla HTML/JS for the viewer. Spec: `docs/superpowers/specs/2026-06-09-dummies-notes-design.md`.

**Conventions:**
- **XML safety:** `render.py` may lint untrusted/LLM-generated SVGs, so it must not be exposed to XXE or billion-laughs. Rather than add `defusedxml` (which breaks the zero-dep design), all parsing goes through `_safe_parse`, which **rejects any file containing `<!DOCTYPE` or `<!ENTITY` before parsing** — legitimate concept-illustrator figures never use either, so this neutralizes both attacks for free.
- Run tests from repo root: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
- `render.py` is both a CLI and an importable module: all checks are functions returning a list of `(level, message)` tuples where `level` is `"ERROR"` or `"WARN"`; `main()` exits non-zero if any `ERROR`.
- Commit messages: this repo has a living-doc pre-commit hook (`drift-check`). During Phase 1 no article's `affects:` glob matches these paths until Task 11, so commits pass cleanly. Task 11 wires the glob and updates the article in the same commit.

---

## File structure

| File | Responsibility |
|------|----------------|
| `.claude/skills/concept-illustrator/scripts/render.py` | Linter + figure validator + viewer generator + PNG export (the quality gate) |
| `.claude/skills/concept-illustrator/scripts/tests/test_render.py` | Unit tests for every check and mode |
| `.claude/skills/concept-illustrator/scripts/tests/fixtures/` | Tiny SVG/figure fixtures used by tests |
| `.claude/skills/concept-illustrator/assets/_style.css` | Source-of-truth embedded stylesheet (palette, classes, dark mode) |
| `.claude/skills/concept-illustrator/assets/template.svg` | Starting SVG: embeds `_style.css` + arrow marker + `cd-svg` wrapper |
| `.claude/skills/concept-illustrator/assets/slideshow.template.html` | Viewer template the generator fills with inlined frames |
| `.claude/skills/concept-illustrator/references/design-system.md` | Full palette/class/type-width reference |
| `.claude/skills/concept-illustrator/references/archetypes.md` | Worked example per archetype incl. the sequence archetype |
| `.claude/skills/concept-illustrator/references/visual-vocabulary.md` | Canonical primitive drawings + reusable snippets |
| `.claude/skills/concept-illustrator/references/voice-and-metaphor.md` | Caption voice rules + metaphor bank |
| `.claude/skills/concept-illustrator/references/review-protocol.md` | Blind-reader + fidelity-critic procedure |
| `.claude/skills/concept-illustrator/references/figure-json.md` | `figure.json` schema reference |
| `.claude/skills/concept-illustrator/SKILL.md` | The real contract: workflow, archetypes, multi-frame I/O, review step |
| `.claude/skills/concept-illustrator/examples/quicksort/` | Golden multi-frame figure produced end-to-end |
| `knowledge/concepts/dummies-notes/illustration-engine.md` | Updated to match the real implementation (Task 11) |

---

## Task 1: Scaffold skill + render.py module skeleton (helpers + palette loader)

**Files:**
- Create: `.claude/skills/concept-illustrator/scripts/render.py`
- Create: `.claude/skills/concept-illustrator/scripts/tests/test_render.py`
- Create: `.claude/skills/concept-illustrator/scripts/tests/__init__.py` (empty)

- [ ] **Step 1: Create the empty test package marker**

```bash
mkdir -p .claude/skills/concept-illustrator/scripts/tests/fixtures
: > .claude/skills/concept-illustrator/scripts/tests/__init__.py
```

- [ ] **Step 2: Write the failing test for `load_palette` and `localname`**

Create `.claude/skills/concept-illustrator/scripts/tests/test_render.py`:

```python
import os
import sys
import unittest
import xml.etree.ElementTree as ET

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import render  # noqa: E402


def svg(body, viewbox="0 0 680 200"):
    return ET.fromstring(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}">{body}</svg>'
    )


class TestHelpers(unittest.TestCase):
    def test_load_palette_extracts_lowercased_hexes(self):
        css = "text.t{fill:#1C1C1A;} .c-teal{stroke:#0F6E56;}"
        self.assertEqual(render.load_palette(css), {"#1c1c1a", "#0f6e56"})

    def test_localname_strips_namespace(self):
        el = svg("<text>hi</text>").find("{http://www.w3.org/2000/svg}text")
        self.assertEqual(render.localname(el.tag), "text")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: FAIL — `ModuleNotFoundError: No module named 'render'` (file does not exist yet).

- [ ] **Step 4: Create `render.py` with the module skeleton**

Create `.claude/skills/concept-illustrator/scripts/render.py`:

```python
#!/usr/bin/env python3
"""Dependency-free SVG linter + figure validator + viewer generator for the
concept-illustrator skill. Importable (functions return (level, message) lists)
and runnable as a CLI."""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

CANVAS_WIDTH = 680
ALLOWED_TEXT_CLASSES = {"t", "ts", "th"}
ALLOWED_NONHEX = {"none", "currentcolor", "inherit", "transparent"}
COLOR_ATTRS = ("fill", "stroke", "stop-color")
PLACEHOLDER_TOKENS = ["{{", "todo", "placeholder", "lorem ipsum", "fixme", "xxx"]
HEX6 = re.compile(r"#[0-9a-f]{6}")
EMOJI = re.compile("[\U0001f000-\U0001faff\U00002600-\U000027bf]")
DTD_PATTERN = re.compile(r"<!(DOCTYPE|ENTITY)", re.IGNORECASE)

DEFAULT_STYLE = os.path.join(os.path.dirname(__file__), "..", "assets", "_style.css")
DEFAULT_TEMPLATE = os.path.join(
    os.path.dirname(__file__), "..", "assets", "slideshow.template.html"
)


def localname(tag):
    return tag.split("}")[-1]


def load_palette(css_text):
    return set(m.group(0).lower() for m in HEX6.finditer(css_text.lower()))


def _f(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _safe_parse(path):
    """Parse an SVG with stdlib ET, but first reject DTD/entity declarations.
    This neutralizes XXE and billion-laughs without an external dependency;
    concept-illustrator figures never use a DOCTYPE or entities. Returns
    (root, issues): root is None when parsing is refused or fails."""
    raw = _read(path)
    if DTD_PATTERN.search(raw):
        return None, [("ERROR", "SVG contains <!DOCTYPE or <!ENTITY (rejected for safety)")]
    try:
        return ET.fromstring(raw), []
    except ET.ParseError as exc:
        return None, [("ERROR", f"malformed SVG: {exc}")]
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/concept-illustrator/scripts/
git commit -m "feat(illustrator): scaffold render.py module + palette/localname helpers"
```

---

## Task 2: Lint group A — canvas width, text classes, placeholders

**Files:**
- Modify: `.claude/skills/concept-illustrator/scripts/render.py`
- Modify: `.claude/skills/concept-illustrator/scripts/tests/test_render.py`

- [ ] **Step 1: Write the failing tests**

Append to `test_render.py` (before the `if __name__` line):

```python
class TestCanvasWidth(unittest.TestCase):
    def test_correct_width_passes(self):
        self.assertEqual(render.check_canvas_width(svg("")), [])

    def test_wrong_width_errors(self):
        out = render.check_canvas_width(svg("", viewbox="0 0 500 200"))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))

    def test_missing_viewbox_errors(self):
        root = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in render.check_canvas_width(root)))


class TestTextClasses(unittest.TestCase):
    def test_classed_text_passes(self):
        self.assertEqual(render.check_text_classes(svg('<text class="t">hi</text>')), [])

    def test_unclassed_text_errors(self):
        self.assertTrue(render.check_text_classes(svg("<text>hi</text>")))

    def test_inline_font_size_errors(self):
        out = render.check_text_classes(svg('<text class="t" font-size="20">hi</text>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))


class TestPlaceholders(unittest.TestCase):
    def test_clean_passes(self):
        self.assertEqual(render.check_placeholders(svg('<text class="t">real</text>')), [])

    def test_token_errors(self):
        self.assertTrue(render.check_placeholders(svg('<text class="t">TODO fix</text>')))
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: FAIL — `AttributeError: module 'render' has no attribute 'check_canvas_width'`.

- [ ] **Step 3: Implement the three checks**

Append to `render.py`:

```python
def check_canvas_width(root):
    vb = root.get("viewBox")
    if not vb:
        return [("ERROR", "missing viewBox")]
    parts = vb.split()
    if len(parts) != 4:
        return [("ERROR", f"malformed viewBox '{vb}'")]
    width = _f(parts[2])
    if width != CANVAS_WIDTH:
        return [("ERROR", f"viewBox width {width} must be {CANVAS_WIDTH}")]
    return []


def check_text_classes(root):
    issues = []
    for el in root.iter():
        if localname(el.tag) != "text":
            continue
        classes = set((el.get("class") or "").split())
        snippet = (el.text or "").strip()[:20]
        if not (classes & ALLOWED_TEXT_CLASSES):
            issues.append(("ERROR", f"<text> '{snippet}' missing class (t/ts/th)"))
        if el.get("font-size") or "font-size" in (el.get("style") or ""):
            issues.append(("ERROR", f"<text> '{snippet}' has inline font-size; use t/ts/th"))
    return issues


def check_placeholders(root):
    blob = " ".join(el.text for el in root.iter() if el.text).lower()
    return [
        ("ERROR", f"placeholder token '{tok}' present")
        for tok in PLACEHOLDER_TOKENS
        if tok in blob
    ]
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: PASS (all tests).

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/concept-illustrator/scripts/
git commit -m "feat(illustrator): lint canvas width, text classes, placeholders"
```

---

## Task 3: Lint group B — palette, decoration, sentence case

**Files:**
- Modify: `.claude/skills/concept-illustrator/scripts/render.py`
- Modify: `.claude/skills/concept-illustrator/scripts/tests/test_render.py`

- [ ] **Step 1: Write the failing tests**

Append to `test_render.py`:

```python
PALETTE = {"#1c1c1a", "#0f6e56"}


class TestPalette(unittest.TestCase):
    def test_palette_color_passes(self):
        out = render.check_palette(svg('<rect fill="#1C1C1A"/>'), PALETTE)
        self.assertEqual(out, [])

    def test_off_palette_errors(self):
        out = render.check_palette(svg('<rect fill="#abcdef"/>'), PALETTE)
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))

    def test_none_and_url_allowed(self):
        out = render.check_palette(
            svg('<path fill="none" marker-end="url(#arrow)" stroke="currentColor"/>'),
            PALETTE,
        )
        self.assertEqual(out, [])

    def test_named_color_errors(self):
        self.assertTrue(render.check_palette(svg('<rect fill="red"/>'), PALETTE))


class TestDecoration(unittest.TestCase):
    def test_filter_errors(self):
        out = render.check_decoration(svg('<filter id="f"></filter>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))

    def test_gradient_warns(self):
        out = render.check_decoration(svg('<linearGradient id="g"></linearGradient>'))
        self.assertTrue(any(lvl == "WARN" for lvl, _ in out))

    def test_emoji_errors(self):
        out = render.check_decoration(svg('<text class="t">hot \U0001f525</text>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))


class TestCaps(unittest.TestCase):
    def test_sentence_case_passes(self):
        self.assertEqual(render.check_caps(svg('<text class="t">Binary search</text>')), [])

    def test_all_caps_errors(self):
        out = render.check_caps(svg('<text class="t">BINARY SEARCH</text>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))

    def test_title_case_warns(self):
        out = render.check_caps(svg('<text class="t">Binary Search Tree</text>'))
        self.assertTrue(any(lvl == "WARN" for lvl, _ in out))
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: FAIL — `check_palette` not defined.

- [ ] **Step 3: Implement the three checks**

Append to `render.py`:

```python
def _check_color_value(value, palette, attr):
    v = value.strip().lower()
    if v in ALLOWED_NONHEX or v.startswith("url("):
        return []
    if not re.fullmatch(r"#[0-9a-f]{6}", v):
        return [("ERROR", f"off-palette {attr} '{value}' (use a hex from the palette)")]
    if v not in palette:
        return [("ERROR", f"off-palette {attr} '{value}'")]
    return []


def check_palette(root, palette):
    issues = []
    for el in root.iter():
        for attr in COLOR_ATTRS:
            if el.get(attr):
                issues += _check_color_value(el.get(attr), palette, attr)
        style = el.get("style") or ""
        for decl in style.split(";"):
            if ":" in decl:
                prop, val = decl.split(":", 1)
                if prop.strip() in COLOR_ATTRS:
                    issues += _check_color_value(val, palette, prop.strip())
    return issues


def check_decoration(root):
    issues = []
    for el in root.iter():
        name = localname(el.tag)
        if name == "filter":
            issues.append(("ERROR", "<filter> not allowed (no shadows/glows)"))
        elif name in ("linearGradient", "radialGradient"):
            issues.append(("WARN", f"<{name}> present; allowed only for a physical "
                                   "property in an illustrative figure"))
        if el.text and EMOJI.search(el.text):
            issues.append(("ERROR", "emoji in text not allowed"))
    return issues


def check_caps(root):
    issues = []
    for el in root.iter():
        if localname(el.tag) != "text" or not el.text:
            continue
        s = el.text.strip()
        letters = [c for c in s if c.isalpha()]
        words = [w for w in s.split() if any(c.isalpha() for c in w)]
        if len(letters) >= 2 and not any(c.islower() for c in s):
            issues.append(("ERROR", f"ALL CAPS text '{s[:20]}'; use sentence case"))
        elif len(words) >= 2 and all(w.lstrip()[0].isupper() for w in words):
            issues.append(("WARN", f"possible Title Case '{s[:20]}'; prefer sentence case"))
    return issues
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/concept-illustrator/scripts/
git commit -m "feat(illustrator): lint palette, decoration, sentence case"
```

---

## Task 4: Lint group C — bounds, connector fill — and the `lint_svg`/`lint_file` aggregators + CLI

**Files:**
- Modify: `.claude/skills/concept-illustrator/scripts/render.py`
- Modify: `.claude/skills/concept-illustrator/scripts/tests/test_render.py`

- [ ] **Step 1: Write the failing tests**

Append to `test_render.py`:

```python
class TestBounds(unittest.TestCase):
    def test_in_bounds_passes(self):
        out = render.check_bounds(svg('<rect x="10" y="10" width="100" height="50"/>'))
        self.assertEqual(out, [])

    def test_overflow_width_errors(self):
        out = render.check_bounds(svg('<rect x="600" y="10" width="200" height="50"/>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))


class TestConnectorFill(unittest.TestCase):
    def test_connector_with_fill_none_passes(self):
        out = render.check_connector_fill(
            svg('<path class="arr" fill="none" marker-end="url(#arrow)"/>')
        )
        self.assertEqual(out, [])

    def test_connector_with_solid_fill_errors(self):
        out = render.check_connector_fill(svg('<path class="arr" fill="#1c1c1a"/>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))


class TestLintSvgAggregate(unittest.TestCase):
    def test_clean_svg_has_no_errors(self):
        root = svg('<text class="t">Binary search</text>')
        errors = [m for lvl, m in render.lint_svg(root, PALETTE) if lvl == "ERROR"]
        self.assertEqual(errors, [])

    def test_dirty_svg_collects_errors(self):
        root = svg('<text>UNCLASSED</text>', viewbox="0 0 500 200")
        errors = [m for lvl, m in render.lint_svg(root, PALETTE) if lvl == "ERROR"]
        self.assertGreaterEqual(len(errors), 2)


class TestSafeParse(unittest.TestCase):
    def test_doctype_is_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "evil.svg")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write('<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY x "x">]>'
                         '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 100"/>')
            out = render.lint_file(path, os.path.join(ASSETS, "_style.css"))
            self.assertTrue(any("DOCTYPE" in m or "ENTITY" in m for _, m in out))
```

Note: `ASSETS` is defined in the Task 5 test additions. If running this test before Task 5, replace `os.path.join(ASSETS, "_style.css")` with `"/nonexistent"` (the safety check fires before the style file is read).

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: FAIL — `check_bounds` not defined.

- [ ] **Step 3: Implement bounds, connector fill, and aggregators**

Append to `render.py`:

```python
def check_bounds(root):
    parts = (root.get("viewBox") or "").split()
    if len(parts) != 4:
        return []
    width, height = _f(parts[2]), _f(parts[3])
    issues = []
    for el in root.iter():
        if localname(el.tag) != "rect":
            continue
        x, y = _f(el.get("x")), _f(el.get("y"))
        w, h = _f(el.get("width")), _f(el.get("height"))
        if x is not None and w is not None and (x < -0.5 or x + w > width + 0.5):
            issues.append(("ERROR", f"rect exceeds canvas width (x={x}, w={w})"))
        if y is not None and h is not None and (y < -0.5 or y + h > height + 0.5):
            issues.append(("ERROR", f"rect exceeds canvas height (y={y}, h={h})"))
    return issues


def check_connector_fill(root):
    issues = []
    for el in root.iter():
        if localname(el.tag) != "path":
            continue
        classes = set((el.get("class") or "").split())
        is_connector = bool(classes & {"arr", "leader"}) or el.get("marker-end")
        fill = (el.get("fill") or "").strip().lower()
        if is_connector and fill and fill != "none":
            issues.append(("ERROR", 'connector <path> must have fill="none"'))
    return issues


def lint_svg(root, palette):
    issues = []
    issues += check_canvas_width(root)
    issues += check_text_classes(root)
    issues += check_placeholders(root)
    issues += check_palette(root, palette)
    issues += check_decoration(root)
    issues += check_caps(root)
    issues += check_bounds(root)
    issues += check_connector_fill(root)
    return issues


def lint_file(svg_path, style_path):
    root, issues = _safe_parse(svg_path)
    if root is None:
        return issues
    palette = load_palette(_read(style_path)) if os.path.exists(style_path) else set()
    return lint_svg(root, palette)
```

(`_read` and `_safe_parse` were defined in the Task 1 skeleton.)

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: PASS.

- [ ] **Step 5: Add the CLI entry point**

Append to `render.py`:

```python
def _print_issues(label, issues):
    errors = [m for lvl, m in issues if lvl == "ERROR"]
    warns = [m for lvl, m in issues if lvl == "WARN"]
    for m in errors:
        print(f"ERROR  {label}: {m}")
    for m in warns:
        print(f"WARN   {label}: {m}")
    if not errors and not warns:
        print(f"OK     {label}: clean")
    return len(errors)


def main(argv=None):
    parser = argparse.ArgumentParser(description="concept-illustrator SVG/figure tool")
    parser.add_argument("path", help="path to a .svg file or a figure directory")
    parser.add_argument("--style", default=DEFAULT_STYLE, help="path to _style.css")
    parser.add_argument("--figure", action="store_true", help="validate a figure dir")
    parser.add_argument("--viewer", metavar="OUT", help="write a slideshow HTML to OUT")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE)
    parser.add_argument("--png", metavar="OUT", help="export PNG to OUT")
    parser.add_argument("--theme", default="light", choices=["light", "dark"])
    parser.add_argument("--scale", type=float, default=2.0)
    args = parser.parse_args(argv)

    if args.viewer:
        build_viewer(args.path, args.template, args.viewer)
        print(f"OK     wrote viewer: {args.viewer}")
        return 0
    if args.png:
        export_png(args.path, args.png, args.theme, args.scale)
        print(f"OK     wrote PNG: {args.png}")
        return 0
    if args.figure or os.path.isdir(args.path):
        errors = _print_issues(args.path, validate_figure(args.path, args.style))
    else:
        errors = _print_issues(args.path, lint_file(args.path, args.style))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
```

Note: `build_viewer`, `validate_figure`, and `export_png` are defined in Tasks 6–8. Until then, running `--viewer`/`--png`/`--figure` raises `NameError`; the default lint path works now.

- [ ] **Step 6: Make executable and smoke-test the lint path on a fixture**

```bash
chmod +x .claude/skills/concept-illustrator/scripts/render.py
printf '%s' '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 100"><text>BAD</text></svg>' \
  > .claude/skills/concept-illustrator/scripts/tests/fixtures/dirty.svg
python3 .claude/skills/concept-illustrator/scripts/render.py \
  .claude/skills/concept-illustrator/scripts/tests/fixtures/dirty.svg; echo "exit: $?"
```
Expected: prints `ERROR` lines for viewBox width and unclassed text; `exit: 1`.

- [ ] **Step 7: Commit**

```bash
git add .claude/skills/concept-illustrator/scripts/
git commit -m "feat(illustrator): bounds/connector checks, lint aggregator, CLI"
```

---

## Task 5: Author `_style.css` + `template.svg`, prove they lint clean

**Files:**
- Create: `.claude/skills/concept-illustrator/assets/_style.css`
- Create: `.claude/skills/concept-illustrator/assets/template.svg`
- Modify: `.claude/skills/concept-illustrator/scripts/tests/test_render.py`

- [ ] **Step 1: Create `_style.css` from the existing example's embedded stylesheet**

The repo already contains a complete, proven stylesheet inside
`example/example-binary-search.svg`. Copy the text **between** `<style>` and
`</style>` in that file verbatim into `.claude/skills/concept-illustrator/assets/_style.css`.

Then append these arrow-marker rules to the end of the file (light + dark), so the
marker color adapts without inline color:

```css
.arrow-head{fill:#6b6a64;}
@media (prefers-color-scheme:dark){.arrow-head{fill:#b0aea4;}}
```

- [ ] **Step 2: Create `template.svg`**

Create `.claude/skills/concept-illustrator/assets/template.svg`. Paste the full
contents of `_style.css` from Step 1 into the `<style>` element where marked:

```xml
<svg class="cd-svg" xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 680 200" role="img" font-family="sans-serif">
  <title>Concept title</title>
  <desc>One-sentence description of what the figure shows.</desc>
  <defs>
    <style>/* PASTE THE FULL CONTENTS OF assets/_style.css HERE */</style>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path class="arrow-head" d="M0,0 L10,5 L0,10 z"/>
    </marker>
  </defs>
  <!-- content goes here; keep within 0..680 wide; set viewBox height to lowest element + ~40 -->
</svg>
```

- [ ] **Step 3: Write the failing test that template + style lint clean**

Append to `test_render.py`:

```python
ASSETS = os.path.join(os.path.dirname(SCRIPTS_DIR), "assets")


class TestShippedAssets(unittest.TestCase):
    def test_style_css_exists_and_has_palette(self):
        css = render._read(os.path.join(ASSETS, "_style.css"))
        self.assertGreaterEqual(len(render.load_palette(css)), 9)

    def test_template_lints_clean(self):
        style = os.path.join(ASSETS, "_style.css")
        errors = [m for lvl, m in render.lint_file(os.path.join(ASSETS, "template.svg"), style)
                  if lvl == "ERROR"]
        self.assertEqual(errors, [], f"template.svg has lint errors: {errors}")
```

- [ ] **Step 4: Run and verify it passes (assets already created in Steps 1–2)**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: PASS. If `test_template_lints_clean` fails, fix `template.svg` (most likely cause: a stray inline color, missing `viewBox`, or an `arrow-head` rule not appended to `_style.css`).

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/concept-illustrator/assets/ .claude/skills/concept-illustrator/scripts/tests/
git commit -m "feat(illustrator): add _style.css + lint-clean template.svg"
```

---

## Task 6: `figure.json` validation + frame-consistency

**Files:**
- Modify: `.claude/skills/concept-illustrator/scripts/render.py`
- Create: `.claude/skills/concept-illustrator/references/figure-json.md`
- Modify: `.claude/skills/concept-illustrator/scripts/tests/test_render.py`

- [ ] **Step 1: Write the `figure.json` reference**

Create `.claude/skills/concept-illustrator/references/figure-json.md`:

```markdown
# figure.json

Every figure directory contains a `figure.json` plus its frame SVGs.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `concept_slug` | string | yes | canonical slug of the concept this figure teaches |
| `title` | string | no | human-readable title |
| `archetype` | string | yes | `illustrative` \| `flowchart` \| `structural` \| `chart` |
| `playback` | string | yes | `static` (N=1) or `slideshow` (N>1) |
| `frames` | array | yes | ordered; each item `{ "file": "frame-01.svg", "caption": "..." }` |

Rules:
- `frames` is non-empty; `static` figures have exactly one frame.
- Every `file` must exist in the directory and lint clean.
- **Frame-consistency:** all frames share the same `viewBox` so the sequence reads
  as evolution, not jump-cuts.

Example:

​```json
{
  "concept_slug": "quicksort",
  "title": "Quicksort partitions around a pivot",
  "archetype": "illustrative",
  "playback": "slideshow",
  "frames": [
    { "file": "frame-01.svg", "caption": "Pick the last element as the pivot." },
    { "file": "frame-02.svg", "caption": "Smaller values shuffle left of it." }
  ]
}
​```
```

(Remove the zero-width spaces before the inner code fences when authoring — they
are only here to keep this plan's outer fence intact.)

- [ ] **Step 2: Write failing tests for `validate_figure`**

Append to `test_render.py`:

```python
import json
import tempfile


class TestValidateFigure(unittest.TestCase):
    def _write_figure(self, root, frames, data_overrides=None):
        os.makedirs(root, exist_ok=True)
        files = []
        for i, vb in enumerate(frames, 1):
            name = f"frame-{i:02d}.svg"
            with open(os.path.join(root, name), "w", encoding="utf-8") as fh:
                fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">'
                         f'<text class="t">Step {i}</text></svg>')
            files.append({"file": name, "caption": f"Step {i}"})
        data = {"concept_slug": "x", "archetype": "illustrative",
                "playback": "slideshow" if len(frames) > 1 else "static", "frames": files}
        data.update(data_overrides or {})
        with open(os.path.join(root, "figure.json"), "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def test_valid_figure_passes(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_figure(d, ["0 0 680 100", "0 0 680 100"])
            style = os.path.join(ASSETS, "_style.css")
            errors = [m for lvl, m in render.validate_figure(d, style) if lvl == "ERROR"]
            self.assertEqual(errors, [])

    def test_inconsistent_viewbox_errors(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_figure(d, ["0 0 680 100", "0 0 680 200"])
            style = os.path.join(ASSETS, "_style.css")
            errors = [m for lvl, m in render.validate_figure(d, style) if lvl == "ERROR"]
            self.assertTrue(any("viewBox" in m for m in errors))

    def test_missing_frame_file_errors(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_figure(d, ["0 0 680 100"])
            os.remove(os.path.join(d, "frame-01.svg"))
            style = os.path.join(ASSETS, "_style.css")
            errors = [m for lvl, m in render.validate_figure(d, style) if lvl == "ERROR"]
            self.assertTrue(errors)

    def test_missing_required_field_errors(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_figure(d, ["0 0 680 100"], {"archetype": None})
            os.remove(os.path.join(d, "figure.json"))
            with open(os.path.join(d, "figure.json"), "w") as fh:
                json.dump({"concept_slug": "x", "playback": "static",
                           "frames": [{"file": "frame-01.svg"}]}, fh)
            style = os.path.join(ASSETS, "_style.css")
            errors = [m for lvl, m in render.validate_figure(d, style) if lvl == "ERROR"]
            self.assertTrue(any("archetype" in m for m in errors))
```

- [ ] **Step 3: Run to verify failure**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: FAIL — `validate_figure` not defined.

- [ ] **Step 4: Implement `validate_figure`**

Append to `render.py`:

```python
FIGURE_REQUIRED = ("concept_slug", "archetype", "playback", "frames")
FIGURE_PLAYBACK = ("static", "slideshow")


def validate_figure(dir_path, style_path):
    figure_json = os.path.join(dir_path, "figure.json")
    if not os.path.exists(figure_json):
        return [("ERROR", "figure.json missing")]
    try:
        data = json.loads(_read(figure_json))
    except json.JSONDecodeError as exc:
        return [("ERROR", f"figure.json invalid JSON: {exc}")]

    issues = []
    for key in FIGURE_REQUIRED:
        if not data.get(key):
            issues.append(("ERROR", f"figure.json missing '{key}'"))
    if data.get("playback") and data["playback"] not in FIGURE_PLAYBACK:
        issues.append(("ERROR", "playback must be 'static' or 'slideshow'"))
    frames = data.get("frames") or []
    if data.get("playback") == "static" and len(frames) != 1:
        issues.append(("ERROR", "static figures must have exactly one frame"))

    palette = load_palette(_read(style_path)) if os.path.exists(style_path) else set()
    viewboxes = set()
    for frame in frames:
        name = frame.get("file") if isinstance(frame, dict) else frame
        fpath = os.path.join(dir_path, name or "")
        if not name or not os.path.exists(fpath):
            issues.append(("ERROR", f"frame file missing: {name}"))
            continue
        root, parse_issues = _safe_parse(fpath)
        if root is None:
            issues += [(lvl, f"{name}: {m}") for lvl, m in parse_issues]
            continue
        viewboxes.add(root.get("viewBox"))
        issues += [(lvl, f"{name}: {m}") for lvl, m in lint_svg(root, palette)]
    if len(viewboxes) > 1:
        issues.append(("ERROR", "frames have inconsistent viewBox (frame-consistency rule)"))
    return issues
```

- [ ] **Step 5: Run to verify pass**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/concept-illustrator/scripts/ .claude/skills/concept-illustrator/references/figure-json.md
git commit -m "feat(illustrator): validate figure.json + frame-consistency"
```

---

## Task 7: Slideshow viewer generator

**Files:**
- Create: `.claude/skills/concept-illustrator/assets/slideshow.template.html`
- Modify: `.claude/skills/concept-illustrator/scripts/render.py`
- Modify: `.claude/skills/concept-illustrator/scripts/tests/test_render.py`

- [ ] **Step 1: Create the viewer template**

Create `.claude/skills/concept-illustrator/assets/slideshow.template.html`:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<style>
  :root { color-scheme: light dark; }
  body { margin:0; font-family:-apple-system,"Segoe UI",Roboto,system-ui,sans-serif;
         display:flex; flex-direction:column; align-items:center; gap:1rem; padding:2rem; }
  #stage svg { max-width:100%; height:auto; }
  #caption { max-width:680px; text-align:center; opacity:.85; min-height:2.5em; }
  #bar { display:flex; gap:.5rem; align-items:center; }
  button { font:inherit; padding:.3rem .8rem; cursor:pointer; }
  #count { font-variant-numeric:tabular-nums; opacity:.7; }
</style>
</head>
<body>
<div id="stage"></div>
<div id="caption"></div>
<div id="bar">
  <button id="prev">&larr; Prev</button>
  <span id="count"></span>
  <button id="next">Next &rarr;</button>
  <button id="play">Auto-play</button>
</div>
<script>
const FRAMES = /*FRAMES*/[];
const CAPTIONS = /*CAPTIONS*/[];
let i = 0, timer = null;
const stage = document.getElementById('stage');
const caption = document.getElementById('caption');
const count = document.getElementById('count');
function show(n){
  i = (n + FRAMES.length) % FRAMES.length;
  stage.innerHTML = FRAMES[i];
  caption.textContent = CAPTIONS[i] || '';
  count.textContent = (i+1) + ' / ' + FRAMES.length;
}
document.getElementById('prev').onclick = () => show(i-1);
document.getElementById('next').onclick = () => show(i+1);
document.getElementById('play').onclick = (e) => {
  if (timer){ clearInterval(timer); timer = null; e.target.textContent = 'Auto-play'; }
  else { timer = setInterval(() => show(i+1), 1200); e.target.textContent = 'Pause'; }
};
show(0);
</script>
</body>
</html>
```

- [ ] **Step 2: Write failing tests for `build_viewer`**

Append to `test_render.py`:

```python
class TestBuildViewer(unittest.TestCase):
    def test_inlines_all_frames(self):
        with tempfile.TemporaryDirectory() as d:
            for i in (1, 2):
                with open(os.path.join(d, f"frame-{i:02d}.svg"), "w") as fh:
                    fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 100">'
                             f'<text class="t">Step {i}</text></svg>')
            with open(os.path.join(d, "figure.json"), "w") as fh:
                json.dump({"concept_slug": "x", "archetype": "illustrative",
                           "playback": "slideshow", "title": "Demo",
                           "frames": [{"file": "frame-01.svg", "caption": "one"},
                                      {"file": "frame-02.svg", "caption": "two"}]}, fh)
            out = os.path.join(d, "figure.html")
            template = os.path.join(ASSETS, "slideshow.template.html")
            render.build_viewer(d, template, out)
            html = render._read(out)
            self.assertEqual(html.count("<svg"), 2)
            self.assertIn("Demo", html)
            self.assertIn("one", html)
            self.assertNotIn("/*FRAMES*/[]", html)
```

- [ ] **Step 3: Run to verify failure**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: FAIL — `build_viewer` not defined.

- [ ] **Step 4: Implement `build_viewer`**

Append to `render.py`:

```python
def build_viewer(dir_path, template_path, out_path):
    data = json.loads(_read(os.path.join(dir_path, "figure.json")))
    frames = data.get("frames") or []
    svgs, captions = [], []
    for frame in frames:
        name = frame.get("file") if isinstance(frame, dict) else frame
        svgs.append(_read(os.path.join(dir_path, name)))
        captions.append(frame.get("caption", "") if isinstance(frame, dict) else "")
    frames_js = "[" + ",".join(json.dumps(s) for s in svgs) + "]"
    captions_js = "[" + ",".join(json.dumps(c) for c in captions) + "]"
    html = (_read(template_path)
            .replace("/*FRAMES*/[]", frames_js)
            .replace("/*CAPTIONS*/[]", captions_js)
            .replace("{{TITLE}}", data.get("title", "Figure")))
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(html)
    return out_path
```

- [ ] **Step 5: Run to verify pass**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/concept-illustrator/assets/slideshow.template.html .claude/skills/concept-illustrator/scripts/
git commit -m "feat(illustrator): self-contained slideshow viewer generator"
```

---

## Task 8: Optional PNG export

**Files:**
- Modify: `.claude/skills/concept-illustrator/scripts/render.py`
- Modify: `.claude/skills/concept-illustrator/scripts/tests/test_render.py`

- [ ] **Step 1: Write the test (skips when no rasterizer is installed)**

Append to `test_render.py`:

```python
import shutil


class TestPngExport(unittest.TestCase):
    def test_png_export_when_backend_available(self):
        if not (shutil.which("rsvg-convert") or _has_cairosvg()):
            self.skipTest("no rasterizer backend installed")
        with tempfile.TemporaryDirectory() as d:
            svg_path = os.path.join(d, "f.svg")
            with open(svg_path, "w") as fh:
                fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 100">'
                         '<rect x="0" y="0" width="680" height="100"/></svg>')
            out = os.path.join(d, "f.png")
            render.export_png(svg_path, out, "light", 2.0)
            self.assertTrue(os.path.exists(out) and os.path.getsize(out) > 0)


def _has_cairosvg():
    try:
        import cairosvg  # noqa: F401
        return True
    except ImportError:
        return False
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: FAIL — `export_png` not defined (or the test errors before skipping).

- [ ] **Step 3: Implement `export_png`**

Append to `render.py`:

```python
import subprocess


def export_png(svg_path, png_path, theme="light", scale=2.0):
    """Rasterize via rsvg-convert or cairosvg. Static rasterizers don't evaluate
    the dark-mode media query, so 'theme' is reserved for a future forced-theme
    pass; for now both backends render the document's default (light)."""
    if subprocess.run(["which", "rsvg-convert"], capture_output=True).returncode == 0:
        subprocess.run(
            ["rsvg-convert", "-z", str(scale), "-o", png_path, svg_path], check=True
        )
        return png_path
    try:
        import cairosvg
    except ImportError:
        raise SystemExit("PNG export needs 'rsvg-convert' or 'cairosvg' installed")
    cairosvg.svg2png(url=svg_path, write_to=png_path, scale=scale)
    return png_path
```

- [ ] **Step 4: Run to verify pass (or skip)**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: PASS (the PNG test is skipped if no backend; all others pass).

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/concept-illustrator/scripts/
git commit -m "feat(illustrator): optional PNG export (rsvg-convert/cairosvg)"
```

---

## Task 9: Author the reference docs

These are authored content (not code). Each must be concrete and complete — no
"TBD". Acceptance is a script check that every file exists and contains its required
headings.

**Files:**
- Create: `.claude/skills/concept-illustrator/references/design-system.md`
- Create: `.claude/skills/concept-illustrator/references/archetypes.md`
- Create: `.claude/skills/concept-illustrator/references/visual-vocabulary.md`
- Create: `.claude/skills/concept-illustrator/references/voice-and-metaphor.md`
- Create: `.claude/skills/concept-illustrator/references/review-protocol.md`

- [ ] **Step 1: Write `design-system.md`**

Must contain these `##` sections, populated from the spec's Style system and the
existing draft's "Core rules":
- `## Palette` — table of the nine named ramps (purple, teal, coral, pink, gray,
  blue, green, amber, red) with their light + dark hexes (read from `assets/_style.css`),
  and the rule "color encodes category, not sequence."
- `## Color-role conventions` — fixed role→ramp mapping: under-consideration = teal,
  eliminated/inactive = gray, target/goal = coral, neutral structure = gray; blue/
  green/amber/red reserved for informational/success/warning/error or physical meaning.
- `## Type` — only `th` (14px medium), `t` (14px), `ts` (12px); sentence case always.
- `## Canvas & geometry` — `viewBox="0 0 680 H"`; box width ≥ `max(title_chars×8,
  subtitle_chars×7)+24`; thin 0.5 strokes; center text with `text-anchor="middle"`
  + `dominant-baseline="central"`.
- `## Banned` — gradients (except one physical-property gradient in an illustrative
  figure), shadows, glows, emoji, jargon.

- [ ] **Step 2: Write `archetypes.md`**

Must contain one `##` section per archetype, each with "when to use" + a small worked
example: `## Flowchart`, `## Structural`, `## Illustrative` (note: the strong default;
invent a spatial metaphor), `## Chart`, and `## Sequence` (the multi-frame archetype —
process/trace concepts; cite quicksort; state the frame-consistency rule: shared
canvas + stable element positions, only highlights/pointers move).

- [ ] **Step 3: Write `visual-vocabulary.md`**

A `##` section per primitive, each with a copy-paste SVG snippet (classed, palette-only,
lint-clean) and a one-line "use for": `## List / array cell`, `## Pointer`,
`## Graph node`, `## Edge`, `## Container / set`, `## Stack frame`, `## Function box`,
and `## State styles` (active = `c-teal`, eliminated = `c-gray`, target = `c-coral`).
State explicitly: this is the only place literal SVG reuse lives — copy a primitive,
don't import a whole figure.

- [ ] **Step 4: Write `voice-and-metaphor.md`**

`## Voice` (knowledgeable friend; concrete; short; metaphor-first; no jargon —
unknown terms get decomposed, not assumed) and `## Metaphor bank` (a table of
concept → metaphor: recursion → nested Russian dolls; stack → plates pushed/popped;
hash map → keys into labeled mailboxes; pointer → a finger marking a spot; etc.).

- [ ] **Step 5: Write `review-protocol.md`**

Document the fresh-eyes review (its automated loop is Phase 3; here it is a manual/
subagent procedure):
- `## Blind-reader test` — give a fresh agent ONLY the rendered figure (PNG) + caption,
  ask "what does this teach, and what's confusing?"; compare to the intended concept;
  divergence = comprehension gap.
- `## Fidelity critic` — give a fresh agent the concept + figure; ask it to find what
  is wrong, misleading, or silently assumed (incl. a missing prerequisite).
- `## Repair loop` — bounded ≈2 retries: figure gap → regenerate with the critique;
  missing-prerequisite gap → flag for re-decomposition. Then flag-and-ship if unresolved.

- [ ] **Step 6: Write the failing acceptance test**

Append to `test_render.py`:

```python
REFS = os.path.join(os.path.dirname(SCRIPTS_DIR), "references")


class TestReferenceDocs(unittest.TestCase):
    REQUIRED = {
        "design-system.md": ["## Palette", "## Color-role conventions", "## Type",
                             "## Canvas & geometry", "## Banned"],
        "archetypes.md": ["## Flowchart", "## Structural", "## Illustrative",
                          "## Chart", "## Sequence"],
        "visual-vocabulary.md": ["## List / array cell", "## Pointer", "## Graph node",
                                 "## State styles"],
        "voice-and-metaphor.md": ["## Voice", "## Metaphor bank"],
        "review-protocol.md": ["## Blind-reader test", "## Fidelity critic",
                               "## Repair loop"],
    }

    def test_required_docs_and_headings(self):
        for name, headings in self.REQUIRED.items():
            path = os.path.join(REFS, name)
            self.assertTrue(os.path.exists(path), f"missing {name}")
            text = render._read(path)
            for h in headings:
                self.assertIn(h, text, f"{name} missing heading '{h}'")
```

- [ ] **Step 7: Run and verify it passes (docs authored in Steps 1–5)**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: PASS. Also lint every snippet in `visual-vocabulary.md` by hand-extracting
it to a temp `.svg` and running `render.py` on it; fix any that error.

- [ ] **Step 8: Commit**

```bash
git add .claude/skills/concept-illustrator/references/ .claude/skills/concept-illustrator/scripts/tests/
git commit -m "docs(illustrator): author design-system, archetypes, vocabulary, voice, review"
```

---

## Task 10: Rewrite `SKILL.md` as the real contract + a reference-integrity check

**Files:**
- Create: `.claude/skills/concept-illustrator/SKILL.md`
- Create: `.claude/skills/concept-illustrator/scripts/check_skill_refs.py`
- Modify: `.claude/skills/concept-illustrator/scripts/tests/test_render.py`

- [ ] **Step 1: Write `SKILL.md`**

Adapt `example/concept-illustrator-SKILL.md` into the real skill. Keep the frontmatter
(`name: concept-illustrator`, the description). Update the body so that:
- Every referenced file path actually exists now: `assets/template.svg`,
  `assets/_style.css`, `scripts/render.py`, `references/design-system.md`,
  `references/archetypes.md`, `references/visual-vocabulary.md`,
  `references/voice-and-metaphor.md`, `references/review-protocol.md`,
  `references/figure-json.md`.
- The workflow gains: **(2.5) Storyboard** — decide static vs sequence; if sequence,
  plan frames honoring the frame-consistency rule.
- The routing table gains the **Sequence** archetype row.
- The output contract is a **figure directory**: `figure.json` + `frame-NN.svg`
  frames + captions (point to `references/figure-json.md`).
- The validate step uses the real commands:
  - one frame: `python3 scripts/render.py path/to/frame.svg`
  - whole figure: `python3 scripts/render.py path/to/figure-dir`
  - viewer: `python3 scripts/render.py path/to/figure-dir --viewer path/to/figure.html`
- A **Review** step points to `references/review-protocol.md` (blind-reader +
  fidelity critic) and notes the automated loop arrives in Phase 3.
- Machine-callable I/O: input = concept slug + name + definition; output = a figure
  directory.

- [ ] **Step 2: Write the reference-integrity checker**

Create `.claude/skills/concept-illustrator/scripts/check_skill_refs.py`:

```python
#!/usr/bin/env python3
"""Fail if SKILL.md references a path that does not exist in the skill dir."""
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = re.compile(r"`((?:assets|references|scripts|examples)/[^`]+)`")


def missing_refs():
    text = open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8").read()
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
```

- [ ] **Step 3: Write the failing test**

Append to `test_render.py`:

```python
class TestSkillRefs(unittest.TestCase):
    def test_all_referenced_paths_exist(self):
        sys.path.insert(0, SCRIPTS_DIR)
        import check_skill_refs
        self.assertEqual(check_skill_refs.missing_refs(), [])
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: PASS. If `MISSING` paths appear, either create the file or fix the path in
`SKILL.md` until the set is empty.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/concept-illustrator/SKILL.md .claude/skills/concept-illustrator/scripts/
git commit -m "feat(illustrator): real SKILL.md contract + reference-integrity check"
```

---

## Task 11: End-to-end golden example + knowledge update

**Files:**
- Create: `.claude/skills/concept-illustrator/examples/quicksort/figure.json`
- Create: `.claude/skills/concept-illustrator/examples/quicksort/frame-01.svg` … `frame-04.svg`
- Modify: `knowledge/concepts/dummies-notes/illustration-engine.md`
- Modify: `knowledge/index.md`, `knowledge/log.md`
- Modify: `CLAUDE.md` (article-mapping `affects` note)

- [ ] **Step 1: Produce the golden figure by following SKILL.md**

Using the skill end-to-end, create a 4-frame **quicksort** sequence in
`.claude/skills/concept-illustrator/examples/quicksort/`. Start each frame from
`assets/template.svg`; use the `## List / array cell`, `## Pointer`, and
`## State styles` primitives from `visual-vocabulary.md`; obey the frame-consistency
rule (identical `viewBox`, cells fixed, only pivot/pointer highlights move). Write
`figure.json` per `references/figure-json.md` with a one-line plain-language caption
per frame.

- [ ] **Step 2: Validate the figure and build its viewer**

Run:
```bash
cd .claude/skills/concept-illustrator
python3 scripts/render.py examples/quicksort
python3 scripts/render.py examples/quicksort --viewer examples/quicksort/figure.html
cd -
```
Expected: figure validation prints `OK` (no `ERROR`); viewer written. Open
`examples/quicksort/figure.html` in a browser and step through all four frames to
confirm the sequence reads as evolution. Fix any lint errors before continuing.

- [ ] **Step 3: Add an end-to-end test pinning the golden example stays valid**

Append to `test_render.py`:

```python
class TestGoldenExample(unittest.TestCase):
    def test_quicksort_figure_is_valid(self):
        root = os.path.join(os.path.dirname(SCRIPTS_DIR), "examples", "quicksort")
        style = os.path.join(ASSETS, "_style.css")
        errors = [m for lvl, m in render.validate_figure(root, style) if lvl == "ERROR"]
        self.assertEqual(errors, [], f"golden quicksort figure has errors: {errors}")
```

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: PASS (full suite green).

- [ ] **Step 4: Update the knowledge article to match the implementation**

Rewrite `knowledge/concepts/dummies-notes/illustration-engine.md`:
- Set `status: mature`, `updated: 2026-06-09`.
- Replace `affects:` with `[".claude/skills/concept-illustrator/SKILL.md"]` (scope the
  drift gate to the contract doc; tooling internals are detail).
- Replace the "Open design questions" with the real shape: skill location, the
  `render.py` gate (list the checks), the `figure.json` contract, multi-frame +
  frame-consistency, the slideshow viewer, and the per-figure review protocol
  (automated in Phase 3). Link `[[concept-decomposition]]` and
  `[[atomic-illustration-catalog]]`.

- [ ] **Step 5: Update the index, log, and CLAUDE.md mapping**

- In `knowledge/index.md`, bump the `illustration-engine.md` row's summary/date.
- Append to `knowledge/log.md`:

```markdown
## [2026-06-09] compile | Phase 1 — concept-illustrator made real

- Built `.claude/skills/concept-illustrator/`: real SKILL.md, _style.css + template.svg,
  reference docs (design-system, archetypes, visual-vocabulary, voice-and-metaphor,
  review-protocol, figure-json), and `scripts/render.py` (lint + figure validation +
  slideshow viewer + optional PNG), all unit-tested with stdlib unittest.
- Added multi-frame figures with the frame-consistency rule; golden quicksort example.
- Updated `illustration-engine.md` to mature; scoped its affects to SKILL.md.
```

- In `CLAUDE.md`, update the article-mapping row for "Figure generation, SVG output,
  archetype routing" to note the live path `.claude/skills/concept-illustrator/`.

- [ ] **Step 6: Commit (single commit so drift-check sees the article alongside SKILL-path work)**

```bash
git add .claude/skills/concept-illustrator/examples/ \
        .claude/skills/concept-illustrator/scripts/tests/ \
        knowledge/ CLAUDE.md
git commit -m "feat(illustrator): golden quicksort example + Phase 1 knowledge update

Phase 1 complete: concept-illustrator renders one concept to a lint-clean,
multi-frame figure with a slideshow viewer. illustration-engine.md matured."
```

- [ ] **Step 7: Run the full suite one final time and push**

```bash
python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'
git push
```
Expected: all tests pass (PNG test may skip); push succeeds.

---

## Definition of done (Phase 1)

- `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'` is green.
- `render.py` lints a single SVG, validates a figure directory (incl. frame-consistency),
  and generates a self-contained slideshow HTML.
- `assets/template.svg` and the golden `examples/quicksort/` figure both lint/validate clean.
- `SKILL.md` references only files that exist (`check_skill_refs.py` passes).
- `knowledge/concepts/dummies-notes/illustration-engine.md` matches the implementation
  and the drift gate is scoped to it.
