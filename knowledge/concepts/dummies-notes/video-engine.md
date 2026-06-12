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
  slide via `render.export_png`, holds each frame for its duration (hard cuts),
  and speaks narration via macOS `say`. When TTS is present the slide duration
  follows the spoken-audio length. ffmpeg/`say`/an SVG rasterizer are
  runtime-detected; missing ffmpeg or no rasterizer (rsvg-convert or cairosvg)
  skips the MP4, missing `say` yields a silent MP4 with burned-in captions.
  Static rasterizers ignore the dark-mode media query, so MP4 frames render at
  the default (light) theme.

v1 MP4: per-slide stage PNG held for its duration, `say` narration muxed in (slide
duration follows the spoken-audio length), silent-with-captions fallback when `say`
is absent. Slide-to-slide transitions are hard cuts in v1; `xfade` crossfade is
deferred (the HTML player remains the primary crossfade-animated target).

Every run also writes `script.md` (human voiceover) and `captions.srt`.

**Task 3 (writers) shipped.** `write_captions(manifest, out_path)` produces standard SRT with sequential 1-based indices, `HH:MM:SS,mmm` timestamps accumulated from each slide's `duration_s`, and the slide narration (falling back to caption) as subtitle text. `write_script(manifest, out_path)` produces a Markdown file with a top-level `#` title and one `##` heading per distinct concept/kind section in reading order, followed by each slide's narration paragraph. Both functions return `out_path`. Helper `_srt_timestamp(seconds)` converts a float to the SRT timestamp format. 3 new tests added (10 total in the suite, all passing).

**Task 4 (stage SVG composer) shipped.** `stage_svg(slide, stage)` composes one 16:9 SVG per slide. For `frame` slides it nests the figure SVG (centered via `preserveAspectRatio="xMidYMid meet"`) inside a content box, adds a top concept-label `<text>` and a bottom caption `<text>`. For `title`/`section`/`closing` slides it renders a single centered text card. `_read_inner_svg(path)` strips any XML prolog before the `<svg` tag so the nested SVG is valid inside the outer document. `_esc(text)` escapes all interpolated user text via `html.escape`. Output is always well-formed XML. 2 new tests added (12 total, all passing).

**Bug fix (duplicate-attribute).** Real figure SVGs carry `width="100%"` on their root. The original nesting code prepended layout attributes via `.replace("<svg", '<svg x=... width=...')`, producing two `width=` on the nested root — a fatal XML well-formedness error on the MP4 path. Fix: `_nest_figure(inner, x, y, width, height)` strips the figure root's own `width`/`height` via `_ROOT_DIM_RE` before injecting the stage-layout dimensions, so the nested element always has exactly one of each. Test fixture updated to use a realistic root (`width="100%"`, `xmlns`, `role="img"`) so the existing `ET.fromstring` assertion catches any regression.

**Security fix (script-breakout in injected manifest).** `json.dumps` does not escape `<`, `>`, or `&`, so narration/caption text containing `</script>` would terminate the inline `<script>` early — breaking the player and creating an HTML-injection vector. Fix: after `json.dumps`, replace `<` → `<`, `>` → `>`, `&` → `&` (valid JSON; browsers decode them back at parse time). A docstring was added to `build_player`; a comment documenting the shared `id="arrow"` marker assumption was added to `_slide_html`. Regression test added: `TestPlayer.test_player_escapes_script_breakout_in_narration`. 74 tests total, all passing.

**Robustness fixes (render_mp4).** Three guards added: (1) empty-manifest early return — `render_mp4` now returns `(None, ["empty manifest — no slides to render."])` immediately when `manifest["slides"]` is absent or empty, preventing a downstream `IndexError` in `_build_silent_video`; (2) all-segments-failed diagnostic — when `say` is present but every `_say_segment` call returns `None`, a note is appended so the silent fallback is explicit; (3) two internal docstrings clarified: `_effective_durations` now says "when ffprobe is present, else computed duration_s" and `_build_audio_track` names the `apad`/`-t` mechanism. Import-order fixed in test file (stdlib imports moved to the top block). 18 tests, 1 skip, all passing.

**Task 5 (HTML player) shipped.** `build_player(manifest, template_path, out_path)` writes a self-contained `video.html` from `.claude/skills/concept-illustrator/assets/video.template.html`. Frame slides inline the raw figure SVG (via `_read_inner_svg`) with a `.cap` paragraph; title/section/closing render as `.card` divs. The template substitutes `{{SLIDES_HTML}}` and `{{MANIFEST_JSON}}`; the injected manifest carries only lightweight fields (no SVG text) to keep the JSON small. The player auto-advances on `duration_s`, crossfades within a concept, has play/pause + prev/next + progress bar + optional Web Speech TTS toggle. Helper `_slide_html(slide)` is also added. 1 new test added (13 total, all passing).

**Task 7 (build orchestrator + CLI) shipped.** `build(graph_dir, registry_root, out_dir, fmt, wpm, stage)` writes `output/<topic>/video/{manifest.json,script.md,captions.srt,video.html}` (and `video.mp4` when `fmt` is `mp4` or `both`). Returns `(result_dict, issues)` where `result_dict` carries `video_dir`, `slides` count, and `notes`; returns `(None, issues)` on ERROR. `main(argv)` is the CLI entry point: `--format html|mp4|both`, `--wpm`, `--out`, `--registry`; exits 0 on success, 1 on error. File ends with exactly one `if __name__ == "__main__": sys.exit(main())` block. 3 new tests added (21 total, 1 skip, all passing). Smoke test on `tcp-connection-lifecycle`: 19 slides, `video.html` 109 KB with `window.__MANIFEST__` and 14 inline SVGs.

**Portability fix + CLI output improvement.** `manifest.json` on disk now stores repo-relative `image` paths (via `os.path.relpath(path, _REPO)`) so the committed artifact does not leak local absolute paths and is machine-portable. The in-memory manifest retains absolute paths so `build_player` / `render_mp4` read frame SVGs without change. Module-level `_REPO = os.path.dirname(_HERE)` added. `result["video_html"]` added to the build result dict; CLI `OK` line now points at `video.html` (or `video_dir` when no HTML was requested). Regression test `test_manifest_image_paths_not_absolute` added. 22 tests total, 1 skip, all passing.

**Rasterizer guard.** `render_mp4` previously only checked for `ffmpeg`/`say`, but `render.export_png` raises `SystemExit` when neither `rsvg-convert` nor `cairosvg` is available — crashing `main` because only `ValueError` was caught. Fix: `_have_rasterizer()` helper detects availability of either rasterizer up front; `render_mp4` now exits early with a `NOTE` when neither is present. The doc bullet above was corrected to say "hard cuts" (xfade is deferred to the HTML player). 1 regression test added (`test_missing_rasterizer_skips_mp4`); 2 existing tests patched to mock `_have_rasterizer=True`. 23 tests, 1 skip, all passing.

**Phase 7 Task 1 (progressive-reveal beats).** `load_frames` now reads the optional `beats` field from each frame entry in `figure.json`. If `beats` is a non-empty list it is returned as-is; any other value (absent, `null`, empty list, wrong type) is normalised to `None`. Every returned frame dict now always carries a `beats` key. The `make_figure` test helper accepts an optional `beats` kwarg applied to the first frame. The function's docstring was updated to document the `beats` key in the return value: `[{file (abs), caption, commentary, beats}]`. 2 new tests in `TestLoadFramesBeats` (`test_beats_read_when_present`, `test_beats_none_when_absent`). 25 tests, 1 skip, all passing.
