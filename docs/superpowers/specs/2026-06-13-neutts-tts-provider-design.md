# `--tts neutts` provider — design spec

**Date:** 2026-06-13
**Status:** approved (brainstorming) — ready for implementation plan
**Phase:** 8 (opt-in NeuTTS Air narration with a cloned voice)
**Builds on:** Phase 6 video engine (`2026-06-11-video-engine-design.md`), Phase 7 progressive reveal, and the tooling notes in `docs/tts-and-ffmpeg-notes.md`.

## Goal

Let the MP4 narration use **NeuTTS Air with a cloned voice** instead of macOS `say`, as an **opt-in** `--tts neutts`. `say` stays the zero-dependency default and behavior is unchanged for anyone who doesn't opt in. Because NeuTTS Air cannot install on the project's system Python 3.14 (it pins `<3.14` and pulls torch + a compiled `llama-cpp-python`), the heavy model runs in a **separate venv invoked as a subprocess** — never imported into the main tool.

## Decisions locked during brainstorming

1. **Scope = MP4 only.** The HTML player keeps today's behavior (browser Web Speech / silent). Wiring cloned audio into the HTML player is explicitly deferred.
2. **Integration = subprocess to a batch runner.** One subprocess per render; the runner loads the model **once** and synthesizes **all** beats. (Per-beat reload and a long-lived server were rejected.)
3. **Fallback = `say` + a NOTE.** If `--tts neutts` is requested but the venv/reference isn't configured or the runner fails, `render_mp4` falls back to `say` and appends a clear NOTE — matching the engine's existing honest-fallback behavior (missing-ffmpeg / missing-rasterizer). The render never hard-fails for this reason.
4. **Voice profile = a named dir in the repo:** `voice-profiles/<name>/`, selected by `--neutts-voice <name>`.

## Non-goals (v1)

- HTML-player audio (deferred).
- Other providers (`kokoro`, `gemini`) — the `--tts` seam leaves room, but only `say` + `neutts` ship now.
- Auto-installing/creating the NeuTTS venv — the user sets it up once per `docs/tts-and-ffmpeg-notes.md`; this feature *consumes* it.
- Smooth-tween MP4 (still deferred from Phase 6).
- Changing the manifest/reveal model.

## Architecture

```
build_video.py (system py3.14)                NeuTTS venv (py3.12, torch+llama-cpp)
  render_mp4(tts="neutts", neutts=cfg)
    └─ _synthesize_segments(...)               scripts/neutts_runner.py  (run by venv python)
         ├─ ensure voice profile prepared        ├─ (if needed) Whisper-transcribe ref_clean.wav
         │    (ffmpeg denoise — system ffmpeg)    ├─ load backbone+codec ONCE, encode ref ONCE
         └─ subprocess: <neutts_python>           └─ synthesize each segment → out_path (wav)
              scripts/neutts_runner.py job.json
    └─ _build_audio_track(...) + mux  (UNCHANGED)
```

Capability split: **ffmpeg denoise** runs in `build_video` (system ffmpeg is always present); **Whisper transcription + NeuTTS synthesis** run in the venv runner (only it has torch/transformers/neutts).

## Components

### 1. Provider seam in `build_video.py`
- `render_mp4(manifest, out_dir, stage, tts="say", neutts=None)` — new `tts` + `neutts` (config dict or None) params; default `tts="say"` keeps current behavior byte-for-byte.
- New `_synthesize_segments(manifest, frames_dir, tts, neutts, have_say)` → returns the ordered list of per-beat audio paths (or `None` for non-narration slides), exactly the shape `_effective_durations`/`_build_audio_track` already consume. It dispatches:
  - `tts == "say"` (or neutts fell back): the current per-beat `_say_segment` loop.
  - `tts == "neutts"`: one batched runner call (below); on any failure return a sentinel that makes `render_mp4` log a NOTE and retry via the `say` path.
- `render_mp4`'s existing body (PNG rasterize, durations, silent video, audio track, mux) is otherwise unchanged — it just calls `_synthesize_segments` where it used to inline the `say` comprehension.

### 2. NeuTTS config + CLI
- `build(graph_dir, registry_root, out_dir, fmt, wpm, stage, tts="say", neutts=None)` and `main` gain:
  - `--tts {say,neutts}` (default `say`).
  - `--neutts-python <path>` (or env `NEUTTS_PYTHON`) — the venv interpreter with `neutts` installed.
  - `--neutts-voice <name>` (default `default`) — resolves to `voice-profiles/<name>/`.
  - `--neutts-backbone <repo>` (default `neuphonic/neutts-air-q8-gguf`).
- `neutts` config dict assembled from these: `{python, voice_dir, backbone}`. If `--tts neutts` but `--neutts-python`/env is unset or the path doesn't exist → NOTE + fall back to `say` (no hard error).

