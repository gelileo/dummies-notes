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

_REPO = os.path.dirname(_HERE)  # repo root (parent of scripts/)

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
    """Per-slide seconds: spoken-audio length when ffprobe is present, else computed duration_s."""
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
    """One clip per slide sized to its duration: apad extends short speech, -t caps long (or silence)."""
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
    if not manifest.get("slides"):
        return None, ["empty manifest — no slides to render."]
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
    if have_say and not any(segments):
        notes.append("`say` was available but all speech segments failed — MP4 will be silent.")
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


def build(graph_dir, registry_root, out_dir, fmt="html", wpm=DEFAULT_WPM, stage=STAGE):
    manifest, issues = build_manifest(graph_dir, registry_root, wpm, stage)
    if manifest is None:
        return None, issues
    video_dir = os.path.join(out_dir, "video")
    os.makedirs(video_dir, exist_ok=True)
    # On disk, store repo-relative image paths so the committed manifest is portable;
    # the in-memory manifest keeps absolute paths for the renderers below.
    portable = dict(manifest)
    portable["slides"] = [
        dict(s, image=os.path.relpath(s["image"], _REPO)) if s.get("image") else s
        for s in manifest["slides"]
    ]
    with open(os.path.join(video_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(portable, fh, indent=2)
    write_script(manifest, os.path.join(video_dir, "script.md"))
    write_captions(manifest, os.path.join(video_dir, "captions.srt"))
    notes = []
    if fmt in ("html", "both"):
        build_player(manifest, PLAYER_TEMPLATE, os.path.join(video_dir, "video.html"))
    if fmt in ("mp4", "both"):
        _, mp4_notes = render_mp4(manifest, video_dir, stage)
        notes.extend(mp4_notes)
    result = {"video_dir": video_dir, "slides": len(manifest["slides"]), "notes": notes,
              "video_html": os.path.join(video_dir, "video.html") if fmt in ("html", "both") else None}
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
    target = result["video_html"] or result["video_dir"]
    print(f"OK     built {result['slides']} slide(s) -> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
