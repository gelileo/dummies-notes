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
