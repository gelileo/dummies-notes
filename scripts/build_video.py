#!/usr/bin/env python3
"""Build a per-topic narrated animated slideshow from an assembled deliverable.

Reads a concept graph (output/<topic>/graph/*.json) + the registry figures and
writes output/<topic>/video/: manifest.json, script.md, captions.srt, video.html
(always) and video.mp4 (when --format mp4|both and ffmpeg is present).

Deterministic and zero-dependency on the default (HTML) path: no agent writes
the video. Reuses assemble.py (graph + ordering), the registry, and render.py."""

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import assemble as asm  # noqa: E402
from concept_registry import DEFAULT_ROOT, lookup  # noqa: E402

_ILLUSTRATOR = os.path.join(os.path.dirname(_HERE), ".claude", "skills",
                            "concept-illustrator", "scripts")
sys.path.insert(0, _ILLUSTRATOR)
import render  # noqa: E402

PLAYER_TEMPLATE = os.path.join(os.path.dirname(_HERE), ".claude", "skills",
                               "concept-illustrator", "assets",
                               "video.template.html")

DEFAULT_WPM = 150
MIN_DUR, MAX_DUR = 2.5, 18.0
MIN_TTS_DUR = 2.0
STAGE = {"width": 1280, "height": 720}


def _duration_for(text, wpm):
    words = len((text or "").split())
    secs = words / (wpm / 60.0) if words else 0.0
    return max(MIN_DUR, min(MAX_DUR, secs))


def load_frames(figure_dir):
    """[{file (abs), caption, commentary}] for a figure dir, or [] if absent."""
    figure_json = os.path.join(figure_dir, "figure.json")
    if not os.path.exists(figure_json):
        return []
    try:
        with open(figure_json, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return []
    frames = []
    for frame in data.get("frames") or []:
        if not isinstance(frame, dict):
            return []
        name = frame.get("file")
        path = os.path.join(figure_dir, name or "")
        if not name or not os.path.exists(path):
            return []
        frames.append({"file": os.path.abspath(path),
                       "caption": frame.get("caption", ""),
                       "commentary": frame.get("commentary", "")})
    return frames


def _slide(kind, slug, image, caption, narration, wpm, transition):
    return {"kind": kind, "concept_slug": slug, "image": image,
            "caption": caption, "narration": narration,
            "duration_s": round(_duration_for(narration, wpm), 3),
            "transition": transition}


def build_manifest(graph_dir, registry_root=DEFAULT_ROOT, wpm=DEFAULT_WPM, stage=STAGE):
    nodes, issues = asm.load_full_graph(graph_dir)
    if any(lvl == "ERROR" for lvl, _ in issues):
        return None, issues
    root = asm.find_root(nodes)
    order = asm.topo_order(nodes)
    title_node = nodes[root]
    slides = [_slide(
        "title", None, None, title_node["name"],
        f"This is {title_node['name'].lower()}. {title_node['definition']}",
        wpm, "cut")]
    for slug in order:
        node = nodes[slug]
        entry = lookup(registry_root, slug)
        figure_dir = asm._figure_dir_for(entry, registry_root)
        frames = load_frames(figure_dir) if figure_dir else []
        if not frames:
            continue
        slides.append(_slide(
            "section", slug, None, node["name"],
            f"Next: {node['name'].lower()}. {node['definition']}", wpm, "cut"))
        for i, fr in enumerate(frames):
            slides.append(_slide(
                "frame", slug, fr["file"], fr["caption"], fr["commentary"],
                wpm, "crossfade" if i > 0 else "cut"))
    slides.append(_slide(
        "closing", None, None, "Recap",
        f"That is {title_node['name'].lower()}, built up one idea at a time.",
        wpm, "cut"))
    manifest = {"topic": root, "title": title_node["name"],
                "definition": title_node["definition"], "stage": dict(stage),
                "reading_rate_wpm": wpm, "slides": slides}
    return manifest, issues


def _srt_timestamp(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_captions(manifest, out_path):
    lines, t = [], 0.0
    for i, slide in enumerate(manifest["slides"], start=1):
        start, end = t, t + slide["duration_s"]
        t = end
        lines.append(str(i))
        lines.append(f"{_srt_timestamp(start)} --> {_srt_timestamp(end)}")
        lines.append(slide["narration"].strip() or slide["caption"].strip())
        lines.append("")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")
    return out_path


def write_script(manifest, out_path):
    parts = [f"# {manifest['title']} — narration script", ""]
    current = object()
    for slide in manifest["slides"]:
        key = slide["kind"] if slide["concept_slug"] is None else slide["concept_slug"]
        if key != current:
            current = key
            heading = slide["caption"] or slide["kind"].title()
            parts.append(f"## {heading}")
            parts.append("")
        parts.append(slide["narration"].strip())
        parts.append("")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts).rstrip() + "\n")
    return out_path


