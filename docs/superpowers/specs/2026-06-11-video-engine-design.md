# Video engine — design spec

**Date:** 2026-06-11
**Status:** approved (brainstorming) — ready for implementation plan
**Phase:** 6 (educational video / animated slideshow from figures)

## Goal

Turn an assembled topic deliverable (`output/<topic>/`) into an **educational
video**: one continuous narrated, animated slideshow for the whole topic, built
from the figures we already generate and their per-frame `commentary`. Two
render targets, selectable so the user can compare them: a zero-dependency
self-contained **HTML player** (screen-record → YouTube, or present live) and an
opt-in **MP4** (ffmpeg + built-in TTS). A slide-deck format is explicitly out of
scope for this phase.

## Decisions locked during brainstorming

1. **Render targets:** HTML player first, MP4 second, **switchable via a
   `--format html|mp4|both` flag** so the two can be compared. No reveal.js /
   PPTX slide deck in this phase.
2. **Video unit:** **one continuous video per topic** (all figured nodes
   stitched in bottom-up teaching order). No per-figure reusable clips in v1.
3. **Audio:** **captions always**; spoken narration is *optional* and uses only
   built-in engines — the browser Web Speech API in the HTML player, macOS
   `say` for the MP4. No paid/cloud TTS, no new heavy deps. Honest fallback to
   silent-with-captions when an engine is missing. `script.md` + `captions.srt`
   ship every run for human voiceover.
4. **Architecture:** a standalone deterministic `scripts/build_video.py`
   (sibling to `assemble.py`), reusing `assemble.py` and `render.py`; plus an
   **opt-in, flag-gated `Video` phase** in the workflow. Not a new skill, not
   folded into `render.py`.
5. **Narration connective tissue** (title/section/closing text) is generated
   **deterministically** from fields we already have; an LLM polish pass is
   deferred (out of v1 scope).

## Non-goals (v1)

- Per-figure reusable video clips (only whole-topic video).
- Slide-deck export (reveal.js / PPTX / speaker-notes).
- Cloud/paid TTS or any LLM call in the standalone script.
- Element-level motion tweening. Within-figure motion is the crossfade between
  consecutive frames only — the frame-consistency rule (shared viewBox, fixed
  element positions) already makes that read as animation.
- Figure invalidation/versioning (a pre-existing open item, unchanged here).

## Reused building blocks (no duplication)

From `scripts/assemble.py` (import directly):
- `load_full_graph(graph_dir)` → `{slug: {name, definition, atomic,
  mechanism_figurable, prerequisites}}`
- `find_root(nodes)`, `topo_order(nodes)` — bottom-up order (prereqs first)
- `classify_prereqs(nodes, registry_root)` → `(covered, frontier)`
- `load_figure(figure_dir)` → `[(svg_text, caption)]` or `None`
- `_figure_dir_for(entry, registry_root)`

From `scripts/concept_registry.py`: `lookup(registry_root, slug)`, `DEFAULT_ROOT`.

From `.claude/skills/concept-illustrator/scripts/render.py`:
- `export_png(svg_path, png_path, theme="light", scale=2.0)` — rasterize via
  rsvg-convert or cairosvg. **Caveat:** static rasterizers do not evaluate
  `@media (prefers-color-scheme)`, so MP4 frames render at a single fixed theme
  (light). This is acceptable and must be stated in the output.

Figure data already on disk: each figure dir has `figure.json` with
`frames:[{file, caption, runbook, commentary}]`. **`caption`** is the short
on-screen subtitle; **`commentary`** is the simple-sentence narration. These are
the two text layers the video consumes — no new authoring per run.

## Output layout

```
output/<topic>/video/
  manifest.json     # ordered slides — the single source of truth
  script.md         # per-concept narration in reading order (human voiceover)
  captions.srt      # timed captions from narration + cumulative durations
  video.html        # self-contained narrated auto-advancing player (always)
  video.mp4         # only when --format mp4|both AND ffmpeg present
  frames/           # rasterized stage PNGs (mp4 path only)
```

## Component 1 — the manifest

`manifest.json`:

