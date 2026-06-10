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
