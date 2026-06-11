import json
import os
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import build_video as bv  # noqa: E402
import concept_registry as reg  # noqa: E402


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


def make_figure(registry_root, slug, n_frames=2):
    """Register slug and attach a figure dir with n_frames SVG frames."""
    reg.register(registry_root, slug, slug.replace("-", " ").title(),
                 f"Plain definition of {slug}.")
    fig_dir = os.path.join(registry_root, slug, "figure")
    os.makedirs(fig_dir, exist_ok=True)
    frames = []
    for i in range(1, n_frames + 1):
        fname = f"frame-{i:02d}.svg"
        with open(os.path.join(fig_dir, fname), "w", encoding="utf-8") as fh:
            fh.write(f'<svg viewBox="0 0 680 220"><text>{slug} {i}</text></svg>')
        frames.append({"file": fname, "caption": f"{slug} caption {i}",
                       "runbook": "rb", "commentary": f"This is narration for {slug} frame {i}."})
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


if __name__ == "__main__":
    unittest.main()
