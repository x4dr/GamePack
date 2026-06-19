"""Tests for the WikiPage module."""

import logging
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

from gamepack.WikiPage import DescriptiveError, WikiPage


class TestWikiPage(unittest.TestCase):
    """Test suite for WikiPage class."""

    temp_dir: ClassVar[Path]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up temporary directory with wiki test files."""
        cls.temp_dir = Path(tempfile.mkdtemp())
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
    def tearDownClass(cls) -> None:
        """Clean up temporary directory."""
        shutil.rmtree(cls.temp_dir)
        WikiPage._wikipath = None

    def setUp(self) -> None:
        """Set up a test wiki page file."""
        self.test_file = Path(self.temp_dir) / "test.md"
        self.test_file.write_text(
            "---\ntitle: Test Page\ntags: [tag1, tag2]\n---\nBody content.",
        )

    def test_wikipath_not_set(self) -> None:
        """Test error when wikipath is not set."""
        with patch.object(WikiPage, "_wikipath", None):
            import os

            with (
                patch.dict(os.environ, clear=True),
                self.assertRaises(DescriptiveError),
            ):
                WikiPage.wikipath()

    def test_locate(self) -> None:
        """Test locating a wiki page by name."""
        path = WikiPage.locate("test")
        self.assertEqual(path, Path("test.md"))

    def test_load(self) -> None:
        """Test loading a wiki page from file."""
        page = WikiPage.load(self.test_file)
        assert page is not None
        self.assertEqual(page.title, "Test Page")
        self.assertEqual(page.tags, {"tag1", "tag2"})
        self.assertEqual(page.body, "Body content.")

    def test_load_not_found(self) -> None:
        """Test error when loading a non-existent page."""
        with self.assertRaises(DescriptiveError):
            WikiPage.load(Path(self.temp_dir) / "missing.md")

    def test_save(self) -> None:
        """Test saving a wiki page."""
        page = WikiPage.load(self.test_file)
        assert page is not None
        page.title = "Updated Title"
        page.save("tester", self.test_file, "Updated content")
        saved_content = self.test_file.read_text()
        self.assertIn("Updated Title", saved_content)

    def test_save_overwrite(self) -> None:
        """Test overwriting a wiki page."""
        page = WikiPage.load(self.test_file)
        assert page is not None
        page.title = "Overwritten Title"
        page.save_overwrite("tester")
        saved_content = self.test_file.read_text()
        self.assertIn("Overwritten Title", saved_content)

    def test_md(self) -> None:
        """Test converting a wiki page to markdown."""
        page = WikiPage.load(self.test_file)
        assert page is not None
        self.assertEqual(page.md().to_md(), "Body content.\n")

    def test_cacheclear(self) -> None:
        """Test reloading cache for a page."""
        WikiPage.reload_cache(self.test_file)
        self.assertIn(
            self.test_file,
            WikiPage.page_cache,
        )  # file should be loaded into cache

    def test_get_clock(self) -> None:
        """Test getting a clock from a wiki page."""
        page = WikiPage("Title", [], "[clock|task|1|10]", [], {})
        match = page.get_clock("task")
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.group("current"), "1")

    def test_change_clock(self) -> None:
        """Test changing a clock value."""
        page = WikiPage("Title", [], "[clock|task|1|10]", [], {})
        page.change_clock("task", 2)
        self.assertIn("[clock|task|3|10]", page.body)

    def test_resolve_address_full_page(self) -> None:
        """Test resolving an address to a full page."""
        result = WikiPage.resolve_address("resolve_test")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertIn("# Main", result)
        self.assertIn("## Skills", result)
        self.assertIn("## Background", result)

    def test_resolve_address_section(self) -> None:
        """Test resolving an address to a section."""
        result = WikiPage.resolve_address("resolve_test#Skills")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertIn("## Skills", result)
        self.assertIn("Skill description", result)
        self.assertIn("### Melee", result)
        self.assertNotIn("## Background", result)

    def test_resolve_address_subsection(self) -> None:
        """Test resolving an address to a subsection."""
        result = WikiPage.resolve_address("resolve_test#Skills:Melee")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertIn("### Melee", result)
        self.assertIn("Melee skill details", result)
        self.assertNotIn("### Ranged", result)

    def test_resolve_address_nonexistent_page(self) -> None:
        """Test resolving an address to a non-existent page."""
        result = WikiPage.resolve_address("no_such_page")
        self.assertIsNone(result)

    def test_resolve_address_nonexistent_section(self) -> None:
        """Test resolving an address to a non-existent section."""
        result = WikiPage.resolve_address("resolve_test#NoSuchHeading")
        self.assertIsNone(result)

    def test_resolve_address_foldable_section(self) -> None:
        """Test resolving an address to a foldable section."""
        result = WikiPage.resolve_address("foldable_test#Hidden")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertIn("Hidden content", result)

    def test_load_none_path(self) -> None:
        """Test load with None path returns None."""
        result = WikiPage.load(None)
        self.assertIsNone(result)

    def test_save_without_file_raises(self) -> None:
        """Test save raises without a file path."""
        page = WikiPage("Title", [], "Body", [], {})
        with self.assertRaises(DescriptiveError):
            page.save("author")

    def test_save_with_non_md_file_raises(self) -> None:
        """Test save raises for non-.md file."""
        page = WikiPage("Title", [], "Body", [], {}, file=self.temp_dir / "test.txt")
        with self.assertRaises(DescriptiveError):
            page.save("author", self.temp_dir / "test.txt")

    def test_save_overwrite_without_file_raises(self) -> None:
        """Test save_overwrite raises without a file."""
        page = WikiPage("Title", [], "Body", [], {})
        with self.assertRaises(DescriptiveError):
            page.save_overwrite("author")

    def test_locate_none(self) -> None:
        """Test locate returns None for None input."""
        self.assertIsNone(WikiPage.locate(None))

    def test_locate_dot(self) -> None:
        """Test locate with '.' returns None."""
        self.assertIsNone(WikiPage.locate("."))

    def test_locate_with_subpath_exists(self) -> None:
        """Test locate with subpath finds the file."""
        path = WikiPage.locate(self.test_file.name)
        self.assertIsNotNone(path)

    def test_tagcheck(self) -> None:
        """Test tagcheck is case-insensitive."""
        page = WikiPage("Title", ["Tag1", "Tag2"], "", [], {})
        self.assertTrue(page.tagcheck("tag1"))
        self.assertTrue(page.tagcheck("TAG2"))
        self.assertFalse(page.tagcheck("tag3"))

    def test_render_returns_none(self) -> None:
        """Test base render returns None."""
        page = WikiPage("Title", [], "", [], {})
        self.assertIsNone(page.render())

    def test_cacheupdate_no_file(self) -> None:
        """Test cacheupdate returns early when no file is set."""
        page = WikiPage("Title", [], "", [], {})
        page.cacheupdate()
        self.assertIsNone(page.file)

    def test_gettags_lazy_init(self) -> None:
        """Test gettags lazily initialises the cache."""
        WikiPage.wikicache.clear()
        tags = WikiPage.gettags()
        self.assertIsInstance(tags, dict)

    def test_getlinks_lazy_init(self) -> None:
        """Test getlinks lazily initialises the cache."""
        WikiPage.wikicache.clear()
        links = WikiPage.getlinks()
        self.assertIsInstance(links, dict)

    def test_set_wikipath_already_set(self) -> None:
        """Test set_wikipath raises when already set."""
        with self.assertRaises(DescriptiveError):
            WikiPage.set_wikipath(self.temp_dir)

    def test_get_clock_not_found(self) -> None:
        """Test get_clock returns None for nonexistent clock."""
        page = WikiPage("Title", [], "no clock here", [], {})
        self.assertIsNone(page.get_clock("nonexistent"))

    def test_change_clock_not_found(self) -> None:
        """Test change_clock returns self when clock not found."""
        page = WikiPage("Title", [], "no clock here", [], {})
        result = page.change_clock("nonexistent", 5)
        self.assertIs(result, page)

    def test_save_low_prio(self) -> None:
        """Test save_low_prio queues messages."""
        page = WikiPage("Title", [], "Body", [], {}, file=self.test_file)
        page.save_low_prio("update 1")
        self.assertIn("update 1", page.save_msg_queue)
        page.save_low_prio("update 1")
        self.assertEqual(len(page.save_msg_queue), 1)
        page.save_low_prio("update 2")
        self.assertEqual(len(page.save_msg_queue), 2)

    def test_resolve_address_empty_fragment(self) -> None:
        """Test resolve_address skips empty fragments."""
        result = WikiPage.resolve_address("resolve_test#Skills::Melee")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertIn("Melee skill details", result)

    def test_commit_and_push_not_live(self) -> None:
        """Test commit_and_push logs and returns when not live."""
        from gamepack.WikiPage import commit_and_push

        WikiPage.live = False
        with self.assertLogs("gamepack.WikiPage", level=logging.INFO):
            commit_and_push(self.temp_dir, self.test_file, "test msg")
        WikiPage.live = True
