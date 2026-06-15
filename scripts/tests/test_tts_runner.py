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

    def test_has_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(tts_runner._has_text(""))
            self.assertFalse(tts_runner._has_text(os.path.join(tmp, "nope.txt")))
            empty = os.path.join(tmp, "e.txt"); open(empty, "w").close()
            self.assertFalse(tts_runner._has_text(empty))
            full = os.path.join(tmp, "f.txt")
            with open(full, "w") as fh: fh.write("hi")
            self.assertTrue(tts_runner._has_text(full))
