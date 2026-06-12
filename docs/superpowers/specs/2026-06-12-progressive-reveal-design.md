# Progressive (narration-synced) reveal — design spec

**Date:** 2026-06-12
**Status:** approved (brainstorming) — ready for implementation plan
**Phase:** 7 (in-slide progressive reveal / "dynamic scaffolding")
**Builds on:** Phase 6 video engine (`docs/superpowers/specs/2026-06-11-video-engine-design.md`)

## Goal

Make a figure's elements appear **progressively, one narration beat at a time**, on a single cohesive canvas — boxes rise in, arrows draw with the head glued to the growing tip, the focus element stays bright while earlier ones recede — instead of a whole frame appearing at once. This is the "dynamic scaffolding" style that keeps the viewer's eye on exactly the thing being explained. It must work in **both** the HTML player (smooth, screen-recordable) and the exported **MP4**.

Reference the user studied: a 2D canvas-style explainer that builds boxes/arrows/text out atomically alongside the narration. The brainstorming demo (`reveal-demo-v3`) is the agreed target experience.

## Decisions locked during brainstorming

1. **Target experience** = the v3 demo: per-element reveal on one canvas, one narration beat per element; entrance = fade+rise for shapes, endpoint-geometry draw for arrows (arrowhead stays attached to the tip); earlier elements dim when a new one is the focus (default on, toggleable); pace ≈ 2.4 s/beat (driven by narration length in practice).
2. **Scope** = both render targets: HTML player animates smoothly; MP4 supported.
3. **MP4 fidelity** = **pop per beat** — each element appears at the start of its narration beat and holds (a genuine progressive build, no smooth tween in the MP4). Smooth-tween MP4 is explicitly deferred. The HTML player still tweens smoothly.
4. **Architecture** = Approach 1: reveal-tagged groups *within* frames + per-beat narration. Additive build lives within a frame; mutation/movement stays across frames (the frame-consistency rule). Backward-compatible: untagged figures behave exactly as today. (Approach 2 "one flat additive canvas" rejected — can't represent mutation; Approach 3 "auto-diff frames" rejected — fragile, no intra-frame ordering.)
5. **Second proof figure** = a quicksort frame (the mutation example), alongside the TCP handshake (the additive example).

## Non-goals (v1)

- Smooth tween in the MP4 (pop only).
- Reveal animation inside the `index.html` bottom-up reading explainer — it stays today's simple slideshow. The **video** (HTML player + MP4) is the watch target.
- Camera pan/zoom across the canvas (the reference pans between sections; that is a larger animation system — deferred).
- Auto-retagging all existing figures. Only new figures (via the illustrator) and the two hand-tagged proof figures get reveal metadata in v1.
- Changing the figure-consistency rule or the decomposition/registry layers.

## Data model — the figure format

Two **optional** additions. A figure with neither behaves exactly as today.

### (a) In the frame SVG
Any `<g>` group may carry:
- `data-reveal="k"` — 1-based integer; the beat at which this group first becomes visible.
- `data-anim="rise|draw|fade"` — optional entrance style. Default `rise` (fade + translateY). `draw` is for arrows/lines/connectors (endpoint-geometry draw in HTML; pop in MP4). `fade` is opacity-only.

Groups **without** `data-reveal` are the always-present backdrop (stage, axis, title) — visible from beat 1.

### (b) In `figure.json`, per frame
A new optional `beats` array:
```json
"beats": [
  {"caption": "Two computers want to talk.", "narration": "Two computers want to talk to each other."},
  {"caption": "Client and server", "narration": "Think of one as you — the client — and one as the website — the server."}
]
```
- One entry per reveal index, in order. `beats[i-1]` supplies the on-screen caption + spoken narration for reveal step *i*.
- The frame's existing top-level `caption` and `commentary` remain as a summary/fallback.

### Consistency rule (lint, in render.py figure validator)
If a frame has any `data-reveal` groups, the frame's `beats` length MUST equal the maximum `data-reveal` index, and reveal indices MUST be a gap-free `1..N`. The validator errors on mismatch or gaps. A frame with `data-reveal` but no `beats` (or vice versa) is an error.

### Backward compatibility
A frame with **no** `data-reveal` groups and **no** `beats` → a single beat using the frame's existing `caption`/`commentary`. All shipped figures keep working unchanged.

## concept-illustrator authoring (skill update)

Extend `.claude/skills/concept-illustrator/SKILL.md` + references so that when a figure (or a frame) builds up additively, the illustrator:
- wraps each progressively-revealed element in `<g data-reveal="k" data-anim="…">`, with reveal order following the explanation order; arrows/connectors get `data-anim="draw"`, new shapes `rise`;
- writes a short, **human, one-sentence narration beat per step** into `figure.json` `beats` (warm, plain language — the agreed voice from the demo);
- documents the build order in the frame's `runbook`.
Mutation between major states continues to use separate frames (unchanged). The design-system/visual-vocabulary references gain a short "progressive reveal" section; the figure-json reference documents `data-reveal`/`data-anim`/`beats`.

## `build_video.py` — manifest expansion + MP4 pop

### load_frames
`load_frames(figure_dir)` additionally reads each frame's `beats` (when present), returning per frame: `{file, caption, commentary, beats: [{caption, narration}] | None}`.

### build_manifest — per-beat expansion
For each frame:
- **If it has beats:** emit one slide **per beat**. Each slide: `kind="frame"`, `image` = the frame SVG path (shared across the frame's beats), `caption`/`narration` from the beat, `reveal_to` = beat index (1-based), `transition` = `reveal` for beats after the first in a frame, and `cut`/`crossfade` for the first beat of a frame (relative to the previous frame/section), `duration_s` from the beat narration.
- **If it has no beats:** emit one slide as today, with `reveal_to = null` (meaning "show the whole figure").

New slide field: **`reveal_to: int | null`**. All other slide fields unchanged. Beats of one frame are contiguous and share the same `image`, so consumers can group them.

### Cumulative-state SVG (MP4)
New helper `_reveal_svg(inner_svg_text, reveal_to)`:
- If `reveal_to is None` → return `inner_svg_text` unchanged.
- Else → **string-transform** the markup: for every group whose `data-reveal` index is **greater than** `reveal_to`, inject `visibility:hidden` into that element's `style` (so layout/geometry is preserved; the element is simply not painted). This deliberately does **not** rely on the rasterizer's CSS attribute-selector support (librsvg/cairosvg coverage varies) — it sets per-element inline visibility, which every rasterizer honors.
- `stage_svg(slide, stage)` calls `_reveal_svg` on the frame SVG (using `slide["reveal_to"]`) before nesting it into the 16:9 stage. The MP4 path therefore rasterizes one PNG per beat, each held for its `say` duration ("pop").

`script.md` and `captions.srt` become per-beat automatically (they already iterate `manifest["slides"]`).

## HTML player — reveal engine

Extend `.claude/skills/concept-illustrator/assets/video.template.html` (and `build_player`/`_slide_html` in `build_video.py`):
- **Group beats by frame:** consecutive slides sharing the same `image` are one frame; the player inlines that figure SVG **once** (not per beat) and steps `reveal_to` across the beats. (`build_player` emits one `.frame` container per distinct frame, with its beats as data; or `_slide_html` is reworked so a frame's SVG appears once and beats are metadata in the injected manifest.)
- **Reveal engine** (from the v3 demo): on entering a frame, hide all `[data-reveal]` groups; per beat, reveal groups with `data-reveal == reveal_to` (cumulative), animating entrance by `data-anim`:
  - `rise` → CSS opacity + translateY transition;
  - `draw` → JS endpoint-geometry tween for `<line>` (animate `x2,y2` from the start point so the `marker-end` arrowhead rides the tip); `stroke-dasharray` draw for `<path>`/`<polyline>`;
  - `fade` → opacity only.
- **Dim past** earlier-revealed groups (`.dim`, ~0.35 opacity) when a new beat is the focus — default on, with a small toggle in the control bar.
- Advance on the per-beat timer / TTS (`utterance.onend`) exactly as today; captions/progress/play-pause/prev-next all operate at beat granularity. Light/dark preserved.

## Components & files

- `.claude/skills/concept-illustrator/scripts/render.py` — figure validator: lint `beats` ↔ max `data-reveal` consistency.
- `.claude/skills/concept-illustrator/SKILL.md` + `references/{figure-json,visual-vocabulary,design-system}.md` — authoring guidance for `data-reveal`/`data-anim`/`beats`.
- `.claude/skills/concept-illustrator/assets/video.template.html` — reveal engine.
- `.claude/skills/concept-illustrator/examples/quicksort/figure.json` (+ a frame SVG) — hand-tag one frame as the mutation proof.
- A TCP-handshake figure (in `registry/` or the illustrator examples) — hand-tag as the additive proof (6 beats, like the demo).
- `scripts/build_video.py` — `load_frames` (read beats), `build_manifest` (per-beat expansion + `reveal_to`), `_reveal_svg` (new), `stage_svg` (apply reveal for MP4), `_slide_html`/`build_player` (group beats by frame + reveal engine wiring).
- `scripts/tests/test_build_video.py` — new tests (below).
- Knowledge: `concepts/dummies-notes/illustration-engine.md`, `concepts/dummies-notes/video-engine.md`, the figure-json reference; `log.md` entry.

## Testing

Unit (stdlib `unittest`):
- `build_manifest` expands a frame with N beats into N slides with correct `reveal_to` (1..N), beat caption/narration, and `transition` (`reveal` within a frame, `crossfade`/`cut` at frame boundaries).
- A beat-less frame → one slide with `reveal_to = None` (backward-compat).
- `_reveal_svg`: with `reveal_to=k`, groups with `data-reveal > k` carry `visibility:hidden`; groups `≤ k` and untagged groups do not; output is well-formed XML (`ET.fromstring`); `reveal_to=None` returns input unchanged.
- `stage_svg` on a reveal slide hides the right groups and stays well-formed.
- `build_player` output contains the reveal CSS/JS hooks and inlines each frame SVG exactly once even when the frame has multiple beats.
- Figure validator: errors when `beats` length ≠ max `data-reveal`, on reveal-index gaps, and on the tagged-but-no-beats / beats-but-untagged mismatches.
- A guarded MP4 smoke (skipped without ffmpeg + rasterizer) that builds a reveal figure end-to-end and asserts slide count = total beats.

## Risks

- **Rasterizer CSS coverage** — sidestepped by per-element inline `visibility` in `_reveal_svg` (no reliance on attribute selectors).
- **Player frame-grouping** — multiple beat-slides must inline the figure SVG once; getting the grouping wrong would duplicate large SVGs. Covered by the `build_player`-inlines-once test.
- **`data-anim="draw"` for non-line shapes** — v1 supports `draw` for `<line>` (geometry tween) and dash-draw for `<path>`/`<polyline>`; other shapes fall back to `rise`. Documented.
- **Authoring burden** — reveal tagging is opt-in; existing figures and the decomposition pipeline are unaffected, so the blast radius is contained to figures that choose to animate.
