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

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_STYLE = os.path.join(_HERE, "..", "assets", "_style.css")
DEFAULT_TEMPLATE = os.path.join(_HERE, "..", "assets", "slideshow.template.html")


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
    (root, issues): root is None when parsing is refused or fails. root is the SVG root Element (from ET.fromstring), not an ElementTree."""
    raw = _read(path)
    if DTD_PATTERN.search(raw):
        return None, [("ERROR", "SVG contains <!DOCTYPE or <!ENTITY (rejected for safety)")]
    try:
        return ET.fromstring(raw), []
    except ET.ParseError as exc:
        return None, [("ERROR", f"malformed SVG: {exc}")]


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


def check_bounds(root):
    parts = (root.get("viewBox") or "").split()
    if len(parts) != 4:
        return []
    width, height = _f(parts[2]), _f(parts[3])
    issues = []
    for el in root.iter():
        if localname(el.tag) != "rect":
            continue
        x = _f(el.get("x"))
        y = _f(el.get("y"))
        x = 0.0 if x is None else x
        y = 0.0 if y is None else y
        w, h = _f(el.get("width")), _f(el.get("height"))
        if w is not None and (x < -0.5 or x + w > width + 0.5):
            issues.append(("ERROR", f"rect exceeds canvas width (x={x}, w={w})"))
        if h is not None and (y < -0.5 or y + h > height + 0.5):
            issues.append(("ERROR", f"rect exceeds canvas height (y={y}, h={h})"))
    return issues


def check_connector_fill(root):
    issues = []
    for el in root.iter():
        if localname(el.tag) != "path":
            continue
        classes = set((el.get("class") or "").split())
        styled_connector = bool(classes & {"arr", "leader"})
        marker_connector = bool(el.get("marker-end")) and not styled_connector
        fill = (el.get("fill") or "").strip().lower()
        if styled_connector and fill and fill != "none":
            issues.append(("ERROR", 'connector <path> has a conflicting inline fill; '
                                    'the arr/leader class already sets fill="none"'))
        elif marker_connector and fill != "none":
            issues.append(("ERROR", 'connector <path> with marker-end must set fill="none"'))
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
