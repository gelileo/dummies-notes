# Pluggable TTS providers (Kokoro default, NeuTTS opt-in) — design spec

**Date:** 2026-06-13 (rev. 2026-06-14)
**Status:** approved (brainstorming) — ready for implementation plan
**Phase:** 8 (better MP4 narration: Kokoro by default, NeuTTS cloned voice opt-in)
**Builds on:** Phase 6 video engine (`2026-06-11-video-engine-design.md`), Phase 7 progressive reveal, and the tooling notes in `docs/tts-and-ffmpeg-notes.md`.

## Goal

Replace robotic macOS `say` as the MP4 narration voice with a small pluggable
provider layer:

- **`kokoro` — the new default.** Local, open-weight, natural, fixed voices, no
  cloning. (Quality you heard in the A/B test.)
- **`neutts` — opt-in.** Local NeuTTS Air with a **cloned voice** from a
  reference clip.
- **`say` — the built-in, zero-dependency fallback/escape hatch.**

**TTS applies only to the MP4 path.** `--format html` (the default deliverable)
uses no TTS at all — the HTML player narrates via the browser's Web Speech API
at play time. So the provider choice only matters for `--format mp4|both`.

Both `kokoro` and `neutts` are heavy enough (model downloads; for NeuTTS, torch +
a Python ≤3.13 constraint) that they run in **separate venvs invoked as
subprocesses** — never imported into the main tool, which stays stdlib-only.

## Decisions locked during brainstorming

1. **Scope = MP4 only.** HTML-player audio is deferred.
2. **Default provider = `kokoro`; `neutts` opt-in; `say` is the zero-dep
   fallback/explicit choice.**
3. **Integration = one subprocess per render to a batch runner** that loads the
   model **once** and synthesizes **all** beats. (Per-beat reload / long-lived
   server rejected.)
