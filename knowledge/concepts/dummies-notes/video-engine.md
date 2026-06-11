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

**Task 2 (manifest builder) shipped.** `build_manifest(graph_dir, registry_root, wpm, stage)` is
implemented and tested. Public constants: `DEFAULT_WPM=150`, `MIN_DUR=2.5`, `MAX_DUR=18.0`,
`MIN_TTS_DUR=2.0`, `STAGE={"width":1280,"height":720}`. `load_frames` reads figure.json and
returns absolute frame paths. Slide dicts carry `kind`, `concept_slug`, `image`, `caption`,
`narration`, `duration_s`, `transition`. 7 tests covering duration clamping, ordering, frame
fields, figureless-node skipping, and crossfade-only-within-concept. Test suite: 67 tests total,
all passing.

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
