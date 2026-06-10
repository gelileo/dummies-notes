import os
import sys
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
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "evil.svg")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write('<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY x "x">]>'
                         '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 100"/>')
            out = render.lint_file(path, "/nonexistent-style.css")
            self.assertTrue(any("DOCTYPE" in m or "ENTITY" in m for _, m in out))


if __name__ == "__main__":
    unittest.main()
