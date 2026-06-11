# Video Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scripts/build_video.py`, which turns an assembled topic deliverable into a per-topic narrated animated slideshow — a zero-dep self-contained HTML player and an opt-in ffmpeg/TTS MP4 — plus `manifest.json`, `script.md`, `captions.srt`.

**Architecture:** A deterministic, zero-dependency Python module (sibling to `scripts/assemble.py`) that reuses `assemble.py`'s graph loading + bottom-up ordering, the registry `lookup`, and `render.py`'s `export_png`. It builds one ordered slide **manifest** from the topic's figures (`caption` → subtitle, `commentary` → narration), then renders it to HTML (default) and/or MP4 (`--format`). An opt-in `Video` phase wires it into the workflow.

**Tech Stack:** Python 3 stdlib (`json`, `os`, `html`, `argparse`, `subprocess`, `shutil`, `tempfile`, `xml.etree`), `unittest`. MP4 path shells out to `ffmpeg` and macOS `say` (runtime-detected). PNG via existing `rsvg-convert`/`cairosvg`.

**Spec:** `docs/superpowers/specs/2026-06-11-video-engine-design.md`

---

## Reference: shared symbols (define once, reuse everywhere)

These are defined in `scripts/build_video.py` and used across tasks. Keep names identical.

```python
DEFAULT_WPM = 150
MIN_DUR, MAX_DUR = 2.5, 18.0          # per-slide seconds clamp (computed timeline)
MIN_TTS_DUR = 2.0                     # floor when TTS audio length drives duration
STAGE = {"width": 1280, "height": 720}
```

Reused from `assemble.py` (import as `import assemble as asm`):
`asm.load_full_graph`, `asm.find_root`, `asm.topo_order`, `asm.classify_prereqs`, `asm._figure_dir_for`.
Reused from `concept_registry.py` (`import concept_registry as reg`): `reg.lookup`, `reg.DEFAULT_ROOT`.
Reused from `render.py` (`import render`): `render.export_png`.

Slide dict shape (every slide has exactly these keys):
```python
{"kind": "title"|"section"|"frame"|"closing",
 "concept_slug": str|None, "image": str|None,   # image = abs path to a frame SVG (frame slides only)
 "caption": str, "narration": str,
 "duration_s": float, "transition": "crossfade"|"cut"}
```

Manifest dict shape:
```python
{"topic": str, "title": str, "definition": str,
 "stage": {"width": int, "height": int},
 "reading_rate_wpm": int, "slides": [<slide>, ...]}
```

---

## Task 1: Knowledge scaffold (article + mapping + log)

Create the doc up front so the same-task drift rule is satisfied for every later code commit, and capture the design.

**Files:**
- Create: `knowledge/concepts/dummies-notes/video-engine.md`
- Modify: `CLAUDE.md` (Article mapping table)
- Modify: `knowledge/log.md`

- [ ] **Step 1: Write the article**

Create `knowledge/concepts/dummies-notes/video-engine.md`:

```markdown
---
title: Video engine
type: concept
area: dummies-notes
updated: 2026-06-11
status: thin
affects:
  - "scripts/build_video.py"
  - ".claude/skills/concept-illustrator/assets/video.template.html"
references:
  - "concepts/dummies-notes/illustration-engine.md"
  - "concepts/dummies-notes/orchestration-workflow.md"
---

# Video engine

Turns an assembled topic deliverable into one continuous narrated animated
slideshow. Deterministic and zero-dependency on the default path, mirroring
[[atomic-illustration-catalog]] and the assembler: no agent writes the video.

## Manifest-first

`scripts/build_video.py` builds a single ordered **manifest** (`manifest.json`)
from the topic graph + registry figures, reusing `assemble.py`'s bottom-up
`topo_order`. Each figure frame becomes a slide whose subtitle is the frame
`caption` and whose narration is the frame `commentary` (the simple-sentence
narration layer the illustrator already writes). A title card opens, a
per-concept section card precedes each figure, and a closing card ends. Nodes
without a loadable figure are skipped to keep the video visual. Slide duration
is `words / (wpm/60)` clamped to [2.5s, 18s] (wpm default 150).

## Two render targets, one manifest

- **HTML player** (`video.html`, default, zero-dep): self-contained, inlines
  every SVG, auto-advances on duration, crossfades within a concept's frames,
  optional Web Speech narration.
- **MP4** (`--format mp4|both`, opt-in): rasterizes a 16:9 **stage SVG** per
  slide via `render.export_png`, holds + `xfade`-crossfades with ffmpeg, and
  speaks narration via macOS `say`. When TTS is present the slide duration
  follows the spoken-audio length. ffmpeg/`say` are runtime-detected; missing
  ffmpeg skips the MP4, missing `say` yields a silent MP4 with burned-in
  captions. Static rasterizers ignore the dark-mode media query, so MP4 frames
  render at the default (light) theme.

Every run also writes `script.md` (human voiceover) and `captions.srt`.
```

- [ ] **Step 2: Add the mapping rows to `CLAUDE.md`**

In the "Article mapping" table, after the `scripts/assemble.py` row, add:

```markdown
| `scripts/build_video.py` | `concepts/dummies-notes/video-engine.md` |
| `.claude/skills/concept-illustrator/assets/video.template.html` | `concepts/dummies-notes/video-engine.md` |
```

