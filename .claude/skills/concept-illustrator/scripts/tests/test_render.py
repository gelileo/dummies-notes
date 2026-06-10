import json
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import render  # noqa: E402


def svg(body, viewbox="0 0 680 200"):
    return ET.fromstring(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}">{body}</svg>'
    )


class TestHelpers(unittest.TestCase):
    def test_load_palette_extracts_lowercased_hexes(self):
        css = "text.t{fill:#1C1C1A;} .c-teal{stroke:#0F6E56;}"
        self.assertEqual(render.load_palette(css), {"#1c1c1a", "#0f6e56"})

    def test_localname_strips_namespace(self):
        el = svg("<text>hi</text>").find("{http://www.w3.org/2000/svg}text")
        self.assertEqual(render.localname(el.tag), "text")


class TestCanvasWidth(unittest.TestCase):
    def test_correct_width_passes(self):
        self.assertEqual(render.check_canvas_width(svg("")), [])

    def test_wrong_width_errors(self):
        out = render.check_canvas_width(svg("", viewbox="0 0 500 200"))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))

    def test_missing_viewbox_errors(self):
        root = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in render.check_canvas_width(root)))


class TestTextClasses(unittest.TestCase):
    def test_classed_text_passes(self):
        self.assertEqual(render.check_text_classes(svg('<text class="t">hi</text>')), [])

    def test_unclassed_text_errors(self):
        self.assertTrue(render.check_text_classes(svg("<text>hi</text>")))

    def test_inline_font_size_errors(self):
        out = render.check_text_classes(svg('<text class="t" font-size="20">hi</text>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))


class TestPlaceholders(unittest.TestCase):
    def test_clean_passes(self):
        self.assertEqual(render.check_placeholders(svg('<text class="t">real</text>')), [])

    def test_token_errors(self):
        self.assertTrue(render.check_placeholders(svg('<text class="t">TODO fix</text>')))


PALETTE = {"#1c1c1a", "#0f6e56"}


class TestPalette(unittest.TestCase):
    def test_palette_color_passes(self):
        out = render.check_palette(svg('<rect fill="#1C1C1A"/>'), PALETTE)
        self.assertEqual(out, [])

    def test_off_palette_errors(self):
        out = render.check_palette(svg('<rect fill="#abcdef"/>'), PALETTE)
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))

    def test_none_and_url_allowed(self):
        out = render.check_palette(
            svg('<path fill="none" marker-end="url(#arrow)" stroke="currentColor"/>'),
            PALETTE,
        )
        self.assertEqual(out, [])

    def test_named_color_errors(self):
        self.assertTrue(render.check_palette(svg('<rect fill="red"/>'), PALETTE))