4. **Error semantics (intentional asymmetry):**
   - `kokoro` requested (it's the default, or explicit) but not configured/usable
     → **HARD ERROR** with setup steps (and "pass `--tts say` for the built-in
     voice"). The render does not silently degrade.
   - `neutts` (explicit opt-in) not configured/usable → **fall back to `say` +
     a NOTE**; the render still completes.
   - `say` always works (silent-with-captions if even `say` is unavailable —
     existing Phase-6 behavior).
5. **Voice profile applies to `neutts` only** (cloning). `kokoro` uses a fixed
   named voice — no profile, no reference clip, no denoise/transcribe.

## Non-goals (v1)

- HTML-player audio (deferred).
- Cloud providers (Gemini/OpenAI) — the `--tts` seam stays open for them, not built now.
- Auto-installing/creating the Kokoro or NeuTTS venvs — the user sets each up
  once per `docs/tts-and-ffmpeg-notes.md`; this feature *consumes* them.
- Smooth-tween MP4; manifest/reveal changes.

## Providers

| `--tts` | Engine | Runs | Voice | Setup needed | Unconfigured → |
|---|---|---|---|---|---|
| `say` | macOS `say` | built-in | system voice | none | (always works) |
| `kokoro` *(default)* | Kokoro (kokoro-onnx) | local venv | fixed (e.g. `af_heart`) | venv + ~340 MB model | **hard error** |
| `neutts` | NeuTTS Air | local venv | **cloned** from your clip | venv + models + `voice-profiles/<name>/ref.wav` | fall back to `say` + NOTE |

## Architecture

```text
build_video.py (system py3.14, stdlib only)        chosen engine's venv (py3.12/3.14)
  render_mp4(tts="kokoro", cfg)
    └─ _synthesize_segments(manifest, dir, tts, cfg, have_say)
         ├─ resolve provider config; validate                scripts/tts_runner.py --engine <e> job.json
         ├─ (neutts only) ffmpeg-denoise ref → ref_clean.wav    ├─ load model ONCE (kokoro-onnx OR neutts)
         ├─ subprocess: <engine_python> tts_runner.py job.json  ├─ (neutts) encode ref once; whisper-transcribe if no ref.txt
         │     → one wav per beat                               └─ synthesize each segment → out_path (24 kHz wav)
         └─ on kokoro failure: raise; on neutts failure: say+NOTE
    └─ _build_audio_track(...) + mux  (UNCHANGED)
```

Capability split: **ffmpeg denoise** runs in `build_video` (system ffmpeg; NeuTTS
only). **Model load + synthesis (+ Whisper transcription for NeuTTS)** run in the
venv runner — only it has the heavy deps.

## Components

### 1. Provider seam in `build_video.py`
- `render_mp4(manifest, out_dir, stage, tts="kokoro", cfg=None)` — new `tts` +
  `cfg` (provider config dict). NOTE: the **MP4-path default becomes `kokoro`**;
  `--format html` is unaffected (no TTS).
- New `_synthesize_segments(manifest, frames_dir, tts, cfg, have_say)` → ordered
  list of per-beat audio paths (or `None` for non-narration slides) — the exact
  shape `_effective_durations`/`_build_audio_track` already consume. Dispatch:
  - `say`: the current per-beat `_say_segment` loop (unchanged).
  - `kokoro` / `neutts`: build a job, run the batch runner once, map outputs back
    to beats. On failure, apply the §Decisions-4 policy (kokoro → raise;
    neutts → return None-sentinel so `render_mp4` logs a NOTE and re-runs `say`).
- The rest of `render_mp4` (rasterize, durations, silent video, audio track, mux)
  is unchanged.

### 2. `scripts/tts_runner.py` (executed by a venv python only)
- One small script, run by **either** engine's venv. Args: `--engine
  kokoro|neutts <job.json>`. Stdlib + that engine's package.
- Job JSON:
  - kokoro: `{"engine":"kokoro","model":"…onnx","voices":"…bin","voice":"af_heart","segments":[{"text","out_path"}]}`
  - neutts: `{"engine":"neutts","ref_audio":"…ref_clean.wav","ref_text_path":"…ref.txt","backbone":"…","segments":[…]}`
- Loads the model **once**; for neutts, transcribes the reference with Whisper
  (`openai/whisper-base.en`) if `ref_text_path` is empty and caches `ref_clean.pt`.
  Writes each segment's wav; prints a JSON summary; non-zero exit on fatal error.
- No dependency on `build_video.py` (clean process boundary).

### 3. Config + CLI (`build` / `main` / workflow)
- `--tts {say,kokoro,neutts}` (default **`kokoro`**).
- Kokoro: `--kokoro-python` / `KOKORO_PYTHON`; `--kokoro-model` / `KOKORO_MODEL`
  + `--kokoro-voices` / `KOKORO_VOICES` (the `.onnx` + `.bin`); `--kokoro-voice`
  (default `af_heart`).
- NeuTTS: `--neutts-python` / `NEUTTS_PYTHON`; `--neutts-voice <name>` →
  `voice-profiles/<name>/`; `--neutts-backbone` (default `neuphonic/neutts-air-q8-gguf`).
- `build_video` assembles the provider `cfg` from these. The workflow `Video`
  phase gains pass-through `tts` / `kokoroVoice` / `neuttsVoice` args and reads
  `KOKORO_PYTHON`/`NEUTTS_PYTHON` from the environment. Default workflow runs
  (no MP4) are unchanged.

### 4. Voice profile (NeuTTS only) — `voice-profiles/<name>/`
```text
voice-profiles/<name>/
  ref.wav         # user-provided raw reference clip (REQUIRED for neutts)
  ref_clean.wav   # generated by build_video (ffmpeg highpass=f=80,afftdn=nr=24:nf=-35)
  ref.txt         # transcript — user-provided OR generated by the runner (Whisper)
  ref_clean.pt    # generated by the runner (NeuTTS encoded reference cache)
```
`voice-profiles/` is **git-ignored** (personal voice data); a committed
`voice-profiles/README.md` documents the layout. Missing `ref.wav` → neutts
fallback to `say` + NOTE. (Kokoro ignores this entirely.)

### 5. Caching
Per-beat audio keyed on a short hash of `(provider, voice, model/backbone,
narration text)`. The runner writes to deterministic cache paths;
`_synthesize_segments` omits beats whose cached wav already exists. Re-rendering
only re-synthesizes changed narration. (Model-load cost is paid once per render.)

## Error handling (summary)

| Situation | Result |
|---|---|
| `--format html` | no TTS invoked at all |
| `kokoro` default/explicit, venv or model missing, or runner fails | **ERROR** + setup steps + suggest `--tts say` |
| `neutts` explicit, venv/ref missing, or runner fails | `say` + NOTE, render completes |
| `say`, or any fallback to it | works; silent+captions if `say` absent |

## Testing

Unit (stdlib `unittest`; mock `subprocess.run` + ffmpeg; no real models):
- Dispatch: `say` uses the per-beat say path (unchanged); `kokoro`/`neutts` build
  a job and call the runner with the right `--engine` + JSON shape.
- Job JSON: correct engine-specific fields; one segment per narration beat.
- **kokoro hard-error**: `--tts kokoro` (default) with no `KOKORO_PYTHON`/model →
  `render_mp4` raises a clear error (no say fallback).
- **neutts fallback**: `--tts neutts` with no venv/ref → NOTE + say-produced segments.
- runner non-zero exit → kokoro raises / neutts falls back, per policy.
- cache: a beat with an existing cached wav is omitted from the job.
- CLI parsing + default `--tts kokoro`; `--format html` path invokes no TTS.
- Guarded integration tests: run the real runner only when `KOKORO_PYTHON` (resp.
  `NEUTTS_PYTHON`) is set; assert non-empty wavs; skipped otherwise.

## Knowledge / drift

- Update `knowledge/concepts/dummies-notes/video-engine.md`: the `--tts` provider
  seam, the venv-subprocess `tts_runner.py`, the default-vs-fallback policy, and
  the NeuTTS voice-profile layout.
- New mapped path `scripts/tts_runner.py` → add to the CLAUDE.md article table (→ `video-engine.md`).
- `.gitignore`: add `voice-profiles/` (keep `voice-profiles/README.md`).
- `knowledge/log.md` entry.

## Dependencies

- `say`: none (built-in).
- `kokoro`: a user-prepared venv with `kokoro-onnx` + `soundfile` and the model
  files (`docs/tts-and-ffmpeg-notes.md` §2). No torch; works on any Python.
- `neutts`: a user-prepared venv (torch + `llama-cpp-python` + `neutts`, Python
  ≤3.13) + models (§3). ffmpeg (already required) does the reference denoise.
All detected at runtime; never installed by the tool.

## Risks

- **Default now needs setup for MP4s.** A fresh checkout can render `--format html`
  (zero-dep) but `--format mp4|both` errors until Kokoro is set up (or `--tts say`
  is passed). This is the intended, documented trade-off of "Kokoro by default."
- **Runner/venv contract drift** (kokoro-onnx / NeuTTS APIs) — keep the runner
  small; covered by the guarded integration tests.
- **Asymmetric unconfigured behavior** (kokoro errors, neutts falls back) — a
  deliberate choice; revisit if it proves confusing.