- [ ] **Step 3: Append a log entry to `knowledge/log.md`**

Append:

```markdown
- 2026-06-11 — Phase 6 (video engine): began `scripts/build_video.py` + new article `video-engine.md`. Manifest-first; HTML player + opt-in MP4; reuses assemble ordering + render.export_png.
```

- [ ] **Step 4: Validate frontmatter**

Run: `python3 scripts/validate-articles`
Expected: exits 0, no errors for `video-engine.md`.

- [ ] **Step 5: Commit**

```bash
git add knowledge/concepts/dummies-notes/video-engine.md CLAUDE.md knowledge/log.md
git commit -m "docs(video): scaffold video-engine article + drift mapping"
```

---

## Task 2: Manifest builder

**Files:**
- Create: `scripts/build_video.py`
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: Write failing tests**

Create `scripts/tests/test_build_video.py`:

```python
import json
import os
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import build_video as bv  # noqa: E402
import concept_registry as reg  # noqa: E402


def write_decomp(graph_dir, slug, atomic, prereqs=(), figurable=None):
    os.makedirs(graph_dir, exist_ok=True)
    data = {
        "concept": {"slug": slug, "name": slug.replace("-", " ").title(),
                    "definition": f"Plain definition of {slug}."},
        "audience": "a curious adult with no domain background",
        "atomic": atomic,
        "mechanism_figurable": atomic if figurable is None else figurable,
        "atomic_reason": "fixture.",
        "prerequisites": [
            {"slug": p, "name": p.replace("-", " ").title(),
             "definition": f"Plain definition of {p}.", "why": f"{slug} needs {p}."}
            for p in prereqs
        ],
    }
    with open(os.path.join(graph_dir, f"{slug}.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def make_figure(registry_root, slug, n_frames=2):
    """Register slug and attach a figure dir with n_frames SVG frames."""
    reg.register(registry_root, slug, slug.replace("-", " ").title(),
                 f"Plain definition of {slug}.")
    fig_dir = os.path.join(registry_root, slug, "figure")
    os.makedirs(fig_dir, exist_ok=True)
    frames = []
    for i in range(1, n_frames + 1):
        fname = f"frame-{i:02d}.svg"
        with open(os.path.join(fig_dir, fname), "w", encoding="utf-8") as fh:
            fh.write(f'<svg viewBox="0 0 680 220"><text>{slug} {i}</text></svg>')
        frames.append({"file": fname, "caption": f"{slug} caption {i}",
                       "runbook": "rb", "commentary": f"This is narration for {slug} frame {i}."})
    with open(os.path.join(fig_dir, "figure.json"), "w", encoding="utf-8") as fh:
        json.dump({"concept_slug": slug, "archetype": "illustrative",
                   "playback": "slideshow", "frames": frames}, fh)
    reg.attach_figure(registry_root, slug, fig_dir)


class TestDuration(unittest.TestCase):
    def test_word_count_drives_duration(self):
        # 15 words at 150 wpm = 6.0s, within clamp.
        text = " ".join(["word"] * 15)
        self.assertAlmostEqual(bv._duration_for(text, 150), 6.0, places=3)

    def test_short_text_clamped_to_min(self):
        self.assertEqual(bv._duration_for("hi", 150), bv.MIN_DUR)

    def test_long_text_clamped_to_max(self):
        text = " ".join(["word"] * 1000)
        self.assertEqual(bv._duration_for(text, 150), bv.MAX_DUR)


class TestManifest(unittest.TestCase):
    def _topic(self, base):
        graph = os.path.join(base, "g")
        registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", False, ["packets"])
        write_decomp(graph, "packets", True)
        make_figure(registry, "tcp", 2)
        make_figure(registry, "packets", 2)
        return graph, registry

    def test_order_and_slide_kinds(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = self._topic(base)
            manifest, issues = bv.build_manifest(graph, registry)
            self.assertEqual([m for lvl, m in issues if lvl == "ERROR"], [])
            kinds = [s["kind"] for s in manifest["slides"]]
            self.assertEqual(kinds[0], "title")
            self.assertEqual(kinds[-1], "closing")
            # packets (prereq) section+frames must precede tcp (root) section+frames
            slugs = [s["concept_slug"] for s in manifest["slides"]]
            self.assertLess(slugs.index("packets"), slugs.index("tcp"))
            # each figured node: one section then its frames
            self.assertIn("section", kinds)
            self.assertEqual(kinds.count("frame"), 4)  # 2 nodes x 2 frames

    def test_frame_slide_fields(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = self._topic(base)
            manifest, _ = bv.build_manifest(graph, registry)
            frame = next(s for s in manifest["slides"] if s["kind"] == "frame")
            self.assertTrue(os.path.isabs(frame["image"]))
            self.assertTrue(frame["image"].endswith(".svg"))
            self.assertTrue(frame["caption"])
            self.assertIn("narration", frame["narration"])  # commentary text

    def test_figureless_node_skipped(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", False, ["packets"])
            write_decomp(graph, "packets", True)
            make_figure(registry, "tcp", 1)  # packets has NO figure
            reg.register(registry, "packets", "Packets", "Plain definition of packets.")
            manifest, _ = bv.build_manifest(graph, registry)
            slugs = {s["concept_slug"] for s in manifest["slides"]}
            self.assertIn("tcp", slugs)
            self.assertNotIn("packets", slugs)

    def test_transition_crossfade_within_concept_only(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = self._topic(base)
            manifest, _ = bv.build_manifest(graph, registry)
            for i, s in enumerate(manifest["slides"]):
                if s["transition"] == "crossfade":
                    prev = manifest["slides"][i - 1]
                    self.assertEqual(s["kind"], "frame")
                    self.assertEqual(prev["concept_slug"], s["concept_slug"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest scripts.tests.test_build_video -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build_video'`.

