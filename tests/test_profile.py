import json
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

from scripts.pixel_art import pixel_text, pixel_width, svg
from scripts.update_stats import stats_card, language_card

ROOT = Path(__file__).resolve().parents[1]


class ProfileTests(unittest.TestCase):
    def test_stats_explanation_is_not_in_readme(self):
        readme = (ROOT / "README.md").read_text()
        self.assertNotIn("What's counted here?", readme)
        self.assertNotIn("These cards use the GitHub REST API", readme)

    def test_pixel_letters_are_paths_not_external_fonts(self):
        result = pixel_text(0, 0, "DANIEL MENDEZ", 2)
        self.assertIn('<path d="', result)
        self.assertNotIn("<text", result)
        self.assertIn("crispEdges", result)
        ET.fromstring(svg(500, 40, "Daniel", result))
        self.assertEqual(pixel_width("ABC", 2), 34)

    def test_unsupported_glyph_is_not_silently_omitted(self):
        with self.assertRaises(ValueError):
            pixel_text(0, 0, "☃")

    def test_every_readme_image_exists_and_has_alternative_text(self):
        images = []

        class Parser(HTMLParser):
            def handle_starttag(self, tag, attrs):
                if tag == "img":
                    images.append(dict(attrs))

        Parser().feed((ROOT / "README.md").read_text())
        self.assertGreater(len(images), 0)
        for image in images:
            self.assertTrue(image.get("alt"), image)
            self.assertTrue(image["src"].startswith("./assets/"))
            self.assertTrue((ROOT / image["src"]).is_file(), image)

    def test_svg_assets_are_self_contained_and_valid(self):
        for asset in (ROOT / "assets").glob("*.svg"):
            ET.parse(asset)
            source = asset.read_text()
            for forbidden in ("<script", "<foreignObject", "@import", "@font-face"):
                self.assertNotIn(forbidden, source, asset.name)

    def test_committed_snapshot_matches_pixel_renderer(self):
        data = json.loads((ROOT / "assets/stats.json").read_text())
        self.assertEqual((ROOT / "assets/github-stats.svg").read_text(), stats_card(data))
        self.assertEqual((ROOT / "assets/top-languages.svg").read_text(), language_card(data))


if __name__ == "__main__":
    unittest.main()
