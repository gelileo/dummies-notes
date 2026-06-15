#!/usr/bin/env python3
"""Batch TTS runner — executed by a provider's venv python (NOT the system one).

Usage:  <engine_python> scripts/tts_runner.py --engine kokoro|neutts job.json

Loads the engine's model ONCE and synthesizes every segment in the job to its
out_path (24 kHz wav). Engine packages are imported lazily so this module's
dispatch logic stays importable under any Python."""
import argparse
import json
import os
import sys


def _has_text(path):
    """True if `path` is a readable file with non-whitespace content."""
    if not path or not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as fh:
        return bool(fh.read().strip())


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
    import soundfile as sf
    from neuttsair.neutts import NeuTTSAir
    ref_text_path = job.get("ref_text_path") or ""
    if not _has_text(ref_text_path):
        from transformers import pipeline
        asr = pipeline("automatic-speech-recognition", model="openai/whisper-base.en")
        text = asr(job["ref_audio"])["text"].strip()
        ref_text_path = ref_text_path or (job["ref_audio"].rsplit(".", 1)[0] + ".txt")
        with open(ref_text_path, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    tts = NeuTTSAir(backbone_repo=job["backbone"], backbone_device="cpu",
                    codec_repo="neuphonic/neucodec", codec_device="cpu")
    ref_codes = tts.encode_reference(job["ref_audio"])
    with open(ref_text_path, encoding="utf-8") as fh:
        ref_text = fh.read().strip()
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
