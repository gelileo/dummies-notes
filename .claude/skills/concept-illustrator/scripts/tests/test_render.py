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


if __name__ == "__main__":
    unittest.main()