- [ ] **Step 3: Write the manifest builder**

Create `scripts/build_video.py`:

```python
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
import tempfile

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
    return max(MIN_DUR, min(MAX_DUR, secs)) if secs else MIN_DUR


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest scripts.tests.test_build_video -v`
Expected: PASS (all tests in `TestDuration` and `TestManifest`).

- [ ] **Step 5: Commit**

```bash
git add scripts/build_video.py scripts/tests/test_build_video.py
git commit -m "feat(video): manifest builder (ordering, slide kinds, durations)"
```

---

## Task 3: script.md and captions.srt writers

**Files:**
- Modify: `scripts/build_video.py`
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: Add failing tests**

Append to `scripts/tests/test_build_video.py` (before the `if __name__` line):

```python
class TestScriptAndCaptions(unittest.TestCase):
    def _manifest(self, base):
        graph = os.path.join(base, "g")
        registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", True)
        make_figure(registry, "tcp", 2)
        manifest, _ = bv.build_manifest(graph, registry)
        return manifest

    def test_srt_timestamp_format(self):
        self.assertEqual(bv._srt_timestamp(0), "00:00:00,000")
        self.assertEqual(bv._srt_timestamp(3661.5), "01:01:01,500")

    def test_captions_sequential_and_increasing(self):
        with tempfile.TemporaryDirectory() as base:
            manifest = self._manifest(base)
            out = os.path.join(base, "captions.srt")
            bv.write_captions(manifest, out)
            text = open(out, encoding="utf-8").read()
            blocks = text.strip().split("\n\n")
            self.assertEqual(len(blocks), len(manifest["slides"]))
            self.assertTrue(blocks[0].startswith("1\n"))
            self.assertIn("-->", blocks[0])

    def test_script_has_concept_headings(self):
        with tempfile.TemporaryDirectory() as base:
            manifest = self._manifest(base)
            out = os.path.join(base, "script.md")
            bv.write_script(manifest, out)
            text = open(out, encoding="utf-8").read()
            self.assertIn("## ", text)
            self.assertIn("narration", text.lower())
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest scripts.tests.test_build_video.TestScriptAndCaptions -v`
Expected: FAIL — `AttributeError: module 'build_video' has no attribute '_srt_timestamp'`.

- [ ] **Step 3: Implement the writers**

Append to `scripts/build_video.py`:

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest scripts.tests.test_build_video -v`
Expected: PASS (all tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/build_video.py scripts/tests/test_build_video.py
git commit -m "feat(video): script.md + captions.srt writers"
```

---

## Task 4: Stage SVG (16:9 composed slide)

**Files:**
- Modify: `scripts/build_video.py`
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: Add failing tests**

Append to `scripts/tests/test_build_video.py`:

```python
import xml.etree.ElementTree as ET  # noqa: E402  (top of file is fine too)


class TestStageSvg(unittest.TestCase):
    def _frame_slide(self, base):
        graph = os.path.join(base, "g")
        registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", True)
        make_figure(registry, "tcp", 1)
        manifest, _ = bv.build_manifest(graph, registry)
        return next(s for s in manifest["slides"] if s["kind"] == "frame")

    def test_frame_stage_embeds_nested_svg_and_caption(self):
        with tempfile.TemporaryDirectory() as base:
            slide = self._frame_slide(base)
            svg = bv.stage_svg(slide, bv.STAGE)
            self.assertTrue(svg.lstrip().startswith("<svg"))
            self.assertIn(f'viewBox="0 0 {bv.STAGE["width"]} {bv.STAGE["height"]}"', svg)
            self.assertEqual(svg.count("<svg"), 2)  # stage + nested figure
            self.assertIn(slide["caption"], svg)
            ET.fromstring(svg)  # well-formed XML

    def test_title_card_is_well_formed_text_only(self):
        slide = bv._slide("title", None, None, "TCP", "Some narration here.", 150, "cut")
        svg = bv.stage_svg(slide, bv.STAGE)
        self.assertEqual(svg.count("<svg"), 1)
        self.assertIn("TCP", svg)
        ET.fromstring(svg)
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest scripts.tests.test_build_video.TestStageSvg -v`
Expected: FAIL — `AttributeError: ... has no attribute 'stage_svg'`.

- [ ] **Step 3: Implement `stage_svg`**

Append to `scripts/build_video.py`. Note: the figure SVG is embedded by stripping its XML declaration and nesting it inside an `<svg x y width height>` positioned element; rsvg/cairosvg honor nested `<svg>` with its own viewBox.

