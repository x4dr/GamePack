import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gamepack.WikiPage import DescriptiveError, WikiPage


class TestWikiPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        WikiPage.set_wikipath(Path(cls.temp_dir))
        (Path(cls.temp_dir) / "items.md").touch()
        (Path(cls.temp_dir) / "pbtaitems.md").touch()
        (Path(cls.temp_dir) / "prices.md").touch()
        resolve_page = Path(cls.temp_dir) / "resolve_test.md"
        resolve_page.write_text(
            "---\ntitle: Resolve Test\n---\n"
            "# Main\n"
            "Main content.\n"
            "## Skills\n"
            "Skill description.\n"
            "### Melee\n"
            "Melee skill details.\n"
            "### Ranged\n"
            "Ranged skill details.\n"
            "## Background\n"
            "Background text.\n",
        )
        foldable_page = Path(cls.temp_dir) / "foldable_test.md"
        foldable_page.write_text(
            "---\ntitle: Foldable Test\n---\n# Main\n## !Hidden\nHidden content\n",
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)
        WikiPage._wikipath = None

    def setUp(self):
        self.test_file = Path(self.temp_dir) / "test.md"
        self.test_file.write_text(
            "---\ntitle: Test Page\ntags: [tag1, tag2]\n---\nBody content.",
        )

    def test_wikipath_not_set(self):
        with patch.object(WikiPage, "_wikipath", None):
            import os

            with (
                patch.dict(os.environ, clear=True),
                self.assertRaises(DescriptiveError),
            ):
                WikiPage.wikipath()

    def test_locate(self):
        path = WikiPage.locate("test")
        self.assertEqual(path, Path("test.md"))

    def test_load(self):
        page = WikiPage.load(self.test_file)
        self.assertEqual(page.title, "Test Page")
        self.assertEqual(page.tags, {"tag1", "tag2"})
        self.assertEqual(page.body, "Body content.")

    def test_load_not_found(self):
        with self.assertRaises(DescriptiveError):
            WikiPage.load(Path(self.temp_dir) / "missing.md")

    def test_save(self):
        page = WikiPage.load(self.test_file)
        page.title = "Updated Title"
        page.save("tester", self.test_file, "Updated content")
        saved_content = self.test_file.read_text()
        self.assertIn("Updated Title", saved_content)

    def test_save_overwrite(self):
        page = WikiPage.load(self.test_file)
        page.title = "Overwritten Title"
        page.save_overwrite("tester")
        saved_content = self.test_file.read_text()
        self.assertIn("Overwritten Title", saved_content)

    def test_md(self):
        page = WikiPage.load(self.test_file)
        self.assertEqual(page.md().to_md(), "Body content.\n")

    def test_cacheclear(self):
        WikiPage.reload_cache(self.test_file)
        self.assertIn(
            self.test_file,
            WikiPage.page_cache,
        )  # file should be loaded into cache

    def test_get_clock(self):
        page = WikiPage("Title", [], "[clock|task|1|10]", [], {})
        match = page.get_clock("task")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("current"), "1")

    def test_change_clock(self):
        page = WikiPage("Title", [], "[clock|task|1|10]", [], {})
        page.change_clock("task", 2)
        self.assertIn("[clock|task|3|10]", page.body)

    def test_resolve_address_full_page(self):
        result = WikiPage.resolve_address("resolve_test")
        self.assertIsNotNone(result)
        self.assertIn("# Main", result)
        self.assertIn("## Skills", result)
        self.assertIn("## Background", result)

    def test_resolve_address_section(self):
        result = WikiPage.resolve_address("resolve_test#Skills")
        self.assertIsNotNone(result)
        self.assertIn("## Skills", result)
        self.assertIn("Skill description", result)
        self.assertIn("### Melee", result)
        self.assertNotIn("## Background", result)

    def test_resolve_address_subsection(self):
        result = WikiPage.resolve_address("resolve_test#Skills:Melee")
        self.assertIsNotNone(result)
        self.assertIn("### Melee", result)
        self.assertIn("Melee skill details", result)
        self.assertNotIn("### Ranged", result)

    def test_resolve_address_nonexistent_page(self):
        result = WikiPage.resolve_address("no_such_page")
        self.assertIsNone(result)

    def test_resolve_address_nonexistent_section(self):
        result = WikiPage.resolve_address("resolve_test#NoSuchHeading")
        self.assertIsNone(result)

    def test_resolve_address_foldable_section(self):
        result = WikiPage.resolve_address("foldable_test#Hidden")
        self.assertIsNotNone(result)
        self.assertIn("Hidden content", result)
