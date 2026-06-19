"""Tests for the WikiCharacterSheet module."""

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, ClassVar
from unittest.mock import patch

from gamepack.FenCharacter import FenCharacter
from gamepack.PBTACharacter import PBTACharacter
from gamepack.WikiCharacterSheet import WikiCharacterSheet
from gamepack.WikiPage import WikiPage


class TestWikiCharacterSheet(unittest.TestCase):
    """Test suite for WikiCharacterSheet class."""

    temp_dir: ClassVar[Path]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up temporary directory and wiki files."""
        cls.temp_dir = Path(tempfile.mkdtemp())
        WikiPage.set_wikipath(Path(cls.temp_dir))
        (Path(cls.temp_dir) / "fen_character.md").touch()
        (Path(cls.temp_dir) / "pbta_character.md").touch()
        (Path(cls.temp_dir) / "items.md").touch()
        (Path(cls.temp_dir) / "pbtaitems.md").touch()
        (Path(cls.temp_dir) / "prices.md").touch()

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up temporary directory."""
        shutil.rmtree(cls.temp_dir)
        WikiPage._wikipath = None

    def setUp(self) -> None:
        """Set up test character files."""
        self.fen_file = Path(self.temp_dir) / "fen_character.md"
        self.pbta_file = Path(self.temp_dir) / "pbta_character.md"

        self.fen_file.write_text(
            "---\ntitle: Fen Character\ntags: [fen]\n---\nBody content.",
        )
        self.pbta_file.write_text(
            "---\ntitle: PBTA Character\ntags: [pbta]\n---\nBody content.",
        )

    def test_init_fen(self) -> None:
        """Test initializing a FenCharacter sheet."""
        page = WikiPage.load(self.fen_file)
        assert page is not None
        sheet: WikiCharacterSheet[Any] | None = WikiCharacterSheet.from_wikipage(page)
        assert sheet is not None
        self.assertIsInstance(sheet.char, FenCharacter)

    def test_init_pbta(self) -> None:
        """Test initializing a PBTACharacter sheet."""
        page = WikiPage.load(self.pbta_file)
        assert page is not None
        sheet: WikiCharacterSheet[Any] | None = WikiCharacterSheet.from_wikipage(page)
        assert sheet is not None
        self.assertIsInstance(sheet.char, PBTACharacter)

    def test_from_wikipage(self) -> None:
        """Test creating a WikiCharacterSheet from a WikiPage."""
        page = WikiPage.load(self.fen_file)
        assert page is not None
        sheet: WikiCharacterSheet[Any] | None = WikiCharacterSheet.from_wikipage(page)
        assert sheet is not None
        self.assertEqual(sheet.title, "Fen Character")
        self.assertEqual(sheet.tags, {"fen"})

    def test_load_fen(self) -> None:
        """Test loading a FenCharacter sheet from file."""
        sheet: WikiCharacterSheet[Any] | None = WikiCharacterSheet.load(self.fen_file)
        assert sheet is not None
        self.assertIsInstance(sheet.char, FenCharacter)

    def test_load_pbta(self) -> None:
        """Test loading a PBTACharacter sheet from file."""
        sheet: WikiCharacterSheet[Any] | None = WikiCharacterSheet.load(self.pbta_file)
        assert sheet is not None
        self.assertIsInstance(sheet.char, PBTACharacter)

    def test_save(self) -> None:
        """Test saving a character sheet."""
        sheet: WikiCharacterSheet[Any] | None = WikiCharacterSheet.load(self.fen_file)
        assert sheet is not None
        sheet.title = "Updated Fen Character"
        sheet.save("tester", self.fen_file, "Updated content")
        saved_content = self.fen_file.read_text()
        self.assertIn("Updated Fen Character", saved_content)

    def test_load_none_returns_none(self) -> None:
        """Test load with None returns None."""
        result: WikiCharacterSheet[Any] | None = WikiCharacterSheet.load(None)
        self.assertIsNone(result)

    def test_load_with_suffix(self) -> None:
        """Test load adds .md suffix when page path lacks extension."""
        no_ext_path = self.temp_dir / "test_noext_page"
        no_ext_path.write_text(
            "---\ntitle: NoExt Character\ntags: [character]\n---\nBody content.",
        )
        sheet: WikiCharacterSheet[Any] | None = WikiCharacterSheet.load(no_ext_path, cache=False)
        assert sheet is not None
        self.assertIsInstance(sheet.char, FenCharacter)
        self.assertEqual(sheet.title, "NoExt Character")

    def test_load_type_error(self) -> None:
        """Test that load raises TypeError when WikiPage.load returns wrong type."""
        with patch.object(WikiPage, "load", return_value="not a WikiPage"), self.assertRaises(TypeError):
            WikiCharacterSheet.load(self.fen_file)

    def test_load_locate_success(self) -> None:
        """Test load_locate successfully locates and loads a character sheet."""
        sheet: WikiCharacterSheet[Any] | None = WikiCharacterSheet.load_locate("fen_character")
        assert sheet is not None
        self.assertIsInstance(sheet.char, FenCharacter)
        self.assertEqual(sheet.title, "Fen Character")

    def test_save_low_prio(self) -> None:
        """Test save_low_prio queues message and calls parent."""
        sheet: WikiCharacterSheet[Any] | None = WikiCharacterSheet.load(self.fen_file)
        assert sheet is not None
        sheet.save_low_prio("test message")
        self.assertEqual(sheet.increment, 1)
        self.assertIn("test message saving charactersheet", sheet.save_msg_queue)

    def test_load_locate_nonexistent_returns_none(self) -> None:
        """Test load_locate with nonexistent page returns None (line 143)."""
        sheet: WikiCharacterSheet[Any] | None = WikiCharacterSheet.load_locate("no_such_page")
        self.assertIsNone(sheet)