```python
def _read_inner_svg(path):
    """Return a frame SVG's markup with any <?xml ...?> / DOCTYPE prolog removed."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    idx = text.find("<svg")
    return text[idx:] if idx >= 0 else text


def _esc(text):
    return html.escape(text or "", quote=True)


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
        inner = _read_inner_svg(slide["image"])
        # nest the frame; preserveAspectRatio centers it within the content box
        nested = inner.replace(
            "<svg", f'<svg x="{pad}" y="{top_h}" width="{inner_w}" '
                    f'height="{inner_h}" preserveAspectRatio="xMidYMid meet"', 1)
        parts.append(nested)
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
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest scripts.tests.test_build_video -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_video.py scripts/tests/test_build_video.py
git commit -m "feat(video): stage_svg composes 16:9 slides (nested figure + caption)"
```

---

## Task 5: HTML player

**Files:**
- Create: `.claude/skills/concept-illustrator/assets/video.template.html`
- Modify: `scripts/build_video.py`
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: Create the template**

Create `.claude/skills/concept-illustrator/assets/video.template.html`. The script reads `window.__MANIFEST__` (injected) and the inlined SVGs (injected) and plays them. `{{MANIFEST_JSON}}` and `{{SLIDES_HTML}}` are the only substitution points.

```html
<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Video</title>
<style>
:root{color-scheme:light dark}
body{margin:0;font-family:-apple-system,"Segoe UI",Roboto,system-ui,sans-serif;
     background:#0f1115;color:#e8e8e8;display:flex;flex-direction:column;
     align-items:center;min-height:100vh}
#stage{position:relative;width:min(96vw,1100px);aspect-ratio:16/9;background:#15181f;
       border-radius:10px;overflow:hidden;margin-top:1.2rem}
.slide{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;
       justify-content:center;opacity:0;transition:opacity .5s ease;padding:2.5rem;box-sizing:border-box}
.slide.show{opacity:1}
.slide.cut{transition:none}
.slide svg{max-width:100%;max-height:70%;height:auto}
.card{font-size:2.4rem;text-align:center;line-height:1.3}
.cap{position:absolute;bottom:1.1rem;left:0;right:0;text-align:center;font-size:1.05rem;
     color:#cfd2d8;padding:0 2rem}
#bar{width:min(96vw,1100px);display:flex;gap:.8rem;align-items:center;margin:.8rem 0}
#prog{flex:1;height:5px;background:#2a2d36;border-radius:3px;overflow:hidden}
#prog>div{height:100%;width:0;background:#5DCAA5}
button{font:inherit;background:#23262e;color:#e8e8e8;border:1px solid #3a3d46;
       border-radius:6px;padding:.35rem .8rem;cursor:pointer}
label{font-size:.9rem;color:#aab;display:flex;gap:.35rem;align-items:center}
</style></head><body>
<div id="stage">{{SLIDES_HTML}}</div>
<div id="bar">
  <button id="play">⏸ Pause</button>
  <button id="prev">←</button><button id="next">→</button>
  <div id="prog"><div></div></div>
  <span id="count"></span>
  <label><input type="checkbox" id="tts"> 🔊 narrate</label>
</div>
<script>
var M=window.__MANIFEST__={{MANIFEST_JSON}};
var slides=[].slice.call(document.querySelectorAll('.slide'));
var i=0,playing=true,timer=null,progRAF=null,start=0;
var progEl=document.querySelector('#prog>div'),count=document.getElementById('count');
function speak(t){try{var u=new SpeechSynthesisUtterance(t);u.onend=function(){if(playing&&tts.checked)next();};speechSynthesis.cancel();speechSynthesis.speak(u);}catch(e){}}
function show(n){
  slides.forEach(function(s){s.classList.remove('show');});
  i=(n+slides.length)%slides.length;
  var s=slides[i];s.classList.toggle('cut',M.slides[i].transition!=='crossfade');
  s.classList.add('show');
  count.textContent=(i+1)+' / '+slides.length;
  clearTimeout(timer);start=performance.now();
  var dur=M.slides[i].duration_s*1000;
  if(tts.checked){speak(M.slides[i].narration);}
  else if(playing){timer=setTimeout(next,dur);}
  animateProg(dur);
}
function animateProg(dur){cancelAnimationFrame(progRAF);
  (function step(){var p=Math.min(1,(performance.now()-start)/dur);progEl.style.width=(p*100)+'%';
    if(p<1&&playing)progRAF=requestAnimationFrame(step);})();}
function next(){show(i+1);}function prev(){show(i-1);}
var tts=document.getElementById('tts');
document.getElementById('next').onclick=next;
document.getElementById('prev').onclick=prev;
document.getElementById('play').onclick=function(){playing=!playing;
  this.textContent=playing?'⏸ Pause':'▶ Play';if(playing)show(i);else{clearTimeout(timer);speechSynthesis.cancel();}};
show(0);
</script></body></html>
```

- [ ] **Step 2: Add failing test**

Append to `scripts/tests/test_build_video.py`:

```python
class TestPlayer(unittest.TestCase):
    def test_player_contains_manifest_and_controls(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", True)
            make_figure(registry, "tcp", 2)
            manifest, _ = bv.build_manifest(graph, registry)
            out = os.path.join(base, "video.html")
            bv.build_player(manifest, bv.PLAYER_TEMPLATE, out)
            text = open(out, encoding="utf-8").read()
            self.assertIn("window.__MANIFEST__", text)
            self.assertIn('id="play"', text)
            self.assertIn('class="slide', text)
            self.assertNotIn("{{MANIFEST_JSON}}", text)
            self.assertNotIn("{{SLIDES_HTML}}", text)
            # one .slide div per manifest slide
            self.assertEqual(text.count('class="slide'), len(manifest["slides"]))
            # frame SVGs are inlined
            self.assertIn("<svg", text)
```