```json
{
  "topic": "tcp-connection-lifecycle",
  "title": "TCP connection lifecycle",
  "definition": "How two computers open, use, and close a reliable connection.",
  "stage": {"width": 1280, "height": 720},
  "reading_rate_wpm": 150,
  "slides": [
    {
      "kind": "title",
      "concept_slug": null,
      "image": null,
      "caption": "TCP connection lifecycle",
      "narration": "This is how two computers open a reliable connection, use it, and close it cleanly.",
      "duration_s": 5.0,
      "transition": "cut"
    },
    {
      "kind": "section",
      "concept_slug": "data-packets",
      "image": null,
      "caption": "Data packets",
      "narration": "First, a building block. Messages travel in small chunks called packets.",
      "duration_s": 4.2,
      "transition": "cut"
    },
    {
      "kind": "frame",
      "concept_slug": "data-packets",
      "image": "...registry path to frame-01.svg...",
      "caption": "A message is split into numbered packets.",
      "narration": "A big message does not travel in one piece. It is split into small numbered packets...",
      "duration_s": 8.1,
      "transition": "crossfade"
    }
  ]
}
```

**Slide kinds:**
- `title` — opens the video: topic name + definition. No figure.
- `section` — one per figured node, in bottom-up order: concept name +
  one-line definition (lead-in card). No figure.
- `frame` — one per figure frame: `image` = the frame SVG, `caption` =
  `frame.caption`, `narration` = `frame.commentary`.
- `closing` — wrap card.

**Ordering:** `topo_order(nodes)`. For each node in order **that has a loadable
figure**, emit a `section` slide then its `frame` slides. Nodes without a figure
(intermediate, frontier, or figure-pending) are **skipped** to keep the video
visual. A `title` slide is prepended and a `closing` slide appended.

**Duration:** `duration_s = clamp(words / (wpm/60), 2.5, 18.0)`, where `words`
is the narration word count and `wpm` defaults to 150 (configurable via
`--wpm`). For the MP4 path *with TTS present*, the slide duration is replaced by
the actual spoken-audio length (clamped to a small minimum) so audio and video
stay in sync.

**Transition:** `crossfade` between consecutive `frame` slides of the **same**
concept (the consistent-frame rule makes this read as motion); `cut` everywhere
else (into/out of title, section, closing, and between different concepts).

## Component 2 — narration assembly (deterministic)

- `frame` narration = `commentary` verbatim.
- `title` narration = templated from topic title + definition.
- `section` narration = templated from concept name + definition (and the
  prerequisite `why` when available from the parent edge).
- `closing` narration = a fixed templated wrap referencing the topic title.

No LLM, no network — byte-reproducible for the same graph + figures.

## Component 3 — stage SVG (unifies both renderers)

`stage_svg(slide, stage)` composes a single 16:9 SVG (default 1280×720):
- concept label (top),
- the figure SVG **nested and centered** (`<svg>` within `<svg>`; the frame
  keeps its own `viewBox="0 0 680 H"`), scaled to fit,
- a caption bar (bottom) with `slide.caption`.

`title` / `section` / `closing` slides are generated as their own simple stage
SVGs (centered text on the stage). Result: **every slide is exactly one SVG**.

- **MP4 path** rasterizes each stage SVG with `export_png` → `frames/NNN.png`
  (captions baked in; fixed light theme per the rasterizer caveat).
- **HTML path** does *not* use the stage SVG; it lays out the raw figure SVG +
  live caption text in HTML (crisp, selectable, and the text drives Web Speech
  TTS). One layout concept, two consumers.

## Component 4 — HTML player (`video.html`, default, zero-dep)

Self-contained single file (inlines every figure SVG, the way `assemble`
inlines frames). Behaviour:
- Auto-advances on `duration_s`; **crossfade** transitions via opacity, **cut**
  transitions instant.
- Caption bar, progress bar, play/pause, prev/next.
- A 🔊 toggle speaks `narration` via the Web Speech API
  (`window.speechSynthesis`). When speech is on, advance syncs to the
  `utterance.onend` event instead of the timer; when off, the timer drives it.
- Title/section/closing rendered as styled HTML cards.
- Light/dark via `prefers-color-scheme`, on-brand with the existing deliverable.

