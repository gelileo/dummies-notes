import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import build_video as bv  # noqa: E402
import concept_registry as reg  # noqa: E402


def _has_cairosvg():
    try:
        import cairosvg  # noqa: F401
        return True
    except ImportError:
        return False


def write_decomp(graph_dir, slug, atomic, prereqs=(), figurable=None):
    os.makedirs(graph_dir, exist_ok=True)
    data = {
        "concept": {"slug": slug, "name": slug.replace("-", " ").title(),
                    "definition": f"Plain definition of {slug}."},
        "audience": "a curious adult with no domain background",
        "atomic": atomic,
        "mechanism_figurable": atomic if figurable is None else figurable,
        "atomic_reason": "fixture.",
        "prerequisites": [
            {"slug": p, "name": p.replace("-", " ").title(),
             "definition": f"Plain definition of {p}.", "why": f"{slug} needs {p}."}
            for p in prereqs
        ],
    }
    with open(os.path.join(graph_dir, f"{slug}.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def make_figure(registry_root, slug, n_frames=2, beats=None):
    """Register slug and attach a figure dir with n_frames SVG frames.
    If beats is given, attach it to the first frame's figure.json entry."""
    reg.register(registry_root, slug, slug.replace("-", " ").title(),
                 f"Plain definition of {slug}.")
    fig_dir = os.path.join(registry_root, slug, "figure")
    os.makedirs(fig_dir, exist_ok=True)
    frames = []
    for i in range(1, n_frames + 1):
        fname = f"frame-{i:02d}.svg"
        with open(os.path.join(fig_dir, fname), "w", encoding="utf-8") as fh:
            fh.write('<svg class="cd-svg" xmlns="http://www.w3.org/2000/svg" '
                     'width="100%" viewBox="0 0 680 220" role="img">'
                     f'<text>{slug} {i}</text></svg>')
        frame = {"file": fname, "caption": f"{slug} caption {i}",
                 "runbook": "rb", "commentary": f"This is narration for {slug} frame {i}."}
        if i == 1 and beats:
            frame["beats"] = beats
        frames.append(frame)
    with open(os.path.join(fig_dir, "figure.json"), "w", encoding="utf-8") as fh:
        json.dump({"concept_slug": slug, "archetype": "illustrative",
                   "playback": "slideshow", "frames": frames}, fh)
    reg.attach_figure(registry_root, slug, fig_dir)


class TestDuration(unittest.TestCase):
    def test_word_count_drives_duration(self):
        # 15 words at 150 wpm = 6.0s, within clamp.
        text = " ".join(["word"] * 15)
        self.assertAlmostEqual(bv._duration_for(text, 150), 6.0, places=3)

    def test_short_text_clamped_to_min(self):
        self.assertEqual(bv._duration_for("hi", 150), bv.MIN_DUR)

    def test_long_text_clamped_to_max(self):
        text = " ".join(["word"] * 1000)
        self.assertEqual(bv._duration_for(text, 150), bv.MAX_DUR)


class TestManifest(unittest.TestCase):
    def _topic(self, base):
        graph = os.path.join(base, "g")
        registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", False, ["packets"])
        write_decomp(graph, "packets", True)
        make_figure(registry, "tcp", 2)
        make_figure(registry, "packets", 2)
        return graph, registry

    def test_order_and_slide_kinds(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = self._topic(base)
            manifest, issues = bv.build_manifest(graph, registry)
            self.assertEqual([m for lvl, m in issues if lvl == "ERROR"], [])
            kinds = [s["kind"] for s in manifest["slides"]]
            self.assertEqual(kinds[0], "title")
            self.assertEqual(kinds[-1], "closing")
            # packets (prereq) section+frames must precede tcp (root) section+frames
            slugs = [s["concept_slug"] for s in manifest["slides"]]
            self.assertLess(slugs.index("packets"), slugs.index("tcp"))
            # each figured node: one section then its frames
            self.assertIn("section", kinds)
            self.assertEqual(kinds.count("frame"), 4)  # 2 nodes x 2 frames

    def test_frame_slide_fields(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = self._topic(base)
            manifest, _ = bv.build_manifest(graph, registry)
            frame = next(s for s in manifest["slides"] if s["kind"] == "frame")
            self.assertTrue(os.path.isabs(frame["image"]))
            self.assertTrue(frame["image"].endswith(".svg"))
            self.assertTrue(frame["caption"])
            self.assertEqual(frame["narration"],
                             f"This is narration for {frame['concept_slug']} frame 1.")

    def test_figureless_node_skipped(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", False, ["packets"])
            write_decomp(graph, "packets", True)
            make_figure(registry, "tcp", 1)  # packets has NO figure
            reg.register(registry, "packets", "Packets", "Plain definition of packets.")
            manifest, _ = bv.build_manifest(graph, registry)
            slugs = {s["concept_slug"] for s in manifest["slides"]}
            self.assertIn("tcp", slugs)
            self.assertNotIn("packets", slugs)

    def test_transition_crossfade_within_concept_only(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = self._topic(base)
            manifest, _ = bv.build_manifest(graph, registry)
            for i, s in enumerate(manifest["slides"]):
                if s["transition"] == "crossfade":
                    prev = manifest["slides"][i - 1]
                    self.assertEqual(s["kind"], "frame")
                    self.assertEqual(prev["concept_slug"], s["concept_slug"])


class TestScriptAndCaptions(unittest.TestCase):
    def _manifest(self, base):
        graph = os.path.join(base, "g")
        registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", True)
        make_figure(registry, "tcp", 2)
        manifest, _ = bv.build_manifest(graph, registry)
        return manifest

    def test_srt_timestamp_format(self):
        self.assertEqual(bv._srt_timestamp(0), "00:00:00,000")
        self.assertEqual(bv._srt_timestamp(3661.5), "01:01:01,500")

    def test_captions_sequential_and_increasing(self):
        with tempfile.TemporaryDirectory() as base:
            manifest = self._manifest(base)
            out = os.path.join(base, "captions.srt")
            bv.write_captions(manifest, out)
            text = open(out, encoding="utf-8").read()
            blocks = text.strip().split("\n\n")
            self.assertEqual(len(blocks), len(manifest["slides"]))
            self.assertTrue(blocks[0].startswith("1\n"))
            self.assertIn("-->", blocks[0])

    def test_script_has_concept_headings(self):
        with tempfile.TemporaryDirectory() as base:
            manifest = self._manifest(base)
            out = os.path.join(base, "script.md")
            bv.write_script(manifest, out)
            text = open(out, encoding="utf-8").read()
            self.assertIn("## ", text)
            self.assertIn("narration", text.lower())


class TestStageSvg(unittest.TestCase):
    def _frame_slide(self, base):
        graph = os.path.join(base, "g")
        registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", True)
        make_figure(registry, "tcp", 1)
        manifest, _ = bv.build_manifest(graph, registry)
        return next(s for s in manifest["slides"] if s["kind"] == "frame")

    def test_frame_stage_embeds_nested_svg_and_caption(self):
        with tempfile.TemporaryDirectory() as base:
            slide = self._frame_slide(base)
            svg = bv.stage_svg(slide, bv.STAGE)
            self.assertTrue(svg.lstrip().startswith("<svg"))
            self.assertIn(f'viewBox="0 0 {bv.STAGE["width"]} {bv.STAGE["height"]}"', svg)
            self.assertEqual(svg.count("<svg"), 2)  # stage + nested figure
            self.assertIn(slide["caption"], svg)
            ET.fromstring(svg)  # well-formed XML

    def test_title_card_is_well_formed_text_only(self):
        slide = bv._slide("title", None, None, "TCP", "Some narration here.", 150, "cut")
        svg = bv.stage_svg(slide, bv.STAGE)
        self.assertEqual(svg.count("<svg"), 1)
        self.assertIn("TCP", svg)
        ET.fromstring(svg)


class TestPlayer(unittest.TestCase):
    def test_player_contains_manifest_and_controls(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", True)
            beats = [{"caption": "c1", "narration": "n1"},
                     {"caption": "c2", "narration": "n2"},
                     {"caption": "c3", "narration": "n3"}]
            make_figure(registry, "tcp", 1, beats=beats)
            manifest, _ = bv.build_manifest(graph, registry)
            out = os.path.join(base, "video.html")
            bv.build_player(manifest, bv.PLAYER_TEMPLATE, out)
            text = open(out, encoding="utf-8").read()
            self.assertIn("window.__MANIFEST__", text)
            self.assertIn('id="play"', text)
            self.assertNotIn("{{MANIFEST_JSON}}", text)
            self.assertNotIn("{{SLIDES_HTML}}", text)
            self.assertEqual(text.count("tcp 1"), 1)  # figure inlined ONCE despite 3 beats
            self.assertIn('"reveal_to"', text)
            self.assertIn('"container"', text)

    def test_player_escapes_script_breakout_in_narration(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", True)
            make_figure(registry, "tcp", 1)
            manifest, _ = bv.build_manifest(graph, registry)
            manifest["slides"][0]["narration"] = "Danger </script><script>alert(1)</script> end."
            out = os.path.join(base, "video.html")
            bv.build_player(manifest, bv.PLAYER_TEMPLATE, out)
            text = open(out, encoding="utf-8").read()
            # the injected narration must NOT introduce a raw script breakout
            self.assertNotIn("</script><script>alert", text)
            # it appears in escaped form instead
            self.assertIn("\\u003c/script\\u003e", text)


class TestPlayerContainers(unittest.TestCase):
    def test_beats_share_one_container_cards_separate(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", True)
            make_figure(registry, "tcp", 1,
                        beats=[{"caption": "a", "narration": "a"},
                               {"caption": "b", "narration": "b"}])
            manifest, _ = bv.build_manifest(graph, registry)
            conts, idx = bv._containers(manifest["slides"])
            frame_slides = [j for j, s in enumerate(manifest["slides"]) if s["kind"] == "frame"]
            self.assertEqual(idx[frame_slides[0]], idx[frame_slides[1]])  # beats -> same container
            self.assertEqual(len(set(idx)), len(conts))  # idx covers every container


class TestMp4Fallback(unittest.TestCase):
    def _manifest(self, base):
        graph = os.path.join(base, "g")
        registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", True)
        make_figure(registry, "tcp", 2)
        manifest, _ = bv.build_manifest(graph, registry)
        return manifest

    def test_missing_ffmpeg_skips_mp4(self):
        with tempfile.TemporaryDirectory() as base:
            manifest = self._manifest(base)
            with mock.patch("build_video.shutil.which", return_value=None):
                path, notes = bv.render_mp4(manifest, base, bv.STAGE)
            self.assertIsNone(path)
            self.assertTrue(any("ffmpeg" in n for n in notes))

    def test_missing_say_renders_silent_with_note(self):
        with tempfile.TemporaryDirectory() as base:
            manifest = self._manifest(base)

            def which(cmd):
                return "/usr/bin/ffmpeg" if cmd == "ffmpeg" else None

            with mock.patch("build_video.shutil.which", side_effect=which), \
                 mock.patch("build_video._have_rasterizer", return_value=True), \
                 mock.patch("build_video.render.export_png",
                            side_effect=lambda s, p, **k: open(p, "wb").close() or p), \
                 mock.patch("build_video.subprocess.run",
                            return_value=mock.Mock(returncode=0)) as run:
                path, notes = bv.render_mp4(manifest, base, bv.STAGE)
            self.assertEqual(path, os.path.join(base, "video.mp4"))
            self.assertTrue(any("silent" in n.lower() for n in notes))
            self.assertFalse(any(c.args and c.args[0] and c.args[0][0] == "say"
                                 for c in run.call_args_list))

    def test_say_present_drives_audio_mux(self):
        with tempfile.TemporaryDirectory() as base:
            manifest = self._manifest(base)

            def which(cmd):
                return f"/usr/bin/{cmd}" if cmd in ("ffmpeg", "say") else None

            with mock.patch("build_video.shutil.which", side_effect=which), \
                 mock.patch("build_video._have_rasterizer", return_value=True), \
                 mock.patch("build_video.render.export_png",
                            side_effect=lambda s, p, **k: open(p, "wb").close() or p), \
                 mock.patch("build_video.subprocess.run",
                            return_value=mock.Mock(returncode=0)) as run:
                path, notes = bv.render_mp4(manifest, base, bv.STAGE)
            self.assertEqual(path, os.path.join(base, "video.mp4"))
            self.assertTrue(any(c.args and c.args[0] and c.args[0][0] == "say"
                                for c in run.call_args_list))

    def test_missing_rasterizer_skips_mp4(self):
        with tempfile.TemporaryDirectory() as base:
            manifest = self._manifest(base)
            with mock.patch("build_video.shutil.which",
                            side_effect=lambda c: "/usr/bin/ffmpeg" if c == "ffmpeg" else None), \
                 mock.patch("build_video._have_rasterizer", return_value=False):
                path, notes = bv.render_mp4(manifest, base, bv.STAGE)
            self.assertIsNone(path)
            self.assertTrue(any("rasterizer" in n.lower() for n in notes))

    @unittest.skipUnless(shutil.which("ffmpeg") and
                         (shutil.which("rsvg-convert") or _has_cairosvg()),
                         "needs ffmpeg + an SVG rasterizer")
    def test_real_mp4_smoke(self):
        with tempfile.TemporaryDirectory() as base:
            manifest = self._manifest(base)
            path, _ = bv.render_mp4(manifest, base, bv.STAGE)
            self.assertTrue(path and os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)


class TestBuildAndCli(unittest.TestCase):
    def _topic(self, base):
        graph = os.path.join(base, "g")
        registry = os.path.join(base, "r")
        write_decomp(graph, "tcp", False, ["packets"])
        write_decomp(graph, "packets", True)
        make_figure(registry, "tcp", 2)
        make_figure(registry, "packets", 2)
        return graph, registry

    def test_build_html_writes_expected_files(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = self._topic(base)
            out = os.path.join(base, "out")
            result, issues = bv.build(graph, registry, out, fmt="html", wpm=150)
            self.assertEqual([m for lvl, m in issues if lvl == "ERROR"], [])
            vdir = os.path.join(out, "video")
            for name in ("manifest.json", "script.md", "captions.srt", "video.html"):
                self.assertTrue(os.path.exists(os.path.join(vdir, name)), name)
            self.assertFalse(os.path.exists(os.path.join(vdir, "video.mp4")))

    def test_cli_exit_zero(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = self._topic(base)
            out = os.path.join(base, "out")
            rc = bv.main([graph, "--registry", registry, "--out", out, "--format", "html"])
            self.assertEqual(rc, 0)

    def test_cli_bad_graph_exit_one(self):
        with tempfile.TemporaryDirectory() as base:
            rc = bv.main([os.path.join(base, "nope"), "--out", os.path.join(base, "o")])
            self.assertEqual(rc, 1)

    def test_manifest_image_paths_not_absolute(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = self._topic(base)
            out = os.path.join(base, "out")
            bv.build(graph, registry, out, fmt="html")
            data = json.load(open(os.path.join(out, "video", "manifest.json"),
                                  encoding="utf-8"))
            imgs = [s["image"] for s in data["slides"] if s["image"]]
            self.assertTrue(imgs)  # there are frame slides
            self.assertFalse(any(os.path.isabs(p) for p in imgs),
                             "on-disk manifest image paths must be repo-relative, not absolute")


class TestLoadFramesBeats(unittest.TestCase):
    def test_beats_read_when_present(self):
        with tempfile.TemporaryDirectory() as base:
            registry = os.path.join(base, "r")
            beats = [{"caption": "b1", "narration": "first beat"},
                     {"caption": "b2", "narration": "second beat"}]
            make_figure(registry, "tcp", 1, beats=beats)
            frames = bv.load_frames(os.path.join(registry, "tcp", "figure"))
            self.assertEqual(frames[0]["beats"], beats)

    def test_beats_none_when_absent(self):
        with tempfile.TemporaryDirectory() as base:
            registry = os.path.join(base, "r")
            make_figure(registry, "tcp", 2)
            frames = bv.load_frames(os.path.join(registry, "tcp", "figure"))
            self.assertIsNone(frames[0]["beats"])


class TestBeatExpansion(unittest.TestCase):
    def test_frame_with_beats_expands_to_one_slide_per_beat(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", True)
            beats = [{"caption": "c1", "narration": "n one"},
                     {"caption": "c2", "narration": "n two"},
                     {"caption": "c3", "narration": "n three"}]
            make_figure(registry, "tcp", 1, beats=beats)
            manifest, _ = bv.build_manifest(graph, registry)
            frames = [s for s in manifest["slides"] if s["kind"] == "frame"]
            self.assertEqual(len(frames), 3)
            self.assertEqual([s["reveal_to"] for s in frames], [1, 2, 3])
            self.assertEqual(frames[0]["caption"], "c1")
            self.assertEqual(frames[1]["narration"], "n two")
            self.assertNotEqual(frames[0]["transition"], "reveal")
            self.assertEqual(frames[1]["transition"], "reveal")
            self.assertEqual(frames[2]["transition"], "reveal")
            self.assertEqual(len({s["image"] for s in frames}), 1)

    def test_frame_without_beats_is_single_slide_reveal_none(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", True)
            make_figure(registry, "tcp", 2)
            manifest, _ = bv.build_manifest(graph, registry)
            frames = [s for s in manifest["slides"] if s["kind"] == "frame"]
            self.assertEqual(len(frames), 2)
            self.assertTrue(all(s["reveal_to"] is None for s in frames))

    def test_title_slides_have_reveal_to_none(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", True)
            make_figure(registry, "tcp", 1)
            manifest, _ = bv.build_manifest(graph, registry)
            self.assertIsNone(manifest["slides"][0]["reveal_to"])


_REVEAL_SVG = (
    '<svg class="cd-svg" xmlns="http://www.w3.org/2000/svg" width="100%" '
    'viewBox="0 0 680 220" role="img">'
    '<g data-reveal="1"><rect x="1" y="1" width="10" height="10"/></g>'
    '<g data-reveal="2" data-anim="draw"><line x1="0" y1="0" x2="9" y2="0"/></g>'
    '<g data-reveal="3"><text>z</text></g>'
    '<g><text>backdrop</text></g>'
    '</svg>')


class TestRevealSvg(unittest.TestCase):
    def test_none_passes_through(self):
        self.assertEqual(bv._reveal_svg(_REVEAL_SVG, None), _REVEAL_SVG)

    def test_hides_groups_beyond_reveal_to(self):
        out = bv._reveal_svg(_REVEAL_SVG, 2)
        ET.fromstring(out)  # well-formed
        self.assertEqual(out.count("visibility:hidden"), 1)
        self.assertIn('data-reveal="3"', out)
        g3 = out[out.index('data-reveal="3"') - 30: out.index('data-reveal="3"') + 30]
        self.assertIn("visibility:hidden", g3)

    def test_reveal_all_hides_nothing(self):
        out = bv._reveal_svg(_REVEAL_SVG, 3)
        self.assertNotIn("visibility:hidden", out)


class TestMixedMultiFrame(unittest.TestCase):
    def test_beats_frame_plus_plain_frame(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", True)
            make_figure(registry, "tcp", 2,
                        beats=[{"caption": "a", "narration": "a"},
                               {"caption": "b", "narration": "b"}])
            manifest, _ = bv.build_manifest(graph, registry)
            frames = [s for s in manifest["slides"] if s["kind"] == "frame"]
            # frame 1 -> 2 beat slides (reveal_to 1,2); frame 2 -> 1 slide (reveal_to None)
            self.assertEqual([s["reveal_to"] for s in frames], [1, 2, None])
            conts, idx = bv._containers(manifest["slides"])
            fidx = [j for j, s in enumerate(manifest["slides"]) if s["kind"] == "frame"]
            self.assertEqual(idx[fidx[0]], idx[fidx[1]])      # frame-1 beats share a container
            self.assertNotEqual(idx[fidx[1]], idx[fidx[2]])   # frame-2 is a distinct container


if __name__ == "__main__":
    unittest.main()