- [ ] **Step 3: Run to verify failure**

Run: `python3 -m unittest scripts.tests.test_build_video.TestPlayer -v`
Expected: FAIL — `AttributeError: ... 'build_player'`.

- [ ] **Step 4: Implement `build_player`**

Append to `scripts/build_video.py`. The player inlines the raw figure SVG for `frame` slides (crisp, selectable text) and renders text cards as HTML.

```python
def _slide_html(slide):
    if slide["kind"] == "frame":
        inner = _read_inner_svg(slide["image"])
        body = inner + f'<p class="cap">{_esc(slide["caption"])}</p>'
    else:
        body = f'<div class="card">{_esc(slide["caption"])}</div>'
    cls = "slide" + ("" if slide["transition"] == "crossfade" else " cut")
    return f'<div class="{cls}">{body}</div>'


def build_player(manifest, template_path, out_path):
    with open(template_path, encoding="utf-8") as fh:
        template = fh.read()
    slides_html = "\n".join(_slide_html(s) for s in manifest["slides"])
    # store only lightweight fields in the injected manifest (no SVG text)
    light = dict(manifest)
    light["slides"] = [{k: s[k] for k in ("kind", "concept_slug", "caption",
                                          "narration", "duration_s", "transition")}
                       for s in manifest["slides"]]
    html_out = (template
                .replace("{{SLIDES_HTML}}", slides_html)
                .replace("{{MANIFEST_JSON}}", json.dumps(light)))
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html_out)
    return out_path
```

- [ ] **Step 5: Run to verify pass**

Run: `python3 -m unittest scripts.tests.test_build_video -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/concept-illustrator/assets/video.template.html scripts/build_video.py scripts/tests/test_build_video.py
git commit -m "feat(video): self-contained HTML player (inline SVGs, TTS toggle)"
```

---

## Task 6: MP4 renderer (ffmpeg + say, with fallback)

**Files:**
- Modify: `scripts/build_video.py`
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: Add failing tests**

Append to `scripts/tests/test_build_video.py`:

```python
import shutil  # noqa: E402
from unittest import mock  # noqa: E402


class TestMp4Fallback(unittest.TestCase):
    def _manifest(self, base):
        graph = os.path.join(base, "g")
        registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", True)
        make_figure(registry, "tcp", 2)
        manifest, _ = bv.build_manifest(graph, registry)
        return manifest

    def test_missing_ffmpeg_skips_mp4(self):
        with tempfile.TemporaryDirectory() as base:
            manifest = self._manifest(base)
            with mock.patch("build_video.shutil.which", return_value=None):
                path, notes = bv.render_mp4(manifest, base, bv.STAGE)
            self.assertIsNone(path)
            self.assertTrue(any("ffmpeg" in n for n in notes))

    def test_missing_say_renders_silent_with_note(self):
        # ffmpeg present, `say`/`ffprobe` absent -> silent MP4, no audio mux.
        with tempfile.TemporaryDirectory() as base:
            manifest = self._manifest(base)

            def which(cmd):
                return "/usr/bin/ffmpeg" if cmd == "ffmpeg" else None

            with mock.patch("build_video.shutil.which", side_effect=which), \
                 mock.patch("build_video.render.export_png",
                            side_effect=lambda s, p, **k: open(p, "wb").close() or p), \
                 mock.patch("build_video.subprocess.run",
                            return_value=mock.Mock(returncode=0)) as run:
                path, notes = bv.render_mp4(manifest, base, bv.STAGE)
            self.assertEqual(path, os.path.join(base, "video.mp4"))
            self.assertTrue(any("silent" in n.lower() for n in notes))
            # no `say` invocations when say is unavailable
            self.assertFalse(any(c.args and c.args[0] and c.args[0][0] == "say"
                                 for c in run.call_args_list))

    def test_say_present_drives_audio_mux(self):
        # ffmpeg + say present -> say segments produced and an audio mux runs.
        with tempfile.TemporaryDirectory() as base:
            manifest = self._manifest(base)

            def which(cmd):
                return f"/usr/bin/{cmd}" if cmd in ("ffmpeg", "say") else None

            with mock.patch("build_video.shutil.which", side_effect=which), \
                 mock.patch("build_video.render.export_png",
                            side_effect=lambda s, p, **k: open(p, "wb").close() or p), \
                 mock.patch("build_video.subprocess.run",
                            return_value=mock.Mock(returncode=0)) as run:
                path, notes = bv.render_mp4(manifest, base, bv.STAGE)
            self.assertEqual(path, os.path.join(base, "video.mp4"))
            self.assertTrue(any(c.args and c.args[0] and c.args[0][0] == "say"
                                for c in run.call_args_list))

    @unittest.skipUnless(shutil.which("ffmpeg") and
                         (shutil.which("rsvg-convert") or _has_cairosvg()),
                         "needs ffmpeg + an SVG rasterizer")
    def test_real_mp4_smoke(self):
        with tempfile.TemporaryDirectory() as base:
            manifest = self._manifest(base)
            path, _ = bv.render_mp4(manifest, base, bv.STAGE)
            self.assertTrue(path and os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)
```

Add this helper near the top of the test file (after the imports), used by the smoke-test guard:

