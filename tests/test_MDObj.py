import unittest
from unittest.mock import MagicMock

from Item import total_table
from MDPack import (
    search_tables,
    traverse_md,
    MDObj,
    table_row_edit,
    table_add,
    table_remove,
)
from fengraph import rawload


class TestMDObj(unittest.TestCase):
    def setUp(self):
        self.md_text = (
            "# Title\n\nSome text\n\n## Subtitle 1\n\n### Sub-subtitle 1.1\n\n"
            "#### Sub-sub-subtitle 1.1.1\n\n## Subtitle 2\n\n### Sub-subtitle 2.1\n\n"
            "| Column 1 | Column 2 |\n| --- | --- |\n| Value 1.1 | Value 1.2 |\n| Value 2.1 | Value 2.2 |\n"
        )
        self.md = (
            "| Column 1 | Column 2 | Column 3 |\n"
            "| -------- | -------- | -------- |\n"
            "| Value 1  | Value 2  | Value 3  |\n"
            "| Value 4  | Value 5  | Value 6  |\n"
        )

    def test_search_children(self):
        self.md_obj = MDObj.from_md(self.md_text, flash=MagicMock())
        # test with existing child
        subsubtitle = self.md_obj.search_children("sub-subtitle 1.1")
        self.assertIsNotNone(subsubtitle)
        self.assertIn("Sub-sub-subtitle 1.1.1", subsubtitle.children.keys())

        # test with non-existing child
        non_existing_child = self.md_obj.search_children("non-existing child")
        self.assertIsNone(non_existing_child)

    def test_search_tables_found(self):
        md = "| heading 1 | heading 2 |\n| --- | --- |\n| value 1 | value 2 |\n"
        expected_result = (
            "| heading 1 | heading 2 |\n| --- | --- |\n| value 1 | value 2 |\n"
        )
        self.assertEqual(search_tables(md, "heading"), expected_result)

    def test_search_tables_not_found(self):
        md = "| heading 1 | heading 2 |\n| --- | --- |\n| value 1 | value 2 |\n"
        expected_result = ""
        self.assertEqual(search_tables(md, "not found"), expected_result)

    def test_search_tables_with_surround(self):
        md = (
            "| heading 1 | heading 2 |\n"
            "| --- | --- |\n"
            "| value 1 | value 2 |\n"
            "| value 3 | value 4 |\n"
            "| value 5 | value 6 |\n"
        )
        expected_result = (
            "| --- | --- |\n| value 1 | value 2 |\n| value 3 | value 4 |\n"
        )
        self.assertEqual(search_tables(md, "value", 1), expected_result)

    def test_traverse_md_found(self):
        md = "# Heading\n\n## Subheading\n\nSome text\n"
        expected_result = "# Heading\n\n## Subheading\n\nSome text\n\n"
        self.assertEqual(traverse_md(md, "heading"), expected_result)

    def test_traverse_md_not_found(self):
        md = "# Heading\n\n## Subheading\n\nSome text\n"
        expected_result = ""
        self.assertEqual(traverse_md(md, "not found"), expected_result)

    def test_traverse_md_multiple_headings(self):
        md = (
            "# Heading 1\n\n## Subheading 1\n\nSome text\n\n### Sub-subheading 1\n\n"
            "More text\n\n## Subheading 2\n\nEven more text\n"
        )
        expected_result = "## Subheading 2\n\nEven more text\n\n"
        self.assertEqual(traverse_md(md, "subheading 2"), expected_result)

    def test_table_row_edit(self):
        expected_result = (
            "| Column 1 | Column 2 | Column 3 |\n"
            "| -------- | -------- | -------- |\n"
            "| Value 1 | New Value 1.1 |\n"
            "| Value 4  | Value 5  | Value 6  |\n"
        )
        result = table_row_edit(self.md, "Value 1", "New Value 1.1")
        self.assertEqual(result, expected_result)

    def test_table_add(self):
        expected_result = (
            "| Column 1 | Column 2 | Column 3 |\n"
            "| -------- | -------- | -------- |\n"
            "| Value 1  | Value 2  | Value 3  |\n"
            "| Value 4  | Value 5  | Value 6  |\n"
            "| New Key | New Value |\n"
        )
        result = table_add(self.md, "New Key", "New Value")
        self.assertEqual(result, expected_result)

        expected_result = (
            "| Column 1 | Column 2 | Column 3 |\n"
            "| -------- | -------- | -------- |\n"
            "| Value 1  | Value 2  | Value 3  |\n"
            "| Value 4  | Value 5  | Value 6  |\n"
            "| New Key | New Value |\n"
            "| Another New Key | Another New Value |\n"
        )
        result = table_add(result, "Another New Key", "Another New Value")
        self.assertEqual(result, expected_result)

    def test_table_remove(self):
        expected_result = (
            "| Column 1 | Column 2 | Column 3 |\n"
            "| -------- | -------- | -------- |\n"
            "| Value 4  | Value 5  | Value 6  |\n"
        )
        result = table_remove(self.md, "Value 1")
        self.assertEqual(result, expected_result)

    def test_just_tables(self):
        tables = [
            [["Header 1", "Header 2"], ["Row 1, Column 1", "Row 1, Column 2"]],
            [["Header 3", "Header 4"], ["Row 2, Column 1", "Row 2, Column 2"]],
        ]
        mdobj = MDObj.just_tables(tables)
        self.assertEqual(mdobj.tables, tables)
        self.assertEqual(mdobj.plaintext, "")
        self.assertEqual(mdobj.children, {})
        self.assertEqual(mdobj.originalMD, "")

    def test_confine_to_tables(self):
        mdtext = "# My Table\n\n| Header 1 | Header 2 |\n| -------- | -------- |\n| Value 1  | Value 2  |"
        mdobj = MDObj.from_md(mdtext)
        result, errors = mdobj.confine_to_tables()
        self.assertDictEqual(result, {"My Table": {"Value 1": "Value 2"}})
        self.assertEqual(errors, [])

        # Test a simple table without headers
        mdtext = "# My Table\n\n| Value 1 | Value 2 |"
        mdobj = MDObj.from_md(mdtext)
        result, errors = mdobj.confine_to_tables()
        self.assertDictEqual(result, {"My Table": {}})
        self.assertEqual(errors, [])

        # Test multiple tables and nested subheadings
        mdtext = """
        preamble
        # My Table 1
        | Header 1 | Header 2 |
        | -------- | -------- |
        | Value 1  | Value 2  |

        ## Subheading
        asd
        ## extraneous subheading
        # My Table 2
        | Header 3 | Header 4 |
        | -------- | -------- |
        | Value 3  | Value 4  |"""
        mdobj = MDObj.from_md(mdtext)
        result, errors = mdobj.confine_to_tables()
        self.assertDictEqual(
            result,
            {
                "My Table 1": {
                    "Value 1": "Value 2",
                    "Subheading": "asd",
                    "extraneous subheading": "",
                },
                "My Table 2": {"Value 3": "Value 4"},
            },
        )
        self.assertEqual(
            errors,
            [
                "Extraneous Subheading: 'Subheading, extraneous subheading'",
                "Extraneous Text: 'preamble'",
            ],
        )

    def test_total_table(self):
        # Define some test input and expected output
        input_table = [
            ["Column 1", "Column 2", "Column 3", "Garbage"],
            ["Row 1", "1", "2", "asdf"],
            ["Row 2", "3", "4", "ghjkl"],
            ["Total", "", "", ""],
        ]
        expected_output = [
            ["Column 1", "Column 2", "Column 3", "Garbage"],
            ["Row 1", "1", "2", "asdf"],
            ["Row 2", "3", "4", "ghjkl"],
            ["Total", "4.0", "6.0", "0"],
        ]

        # Call the function with the input
        total_table(input_table, lambda x: None)

        # Check that the output matches the expected output
        self.assertEqual(input_table, expected_output)

    def test_to_md(self):
        # iterate over all files in ~/wiki/character
        import pathlib

        sut = MDObj.from_md(rawload("character/ragin"))
        self.maxDiff = None
        self.assertEqual(rawload("character/ragin"), sut.originalMD)

        with open("test_chr.md", "w") as f:
            f.write(sut.to_md())

        self.assertEqual(sut.originalMD, sut.to_md())
        for file in pathlib.Path.expanduser(pathlib.Path("~/wiki/character")).iterdir():
            if file.is_file():
                with file.open() as f:
                    md = f.read()
                    mdobj = MDObj.from_md(md)
                with file.open("w") as f:
                    f.write(mdobj.to_md())
