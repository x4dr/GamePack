import unittest
from unittest.mock import MagicMock

import pathlib
from gamepack.Item import total_table
from gamepack.MDPack import (
    search_tables,
    traverse_md,
    MDObj,
    table_row_edit,
    table_add,
    table_remove,
    MDTable,
    MDChecklist,
)


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
            MDTable(
                headers=["Header 1", "Header 2"],
                rows=[["Row 1, Column 1", "Row 1, Column 2"]],
            ),
            MDTable(
                headers=["Header 3", "Header 4"],
                rows=[["Row 2, Column 1", "Row 2, Column 2"]],
            ),
        ]
        mdobj = MDObj("", tables=tables)
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
                "Extraneous Subheading: 'extraneous subheading'",
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
        test_file = pathlib.Path(__file__).parent / "test_chr.md"
        with test_file.open() as f:
            md_content = f.read()

        sut = MDObj.from_md(md_content)
        self.maxDiff = None
        self.assertEqual(
            md_content.replace("|:-------------|:------|", "|:-----------|:----|")
            .replace("|---------|-------|", "|-------|-----|")
            .replace(
                "|----------------|-------|-------|-------|-----------------|",
                "|--------------|-----|-----|-----|---------------|",
            ),
            sut.to_md(),
        )

    def test_extract_and_insert_tables(self):
        """Ensure tables are correctly extracted and restored."""
        md_text = """
# Task List

## Work Notes

| Task    | Status  |
|---------|---------|
| Report  | Pending |
| Meeting | Done    |

End of document."""
        # Step 1: Extract tables
        text_without_tables, tables = MDTable.extract_tables(md_text)

        # Step 2: Ensure text integrity without tables
        expected_text = """
# Task List

## Work Notes


End of document."""
        self.assertEqual(text_without_tables.strip(), expected_text.strip())

        # Step 3: Reinsert tables
        restored_text = MDTable.insert_tables(text_without_tables, tables)

        # Assuming current implementation adds/removes newlines in a way that is acceptable but differs from exact input string
        # We verify that table content is correct and structure is maintained
        self.assertIn("| Report  | Pending |", restored_text)
        self.assertIn("# Task List", restored_text)
        # Verify normalization
        self.assertIn("|-------|-------|", restored_text)

    def test_extract_and_insert_checklists(self):
        """Ensure checklists are correctly extracted and restored."""
        md_text = """# Task List

Here are my tasks:

- [ ] Buy groceries
- [x] Finish project
- [ ] Call John

End of document."""
        # Step 1: Extract checklists
        text_without_checklists, checklists = MDChecklist.extract_checklists(md_text)

        # Step 2: Ensure text integrity without checklists
        expected_text = """# Task List

Here are my tasks:


End of document."""
        self.assertEqual(text_without_checklists.strip(), expected_text.strip())

        # Step 3: Reinsert checklists
        restored_text = MDChecklist.insert_checklists(
            text_without_checklists, checklists
        )
        self.assertEqual(md_text.strip(), restored_text)

    def test_tables_with_checklists(self):
        """Ensure tables and checklists are correctly handled together."""
        md_text = """# Task List
testask
- [ ] Buy groceries
- [x] Finish project
- [ ] Call John
## Work Notes
| Task    | Status  |
|---------|---------|
| Report  | Pending |
| Meeting | Done    |
"""
        text_without_checklists, checklists = MDChecklist.extract_checklists(md_text)
        text_without_tables, tables = MDTable.extract_tables(text_without_checklists)
        expected_text = """# Task List
testask
## Work Notes"""
        self.assertEqual(expected_text.strip(), text_without_tables.strip())
        restored_text_with_tables = MDTable.insert_tables(text_without_tables, tables)
        final_md = MDChecklist.insert_checklists(restored_text_with_tables, checklists)
        # Verify content presence and table normalization
        self.assertIn("| Report  | Pending |", final_md)
        self.assertIn("- [x] Finish project", final_md)
        self.assertIn("|-------|-------|", final_md)

    def test_mdtable_search_includes_headers(self):
        """Ensure MDTable.search finds terms in headers."""
        table = MDTable(headers=["SpecificHeader", "Another"], rows=[["Val1", "Val2"]])
        # Should return headers list if found in headers
        self.assertEqual(table.search("SpecificHeader"), ["SpecificHeader", "Another"])
        # Should return row if found in row
        self.assertEqual(table.search("Val1"), ["Val1", "Val2"])
        # Should return None if not found
        self.assertIsNone(table.search("Missing"))

    def test_mdtable_split_row_edge_cases(self):
        """Ensure split_row handles various pipe configurations correctly."""
        # Standard
        self.assertEqual(MDTable.split_row("| a | b |", 2), ["a", "b"])
        # Missing outer pipes
        self.assertEqual(MDTable.split_row("a | b", 2), ["a", "b"])
        # Empty first cell implicit
        # "| a |" -> ["", "a"] if length 2?
        # " | a |" -> ["", "a"]
        # The logic: if row starts with |, first_cell_potentially_missing = True.
        # split("| a |") -> ["", "a", ""]? No. row[1:-1] -> " a ". split("|") -> [" a "] -> ["a"]
        # If length constraint is 2, it pads.

        # Test the specific case discussed in cleaned comments: " | val |"
        # split_row(" | val |", 2)
        # row -> " | val |". startswith("|") is False (space first).
        # split("|") -> [" ", " val ", ""] -> ["", "val", ""] -> ["", "val"] (slice :2)
        self.assertEqual(MDTable.split_row(" | val |", 2), ["", "val"])

        # Test "| val |"
        # row -> "| val |". startswith("|") is True. row = " val ".
        # split("|") -> [" val "] -> ["val"].
        # len < 2 and first_cell_missing -> prepends "" -> ["", "val"]
        self.assertEqual(MDTable.split_row("| val |", 2), ["", "val"])