def _read_inner_svg(path):
    """Return a frame SVG's markup with any <?xml ...?> / DOCTYPE prolog removed."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    idx = text.find("<svg")
    return text[idx:] if idx >= 0 else text


def _esc(text):
    return html.escape(text or "", quote=True)


_ROOT_DIM_RE = re.compile(r'\s(?:width|height)="[^"]*"')


def _slide_html(slide):
    # NOTE: figures share id="arrow" on their <marker>; when several frame SVGs are
    # inlined into one player document, url(#arrow) resolves to the first in document
    # order. Safe only because the design system uses one marker geometry across figures.
    if slide["kind"] == "frame":
        inner = _read_inner_svg(slide["image"])
        body = inner + f'<p class="cap">{_esc(slide["caption"])}</p>'
    else:
        body = f'<div class="card">{_esc(slide["caption"])}</div>'
    cls = "slide" + ("" if slide["transition"] == "crossfade" else " cut")
    return f'<div class="{cls}">{body}</div>'


def build_player(manifest, template_path, out_path):
    """Render the self-contained HTML player from a manifest + template; returns out_path."""
    with open(template_path, encoding="utf-8") as fh:
        template = fh.read()
    slides_html = "\n".join(_slide_html(s) for s in manifest["slides"])
    # store only lightweight fields in the injected manifest (no SVG text)
    light = dict(manifest)
    light["slides"] = [{k: s[k] for k in ("kind", "concept_slug", "caption",
                                          "narration", "duration_s", "transition")}
                       for s in manifest["slides"]]
    # json.dumps does not escape <,>,& — escape them for safe embedding inside an
    # inline <script> (prevents a narration containing "</script>" from breaking out).
    # \uXXXX escapes are valid JSON and JSON.parse / the var assignment decode them back.
    manifest_json = (json.dumps(light)
                     .replace("<", "\\u003c")
                     .replace(">", "\\u003e")
                     .replace("&", "\\u0026"))
    html_out = (template
                .replace("{{SLIDES_HTML}}", slides_html)
                .replace("{{MANIFEST_JSON}}", manifest_json))
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html_out)
    return out_path


def _nest_figure(inner, x, y, width, height):
    """Position a figure SVG inside the stage by injecting layout attributes on
    its root <svg>. The figure's own width/height (real figures carry width="100%")
    are stripped first, so the nested element has exactly one width/height — a
    duplicate XML attribute is a fatal parse error. Its viewBox is kept so it
    scales to fit the given box."""
    end = inner.find(">")
    if end < 0:
        return inner
    head, rest = inner[:end], inner[end:]
    head = _ROOT_DIM_RE.sub("", head)
    head = head.replace(
        "<svg", f'<svg x="{x}" y="{y}" width="{width}" height="{height}" '
                f'preserveAspectRatio="xMidYMid meet"', 1)
    return head + rest


def stage_svg(slide, stage):
    w, h = stage["width"], stage["height"]
    pad, cap_h, top_h = 40, 90, 70
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
             f'width="{w}" height="{h}">',
             f'<rect width="{w}" height="{h}" fill="#ffffff"/>']
    label = slide["concept_slug"] or slide["kind"]
    if slide["kind"] == "frame":
        parts.append(f'<text x="{w/2:.0f}" y="44" text-anchor="middle" '
                     f'font-family="sans-serif" font-size="22" fill="#444">'
                     f'{_esc(label.replace("-", " "))}</text>')
        inner_w, inner_h = w - 2 * pad, h - top_h - cap_h
        parts.append(_nest_figure(_read_inner_svg(slide["image"]),
                                  pad, top_h, inner_w, inner_h))
        parts.append(f'<text x="{w/2:.0f}" y="{h-34}" text-anchor="middle" '
                     f'font-family="sans-serif" font-size="24" fill="#222">'
                     f'{_esc(slide["caption"])}</text>')
    else:
        # title / section / closing: centered card text
        parts.append(f'<text x="{w/2:.0f}" y="{h/2-10:.0f}" text-anchor="middle" '
                     f'font-family="sans-serif" font-size="48" fill="#111">'
                     f'{_esc(slide["caption"])}</text>')
    parts.append("</svg>")
    return "\n".join(parts)
