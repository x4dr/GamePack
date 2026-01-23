import unittest
from gamepack.Item import Item, total_table
from gamepack.PBTAItem import PBTAItem
from gamepack.MDPack import MDObj, MDTable
from gamepack.ItemBase import fenconvert, fendeconvert, tryfloatdefault, value_category


class TestItems(unittest.TestCase):
    def test_tryfloatdefault(self):
        self.assertEqual(tryfloatdefault("10.5"), 10.5)
        self.assertEqual(tryfloatdefault("10.5abc"), 10.5)
        self.assertEqual(tryfloatdefault("abc"), 0.0)
        self.assertEqual(tryfloatdefault(None, 1.0), 1.0)

    def test_value_category(self):
        self.assertEqual(value_category("10kg"), "weight")
        self.assertEqual(value_category("10s"), "money")
        self.assertEqual(value_category("10"), "")

    def test_fenconvert(self):
        self.assertEqual(fenconvert("1kg"), 1000.0)
        self.assertEqual(fenconvert("1s"), 100.0)
        self.assertEqual(fenconvert("10"), 10.0)

    def test_fendeconvert(self):
        self.assertEqual(fendeconvert(1000.0, "weight"), "1kg")
        self.assertEqual(fendeconvert(100.0, "money"), "1s")
        self.assertEqual(fendeconvert(5.0, "unknown"), "5")

    def test_item_from_mdobj(self):
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

    def test_pbta_item_from_mdobj(self):
        md_text = "# Ration\n## Load\n1\n## Amount\n3\n## Description\nTasty"
        mdobj = MDObj.from_md(md_text)
        ration_node = mdobj.children["Ration"]
        item = PBTAItem.from_mdobj("Ration", ration_node)

        self.assertEqual(item.name, "Ration")
        self.assertEqual(item.load, 1.0)
        self.assertEqual(item.count, 3.0)
        self.assertEqual(item.description, "Tasty")

    def test_item_process_table(self):
        table = MDTable(
            headers=["Name", "Weight", "Price", "Amount"],
            rows=[["Axe", "2kg", "30s", "1"], ["Shield", "5kg", "20s", "1"]],
        )
        items, unknowns = Item.process_table(table)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].name, "Axe")
        self.assertEqual(items[0].weight, 2000.0)
        self.assertEqual(len(unknowns), 0)

    def test_item_process_tree(self):
        md_text = (
            "# Category\n| Name | Weight | Price |\n|---|---|---|\n| Item1 | 1kg | 10s |\n"
            "# Item2\nitem\n## Weight\n2kg\n## Price\n20s"
        )
        mdobj = MDObj.from_md(md_text)
        items, bonus = Item.process_tree(mdobj, print)
        # Should find Item1 from table and Item2 from mdobj
        self.assertEqual(len(items), 2)
        names = [i.name for i in items]
        self.assertIn("Item1", names)
        self.assertIn("Item2", names)

    def test_total_table_complex(self):
        table_input = [
            ["Item", "Weight", "Price"],
            ["A", "1kg", "10s"],
            ["B", "2kg", "20s"],
            ["Total", "", ""],
        ]
        total_table(table_input, print)
        self.assertEqual(table_input[-1][1], "3kg")
        self.assertEqual(table_input[-1][2], "30s")

    def test_item_caching(self):
        Item.item_cache = {
            "CachedItem": Item("CachedItem", 100, 100, "Old description")
        }
        table = MDTable(headers=["Name", "Price"], rows=[["CachedItem", "200s"]])
        items, _ = Item.process_table(table)
        self.assertEqual(items[0].weight, 100.0)  # From cache
        self.assertEqual(items[0].price, 20000.0)  # From table
        self.assertEqual(items[0].description, "Old description")  # From cache


if __name__ == "__main__":
    unittest.main()
