# TTS Providers (Kokoro default, NeuTTS opt-in) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pluggable MP4-narration provider layer — `--tts say|kokoro|neutts` — where Kokoro is the user-facing default, NeuTTS clones a configured voice, and both run in their own venvs via one batch subprocess runner; `say` stays the built-in fallback.

**Architecture:** `build_video.py` stays stdlib-only. The per-beat audio step in `render_mp4` is extracted into `_synthesize_segments(...)`, which dispatches to the existing `say` path or to `scripts/tts_runner.py` (executed by the engine's venv python, loads the model once, batch-synthesizes all beats). Kokoro-unconfigured raises a `TtsError` (hard fail); NeuTTS-unconfigured falls back to `say` + a NOTE. TTS only runs for `--format mp4|both`.

**Tech Stack:** Python 3 stdlib + `unittest`; `subprocess` to venv pythons; ffmpeg (reference denoise); the user-prepared Kokoro (`kokoro-onnx`) and NeuTTS (`neutts`) venvs documented in `docs/tts-and-ffmpeg-notes.md`.

**Spec:** `docs/superpowers/specs/2026-06-13-neutts-tts-provider-design.md`

---

## Reference: contracts (keep identical across tasks)

In `scripts/build_video.py`:
```python
TTS_RUNNER = os.path.join(_HERE, "tts_runner.py")   # _HERE already = scripts dir

class TtsError(Exception):
    """Raised when a hard-required TTS provider (kokoro) is unavailable/failed."""
```
Provider config dicts (assembled by `build`/`main`):
```python
# kokoro:  {"python": "<venv py>", "model": "<.onnx>", "voices": "<.bin>", "voice": "af_heart"}
# neutts:  {"python": "<venv py>", "voice_dir": "voice-profiles/<name>", "backbone": "neuphonic/neutts-air-q8-gguf"}
```
`_synthesize_segments(manifest, frames_dir, tts, cfg, have_say) -> (segments, notes)`
returns a per-slide list (abs wav/aiff path or `None`) aligned 1:1 with
`manifest["slides"]`, plus a list of NOTE strings. It raises `TtsError` only for
the kokoro hard-fail case.

`tts_runner.py` is run as: `<engine_python> scripts/tts_runner.py --engine kokoro|neutts <job.json>`.
Job JSON:
```json
{"engine":"kokoro","model":"…onnx","voices":"…bin","voice":"af_heart",
 "segments":[{"text":"…","out_path":"…wav"}]}
{"engine":"neutts","ref_audio":"…ref_clean.wav","ref_text_path":"…ref.txt",
 "backbone":"…","segments":[{"text":"…","out_path":"…wav"}]}
```

Run tests from the repo root. Never `git commit --no-verify`; `scripts/build_video.py`
and `scripts/tts_runner.py` map to `knowledge/concepts/dummies-notes/video-engine.md`
— update it in the same commit (keep `status` ∈ {thin,mature,deprecated}) and keep
`python3 scripts/validate-articles` green.

---

## Task 1: scaffolding — gitignore, voice-profiles README, drift mapping

**Files:**
- Modify: `.gitignore`
- Create: `voice-profiles/README.md`
- Modify: `CLAUDE.md` (Article mapping table)
- Modify: `knowledge/concepts/dummies-notes/video-engine.md`
- Modify: `knowledge/log.md`

- [ ] **Step 1: gitignore personal voice data**

Append to `.gitignore`:
```
# NeuTTS voice profiles (personal voice clips) — keep only the README
voice-profiles/*
!voice-profiles/README.md
```

- [ ] **Step 2: create `voice-profiles/README.md`**
```markdown
# Voice profiles (NeuTTS cloned voices)

Each profile is a directory `voice-profiles/<name>/` used by `--tts neutts --neutts-voice <name>`:

- `ref.wav` — **you provide this**: a clean ~10–15 s mono clip of the voice to clone.
- `ref_clean.wav` — generated (ffmpeg denoise of `ref.wav`).
- `ref.txt` — transcript; provide it, or it is auto-generated (Whisper) on first run.
- `ref_clean.pt` — generated NeuTTS encoded-reference cache.

Everything except this README is git-ignored — voice clips never get committed.
Setup for the NeuTTS venv itself is in `docs/tts-and-ffmpeg-notes.md`.
```

- [ ] **Step 3: CLAUDE.md mapping row**

In the "Article mapping" table, after the `scripts/build_video.py` row add:
```markdown
| `scripts/tts_runner.py` | `concepts/dummies-notes/video-engine.md` |
```

- [ ] **Step 4: thin note in `video-engine.md`** (append a short paragraph)
```markdown

## TTS providers (Phase 8)

MP4 narration is pluggable via `--tts say|kokoro|neutts` (default **kokoro** at
the CLI). `say` is the built-in zero-dep fallback. `kokoro` and `neutts` are
heavy local engines run in their own venvs through one batch subprocess runner,
`scripts/tts_runner.py` (loads the model once, synthesizes all beats). Kokoro
unconfigured → hard error; NeuTTS unconfigured → `say` + NOTE. TTS only applies
to `--format mp4|both`. Setup: `docs/tts-and-ffmpeg-notes.md`.
```

- [ ] **Step 5: log + validate + commit**

Append to the END of `knowledge/log.md`:
```markdown
- 2026-06-14 — Phase 8 start: scaffolding for pluggable --tts providers (gitignore voice-profiles/, README, drift mapping for tts_runner.py).
```
Run `python3 scripts/validate-articles` (exit 0), then:
```bash
git add .gitignore voice-profiles/README.md CLAUDE.md knowledge/concepts/dummies-notes/video-engine.md knowledge/log.md
git commit -m "docs(tts): scaffold provider layer (gitignore, voice-profiles README, drift mapping)"
```

---

## Task 2: extract `_synthesize_segments` (behaviour-preserving `say` refactor)

**Files:**
- Modify: `scripts/build_video.py`
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: add tests**
```python
class TestSynthesizeSegments(unittest.TestCase):
    def _manifest(self, base):
        graph = os.path.join(base, "g"); registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", True); make_figure(registry, "tcp", 2)
        m, _ = bv.build_manifest(graph, registry); return m

    def test_say_path_one_segment_per_slide(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as base:
            m = self._manifest(base); fr = os.path.join(base, "f"); os.makedirs(fr)
            with mock.patch("build_video._say_segment",
                            side_effect=lambda t, p: (open(p, "wb").close() or p) if t.strip() else None):
                segs, notes = bv._synthesize_segments(m, fr, "say", None, have_say=True)
            self.assertEqual(len(segs), len(m["slides"]))
            self.assertEqual(notes, [])

    def test_say_unavailable_notes_and_all_none(self):
        with tempfile.TemporaryDirectory() as base:
            m = self._manifest(base); fr = os.path.join(base, "f"); os.makedirs(fr)
            segs, notes = bv._synthesize_segments(m, fr, "say", None, have_say=False)
            self.assertTrue(all(s is None for s in segs))
            self.assertTrue(any("say" in n for n in notes))
```

- [ ] **Step 2: run → fail** (`AttributeError: ... '_synthesize_segments'`):
`python3 -m unittest scripts.tests.test_build_video.TestSynthesizeSegments -v`

- [ ] **Step 3: implement**

Add near `_say_segment` in `scripts/build_video.py`:
```python
class TtsError(Exception):
    """A hard-required TTS provider (kokoro) is unavailable or failed."""


def _say_segments(manifest, frames_dir, have_say, notes):
    if not have_say:
        notes.append("`say` not found — rendering a silent MP4 with burned-in captions.")
        return [None] * len(manifest["slides"])
    segs = [_say_segment(s["narration"], os.path.join(frames_dir, f"seg-{n:03d}.aiff"))
            for n, s in enumerate(manifest["slides"])]
    if not any(segs):
        notes.append("`say` was available but all speech segments failed — MP4 will be silent.")
    return segs


def _synthesize_segments(manifest, frames_dir, tts, cfg, have_say):
    """Per-slide audio paths (or None) + NOTE list. Raises TtsError for the
    kokoro hard-fail case; neutts failures fall back to say with a NOTE."""
    notes = []
    if tts == "say":
        return _say_segments(manifest, frames_dir, have_say, notes), notes
    # kokoro / neutts dispatch is added in later tasks; until then, treat unknown
    # providers as say so this refactor is behaviour-preserving.
    return _say_segments(manifest, frames_dir, have_say, notes), notes
```

Then in `render_mp4`, REPLACE the inline say block:
```python
    segments = [
        _say_segment(s["narration"], os.path.join(frames_dir, f"seg-{n:03d}.aiff"))
        if have_say else None
        for n, s in enumerate(manifest["slides"])]
    if have_say and not any(segments):
        notes.append("`say` was available but all speech segments failed — MP4 will be silent.")
```
with:
```python
    segments, seg_notes = _synthesize_segments(manifest, frames_dir, "say", None, have_say)
    notes.extend(seg_notes)
```
(`render_mp4` signature is unchanged in this task — it still hard-codes `"say"`;
the `tts`/`cfg` parameters are added in Task 5. Behaviour is identical.)

- [ ] **Step 4: run → pass** (`python3 -m unittest scripts.tests.test_build_video -v`; existing TestMp4Fallback still green).

- [ ] **Step 5: commit**
```bash
git add scripts/build_video.py scripts/tests/test_build_video.py
git commit -m "refactor(tts): extract _synthesize_segments (say path, behaviour-preserving)"
```
Touch `video-engine.md` (one line) if the drift hook asks; keep validate-articles green.

---

## Task 3: `scripts/tts_runner.py` — the venv batch runner

**Files:**
- Create: `scripts/tts_runner.py`
- Test: `scripts/tests/test_tts_runner.py`

The runner's **top-level imports are stdlib only**; engine packages are imported
**lazily** inside the synth functions, so the dispatch logic is unit-testable
under the system Python (which has neither engine installed).

- [ ] **Step 1: write tests**

Create `scripts/tests/test_tts_runner.py`:
```python
import json, os, sys, tempfile, unittest
from unittest import mock

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import tts_runner  # noqa: E402


class TestTtsRunner(unittest.TestCase):
    def _job(self, tmp, engine):
        seg = {"text": "hello", "out_path": os.path.join(tmp, "a.wav")}
        base = {"engine": engine, "segments": [seg]}
        if engine == "kokoro":
            base.update(model="m.onnx", voices="v.bin", voice="af_heart")
        else:
            base.update(ref_audio="ref.wav", ref_text_path="ref.txt", backbone="bb")
        p = os.path.join(tmp, "job.json")
        json.dump(base, open(p, "w"))
        return p

    def test_dispatch_kokoro(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = self._job(tmp, "kokoro")
            with mock.patch("tts_runner.synth_kokoro") as k, \
                 mock.patch("tts_runner.synth_neutts") as n:
                rc = tts_runner.main(["--engine", "kokoro", job])
            self.assertEqual(rc, 0); k.assert_called_once(); n.assert_not_called()

    def test_dispatch_neutts(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = self._job(tmp, "neutts")
            with mock.patch("tts_runner.synth_kokoro") as k, \
                 mock.patch("tts_runner.synth_neutts") as n:
                rc = tts_runner.main(["--engine", "neutts", job])
            self.assertEqual(rc, 0); n.assert_called_once(); k.assert_not_called()

    def test_engine_failure_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = self._job(tmp, "kokoro")
            with mock.patch("tts_runner.synth_kokoro", side_effect=RuntimeError("boom")):
                rc = tts_runner.main(["--engine", "kokoro", job])
            self.assertEqual(rc, 1)
```

- [ ] **Step 2: run → fail** (`ModuleNotFoundError: No module named 'tts_runner'`):
`python3 -m unittest scripts.tests.test_tts_runner -v`

- [ ] **Step 3: implement**

Create `scripts/tts_runner.py`:
```python
#!/usr/bin/env python3
"""Batch TTS runner — executed by a provider's venv python (NOT the system one).

Usage:  <engine_python> scripts/tts_runner.py --engine kokoro|neutts job.json

Loads the engine's model ONCE and synthesizes every segment in the job to its
out_path (24 kHz wav). Engine packages are imported lazily so this module's
dispatch logic stays importable under any Python."""
import argparse
import json
import sys


def synth_kokoro(job):
    """Synthesize all segments with Kokoro (kokoro-onnx). Loads model once."""
    import soundfile as sf
    from kokoro_onnx import Kokoro
    k = Kokoro(job["model"], job["voices"])
    for seg in job["segments"]:
        samples, sr = k.create(seg["text"], voice=job.get("voice", "af_heart"),
                               speed=1.0, lang="en-us")
        sf.write(seg["out_path"], samples, sr)


def synth_neutts(job):
    """Synthesize all segments with NeuTTS Air. Transcribes the reference with
    Whisper if no transcript; loads backbone+codec once; encodes reference once."""
    import os
    import soundfile as sf
    from neuttsair.neutts import NeuTTSAir
    ref_text_path = job.get("ref_text_path") or ""
    if not (ref_text_path and os.path.exists(ref_text_path) and open(ref_text_path).read().strip()):
        from transformers import pipeline
        asr = pipeline("automatic-speech-recognition", model="openai/whisper-base.en")
        text = asr(job["ref_audio"])["text"].strip()
        ref_text_path = ref_text_path or (job["ref_audio"].rsplit(".", 1)[0] + ".txt")
        open(ref_text_path, "w", encoding="utf-8").write(text + "\n")
    tts = NeuTTSAir(backbone_repo=job["backbone"], backbone_device="cpu",
                    codec_repo="neuphonic/neucodec", codec_device="cpu")
    ref_codes = tts.encode_reference(job["ref_audio"])
    ref_text = open(ref_text_path, encoding="utf-8").read().strip()
    for seg in job["segments"]:
        wav = tts.infer(seg["text"], ref_codes, ref_text)
        sf.write(seg["out_path"], wav, 24000)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tts_runner")
    parser.add_argument("--engine", required=True, choices=("kokoro", "neutts"))
    parser.add_argument("job")
    args = parser.parse_args(argv)
    with open(args.job, encoding="utf-8") as fh:
        job = json.load(fh)
    try:
        (synth_kokoro if args.engine == "kokoro" else synth_neutts)(job)
    except Exception as exc:  # noqa: BLE001 — report any engine failure as exit 1
        print(f"tts_runner ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"written": [s["out_path"] for s in job["segments"]]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
**Verify the NeuTTS API before finalizing `synth_neutts`:** read the cloned
repo's `examples/basic_example.py` and `neuttsair/neutts.py` (the `NeuTTSAir`
class) to confirm the exact constructor kwargs and the encode/infer method names
(`encode_reference`, `infer`, sample rate). The example is the source of truth —
`synth_neutts` must batch (load once, loop `infer`) rather than call the example
per beat. This function is isolated and covered by the guarded integration test
(Task 7) when `NEUTTS_PYTHON` is set; adjust only `synth_neutts` if names differ.

- [ ] **Step 4: run → pass** (`python3 -m unittest scripts.tests.test_tts_runner -v`).

- [ ] **Step 5: commit**
```bash
git add scripts/tts_runner.py scripts/tests/test_tts_runner.py
git commit -m "feat(tts): batch venv runner (kokoro/neutts dispatch, lazy engine imports)"
```
`scripts/tts_runner.py` is drift-mapped → add a sentence to `video-engine.md` in this commit; keep validate-articles green.

---

## Task 4: build_video provider plumbing — readiness, job build, runner call, caching

**Files:**
- Modify: `scripts/build_video.py`
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: tests**
```python
class TestProviderPlumbing(unittest.TestCase):
    def _manifest(self, base):
        graph = os.path.join(base, "g"); registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", True); make_figure(registry, "tcp", 2)
        return bv.build_manifest(graph, registry)[0]

    def test_kokoro_unconfigured_raises(self):
        with tempfile.TemporaryDirectory() as base:
            m = self._manifest(base); fr = os.path.join(base, "f"); os.makedirs(fr)
            cfg = {"python": "/no/such/py", "model": "x.onnx", "voices": "v.bin", "voice": "af_heart"}
            with self.assertRaises(bv.TtsError):
                bv._synthesize_segments(m, fr, "kokoro", cfg, have_say=True)

    def test_neutts_unconfigured_falls_back_to_say(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as base:
            m = self._manifest(base); fr = os.path.join(base, "f"); os.makedirs(fr)
            cfg = {"python": "/no/such/py", "voice_dir": os.path.join(base, "vp"), "backbone": "bb"}
            with mock.patch("build_video._say_segment",
                            side_effect=lambda t, p: (open(p, "wb").close() or p) if t.strip() else None):
                segs, notes = bv._synthesize_segments(m, fr, "neutts", cfg, have_say=True)
            self.assertTrue(any("neutts" in n.lower() for n in notes))
            self.assertEqual(len(segs), len(m["slides"]))

    def test_kokoro_ready_calls_runner_and_maps_segments(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as base:
            m = self._manifest(base); fr = os.path.join(base, "f"); os.makedirs(fr)
            py = os.path.join(base, "py"); open(py, "w").close()
            model = os.path.join(base, "m.onnx"); open(model, "w").close()
            voices = os.path.join(base, "v.bin"); open(voices, "w").close()
            cfg = {"python": py, "model": model, "voices": voices, "voice": "af_heart"}
            def fake_run(args, **k):
                job = json.load(open(args[-1]))
                for s in job["segments"]:
                    open(s["out_path"], "wb").close()
                return mock.Mock(returncode=0)
            with mock.patch("build_video.subprocess.run", side_effect=fake_run) as run:
                segs, notes = bv._synthesize_segments(m, fr, "kokoro", cfg, have_say=True)
            self.assertTrue(run.called)
            narrated = [s for s, sl in zip(segs, m["slides"]) if sl["narration"].strip()]
            self.assertTrue(all(p and os.path.exists(p) for p in narrated))
```

- [ ] **Step 2: run → fail** (kokoro/neutts branches don't exist yet; tests error/assert-fail):
`python3 -m unittest scripts.tests.test_build_video.TestProviderPlumbing -v`

- [ ] **Step 3: implement**

Add to `scripts/build_video.py`: `import hashlib` (to the import block) and the
module constant `TTS_RUNNER = os.path.join(_HERE, "tts_runner.py")` near the
other path constants (`_HERE`/`_REPO`/`PLAYER_TEMPLATE` already exist). Then add:
```python
def _kokoro_ready(cfg):
    if not cfg or not cfg.get("python") or not os.path.exists(cfg["python"]):
        return False, "set --kokoro-python / KOKORO_PYTHON to the Kokoro venv"
    for key in ("model", "voices"):
        if not cfg.get(key) or not os.path.exists(cfg[key]):
            return False, f"set --kokoro-{key} / KOKORO_{key.upper()} (missing {key} file)"
    return True, None


def _neutts_ready(cfg):
    if not cfg or not cfg.get("python") or not os.path.exists(cfg["python"]):
        return False, "set --neutts-python / NEUTTS_PYTHON to the NeuTTS venv"
    ref = os.path.join(cfg.get("voice_dir", ""), "ref.wav")
    if not os.path.exists(ref):
        return False, f"missing reference clip: {ref}"
    return True, None


def _seg_cache_path(frames_dir, engine, voice_key, text):
    h = hashlib.sha1(f"{engine}|{voice_key}|{text}".encode("utf-8")).hexdigest()[:16]
    return os.path.join(frames_dir, f"tts-{engine}-{h}.wav")


def _engine_segments(engine, cfg, manifest, frames_dir):
    """Build a job (uncached beats only), run the venv runner once, return a
    per-slide list of wav paths (or None for non-narration slides)."""
    voice_key = cfg.get("voice") or cfg.get("backbone") or ""
    out_paths, todo = [], []
    for s in manifest["slides"]:
        text = (s["narration"] or "").strip()
        if not text:
            out_paths.append(None); continue
        p = _seg_cache_path(frames_dir, engine, voice_key, text)
        out_paths.append(p)
        if not os.path.exists(p):
            todo.append({"text": text, "out_path": p})
    if todo:
        job = {"engine": engine, "segments": todo}
        if engine == "kokoro":
            job.update(model=cfg["model"], voices=cfg["voices"], voice=cfg.get("voice", "af_heart"))
        else:
            ref_clean = _prepare_neutts_ref(cfg["voice_dir"])
            job.update(ref_audio=ref_clean,
                       ref_text_path=os.path.join(cfg["voice_dir"], "ref.txt"),
                       backbone=cfg.get("backbone", "neuphonic/neutts-air-q8-gguf"))
        job_path = os.path.join(frames_dir, f"tts-job-{engine}.json")
        os.makedirs(frames_dir, exist_ok=True)
        with open(job_path, "w", encoding="utf-8") as fh:
            json.dump(job, fh)
        subprocess.run([cfg["python"], TTS_RUNNER, "--engine", engine, job_path], check=True)
    return out_paths


def _prepare_neutts_ref(voice_dir):
    """Ensure a denoised ref_clean.wav exists (ffmpeg); return its path."""
    raw = os.path.join(voice_dir, "ref.wav")
    clean = os.path.join(voice_dir, "ref_clean.wav")
    if not os.path.exists(clean):
        subprocess.run(["ffmpeg", "-y", "-i", raw, "-ac", "1", "-ar", "16000",
                        "-af", "highpass=f=80,afftdn=nr=24:nf=-35", clean], check=True)
    return clean
```
Then extend `_synthesize_segments` — replace its kokoro/neutts placeholder tail
(everything after the `if tts == "say":` block) with:
```python
    if tts == "kokoro":
        ok, why = _kokoro_ready(cfg)
        if not ok:
            raise TtsError(f"--tts kokoro: {why}. See docs/tts-and-ffmpeg-notes.md, "
                           f"or use --tts say.")
        try:
            return _engine_segments("kokoro", cfg, manifest, frames_dir), notes
        except (subprocess.CalledProcessError, OSError) as exc:
            raise TtsError(f"kokoro synthesis failed: {exc}. See docs/tts-and-ffmpeg-notes.md, "
                           f"or use --tts say.")
    if tts == "neutts":
        ok, why = _neutts_ready(cfg)
        if not ok:
            notes.append(f"--tts neutts unavailable ({why}) — narrating with `say`. "
                         f"See docs/tts-and-ffmpeg-notes.md.")
            return _say_segments(manifest, frames_dir, have_say, notes), notes
        try:
            return _engine_segments("neutts", cfg, manifest, frames_dir), notes
        except (subprocess.CalledProcessError, OSError) as exc:
            notes.append(f"neutts synthesis failed ({exc}) — narrating with `say`.")
            return _say_segments(manifest, frames_dir, have_say, notes), notes
    return _say_segments(manifest, frames_dir, have_say, notes), notes
```

- [ ] **Step 4: run → pass** (`python3 -m unittest scripts.tests.test_build_video -v`).

- [ ] **Step 5: commit**
```bash
git add scripts/build_video.py scripts/tests/test_build_video.py
git commit -m "feat(tts): kokoro/neutts dispatch, readiness checks, caching, ref denoise"
```
Update `video-engine.md`; keep validate-articles green.

---

## Task 5: wire `tts`/`cfg` through `render_mp4` + `build`

**Files:**
- Modify: `scripts/build_video.py`
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: tests**
```python
class TestRenderMp4Tts(unittest.TestCase):
    def _manifest(self, base):
        graph = os.path.join(base, "g"); registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", True); make_figure(registry, "tcp", 1)
        return bv.build_manifest(graph, registry)[0]

    def test_render_mp4_default_tts_is_say(self):
        # render_mp4's own default param stays "say" (keeps existing direct callers working)
        from unittest import mock
        with tempfile.TemporaryDirectory() as base:
            m = self._manifest(base)
            def which(c): return "/usr/bin/ffmpeg" if c == "ffmpeg" else ("/usr/bin/say" if c == "say" else None)
            with mock.patch("build_video.shutil.which", side_effect=which), \
                 mock.patch("build_video._have_rasterizer", return_value=True), \
                 mock.patch("build_video.render.export_png", side_effect=lambda s, p, **k: open(p, "wb").close() or p), \
                 mock.patch("build_video.subprocess.run", return_value=mock.Mock(returncode=0)), \
                 mock.patch("build_video._say_segment", side_effect=lambda t, p: (open(p, "wb").close() or p) if t.strip() else None):
                path, notes = bv.render_mp4(m, base, bv.STAGE)   # no tts arg
            self.assertEqual(path, os.path.join(base, "video.mp4"))

    def test_render_mp4_kokoro_unconfigured_raises(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as base:
            m = self._manifest(base)
            def which(c): return "/usr/bin/ffmpeg" if c == "ffmpeg" else None
            with mock.patch("build_video.shutil.which", side_effect=which), \
                 mock.patch("build_video._have_rasterizer", return_value=True), \
                 mock.patch("build_video.render.export_png", side_effect=lambda s, p, **k: open(p, "wb").close() or p):
                with self.assertRaises(bv.TtsError):
                    bv.render_mp4(m, base, bv.STAGE, tts="kokoro",
                                  cfg={"python": "/no/such", "model": "m", "voices": "v", "voice": "af_heart"})
```

- [ ] **Step 2: run → fail** (`render_mp4` has no `tts`/`cfg` kwargs):
`python3 -m unittest scripts.tests.test_build_video.TestRenderMp4Tts -v`

- [ ] **Step 3: implement**

Change `render_mp4`'s signature and its segment call. Signature:
```python
def render_mp4(manifest, out_dir, stage, tts="say", cfg=None):
```
Replace the Task-2 line `segments, seg_notes = _synthesize_segments(manifest, frames_dir, "say", None, have_say)` with:
```python
    segments, seg_notes = _synthesize_segments(manifest, frames_dir, tts, cfg, have_say)
    notes.extend(seg_notes)
```
In `build(...)`, change the signature and the `render_mp4` call:
```python
def build(graph_dir, registry_root, out_dir, fmt="html", wpm=DEFAULT_WPM, stage=STAGE,
          tts="kokoro", cfg=None):
    ...
    if fmt in ("mp4", "both"):
        _, mp4_notes = render_mp4(manifest, video_dir, stage, tts=tts, cfg=cfg)
        notes.extend(mp4_notes)
```
(`build`'s default `tts="kokoro"` is the user-facing default; `render_mp4`'s own
default stays `"say"` so direct/unit callers and existing tests are unaffected.)

- [ ] **Step 4: run → pass** (`python3 -m unittest scripts.tests.test_build_video -v`; the existing TestBuildAndCli/TestMp4Fallback all still pass because they call `render_mp4`/`build` without a `tts` arg → `say` for render_mp4, and `build`'s mp4 tests use `fmt="html"`).

NOTE: verify `TestBuildAndCli.test_build_html_writes_expected_files` still passes
— it uses `fmt="html"`, so no TTS runs. If any existing `build(...)` test uses
`fmt="mp4"`/`"both"` it would now default to kokoro and raise; none do (the suite
only exercises mp4 via `render_mp4` directly), but confirm in the run.

- [ ] **Step 5: commit**
```bash
git add scripts/build_video.py scripts/tests/test_build_video.py
git commit -m "feat(tts): thread tts/cfg through render_mp4 and build (CLI default kokoro)"
```

---

## Task 6: CLI flags + main() error handling + workflow pass-through

**Files:**
- Modify: `scripts/build_video.py` (`main`)
- Modify: `.claude/workflows/dummies-notes.js`
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: tests**
```python
class TestTtsCli(unittest.TestCase):
    def _topic(self, base):
        graph = os.path.join(base, "g"); registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", True); make_figure(registry, "tcp", 1)
        return graph, registry

    def test_cli_html_ignores_tts(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = self._topic(base); out = os.path.join(base, "o")
            rc = bv.main([graph, "--registry", registry, "--out", out,
                          "--format", "html", "--tts", "kokoro"])
            self.assertEqual(rc, 0)  # html path runs no TTS, so kokoro config is irrelevant

    def test_cli_mp4_kokoro_unconfigured_exits_1(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as base:
            graph, registry = self._topic(base); out = os.path.join(base, "o")
            def which(c): return "/usr/bin/ffmpeg" if c == "ffmpeg" else None
            with mock.patch("build_video.shutil.which", side_effect=which), \
                 mock.patch("build_video._have_rasterizer", return_value=True), \
                 mock.patch("build_video.render.export_png", side_effect=lambda s, p, **k: open(p, "wb").close() or p):
                rc = bv.main([graph, "--registry", registry, "--out", out,
                              "--format", "mp4", "--tts", "kokoro"])  # no KOKORO_PYTHON
            self.assertEqual(rc, 1)
```

- [ ] **Step 2: run → fail** (`--tts` unknown arg / no TtsError handling):
`python3 -m unittest scripts.tests.test_build_video.TestTtsCli -v`

- [ ] **Step 3: implement `main` flags + error handling**

In `main`, add args after `--wpm`:
```python
    parser.add_argument("--tts", choices=("say", "kokoro", "neutts"), default="kokoro")
    parser.add_argument("--kokoro-python", default=os.environ.get("KOKORO_PYTHON"))
    parser.add_argument("--kokoro-model", default=os.environ.get("KOKORO_MODEL"))
    parser.add_argument("--kokoro-voices", default=os.environ.get("KOKORO_VOICES"))
    parser.add_argument("--kokoro-voice", default="af_heart")
    parser.add_argument("--neutts-python", default=os.environ.get("NEUTTS_PYTHON"))
    parser.add_argument("--neutts-voice", default="default")
    parser.add_argument("--neutts-backbone", default="neuphonic/neutts-air-q8-gguf")
```
Build `cfg` and call `build`, catching `TtsError`:
```python
    if args.tts == "kokoro":
        cfg = {"python": args.kokoro_python, "model": args.kokoro_model,
               "voices": args.kokoro_voices, "voice": args.kokoro_voice}
    elif args.tts == "neutts":
        cfg = {"python": args.neutts_python,
               "voice_dir": os.path.join(_REPO, "voice-profiles", args.neutts_voice),
               "backbone": args.neutts_backbone}
    else:
        cfg = None
    try:
        result, issues = build(args.graph_dir, args.registry, args.out,
                               fmt=args.format, wpm=args.wpm, tts=args.tts, cfg=cfg)
    except (ValueError, TtsError) as exc:
        print(f"ERROR  {exc}")
        return 1
```
(Replace the existing `try/except ValueError` block with the above.)

- [ ] **Step 4: workflow pass-through**

In `.claude/workflows/dummies-notes.js`, in the flag-gated `Video` phase, extend
the `build_video.py` command the agent runs to forward TTS settings from args/env.
After the existing args parse near the top, add:
```javascript
const TTS = (A && A.tts) || 'say'   // workflow default = say (zero-dep); opt into kokoro/neutts explicitly
```
and in the Video phase agent prompt, change the command string to include
`--tts ${TTS}` and instruct the agent to pass `--kokoro-python "$KOKORO_PYTHON"`
(resp. `--neutts-python "$NEUTTS_PYTHON"`) when that env var is set. Update the
`meta.whenToUse` to mention `tts?: "say"|"kokoro"|"neutts"`.
(The workflow keeps `say` as ITS default — a hands-off `makeVideo` run shouldn't
hard-fail on a server without Kokoro; users opt into kokoro/neutts via `tts`.)

- [ ] **Step 5: run → pass + `node --check`**
```bash
python3 -m unittest scripts.tests.test_build_video -v
node --check .claude/workflows/dummies-notes.js
```

- [ ] **Step 6: commit**
```bash
git add scripts/build_video.py .claude/workflows/dummies-notes.js scripts/tests/test_build_video.py
git commit -m "feat(tts): --tts CLI flags + kokoro hard-error exit + workflow pass-through"
```
Update `video-engine.md` AND `orchestration-workflow.md` (workflow change) in this commit; keep validate-articles green.

---

## Task 7: docs, regression, guarded real-engine smoke

**Files:**
- Modify: `knowledge/concepts/dummies-notes/video-engine.md`, `knowledge/log.md`
- Test: `scripts/tests/test_build_video.py` (one guarded test)

- [ ] **Step 1: guarded integration test** (runs only if a real Kokoro venv is configured)
```python
class TestKokoroReal(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("KOKORO_PYTHON") and os.environ.get("KOKORO_MODEL")
                         and os.environ.get("KOKORO_VOICES"), "Kokoro venv not configured")
    def test_real_kokoro_one_beat(self):
        with tempfile.TemporaryDirectory() as base:
            fr = os.path.join(base, "f"); os.makedirs(fr)
            cfg = {"python": os.environ["KOKORO_PYTHON"], "model": os.environ["KOKORO_MODEL"],
                   "voices": os.environ["KOKORO_VOICES"], "voice": "af_heart"}
            m = {"slides": [{"narration": "Hello from Kokoro.", "image": None,
                             "caption": "", "kind": "frame", "concept_slug": "x",
                             "duration_s": 2.0, "transition": "cut", "reveal_to": None}]}
            segs, notes = bv._synthesize_segments(m, fr, "kokoro", cfg, have_say=True)
            self.assertTrue(segs[0] and os.path.exists(segs[0]) and os.path.getsize(segs[0]) > 0)
```

- [ ] **Step 2: run the full suites**
```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'
```
Expected: all pass (the Kokoro real test SKIPS unless env is set).

- [ ] **Step 3: finalize `video-engine.md`** — ensure it documents: the three providers, the `tts_runner.py` job shape, the default (CLI kokoro / workflow say), the kokoro-hard-error vs neutts-fallback policy, the voice-profile layout, and that TTS is MP4-only. Bump `updated: 2026-06-14`.

- [ ] **Step 4: log + validate + commit**

Append to END of `knowledge/log.md`:
```markdown
- 2026-06-14 — Phase 8 complete: pluggable --tts say|kokoro|neutts. CLI default kokoro (hard-error if unconfigured), neutts opt-in cloned voice (falls back to say), say zero-dep fallback. One venv batch runner scripts/tts_runner.py; ffmpeg-denoised + Whisper-auto-transcribed NeuTTS reference; per-beat caching; MP4-only. Workflow default stays say.
```
```bash
python3 scripts/validate-articles
git add knowledge/concepts/dummies-notes/video-engine.md knowledge/log.md scripts/tests/test_build_video.py
git commit -m "docs(tts): finalize video-engine provider docs + guarded kokoro smoke"
```

---

## Notes for the implementer

- **Never `--no-verify`.** `scripts/build_video.py` + `scripts/tts_runner.py` → `video-engine.md`; `.claude/workflows/**` → `orchestration-workflow.md`. Update the mapped article in the same commit; keep `validate-articles` green.
- **Backward compatibility:** `render_mp4`'s own `tts` default is `"say"` and `--format html` runs no TTS — so all existing tests and the zero-dep HTML path are unchanged. Only `build`/CLI default to `kokoro`, and only for `--format mp4|both`.
- **Zero new deps in `build_video.py`/`tts_runner.py` top level** — engine packages are imported lazily inside the runner, which executes under the user's venv, never the system Python.
- Run tests from the repo root so `build_video`/`tts_runner` resolve their sibling imports.
