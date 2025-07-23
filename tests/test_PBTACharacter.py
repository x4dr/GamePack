import unittest
from gamepack.PBTACharacter import PBTACharacter
from gamepack.PBTAItem import PBTAItem


class TestPBTACharacter(unittest.TestCase):
    def setUp(self):
        # Create an example character
        self.example_character = PBTACharacter(
            info={"Name": "Alice", "Player Name": "Bob"},
            moves=[["Move 1", False], ["Move 2", True]],
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

    def test_character_creation(self):
        # Ensure the character is created with correct attributes
        self.assertEqual(self.example_character.info["Name"], "Alice")
        self.assertEqual(self.example_character.info["Player Name"], "Bob")
        self.assertIn("Move 1", (x[0] for x in self.example_character.moves))
        self.assertIn("Move 2", (x[0] for x in self.example_character.moves))
        self.assertEqual(self.example_character.stats["Insight"]["Hunt"], "3")
        self.assertEqual(self.example_character.stats["Resolve"]["Attune"], "4")
        self.assertEqual(len(self.example_character.inventory), 2)

    def test_to_mdobj_conversion(self):
        # Convert the character to an MDObj
        md_obj = self.example_character.to_mdobj()
        self.assertIsNotNone(md_obj)
        self.assertGreater(len(md_obj.children), 0)

    def test_round_trip_conversion(self):
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
            len(self.example_character.inventory), len(loaded_character.inventory)
        )
        for a in self.example_character.inventory:
            self.assertIn(str(a), (str(b) for b in loaded_character.inventory))
        self.assertEqual(self.example_character.notes, loaded_character.notes)

    def test_from_md_conversion(self):
        # Convert the character to Markdown and back using from_md
        md_obj = self.example_character.to_mdobj()
        md_content = md_obj.to_md()
        loaded_character = PBTACharacter.from_md(md_content)

        # Compare the original and loaded characters
        self.assertEqual(self.example_character.info, loaded_character.info)
        self.assertEqual(self.example_character.moves, loaded_character.moves)
        self.assertEqual(
            len(self.example_character.inventory), len(loaded_character.inventory)
        )
        for a in self.example_character.inventory:
            self.assertIn(str(a), (str(b) for b in loaded_character.inventory))
        self.assertEqual(
            self.example_character.notes.strip(), loaded_character.notes.strip()
        )