```python
def _has_cairosvg():
    try:
        import cairosvg  # noqa: F401
        return True
    except ImportError:
        return False
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest scripts.tests.test_build_video.TestMp4Fallback -v`
Expected: FAIL — `AttributeError: ... 'render_mp4'`.

- [ ] **Step 3: Implement `render_mp4`**

Append to `scripts/build_video.py`. Rasterize each stage SVG, speak each narration with `say` (when present), set each slide's effective duration to its spoken-audio length, build a silent video by holding each PNG, build a per-slide-padded audio track, and mux. **Transitions are hard cuts in v1** (xfade crossfade is the one deferred item — see the handoff note).

```python
def _png_for_slides(manifest, frames_dir, stage):
    """Write a stage PNG per slide; return ordered list of png paths."""
    os.makedirs(frames_dir, exist_ok=True)
    pngs = []
    for n, slide in enumerate(manifest["slides"]):
        svg_path = os.path.join(frames_dir, f"slide-{n:03d}.svg")
        with open(svg_path, "w", encoding="utf-8") as fh:
            fh.write(stage_svg(slide, stage))
        png_path = os.path.join(frames_dir, f"slide-{n:03d}.png")
        render.export_png(svg_path, png_path, scale=1.0)
        pngs.append(png_path)
    return pngs


def _probe_duration(path):
    """Seconds for a media file via ffprobe, or None when unavailable."""
    if not shutil.which("ffprobe"):
        return None
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, check=True).stdout.strip()
        return float(out)
    except (subprocess.CalledProcessError, ValueError):
        return None


def _say_segment(text, out_aiff):
    """Speak text to an AIFF via macOS `say`; return path or None on failure."""
    if not (text or "").strip():
        return None
    try:
        subprocess.run(["say", "-o", out_aiff, text], check=True)
        return out_aiff
    except subprocess.CalledProcessError:
        return None


def _effective_durations(manifest, segments):
    """Per-slide seconds: spoken-audio length (when present) else computed."""
    durs = []
    for slide, seg in zip(manifest["slides"], segments):
        probed = _probe_duration(seg) if seg else None
        durs.append(max(MIN_TTS_DUR, probed) if probed else slide["duration_s"])
    return durs


def _build_silent_video(pngs, durations, out_path):
    listfile = out_path + ".concat.txt"
    lines = []
    for png, dur in zip(pngs, durations):
        lines.append(f"file '{png}'")
        lines.append(f"duration {dur:.3f}")
    lines.append(f"file '{pngs[-1]}'")  # concat demuxer needs the last frame repeated
    with open(listfile, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                    "-vf", "fps=30,format=yuv420p", out_path], check=True)
    return out_path


def _build_audio_track(segments, durations, work_dir, out_path):
    """One clip per slide padded/sized to its duration (spoken or silence)."""
    clips = []
    for n, (seg, dur) in enumerate(zip(segments, durations)):
        clip = os.path.join(work_dir, f"aud-{n:03d}.wav")
        if seg:
            subprocess.run(["ffmpeg", "-y", "-i", seg, "-af", "apad",
                            "-t", f"{dur:.3f}", "-ar", "44100", "-ac", "2", clip],
                           check=True)
        else:
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                            "anullsrc=r=44100:cl=stereo", "-t", f"{dur:.3f}",
                            "-ar", "44100", "-ac", "2", clip], check=True)
        clips.append(clip)
    listfile = out_path + ".concat.txt"
    with open(listfile, "w", encoding="utf-8") as fh:
        fh.write("\n".join(f"file '{c}'" for c in clips) + "\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                    "-c", "copy", out_path], check=True)
    return out_path


def render_mp4(manifest, out_dir, stage):
    """Return (mp4_path|None, notes). Honest fallback when tools are missing."""
    notes = []
    if not shutil.which("ffmpeg"):
        notes.append("ffmpeg not found — MP4 skipped (HTML player still produced).")
        return None, notes
    frames_dir = os.path.join(out_dir, "frames")
    pngs = _png_for_slides(manifest, frames_dir, stage)
    have_say = bool(shutil.which("say"))
    if not have_say:
        notes.append("`say` not found — rendering a silent MP4 with burned-in captions.")
    segments = [
        _say_segment(s["narration"], os.path.join(frames_dir, f"seg-{n:03d}.aiff"))
        if have_say else None
        for n, s in enumerate(manifest["slides"])]
    durations = _effective_durations(manifest, segments)
    silent = os.path.join(frames_dir, "silent.mp4")
    _build_silent_video(pngs, durations, silent)
    mp4_path = os.path.join(out_dir, "video.mp4")
    if any(segments):
        audio = _build_audio_track(segments, durations, frames_dir,
                                   os.path.join(frames_dir, "audio.wav"))
        subprocess.run(["ffmpeg", "-y", "-i", silent, "-i", audio,
                        "-c:v", "copy", "-c:a", "aac", "-shortest", mp4_path],
                       check=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-i", silent, "-c", "copy", mp4_path],
                       check=True)
    return mp4_path, notes
```

The MP4 honors the chosen audio decision: `say` narration with TTS-driven slide durations and a silent-with-captions fallback. The **only** deferred item is the `xfade` crossfade *between* frames (v1 uses hard cuts); record that in the article (Step 5).

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest scripts.tests.test_build_video -v`
Expected: PASS.

- [ ] **Step 5: Update the article for the MP4 v1 scope**

In `knowledge/concepts/dummies-notes/video-engine.md`, under the MP4 bullet, append:

```markdown

