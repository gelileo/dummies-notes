# TTS & audio-tooling notes

Working reference captured while exploring how to give the video engine more
natural narration than macOS `say`. None of this is wired into the code yet (the
`--tts` provider is still a future feature); these are reproducible setup +
recipe notes for the options we actually tried.

Throwaway exploration artifacts from the session live in `/tmp/tts-compare/`
(samples) and `/tmp/neutts-air` + `/tmp/neuttsvenv` (NeuTTS install). They are
disposable — this doc is the durable record.

**Quick verdict (June 2026):**

| Option | Quality | Runs | Cloning | Install weight | Cost |
|---|---|---|---|---|---|
| macOS `say` (legacy voices) | poor | offline | no | none (built in) | free |
| **Kokoro** | very good | offline, CPU | no (fixed voices) | light (ONNX, no torch) | free |
| **NeuTTS Air** | very good | offline, CPU | **yes** (from ~12s clip) | heavy (torch + llama-cpp + py≤3.13) | free |
| **Gemini 3.1 Flash TTS** | best (audio tags) | cloud | no (prebuilt voices) | none (HTTP) | API key + per-use |

All four emit audio per chunk; the video engine already generates **one clip per
beat**, so any of them slots into the same `_say_segment`-style step.

---

## 1. ffmpeg / ffprobe recipes (inspect, convert, cut, denoise, wrap PCM)

All zero-install (ffmpeg + ffprobe are already on the machine via Homebrew).

**Inspect a media file** (duration, channels, sample rate, codec):
```bash
ffprobe -v error \
  -show_entries format=duration:stream=channels,sample_rate,codec_name \
  -of default=noprint_wrappers=1 input.m4a
```

**Convert to mono 16 kHz WAV** (what TTS reference clips want):
```bash
ffmpeg -y -i clip.m4a -ac 1 -ar 16000 out.wav
```

**Cut / trim** — take the first N seconds, or a window `[START, START+DUR]`:
```bash
ffmpeg -y -i clip.m4a -t 12 first12s.wav                 # first 12 s
ffmpeg -y -i clip.m4a -ss 00:00:05 -t 12 window.wav      # 5 s → 17 s
```
(`-ss` before `-i` is faster/seek-accurate for big files; after `-i` is sample-accurate.)

**Denoise a reference clip** — the high-leverage fix when a cloned voice carries
room tone/hiss (clean the *reference*, not the output):
```bash
ffmpeg -y -i ref.wav -af "highpass=f=80,afftdn=nr=24:nf=-35" ref_clean.wav
```
- `highpass=f=80` — removes low rumble/AC hum below 80 Hz.
- `afftdn` — FFT denoiser; `nr` = noise reduction in dB (12–30; higher = more
  aggressive but riskier), `nf` = assumed noise floor in dB.
- Stronger options if needed: add `anlmdn` (non-local-means, good for steady
  noise) or `arnndn=m=model.rnnn` (RNN denoise, needs a model file). Pushing too
  hard yields a warbly/"underwater" voice — re-recording cleanly beats heavy
  denoise. For studio-clean results, a dedicated speech enhancer
  (DeepFilterNet, Resemble Enhance) outperforms ffmpeg.

**Wrap raw PCM into WAV** — cloud TTS (e.g. Gemini) returns headerless PCM
(signed 16-bit LE, 24 kHz, mono):
```bash
ffmpeg -y -f s16le -ar 24000 -ac 1 -i audio.pcm audio.wav
```
(Python stdlib alternative: the `wave` module — see §4.)

**(Reference)** the MP4 builder's own ffmpeg usage — image-concat with per-slide
hold, `apad`/`anullsrc` per-beat audio padding, and `-shortest` mux — is in
`scripts/build_video.py` / `knowledge/concepts/dummies-notes/video-engine.md`.

---

## 2. Kokoro — local, open-weight, offline (easiest local; no cloning)

Apache-2.0, 82M params, 54 baked-in voices, 8 languages, 24 kHz output. Runs on
CPU/Apple-Silicon via ONNX — **no torch**. Cannot clone (fixed voicepacks).

**Install** (works even on system Python 3.14):
```bash
python3 -m venv ~/.venvs/kokoro
~/.venvs/kokoro/bin/pip install kokoro-onnx soundfile
# optional, improves some G2P:  brew install espeak-ng
```

**Model files** (download once, ~340 MB) from the kokoro-onnx release:
```bash
B=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
curl -L -o kokoro-v1.0.onnx "$B/kokoro-v1.0.onnx"   # ~310 MB
curl -L -o voices-v1.0.bin  "$B/voices-v1.0.bin"    # ~27 MB
```

**Use:**
```python
from kokoro_onnx import Kokoro
import soundfile as sf
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
samples, sr = k.create("Your narration text.", voice="af_heart", speed=1.0, lang="en-us")
sf.write("out.wav", samples, sr)   # sr == 24000
```
Voices tried: `af_heart` (US ♀), `am_michael` (US ♂); also `bm_george` (UK ♂),
`bf_emma`, etc. Synthesis of one beat is fast on CPU.

