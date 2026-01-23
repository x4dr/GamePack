import unittest
from pathlib import Path
from typing import cast
from unittest.mock import patch, MagicMock
from gamepack.WikiPage import WikiPage
from gamepack.WikiCharacterSheet import WikiCharacterSheet
from gamepack.MDPack import MDObj


class TestWiki(unittest.TestCase):
    def setUp(self):
        # Setup a temporary wiki root
        self.wiki_root = Path("test_wiki").absolute()
        self.wiki_root.mkdir(exist_ok=True)
        WikiPage._wikipath = self.wiki_root
        WikiPage.page_cache.clear()
        WikiPage.wikicache.clear()

    def tearDown(self):
        import shutil

        if self.wiki_root.exists():
            shutil.rmtree(self.wiki_root)
        WikiPage._wikipath = None

    def test_wikipath_errors(self):
        WikiPage._wikipath = None
        with self.assertRaises(Exception):
            WikiPage.wikipath()

        WikiPage.set_wikipath(self.wiki_root)
        with self.assertRaises(Exception):
            WikiPage.set_wikipath(Path("another"))

    def test_locate(self):
        (self.wiki_root / "test.md").touch()
        (self.wiki_root / "subdir").mkdir()
        (self.wiki_root / "subdir" / "nested.md").touch()

        self.assertEqual(WikiPage.locate("test"), Path("test.md"))
        self.assertEqual(WikiPage.locate("nested"), Path("subdir/nested.md"))
        self.assertIsNone(WikiPage.locate("nonexistent"))
        self.assertIsNone(WikiPage.locate(None))

    def test_load_and_save(self):
        page_path = self.wiki_root / "page1.md"
        content = "---\ntitle: Page 1\ntags: [tag1]\n---\nBody text"
        page_path.write_text(content)

        page = WikiPage.load(Path("page1.md"))
        self.assertIsNotNone(page)
        assert page is not None
        self.assertEqual(page.title, "Page 1")
        self.assertEqual(page.body, "Body text")
        self.assertIn("tag1", page.tags)

        # Save
        page.title = "Updated Title"
        with patch("gamepack.WikiPage.commit_and_push") as mock_push:
            page.save("author")
            mock_push.assert_called()

        saved_content = page_path.read_text()
        self.assertIn("title: Updated Title", saved_content)

    def test_md_conversion(self):
        page = WikiPage("Title", [], "# Header\nText", [], {})
        mdo = page.md()
        self.assertIsInstance(mdo, MDObj)
        self.assertIn("Header", mdo.children)

    def test_clocks(self):
        body = "Some text [clock|Task|2|4] more text"
        page = WikiPage("Title", [], body, [], {})

        match = page.get_clock("Task")
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.group("current"), "2")

        page.change_clock("Task", 1)
        self.assertIn("[clock|Task|3|4]", page.body)

    def test_wikindex(self):
        (self.wiki_root / "a.md").touch()
        (self.wiki_root / "b.md").touch()
        (self.wiki_root / ".hidden.md").touch()

        index = WikiPage.wikindex()
        self.assertEqual(len(index), 2)
        self.assertEqual(index[0].name, "a.md")

    def test_character_sheet_loading(self):
        page_path = self.wiki_root / "char.md"
        # Content that looks like a FenCharacter
        content = (
            "---\ntags: [character]\n---\n# Description\n## Name\nHero\n"
            "# Values\n## Stats\n| S | V |\n|---|---|\n| Str | 10 |"
        )
        page_path.write_text(content)

        # First load - creates from WikiPage
        sheet = WikiCharacterSheet.load(Path("char.md"))
        self.assertIsNotNone(sheet)
        assert sheet is not None
        self.assertIsInstance(sheet, WikiCharacterSheet)

        # Second load - from cache (should be WikiCharacterSheet already)
        sheet2 = WikiCharacterSheet.load(Path("char.md"))
        self.assertEqual(sheet, sheet2)

        # load_locate
        sheet3 = WikiCharacterSheet.load_locate("char")
        self.assertEqual(sheet, sheet3)

        self.assertIsNotNone(sheet.char)
        from gamepack.FenCharacter import FenCharacter

        char = cast(FenCharacter, sheet.char)
        self.assertEqual(char.Character.get("Name"), "Hero")

    @patch("gamepack.WikiPage.WikiPage.load_locate")
    def test_cache_items(self, mock_load):
        # Mock load_locate to return pages with tables
        mock_page = MagicMock()
        mock_page.md.return_value = MDObj.from_md(
            "| Name | Weight | Price |\n|---|---|---|\n| Item1 | 1kg | 10s |"
        )
        mock_load.return_value = mock_page

        WikiPage.cache_items()
        from gamepack.Item import Item

        self.assertIn("Item1", Item.item_cache)


if __name__ == "__main__":
    unittest.main()