v1 MP4: per-slide stage PNG held for its duration, `say` narration muxed in (slide
duration follows the spoken-audio length), silent-with-captions fallback when `say`
is absent. Slide-to-slide transitions are hard cuts in v1; `xfade` crossfade is
deferred (the HTML player remains the primary crossfade-animated target).
```

- [ ] **Step 6: Commit**

```bash
git add scripts/build_video.py scripts/tests/test_build_video.py knowledge/concepts/dummies-notes/video-engine.md
git commit -m "feat(video): MP4 renderer (concat) with ffmpeg/say detection + fallback"
```

---

## Task 7: CLI orchestration (`build` + `main`)

**Files:**
- Modify: `scripts/build_video.py`
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: Add failing tests**

Append to `scripts/tests/test_build_video.py`:

```python
class TestBuildAndCli(unittest.TestCase):
    def _topic(self, base):
        graph = os.path.join(base, "g")
        registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", False, ["packets"])
        write_decomp(graph, "packets", True)
        make_figure(registry, "tcp", 2)
        make_figure(registry, "packets", 2)
        return graph, registry

    def test_build_html_writes_expected_files(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = self._topic(base)
            out = os.path.join(base, "out")
            result, issues = bv.build(graph, registry, out, fmt="html", wpm=150)
            self.assertEqual([m for lvl, m in issues if lvl == "ERROR"], [])
            vdir = os.path.join(out, "video")
            for name in ("manifest.json", "script.md", "captions.srt", "video.html"):
                self.assertTrue(os.path.exists(os.path.join(vdir, name)), name)
            self.assertFalse(os.path.exists(os.path.join(vdir, "video.mp4")))

    def test_cli_exit_zero(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = self._topic(base)
            out = os.path.join(base, "out")
            rc = bv.main([graph, "--registry", registry, "--out", out, "--format", "html"])
            self.assertEqual(rc, 0)

    def test_cli_bad_graph_exit_one(self):
        with tempfile.TemporaryDirectory() as base:
            rc = bv.main([os.path.join(base, "nope"), "--out", os.path.join(base, "o")])
            self.assertEqual(rc, 1)
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest scripts.tests.test_build_video.TestBuildAndCli -v`
Expected: FAIL — `AttributeError: ... 'build'`.

- [ ] **Step 3: Implement `build` and `main`**

Append to `scripts/build_video.py`:

```python
def build(graph_dir, registry_root, out_dir, fmt="html", wpm=DEFAULT_WPM, stage=STAGE):
    manifest, issues = build_manifest(graph_dir, registry_root, wpm, stage)
    if manifest is None:
        return None, issues
    video_dir = os.path.join(out_dir, "video")
    os.makedirs(video_dir, exist_ok=True)
    with open(os.path.join(video_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    write_script(manifest, os.path.join(video_dir, "script.md"))
    write_captions(manifest, os.path.join(video_dir, "captions.srt"))
    notes = []
    if fmt in ("html", "both"):
        build_player(manifest, PLAYER_TEMPLATE, os.path.join(video_dir, "video.html"))
    if fmt in ("mp4", "both"):
        _, mp4_notes = render_mp4(manifest, video_dir, stage)
        notes.extend(mp4_notes)
    result = {"video_dir": video_dir, "slides": len(manifest["slides"]), "notes": notes}
    return result, issues


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="build_video",
        description="build output/<topic>/video/ from a concept graph")
    parser.add_argument("graph_dir")
    parser.add_argument("--registry", default=DEFAULT_ROOT)
    parser.add_argument("--out", required=True)
    parser.add_argument("--format", choices=("html", "mp4", "both"), default="html")
    parser.add_argument("--wpm", type=int, default=DEFAULT_WPM)
    args = parser.parse_args(argv)
    try:
        result, issues = build(args.graph_dir, args.registry, args.out,
                               fmt=args.format, wpm=args.wpm)
    except ValueError as exc:
        print(f"ERROR  {exc}")
        return 1
    for level, message in issues:
        print(f"{level:<6} {message}")
    if result is None:
        return 1
    for note in result["notes"]:
        print(f"NOTE   {note}")
    print(f"OK     built {result['slides']} slide(s) -> {result['video_dir']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the full module test suite**

Run: `python3 -m unittest scripts.tests.test_build_video -v`
Expected: PASS (all classes).

- [ ] **Step 5: Smoke-test on a real deliverable**

Run: `python3 scripts/build_video.py output/tcp-connection-lifecycle/graph --out output/tcp-connection-lifecycle --format html`
Expected: prints `OK built N slide(s) -> output/tcp-connection-lifecycle/video`; `output/tcp-connection-lifecycle/video/video.html` opens in a browser and auto-plays the lesson.

- [ ] **Step 6: Commit**

```bash
git add scripts/build_video.py scripts/tests/test_build_video.py
git commit -m "feat(video): build() orchestration + CLI (--format, --wpm)"
```

---

## Task 8: Workflow `Video` phase (opt-in)

**Files:**
- Modify: `.claude/workflows/dummies-notes.js`
- Modify: `knowledge/concepts/dummies-notes/orchestration-workflow.md`
- Modify: `knowledge/log.md`

- [ ] **Step 1: Parse the new args**

In `.claude/workflows/dummies-notes.js`, after line 21 (`const MAX_NODES = ...`), add:

```javascript
const MAKE_VIDEO = !!(A && A.makeVideo)
const VIDEO_FORMAT = (A && A.videoFormat) || 'html'
```

- [ ] **Step 2: Declare the meta phase**

In the `meta.phases` array, after the `Assemble` entry and before `ChainReview`, add:

```javascript
    { title: 'Video', detail: 'optional: build the narrated animated slideshow (flag-gated)' },
```

Also update `meta.whenToUse` to mention the flags — replace it with:

```javascript
  whenToUse: 'args: {topic: string, definition?: string, maxDepth?: number, maxNodes?: number, makeVideo?: boolean, videoFormat?: "html"|"mp4"|"both"}. Run produces output/<topic>/index.html + map.html; with makeVideo it also builds output/<topic>/video/.',
```

- [ ] **Step 3: Insert the Video phase block**

In `.claude/workflows/dummies-notes.js`, immediately after the Assemble guard (the line `if (!assembled || !assembled.assemble_clean) throw new Error('assembly failed')`) and before the `// ---- Phase 6: end-to-end chain review` comment, insert:

```javascript
// ---- Phase: optional narrated video (flag-gated) ----------------------------
let videoResult = null
if (MAKE_VIDEO) {
  phase('Video')
  const VIDEO_SCHEMA = {
    type: 'object',
    properties: {
      video_dir: { type: 'string' },
      video_clean: { type: 'boolean' },
      notes: { type: 'string' },
    },
    required: ['video_dir', 'video_clean'],
  }
  videoResult = await agent(
    `Run from the repo root: python3 scripts/build_video.py output/${rootSlug}/graph ` +
    `--out output/${rootSlug} --format ${VIDEO_FORMAT}\n` +
    'It must exit 0 (prints "OK built N slide(s) ..."). Return video_dir = ' +
    `output/${rootSlug}/video, video_clean = (exit code was 0), and notes = any NOTE ` +
    'lines (e.g. ffmpeg/say missing fallbacks), joined with "; ".',
    { label: 'build-video', phase: 'Video', schema: VIDEO_SCHEMA })
  if (videoResult && !videoResult.video_clean) {
    log(`video build reported issues — see output/${rootSlug}/video`)
  } else if (videoResult && videoResult.notes) {
    log(`video built with notes: ${videoResult.notes}`)
  }
}
```

- [ ] **Step 4: Add the video path to the return object**

In the final `return { ... }` object, after the `chain_gaps:` line, add:

```javascript
  video_dir: videoResult ? videoResult.video_dir : null,
```

- [ ] **Step 5: Update the orchestration article**

In `knowledge/concepts/dummies-notes/orchestration-workflow.md`, add a short subsection documenting the opt-in `Video` phase (flags `makeVideo` default false, `videoFormat` default `"html"`; runs after Assemble; calls `scripts/build_video.py`; links to [[video-engine]]). Bump its `updated:` to `2026-06-11`.

- [ ] **Step 6: Append a log entry**

Append to `knowledge/log.md`:

```markdown
- 2026-06-11 — Phase 6: wired opt-in `Video` phase into dummies-notes.js (makeVideo/videoFormat); runs build_video.py after Assemble. Default runs unchanged.
```

- [ ] **Step 7: Verify the workflow file parses**

Run: `node --check .claude/workflows/dummies-notes.js`
Expected: no output, exit 0 (syntax OK).

- [ ] **Step 8: Commit**

```bash
git add .claude/workflows/dummies-notes.js knowledge/concepts/dummies-notes/orchestration-workflow.md knowledge/log.md
git commit -m "feat(video): opt-in Video phase in the dummies-notes workflow"
```

---

## Task 9: Full regression + drift check

**Files:** none (verification only)

- [ ] **Step 1: Run every test suite**

Run:
```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'
python3 -m unittest discover -s .claude/skills/concept-decompose/scripts/tests -p 'test_*.py'
```
Expected: all PASS (no regressions; new `test_build_video` included in the first).

- [ ] **Step 2: Validate knowledge + drift**

Run:
```bash
python3 scripts/validate-articles
python3 scripts/drift-check --warn-only
```
Expected: `validate-articles` exits 0; `drift-check` reports the new `build_video.py`/`video.template.html`/workflow paths mapped to their articles with no unexplained drift.

- [ ] **Step 3: Final commit if anything was adjusted**

If Steps 1–2 surfaced fixes, commit them:
```bash
git add -A
git commit -m "chore(video): regression + drift reconciliation"
```
Otherwise note "no changes — clean" and finish.

---

## Notes for the implementer

- **Drift discipline:** never use `git commit --no-verify`. If the pre-commit hook blocks because a mapped code path changed without an article update, append the relevant detail to `knowledge/concepts/dummies-notes/video-engine.md` (or `orchestration-workflow.md` for workflow changes) and re-stage — that is the same-task rule, not an obstacle.
- **Zero-dep default:** the HTML path must not import any third-party package. Only the MP4 path may shell out to `ffmpeg`/`say`, and only behind runtime detection.
- **Run tests from the repo root** so the `sys.path` insertions in `build_video.py` resolve `assemble`, `concept_registry`, and `render`.
