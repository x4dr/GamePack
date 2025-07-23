import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gamepack.WikiPage import WikiPage, DescriptiveError


class TestWikiPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        WikiPage.set_wikipath(Path(cls.temp_dir))
        (Path(cls.temp_dir) / "items.md").touch()
        (Path(cls.temp_dir) / "pbtaitems.md").touch()
        (Path(cls.temp_dir) / "prices.md").touch()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)
        WikiPage._wikipath = None  # noqa

    def setUp(self):
        self.test_file = Path(self.temp_dir) / "test.md"
        self.test_file.write_text(
            "---\ntitle: Test Page\ntags: [tag1, tag2]\n---\nBody content."
        )

    def test_wikipath_not_set(self):
        with patch.object(WikiPage, "_wikipath", None):
            with self.assertRaises(DescriptiveError):
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
            self.test_file, WikiPage.page_cache
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