---

## 3. NeuTTS Air — local, on-device **voice cloning**

Neuphonic, ~0.5B LLM backbone + NeuCodec, GGUF on-device. Clones a speaker from
a ~3–15 s reference clip + its transcript. ~30 s / 2048-token context (use short
per-beat chunks). Outputs carry a **Perth** watermark.

**Prereqs / gotchas:**
- **Python 3.10–3.13 only** (NOT 3.14 — the package pins `<3.14`). On this Mac:
  `python3.12` from Homebrew.
- System deps: `brew install espeak-ng cmake` (cmake builds `llama-cpp-python`).
- Heavy: pulls **torch**, `neucodec`, `phonemizer`, compiled `llama-cpp-python`,
  plus model downloads (backbone GGUF + codec) on first run (~GBs total).

**Install:**
```bash
git clone https://github.com/neuphonic/neutts-air.git
python3.12 -m venv ~/.venvs/neutts
cd neutts-air
~/.venvs/neutts/bin/pip install ".[llama]" soundfile   # ".[onnx]" for the ONNX path
```

**Clone a voice** — reference WAV (mono, clean, denoised per §1) + a transcript
text file matching it:
```bash
~/.venvs/neutts/bin/python -m examples.basic_example \
  --input_text "Your narration text." \
  --ref_audio ref_clean.wav \
  --ref_text  ref.txt \
  --backbone  neuphonic/neutts-air-q8-gguf \
  --output_path out.wav
```
- `--ref_text` is a **path to a .txt file**, not inline text.
- First run downloads `neuphonic/neutts-air-q8-gguf` (backbone) + `neuphonic/neucodec`.
- It caches encoded reference codes next to the WAV as `ref_clean.pt`; delete
  that `.pt` if you change/clean the reference, or it reuses the stale encoding.

**Auto-transcribe the reference** (so you don't hand-type `ref.txt`) — reuse the
already-installed `transformers` + `torch`, no extra package:
```python
from transformers import pipeline
asr = pipeline("automatic-speech-recognition", model="openai/whisper-base.en")
open("ref.txt", "w").write(asr("ref_clean.wav")["text"].strip())
```

**Cloning tips:** the clone copies the reference's acoustics — denoise first
(§1); keep the reference single-speaker, ~10–15 s, clean; cloning quality tracks
reference quality far more than reference length.

---

## 4. Gemini 3.1 Flash TTS — cloud, highest quality + audio tags

Google, launched 2026-04-15. Most expressive/controllable option: **audio tags**
(`[excited]`, `[whispers]`, `[sighs]`, `[very fast]`, …) inline in the text,
30 voices, 70+ languages, multi-speaker. Output is base64 **PCM L16 @ 24 kHz
mono**. SynthID watermark. Preview model.

**Key:** create a developer API key at <https://aistudio.google.com/apikey>
(format `AIza…`, ~39 chars). NOTE: a consumer *Gemini Advanced / Google One AI*
subscription is **not** the same as a developer API key. Put it in `.env`
(already gitignored):
```
GEMINI_API_KEY=AIza...your-real-key...
```

**Call** (stdlib only — `urllib`, `base64`, `wave`; no pip installs):
```python
import base64, json, os, urllib.request, wave
MODEL = "gemini-3.1-flash-tts-preview"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
body = {
    "contents": [{"parts": [{"text": "Your narration text."}]}],
    "generationConfig": {
        "responseModalities": ["AUDIO"],
        "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}},
    },
}
req = urllib.request.Request(
    URL, data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json",
             "x-goog-api-key": os.environ["GEMINI_API_KEY"]}, method="POST")
data = json.load(urllib.request.urlopen(req, timeout=60))
pcm = base64.b64decode(data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
with wave.open("out.wav", "wb") as w:        # PCM L16 24 kHz mono
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
```
Voices tried: `Kore`, `Puck`; also `Zephyr`, `Charon`, `Enceladus`. Read the key
from `.env` without echoing it:
```bash
KEY=$(grep -E '^[[:space:]]*(export[[:space:]]+)?GEMINI_API_KEY=' .env | head -1 \
      | sed -E 's/^[[:space:]]*(export[[:space:]]+)?GEMINI_API_KEY=//; s/\r$//; s/^["'"'"']//; s/["'"'"']$//')
GEMINI_API_KEY="$KEY" python3 your_script.py
```
The TTS preview model may need billing enabled on the key's Google Cloud project
even though a free tier exists for other models.

---

## 5. How these fit the video engine (forward note)

The planned `--tts say|kokoro|gemini|neutts` provider layer is just a swap of the
per-beat audio step: each provider returns one audio file per beat; the existing
duration-probe → concat → mux pipeline (`render_mp4` in `scripts/build_video.py`)
is unchanged. `say` stays the zero-dep default. NeuTTS would carry a configured
**voice profile** (reference clip + transcript), with a denoise pass (§1) and
optional Whisper auto-transcription (§3) applied to the reference automatically.
This is not built yet — see the brainstorming thread before implementing.
