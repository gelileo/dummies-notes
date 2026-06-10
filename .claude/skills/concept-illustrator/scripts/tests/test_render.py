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


if __name__ == "__main__":
    unittest.main()