class TestDecoration(unittest.TestCase):
    def test_filter_errors(self):
        out = render.check_decoration(svg('<filter id="f"></filter>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))

    def test_gradient_warns(self):
        out = render.check_decoration(svg('<linearGradient id="g"></linearGradient>'))
        self.assertTrue(any(lvl == "WARN" for lvl, _ in out))

    def test_emoji_errors(self):
        out = render.check_decoration(svg('<text class="t">hot \U0001f525</text>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))


class TestCaps(unittest.TestCase):
    def test_sentence_case_passes(self):
        self.assertEqual(render.check_caps(svg('<text class="t">Binary search</text>')), [])

    def test_all_caps_errors(self):
        out = render.check_caps(svg('<text class="t">BINARY SEARCH</text>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))

    def test_title_case_warns(self):
        out = render.check_caps(svg('<text class="t">Binary Search Tree</text>'))
        self.assertTrue(any(lvl == "WARN" for lvl, _ in out))


class TestBounds(unittest.TestCase):
    def test_in_bounds_passes(self):
        out = render.check_bounds(svg('<rect x="10" y="10" width="100" height="50"/>'))
        self.assertEqual(out, [])

    def test_overflow_width_errors(self):
        out = render.check_bounds(svg('<rect x="600" y="10" width="200" height="50"/>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))

    def test_overflow_height_errors(self):
        out = render.check_bounds(svg('<rect x="10" y="150" width="100" height="100"/>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))

    def test_missing_x_defaults_to_zero_and_overflow_errors(self):
        out = render.check_bounds(svg('<rect width="1000" height="50"/>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))


class TestConnectorFill(unittest.TestCase):
    def test_styled_connector_relying_on_css_passes(self):
        # class arr gets fill:none from the stylesheet; no inline fill is correct
        out = render.check_connector_fill(svg('<path class="arr" marker-end="url(#arrow)"/>'))
        self.assertEqual(out, [])

    def test_connector_with_fill_none_passes(self):
        out = render.check_connector_fill(
            svg('<path class="arr" fill="none" marker-end="url(#arrow)"/>')
        )
        self.assertEqual(out, [])

    def test_styled_connector_with_solid_fill_errors(self):
        out = render.check_connector_fill(svg('<path class="arr" fill="#1c1c1a"/>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))

    def test_marker_only_connector_requires_fill_none(self):
        out = render.check_connector_fill(svg('<path marker-end="url(#arrow)" d="M0,0 L9,0"/>'))
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))

    def test_marker_only_connector_with_fill_none_passes(self):
        out = render.check_connector_fill(
            svg('<path marker-end="url(#arrow)" fill="none" d="M0,0 L9,0"/>')
        )
        self.assertEqual(out, [])


class TestLintFile(unittest.TestCase):
    def test_reads_dirty_fixture_and_reports_errors(self):
        path = os.path.join(SCRIPTS_DIR, "tests", "fixtures", "dirty.svg")
        out = render.lint_file(path, "/nonexistent-style.css")
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in out))


class TestLintSvgAggregate(unittest.TestCase):
    def test_clean_svg_has_no_errors(self):
        root = svg('<text class="t">Binary search</text>')
        errors = [m for lvl, m in render.lint_svg(root, PALETTE) if lvl == "ERROR"]
        self.assertEqual(errors, [])

    def test_dirty_svg_collects_errors(self):
        root = svg('<text>UNCLASSED</text>', viewbox="0 0 500 200")
        errors = [m for lvl, m in render.lint_svg(root, PALETTE) if lvl == "ERROR"]
        self.assertGreaterEqual(len(errors), 2)


class TestSafeParse(unittest.TestCase):
    def test_doctype_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "evil.svg")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write('<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY x "x">]>'
                         '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 100"/>')
            out = render.lint_file(path, "/nonexistent-style.css")
            self.assertTrue(any("DOCTYPE" in m or "ENTITY" in m for _, m in out))


ASSETS = os.path.join(os.path.dirname(SCRIPTS_DIR), "assets")


class TestShippedAssets(unittest.TestCase):
    def test_style_css_exists_and_has_palette(self):
        css = render._read(os.path.join(ASSETS, "_style.css"))
        self.assertGreaterEqual(len(render.load_palette(css)), 9)

    def test_template_lints_clean(self):
        style = os.path.join(ASSETS, "_style.css")
        errors = [m for lvl, m in render.lint_file(os.path.join(ASSETS, "template.svg"), style)
                  if lvl == "ERROR"]
        self.assertEqual(errors, [], f"template.svg has lint errors: {errors}")


class TestValidateFigure(unittest.TestCase):
    def _write_figure(self, root, frames, data_overrides=None):
        os.makedirs(root, exist_ok=True)
        files = []
        for i, vb in enumerate(frames, 1):
            name = f"frame-{i:02d}.svg"
            with open(os.path.join(root, name), "w", encoding="utf-8") as fh:
                fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">'
                         f'<text class="t">Step {i}</text></svg>')
            files.append({"file": name, "caption": f"Step {i}"})
        data = {"concept_slug": "x", "archetype": "illustrative",
                "playback": "slideshow" if len(frames) > 1 else "static", "frames": files}
        data.update(data_overrides or {})
        with open(os.path.join(root, "figure.json"), "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def test_valid_figure_passes(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_figure(d, ["0 0 680 100", "0 0 680 100"])
            style = os.path.join(ASSETS, "_style.css")
            errors = [m for lvl, m in render.validate_figure(d, style) if lvl == "ERROR"]
            self.assertEqual(errors, [])

    def test_inconsistent_viewbox_errors(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_figure(d, ["0 0 680 100", "0 0 680 200"])
            style = os.path.join(ASSETS, "_style.css")
            errors = [m for lvl, m in render.validate_figure(d, style) if lvl == "ERROR"]
            self.assertTrue(any("viewBox" in m for m in errors))

    def test_missing_frame_file_errors(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_figure(d, ["0 0 680 100"])
            os.remove(os.path.join(d, "frame-01.svg"))
            style = os.path.join(ASSETS, "_style.css")
            errors = [m for lvl, m in render.validate_figure(d, style) if lvl == "ERROR"]
            self.assertTrue(errors)

    def test_missing_required_field_errors(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_figure(d, ["0 0 680 100"])
            with open(os.path.join(d, "figure.json"), "w") as fh:
                json.dump({"concept_slug": "x", "playback": "static",
                           "frames": [{"file": "frame-01.svg"}]}, fh)
            style = os.path.join(ASSETS, "_style.css")
            errors = [m for lvl, m in render.validate_figure(d, style) if lvl == "ERROR"]
            self.assertTrue(any("archetype" in m for m in errors))


class TestValidateFigurePlaybackAndViewbox(unittest.TestCase):
    def test_slideshow_with_one_frame_errors(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "frame-01.svg"), "w", encoding="utf-8") as fh:
                fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 100">'
                         '<text class="t">Only one</text></svg>')
            with open(os.path.join(d, "figure.json"), "w", encoding="utf-8") as fh:
                json.dump({"concept_slug": "x", "archetype": "illustrative",
                           "playback": "slideshow",
                           "frames": [{"file": "frame-01.svg", "caption": "one"}]}, fh)
            errors = [m for lvl, m in render.validate_figure(d, "/nonexistent.css")
                      if lvl == "ERROR"]
            self.assertTrue(any("more than one frame" in m for m in errors))

    def test_missing_viewbox_not_reported_as_inconsistency(self):
        with tempfile.TemporaryDirectory() as d:
            for i in (1, 2):
                with open(os.path.join(d, f"frame-{i:02d}.svg"), "w", encoding="utf-8") as fh:
                    fh.write(f'<svg xmlns="http://www.w3.org/2000/svg">'
                             f'<text class="t">Step {i}</text></svg>')
            with open(os.path.join(d, "figure.json"), "w", encoding="utf-8") as fh:
                json.dump({"concept_slug": "x", "archetype": "illustrative",
                           "playback": "slideshow",
                           "frames": [{"file": "frame-01.svg"}, {"file": "frame-02.svg"}]}, fh)
            msgs = [m for _, m in render.validate_figure(d, "/nonexistent.css")]
            self.assertFalse(any("inconsistent viewBox" in m for m in msgs))


class TestBuildViewer(unittest.TestCase):
    def test_inlines_all_frames(self):
        with tempfile.TemporaryDirectory() as d:
            for i in (1, 2):
                with open(os.path.join(d, f"frame-{i:02d}.svg"), "w") as fh:
                    fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 100">'
                             f'<text class="t">Step {i}</text></svg>')
            with open(os.path.join(d, "figure.json"), "w") as fh:
                json.dump({"concept_slug": "x", "archetype": "illustrative",
                           "playback": "slideshow", "title": "Demo",
                           "frames": [{"file": "frame-01.svg", "caption": "one"},
                                      {"file": "frame-02.svg", "caption": "two"}]}, fh)
            out = os.path.join(d, "figure.html")
            template = os.path.join(ASSETS, "slideshow.template.html")
            render.build_viewer(d, template, out)
            html = render._read(out)
            self.assertEqual(html.count("<svg"), 2)
            self.assertIn("Demo", html)
            self.assertIn("one", html)
            self.assertIn("two", html)
            self.assertNotIn("/*FRAMES*/[]", html)


import shutil


class TestPngExport(unittest.TestCase):
    def test_png_export_when_backend_available(self):
        if not (shutil.which("rsvg-convert") or _has_cairosvg()):
            self.skipTest("no rasterizer backend installed")
        with tempfile.TemporaryDirectory() as d:
            svg_path = os.path.join(d, "f.svg")
            with open(svg_path, "w") as fh:
                fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 100">'
                         '<rect x="0" y="0" width="680" height="100"/></svg>')
            out = os.path.join(d, "f.png")
            render.export_png(svg_path, out, "light", 2.0)
            self.assertTrue(os.path.exists(out) and os.path.getsize(out) > 0)


def _has_cairosvg():
    try:
        import cairosvg  # noqa: F401
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    unittest.main()
