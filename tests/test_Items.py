"""Tests for the Items module."""

import unittest

from gamepack.BaseCharacter import BaseCharacter
from gamepack.Item import Item, total_table
from gamepack.ItemBase import (
    ItemBase,
    extract,
    fenconvert,
    fendeconvert,
    tryfloatdefault,
    value_category,
)
from gamepack.MDPack import MDObj, MDTable
from gamepack.PBTAItem import PBTAItem


class TestItems(unittest.TestCase):
    """Test suite for Item classes."""

    def test_tryfloatdefault(self) -> None:
        """Test tryfloatdefault helper."""
        self.assertEqual(tryfloatdefault("10.5"), 10.5)
        self.assertEqual(tryfloatdefault("10.5abc"), 10.5)
        self.assertEqual(tryfloatdefault("abc"), 0.0)
        self.assertEqual(tryfloatdefault(None, 1.0), 1.0)

    def test_value_category(self) -> None:
        """Test value_category helper."""
        self.assertEqual(value_category("10kg"), "weight")
        self.assertEqual(value_category("10s"), "money")
        self.assertEqual(value_category("10"), "")

    def test_fenconvert(self) -> None:
        """Test fenconvert helper."""
        self.assertEqual(fenconvert("1kg"), 1000.0)
        self.assertEqual(fenconvert("1s"), 100.0)
        self.assertEqual(fenconvert("10"), 10.0)

    def test_fendeconvert(self) -> None:
        """Test fendeconvert helper."""
        self.assertEqual(fendeconvert(1000.0, "weight"), "1kg")
        self.assertEqual(fendeconvert(100.0, "money"), "1s")
        self.assertEqual(fendeconvert(5.0, "unknown"), "5")

    def test_item_from_mdobj(self) -> None:
        """Test Item creation from MDObj."""
        md_text = "# Sword\n## Weight\n1.5kg\n## Price\n50s\n## Description\nSharp sword\n## Quality\nExcellent"
        mdobj = MDObj.from_md(md_text)
        # MDObj.from_md might put everything under root or split by headers
        # In this case, 'Sword' is level 1, so it's a child of the root MDObj
        sword_node = mdobj.children["Sword"]
        item = Item.from_mdobj("Sword", sword_node)

        self.assertEqual(item.name, "Sword")
        self.assertEqual(item.weight, 1500.0)
        self.assertEqual(item.price, 5000.0)
        self.assertEqual(item.description, "Sharp sword")
        self.assertEqual(item.additional_info["Quality"].strip(), "Excellent")

    def test_pbta_item_from_mdobj(self) -> None:
        """Test PBTAItem creation from MDObj."""
        md_text = "# Ration\n## Load\n1\n## Amount\n3\n## Description\nTasty"
        mdobj = MDObj.from_md(md_text)
        ration_node = mdobj.children["Ration"]
        item = PBTAItem.from_mdobj("Ration", ration_node)

        self.assertEqual(item.name, "Ration")
        self.assertEqual(item.load, 1.0)
        self.assertEqual(item.count, 3.0)
        self.assertEqual(item.description, "Tasty")

    def test_item_process_table(self) -> None:
        """Test processing items from a table."""
        table = MDTable(
            headers=["Name", "Weight", "Price", "Amount"],
            rows=[["Axe", "2kg", "30s", "1"], ["Shield", "5kg", "20s", "1"]],
        )
        items, unknowns = Item.process_table(table)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].name, "Axe")
        self.assertEqual(items[0].weight, 2000.0)
        self.assertEqual(len(unknowns), 0)

    def test_item_process_tree(self) -> None:
        """Test processing items from a markdown tree."""
        md_text = (
            "# Category\n| Name | Weight | Price |\n|---|---|---|\n| Item1 | 1kg | 10s |\n"
            "# Item2\nitem\n## Weight\n2kg\n## Price\n20s"
        )
        mdobj = MDObj.from_md(md_text)
        items, _bonus = Item.process_tree(mdobj, print)
        # Should find Item1 from table and Item2 from mdobj
        self.assertEqual(len(items), 2)
        names = [i.name for i in items]
        self.assertIn("Item1", names)
        self.assertIn("Item2", names)

    def test_total_table_complex(self) -> None:
        """Test total_table calculation."""
        table_input = [
            ["Item", "Weight", "Price"],
            ["A", "1kg", "10s"],
            ["B", "2kg", "20s"],
            ["Total", "", ""],
        ]
        total_table(table_input, print)
        self.assertEqual(table_input[-1][1], "3kg")
        self.assertEqual(table_input[-1][2], "30s")

    def test_item_caching(self) -> None:
        """Test item cache behavior."""
        Item.item_cache = {
            "CachedItem": Item("CachedItem", 100, 100, "Old description"),
        }
        table = MDTable(headers=["Name", "Price"], rows=[["CachedItem", "200s"]])
        items, _ = Item.process_table(table)
        self.assertEqual(items[0].weight, 100.0)  # From cache
        self.assertEqual(items[0].price, 20000.0)  # From table
        self.assertEqual(items[0].description, "Old description")  # From cache

    def test_item_cache_fallback_price_and_additional(self) -> None:
        """Test cache fallback for price and additional_info when columns are missing."""
        Item.item_cache = {
            "CachedItem": Item(
                "CachedItem",
                100,
                50,
                "Old description",
                additional={"Quality": "Good"},
            ),
        }
        # Table has no price column and no extra columns → both come from cache
        table = MDTable(rows=[["CachedItem"]], headers=["Name"])
        items, _ = Item.process_table(table)
        self.assertEqual(items[0].price, 50.0)  # From cache (line 136)
        self.assertEqual(items[0].weight, 100.0)  # From cache (line 134)
        self.assertEqual(items[0].description, "Old description")  # From cache
        self.assertEqual(items[0].additional_info.get("Quality"), "Good")  # From cache (lines 140-141)

    def test_total_table_non_numeric(self) -> None:
        """Test total_table handles non-numeric values gracefully."""
        table_input = [
            ["Item", "Price"],
            ["A", "abc"],
            ["Total", ""],
        ]
        total_table(table_input, print)
        self.assertEqual(table_input[-1][1], "0")

    def test_total_table_error_handling(self) -> None:
        """Test total_table error path with malformed input (outer except path)."""
        messages: list[str] = []
        total_table([], lambda x: messages.append(x))
        self.assertEqual(len(messages), 1)
        self.assertIn("tabletotal failed", messages[0])

    def test_pbta_item_cache_fallback_load(self) -> None:
        """Test PBTAItem cache fallback for load when column is missing."""
        PBTAItem.item_cache = {
            "CachedLoadItem": PBTAItem("CachedLoadItem", 3.0, "Old desc", 1, 5),
        }
        table = MDTable(rows=[["CachedLoadItem"]], headers=["Name"])
        items, _ = PBTAItem.process_table(table)
        self.assertEqual(items[0].load, 3.0)  # From cache (line 126)
        self.assertEqual(items[0].description, "Old desc")  # From cache (line 128)

    def test_pbta_item_total_load(self) -> None:
        """Test PBTAItem total_load property (load * count)."""
        item = PBTAItem("Torch", 1.0, "Light source", 3)
        self.assertEqual(item.total_load, 3.0)

    def test_pbta_item_from_mdobj_additional_fields(self) -> None:
        """Test PBTAItem from_mdobj extracts additional metadata fields."""
        md_text = "# Charm\n## Load\n1\n## Description\nLucky charm\n## Tags\nMystical\n## Effect\n+1 luck"
        mdobj = MDObj.from_md(md_text)
        charm_node = mdobj.children["Charm"]
        item = PBTAItem.from_mdobj("Charm", charm_node)
        self.assertEqual(item.load, 1.0)
        self.assertIn("Tags", item.additional_info)
        self.assertEqual(item.additional_info["Tags"].strip(), "Mystical")
        self.assertIn("Effect", item.additional_info)
        self.assertEqual(item.additional_info["Effect"].strip(), "+1 luck")

    def test_item_base_empty_row_skip(self) -> None:
        """Test process_table skips empty rows."""
        table = MDTable(
            headers=["Name", "Weight"],
            rows=[["", ""], ["Axe", "2kg"]],
        )
        items, _ = Item.process_table(table)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].name, "Axe")

    def test_item_base_row_padding(self) -> None:
        """Test process_table pads short rows (through from_md which normalizes)."""
        md = "| Name | Weight | Price |\n|---|---|---|\n| Sword | 3kg | 20s |\n| Shield | 5kg |"
        table = MDTable.from_md(md)
        items, _ = Item.process_table(table)
        self.assertEqual(len(items), 2)
        names = {i.name for i in items}
        self.assertIn("Sword", names)
        self.assertIn("Shield", names)

    def test_extract_plaintext_fallback(self) -> None:
        """Test extract falls back to plaintext when heading not found in children."""
        md_text = "# Potion\nWeight: 0.5kg\nPrice: 10s"
        mdobj = MDObj.from_md(md_text)
        potion_node = mdobj.children["Potion"]
        weight_raw, heading = extract(Item.table_weight, potion_node)
        self.assertEqual(weight_raw, "0.5kg")
        self.assertIsNotNone(heading)

    def test_item_base_from_table_row_raises(self) -> None:
        """Test ItemBase.from_table_row raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            ItemBase.from_table_row([], {})

    def test_item_base_from_mdobj_raises(self) -> None:
        """Test ItemBase.from_mdobj raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            ItemBase.from_mdobj("test", MDObj.from_md("## Dummy\ncontent"))

    def test_base_character_from_mdobj_raises(self) -> None:
        """Test BaseCharacter.from_mdobj raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            BaseCharacter.from_mdobj(MDObj.from_md("# Test\nbody"))

    def test_base_character_to_mdobj_raises(self) -> None:
        """Test BaseCharacter.to_mdobj raises NotImplementedError."""
        char = BaseCharacter()
        with self.assertRaises(NotImplementedError):
            char.to_mdobj()

    def test_pbta_item_cache_fallback_additional_info(self) -> None:
        """Test PBTAItem cache fallback for additional_info (lines 130-131)."""
        PBTAItem.item_cache = {
            "CachedItem": PBTAItem(
                "CachedItem",
                2.0,
                "desc",
                1,
                1,
                additional={"Tags": "Mystical", "Effect": "+1"},
            ),
        }
        table = MDTable(rows=[["CachedItem"]], headers=["Name"])
        items, _ = PBTAItem.process_table(table)
        self.assertEqual(items[0].additional_info.get("Tags"), "Mystical")
        self.assertEqual(items[0].additional_info.get("Effect"), "+1")


if __name__ == "__main__":
    unittest.main()