The player template lives in the illustrator's `assets/`
(`video.template.html`), filled by `build_video.py` (same pattern as
`slideshow.template.html`).

## Component 5 — MP4 renderer (`--format mp4|both`, opt-in)

1. Rasterize every stage SVG → `frames/NNN.png` via `export_png`.
2. Audio (optional): for each slide with narration, `say -o segNNN.aiff "<text>"`
   (macOS). Measure each segment's length; set that slide's effective duration
   to `max(audio_len, 2.0)`. Concatenate segments into one track aligned to the
   slide timeline.
3. Video: ffmpeg holds each PNG for its effective duration; `xfade` applies
   crossfades where `transition == "crossfade"`, hard cuts otherwise; mux the
   audio track.
4. **Detection & fallback:** `shutil.which("ffmpeg")` and `shutil.which("say")`
   are checked up front. Missing ffmpeg → MP4 is skipped with a clear message
   (HTML still produced). Missing `say` → silent MP4 with burned-in captions,
   stated in the run output. No silent capability gaps.

## Component 6 — script.md and captions.srt (always)

- `script.md` — markdown, one `##` heading per concept in reading order, each
  followed by its narration paragraphs (title/closing as their own sections).
  For a human reading voiceover.
- `captions.srt` — standard SRT: sequential index, `HH:MM:SS,mmm` start/end from
  cumulative `duration_s`, text = `narration` (wrapped to ~2 lines). Usable as
  YouTube captions or a VTT source.

## Component 7 — CLI & workflow integration

CLI:
```
python3 scripts/build_video.py output/<topic>/graph \
    --out output/<topic> [--registry <root>] \
    --format html|mp4|both [--wpm 150]
```
Standalone runs on any existing deliverable so HTML vs MP4 can be compared.

Workflow: an **opt-in, flag-gated `Video` phase** in
`.claude/workflows/dummies-notes.js`. New meta args `makeVideo` (default
`false`) and `videoFormat` (default `"html"`). When `makeVideo` is true, after
the Assemble phase the workflow runs `build_video.py` on the graph. Default runs
are unchanged (no video, no extra cost).

## Component 8 — testing

`scripts/tests/test_build_video.py` (stdlib `unittest`, zero-dep), covering:
- manifest ordering (bottom-up; section-then-frames per figured node; figure-less
  nodes skipped; title first, closing last),
- slide-kind assignment and transition rules (crossfade only within one
  concept's frames),
- duration math (word count / wpm, clamping),
- SRT timestamp formatting and indexing,
- `stage_svg` structure (nested figure svg present, caption text present),
- `--format` selection (html only vs both),
- ffmpeg/`say` absence → documented fallback (mocked `shutil.which`),
- HTML player built and asserted to contain the manifest data + controls.

## Component 9 — knowledge / drift (same-task)

- New article `knowledge/concepts/dummies-notes/video-engine.md` (why
  manifest-first, the two render targets, the audio policy, the rasterizer-theme
  caveat, fallbacks).
- CLAUDE.md "Article mapping" table: add
  `scripts/build_video.py → video-engine.md` and the `video.template.html`
  asset; the workflow `Video` phase maps to the existing
  `orchestration-workflow.md` (note the new phase there).
- `knowledge/log.md` compile entry.
- These land in the **same commits** as the code, per the drift rule.

## Dependencies

- Default (HTML) path: **zero new deps** (stdlib + a static HTML template).
- MP4 path: ffmpeg (video), macOS `say` (voice) — both runtime-detected with
  honest fallback. `export_png` already needs rsvg-convert *or* cairosvg.

## Risks / open questions

- **Nested-SVG rasterization:** rsvg-convert and cairosvg both handle `<svg>`
  nested in `<svg>`; to be confirmed early in implementation. If a rasterizer
  chokes, fall back to embedding the frame as an `<image>` referencing its PNG.
- **xfade timeline math:** ffmpeg `xfade` offsets are cumulative; the segment
  assembly must compute offsets carefully. Covered by an integration smoke test
  guarded on ffmpeg availability (skipped when absent).
- **TTS-driven durations** make the MP4 timeline differ from the HTML timeline
  (which uses computed durations unless speech is on). This is acceptable and
  documented; `captions.srt` is generated from the computed timeline.