### 3. `scripts/neutts_runner.py` (executed by the venv python only)
- Stdlib + neutts/transformers (available in the venv). Reads a **job JSON** (path as argv): `{"ref_audio": ".../ref_clean.wav", "ref_text_path": ".../ref.txt", "backbone": "...", "segments": [{"text": "...", "out_path": "..."}, ...]}`.
- If `ref_text_path` is missing/empty → transcribe `ref_audio` with `transformers` Whisper (`openai/whisper-base.en`), write it.
- Load backbone + codec **once**; encode the reference **once** (cache codes as `<ref_clean>.pt`, reuse if present); synthesize each segment to its `out_path` (24 kHz wav). Print a small JSON summary (`{"written": [...]}`) to stdout; non-zero exit on fatal error.
- Has no dependency on `build_video.py` (clean process boundary); reuses the patterns proven in `docs/tts-and-ffmpeg-notes.md`.

### 4. Voice profile (`voice-profiles/<name>/`)
```
voice-profiles/<name>/
  ref.wav         # user-provided raw reference clip (REQUIRED input)
  ref_clean.wav   # generated by build_video (ffmpeg highpass+afftdn denoise)
  ref.txt         # transcript — user-provided OR generated by the runner (Whisper)
  ref_clean.pt    # generated by the runner (NeuTTS encoded reference cache)
```
- `build_video` ensures `ref_clean.wav` exists (denoise `ref.wav` via the approved ffmpeg chain `highpass=f=80,afftdn=nr=24:nf=-35`) before invoking the runner; the runner handles `ref.txt` (transcribe if absent) and `ref_clean.pt`.
- `voice-profiles/` is **git-ignored** (personal voice data must not be committed). A committed `voice-profiles/README.md` documents the layout; everything else under it is ignored.
- Missing `ref.wav` for the named voice → NOTE + fall back to `say`.

### 5. Caching
- Per-beat audio is keyed on a short hash of `(provider, voice name, backbone, narration text)`. The runner writes beat wavs to deterministic cache paths; `_synthesize_segments` skips beats whose cached wav already exists. Re-rendering a topic only re-synthesizes beats whose narration changed. (Model-load cost is already paid once per render via batching.)

### 6. Workflow `Video` phase
- The opt-in `Video` phase in `.claude/workflows/dummies-notes.js` gains pass-through args `tts` (default `"say"`), `neuttsVoice`, and reads `NEUTTS_PYTHON` from the environment — forwarded to the `build_video.py` invocation. Default workflow runs are unchanged.

## Error handling

Every NeuTTS failure mode → **NOTE + fall back to `say`**, render still completes:
- `--neutts-python` unset / not a file.
- `voice-profiles/<name>/ref.wav` missing.
- Runner exits non-zero / times out / produces no audio.
The NOTE states the cause and points at `docs/tts-and-ffmpeg-notes.md` for setup.

## Testing

Unit (stdlib `unittest`, mock `subprocess.run` + ffmpeg; no real model):
- Provider dispatch: `tts="say"` uses the per-beat say path (existing behavior intact); `tts="neutts"` builds a job and calls the runner subprocess.
- Job JSON shape: correct `ref_audio`/`ref_text_path`/`backbone`/`segments[{text,out_path}]`, one segment per narration beat.
- Fallback: neutts requested but `--neutts-python` missing → NOTE present + segments produced via `say` (mocked).
- Fallback: runner subprocess returns non-zero → NOTE + say fallback.
- Cache: a beat whose cached wav exists is not re-synthesized (runner job omits it).
- `--tts`/`--neutts-*` CLI parsing; default `say` unchanged.
- Guarded integration test: only when `NEUTTS_PYTHON` is set, run the real runner on a 1-beat job and assert a non-empty wav (skipped otherwise).

## Knowledge / drift

- Update `knowledge/concepts/dummies-notes/video-engine.md`: the `--tts` provider seam, the NeuTTS venv-subprocess runner, the voice-profile layout, and the fallback contract.
- `scripts/neutts_runner.py` is a new mapped path → add it to the CLAUDE.md article-mapping table (→ `video-engine.md`).
- `.gitignore`: add `voice-profiles/` (keep `voice-profiles/README.md`).
- `knowledge/log.md` entry.

## Dependencies

- Default path: zero new deps (unchanged).
- `--tts neutts`: requires a user-prepared NeuTTS venv (torch + `llama-cpp-python` + `neutts`, Python ≤3.13) per the tooling notes — detected at runtime, never installed by the tool. ffmpeg (already required by the MP4 path) does the denoise.

## Risks

- **Runner/venv contract drift:** the runner depends on NeuTTS's `examples`/API; pin the documented usage and keep the runner small. Covered by the guarded integration test.
- **First-run latency:** model load + reference encode happen once per render (acceptable; batching amortizes). Documented.
- **Profile not committed:** `voice-profiles/` is git-ignored, so a fresh checkout has no voice until the user adds `ref.wav` — the fallback-to-`say` keeps renders working meanwhile.
