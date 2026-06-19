"""Tests for the PBTACharacter module."""

import unittest

from gamepack.MDPack import MDObj, MDTable
from gamepack.PBTACharacter import PBTACharacter
from gamepack.PBTAItem import PBTAItem


class TestPBTACharacter(unittest.TestCase):
    """Test suite for PBTACharacter."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create an example character
        self.example_character = PBTACharacter(
            info={"Name": "Alice", "Player Name": "Bob"},
            moves=[("Move 1", False), ("Move 2", True)],
            health={
                "Healing": {"Current": 3, "Maximum": 4},
                "3": ["level 3 wound", "somehow, another"],
            },
            stats={"Insight": {"Hunt": "3"}, "Resolve": {"Attune": "4"}},
            inventory=[
                PBTAItem("Sword", 1, "A sharp sword"),
                PBTAItem("Shield", 1, "A sturdy shield"),
            ],
            notes="",
        )

    def test_character_creation(self) -> None:
        """Test character creation with correct attributes."""
        # Ensure the character is created with correct attributes
        self.assertEqual(self.example_character.info["Name"], "Alice")
        self.assertEqual(self.example_character.info["Player Name"], "Bob")
        self.assertIn("Move 1", (x[0] for x in self.example_character.moves))
        self.assertIn("Move 2", (x[0] for x in self.example_character.moves))
        self.assertEqual(self.example_character.stats["Insight"]["Hunt"], "3")
        self.assertEqual(self.example_character.stats["Resolve"]["Attune"], "4")
        self.assertEqual(len(self.example_character.inventory), 2)

    def test_to_mdobj_conversion(self) -> None:
        """Test character to MDObj conversion."""
        md_obj = self.example_character.to_mdobj()
        self.assertIsNotNone(md_obj)
        self.assertGreater(len(md_obj.children), 0)

    def test_round_trip_conversion(self) -> None:
        """Test markdown round-trip conversion."""
        # Convert the character to Markdown and back to a character
        md_obj = self.example_character.to_mdobj()
        loaded_character = PBTACharacter.from_mdobj(md_obj)

        # Compare the original and loaded characters
        self.assertEqual(self.example_character.info, loaded_character.info)
        self.assertEqual(self.example_character.moves, loaded_character.moves)

        for catname, cat in self.example_character.stats.items():
            for key, value in cat.items():
                self.assertIn(key, loaded_character.stats[catname])
                self.assertEqual(
                    value,
                    loaded_character.stats[catname][key],
                    f"{cat} in {loaded_character.stats[catname]}",
                )

        self.assertEqual(
            len(self.example_character.inventory),
            len(loaded_character.inventory),
        )
        for a in self.example_character.inventory:
            self.assertIn(str(a), (str(b) for b in loaded_character.inventory))
        self.assertEqual(self.example_character.notes, loaded_character.notes)

    def test_health_and_inventory_get(self) -> None:
        """Test health and inventory retrieval."""
        # test health_get
        cur, maxx = self.example_character.health_get("Healing")
        self.assertEqual(cur, 3)
        self.assertEqual(maxx, 4)

        # test nonexistent health
        self.assertEqual(self.example_character.health_get("Missing"), (1, 1))

        # test inventory_get
        item = self.example_character.inventory_get("Sword")
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item.load, 1.0)

        self.assertIsNone(self.example_character.inventory_get("Missing"))

    def test_from_md_conversion(self) -> None:
        """Test loading character from markdown."""
        # Convert the character to Markdown and back using from_md
        md_obj = self.example_character.to_mdobj()
        md_content = md_obj.to_md()
        loaded_character = PBTACharacter.from_md(md_content)

        # Compare the original and loaded characters
        self.assertEqual(self.example_character.info, loaded_character.info)
        self.assertEqual(self.example_character.moves, loaded_character.moves)
        self.assertEqual(
            len(self.example_character.inventory),
            len(loaded_character.inventory),
        )
        for a in self.example_character.inventory:
            self.assertIn(str(a), (str(b) for b in loaded_character.inventory))
        self.assertEqual(
            self.example_character.notes.strip(),
            loaded_character.notes.strip(),
        )

    # ── Additional coverage tests ────────────────────────────────────────

    def test_health_get_malformed_values(self) -> None:
        """Test health_get with nan values triggers try/except default to (1, 1).

        'nan' passes through tryfloatdefault (float('nan') succeeds) but
        int(float('nan')) raises ValueError, exercising the except blocks.
        """
        # Must use a key where .title() is idempotent (e.g. "Hp" -> "Hp")
        # so health_get enters the try/except blocks instead of short-circuiting.
        char = PBTACharacter(
            info={"Name": "Test"},
            moves=[],
            health={"Hp": {"Current": "nan", "Maximum": "nan"}},
            stats={},
        )
        cur, maxx = char.health_get("Hp")
        self.assertEqual(cur, 1)
        self.assertEqual(maxx, 1)

    def test_notes_extraction_from_meta(self) -> None:
        """Test post_process extracts Notes from meta dict."""
        meta_notes = MDObj("Adventuring notes here", header="Notes")
        char = PBTACharacter(
            info={"Name": "Test"},
            moves=[],
            health={},
            stats={},
            meta={"Notes": meta_notes},
        )
        # Before post_process notes are empty and Notes key is in meta
        self.assertEqual(char.notes, "")
        self.assertIn("Notes", char.meta)

        # After post_process notes are populated and meta key is removed
        char.post_process(print)
        self.assertEqual(char.notes, "Adventuring notes here")
        self.assertNotIn("Notes", char.meta)

    def test_inventory_empty_to_mdobj(self) -> None:
        """Test to_mdobj with empty inventory."""
        char = PBTACharacter(
            info={"Name": "Test"},
            moves=[],
            health={},
            stats={},
            inventory=[],
        )
        mdobj = char.to_mdobj()
        self.assertIsNotNone(mdobj)
        # No Inventory section should be present
        self.assertNotIn("Inventory", mdobj.children)

    def test_bonus_headers_in_inventory(self) -> None:
        """Test inventory items with additional_info create bonus columns.

        Line covered: 365
        """
        item1 = PBTAItem(
            "Sword",
            1,
            "A sharp sword",
            additional={"Tags": "melee"},
        )
        item2 = PBTAItem(
            "Bow",
            1,
            "A ranged bow",
            additional={"Tags": "ranged"},
        )
        char = PBTACharacter(
            info={"Name": "Test"},
            moves=[],
            health={},
            stats={},
            inventory=[item1, item2],
            inventory_bonus_headers={"Tags"},
        )
        mdobj = char.to_mdobj()
        inv_section = mdobj.children.get("Inventory")
        self.assertIsNotNone(inv_section)
        assert inv_section is not None
        self.assertEqual(len(inv_section.tables), 1)
        table = inv_section.tables[0]
        self.assertIn("Tags", table.headers)
        tags_idx = table.headers.index("Tags")
        for row in table.rows:
            if row[0] == "Sword":
                self.assertEqual(row[tags_idx], "melee")
            elif row[0] == "Bow":
                self.assertEqual(row[tags_idx], "ranged")

    def test_from_mdobj_malformed_table_error(self) -> None:
        """Test from_mdobj with malformed tables triggers flash_func.

        3-column tables (not 2 key-value columns) in both Info and Stats
        sections cause confine_to_tables to report Malformed KeyValue
        errors, exercising flash_func at lines 159 and 165.

        Lines covered: 159, 165
        """
        mdobj = MDObj(
            "",
            children={
                "Info": MDObj(
                    "",
                    tables=[
                        MDTable(
                            rows=[["Alice", "30", "NYC"]],
                            headers=["Name", "Age", "City"],
                        ),
                    ],
                ),
                "Stats": MDObj(
                    "",
                    tables=[
                        MDTable(
                            rows=[["Strength", "High", "18"]],
                            headers=["Stat", "Desc", "Value"],
                        ),
                    ],
                ),
            },
        )
        errors: list[str] = []
        PBTACharacter.from_mdobj(mdobj, errors.append)
        # Each malformed row produces one error — we expect at least 2
        self.assertGreaterEqual(len(errors), 2)
        self.assertTrue(
            all("Malformed" in e for e in errors),
            f"Expected all errors to contain 'Malformed', got: {errors}",
        )

    def test_to_md_returns_string(self) -> None:
        """Test to_md() is callable and returns a non-empty string.

        Line covered: 246
        """
        md_str = self.example_character.to_md()
        self.assertIsInstance(md_str, str)
        self.assertGreater(len(md_str), 0)

    def test_errors_passed_through_init(self) -> None:
        """Test that errors passed to __init__ are stored in self.errors.

        Line covered: 63
        """
        char = PBTACharacter(
            info={"Name": "Test"},
            moves=[],
            health={},
            stats={},
            errors=["something went wrong", "another issue"],
        )
        self.assertIn("something went wrong", char.errors)
        self.assertIn("another issue", char.errors)

    def test_notes_section_in_to_mdobj(self) -> None:
        """Test that non-empty notes produce a Notes section in to_mdobj.

        Line covered: 328
        """
        char = PBTACharacter(
            info={"Name": "Test"},
            moves=[],
            health={},
            stats={},
            notes="Some backstory\nand more.",
        )
        mdobj = char.to_mdobj()
        notes_node = mdobj.children.get("Notes")
        self.assertIsNotNone(notes_node)
        assert notes_node is not None
        self.assertIn("Some backstory", notes_node.plaintext)

    def test_recursive_process_inventory(self) -> None:
        """Test process_inventory recurses into nested sub-sections.

        Creates markdown with inventory split into "Weapons" and "Gear"
        subsections, exercising the recursive call in process_inventory.

        Line covered: 123
        """
        md = (
            "# Info\n"
            "| Name | Value |\n"
            "| --- | --- |\n"
            "| Character Name | Test |\n"
            "\n"
            "# Inventory\n"
            "## Weapons\n"
            "| Name | Count | Max | Description |\n"
            "| --- | --- | --- | --- |\n"
            "| Sword | 1 | 1 | A sharp sword |\n"
            "\n"
            "## Gear\n"
            "| Name | Count | Max | Description |\n"
            "| --- | --- | --- | --- |\n"
            "| Rope | 1 | 1 | A sturdy rope |\n"
        )
        char = PBTACharacter.from_md(md)
        self.assertEqual(len(char.inventory), 2)
        self.assertIsNotNone(char.inventory_get("Sword"))
        self.assertIsNotNone(char.inventory_get("Rope"))
