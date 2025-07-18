import shutil
import tempfile
import unittest
from pathlib import Path

from gamepack.FenCharacter import FenCharacter
from gamepack.PBTACharacter import PBTACharacter
from gamepack.WikiCharacterSheet import WikiCharacterSheet
from gamepack.WikiPage import WikiPage


class TestWikiCharacterSheet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        WikiPage.set_wikipath(Path(cls.temp_dir))
        (Path(cls.temp_dir) / "fen_character.md").touch()
        (Path(cls.temp_dir) / "pbta_character.md").touch()
        (Path(cls.temp_dir) / "items.md").touch()
        (Path(cls.temp_dir) / "pbtaitems.md").touch()
        (Path(cls.temp_dir) / "prices.md").touch()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)
        WikiPage._wikipath = None  # noqa

    def setUp(self):
        self.fen_file = Path(self.temp_dir) / "fen_character.md"
        self.pbta_file = Path(self.temp_dir) / "pbta_character.md"

        self.fen_file.write_text(
            "---\ntitle: Fen Character\ntags: [fen]\n---\nBody content."
        )
        self.pbta_file.write_text(
            "---\ntitle: PBTA Character\ntags: [pbta]\n---\nBody content."
        )

    def test_init_fen(self):
        sheet = WikiCharacterSheet.from_wikipage(WikiPage.load(self.fen_file))
        self.assertIsInstance(sheet.char, FenCharacter)

    def test_init_pbta(self):
        sheet = WikiCharacterSheet.from_wikipage(WikiPage.load(self.pbta_file))
        self.assertIsInstance(sheet.char, PBTACharacter)

    def test_from_wikipage(self):
        page = WikiPage.load(self.fen_file)
        sheet = WikiCharacterSheet.from_wikipage(page)
        self.assertEqual(sheet.title, "Fen Character")
        self.assertEqual(sheet.tags, ["fen"])

    def test_load_fen(self):
        sheet = WikiCharacterSheet.load(self.fen_file)
        self.assertIsInstance(sheet.char, FenCharacter)

    def test_load_pbta(self):
        sheet = WikiCharacterSheet.load(self.pbta_file)
        self.assertIsInstance(sheet.char, PBTACharacter)

    def test_save(self):
        sheet = WikiCharacterSheet.load(self.fen_file)
        sheet.title = "Updated Fen Character"
        sheet.save("tester", self.fen_file, "Updated content")
        saved_content = self.fen_file.read_text()
        self.assertIn("Updated Fen Character", saved_content)
