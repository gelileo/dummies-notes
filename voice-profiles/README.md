# Voice profiles (NeuTTS cloned voices)

Each profile is a directory `voice-profiles/<name>/` used by `--tts neutts --neutts-voice <name>`:

- `ref.wav` — **you provide this**: a clean ~10–15 s mono clip of the voice to clone.
- `ref_clean.wav` — generated (ffmpeg denoise of `ref.wav`).
- `ref.txt` — transcript; provide it, or it is auto-generated (Whisper) on first run.
- `ref_clean.pt` — generated NeuTTS encoded-reference cache.

Everything except this README is git-ignored — voice clips never get committed.
Setup for the NeuTTS venv itself is in `docs/tts-and-ffmpeg-notes.md`.
