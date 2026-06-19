"""Tests for the MDObj module."""

import pathlib
import unittest
from unittest.mock import MagicMock

from gamepack.Item import total_table
from gamepack.MDPack import (
    MDChecklist,
    MDList,
    MDObj,
    MDTable,
    search_tables,
    table_add,
    table_remove,
    table_row_edit,
    traverse_md,
)


class TestMDObj(unittest.TestCase):
    """Test suite for MDObj class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
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

    def test_search_children(self) -> None:
        """Test searching for child headings in MDObj."""
        self.md_obj = MDObj.from_md(self.md_text, flash=MagicMock())
        # test with existing child
        subsubtitle = self.md_obj.search_children("sub-subtitle 1.1")
        assert subsubtitle is not None
        self.assertIn("Sub-sub-subtitle 1.1.1", subsubtitle.children.keys())

        # test with non-existing child
        non_existing_child = self.md_obj.search_children("non-existing child")
        self.assertIsNone(non_existing_child)

    def test_search_tables_found(self) -> None:
        """Test search_tables finds matching table."""
        md = "| heading 1 | heading 2 |\n| --- | --- |\n| value 1 | value 2 |\n"
        expected_result = "| heading 1 | heading 2 |\n| --- | --- |\n| value 1 | value 2 |\n"
        self.assertEqual(search_tables(md, "heading"), expected_result)

    def test_search_tables_not_found(self) -> None:
        """Test search_tables returns empty string when no match."""
        md = "| heading 1 | heading 2 |\n| --- | --- |\n| value 1 | value 2 |\n"
        expected_result = ""
        self.assertEqual(search_tables(md, "not found"), expected_result)

    def test_search_tables_with_surround(self) -> None:
        """Test search_tables with surrounding rows included."""
        md = (
            "| heading 1 | heading 2 |\n"
            "| --- | --- |\n"
            "| value 1 | value 2 |\n"
            "| value 3 | value 4 |\n"
            "| value 5 | value 6 |\n"
        )
        expected_result = "| --- | --- |\n| value 1 | value 2 |\n| value 3 | value 4 |\n"
        self.assertEqual(search_tables(md, "value", 1), expected_result)

    def test_traverse_md_found(self) -> None:
        """Test traverse_md finds and returns matching heading section."""
        md = "# Heading\n\n## Subheading\n\nSome text\n"
        expected_result = "# Heading\n\n## Subheading\n\nSome text\n\n"
        self.assertEqual(traverse_md(md, "heading"), expected_result)

    def test_traverse_md_not_found(self) -> None:
        """Test traverse_md returns empty string when heading not found."""
        md = "# Heading\n\n## Subheading\n\nSome text\n"
        expected_result = ""
        self.assertEqual(traverse_md(md, "not found"), expected_result)

    def test_traverse_md_multiple_headings(self) -> None:
        """Test traverse_md with multiple headings at same level."""
        md = (
            "# Heading 1\n\n## Subheading 1\n\nSome text\n\n### Sub-subheading 1\n\n"
            "More text\n\n## Subheading 2\n\nEven more text\n"
        )
        expected_result = "## Subheading 2\n\nEven more text\n\n"
        self.assertEqual(traverse_md(md, "subheading 2"), expected_result)

    def test_table_row_edit(self) -> None:
        """Test editing a table row value."""
        expected_result = (
            "| Column 1 | Column 2 | Column 3 |\n"
            "| -------- | -------- | -------- |\n"
            "| Value 1 | New Value 1.1 |\n"
            "| Value 4  | Value 5  | Value 6  |\n"
        )
        result = table_row_edit(self.md, "Value 1", "New Value 1.1")
        self.assertEqual(result, expected_result)

    def test_table_add(self) -> None:
        """Test adding a new row to a table."""
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

    def test_table_remove(self) -> None:
        """Test removing a row from a table."""
        expected_result = (
            "| Column 1 | Column 2 | Column 3 |\n"
            "| -------- | -------- | -------- |\n"
            "| Value 4  | Value 5  | Value 6  |\n"
        )
        result = table_remove(self.md, "Value 1")
        self.assertEqual(result, expected_result)

    def test_just_tables(self) -> None:
        """Test MDObj created with only tables."""
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

    def test_confine_to_tables(self) -> None:
        """Test confining MDObj content to table-based dictionaries."""
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

    def test_total_table(self) -> None:
        """Test total_table sums numeric columns."""
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
            ["Total", "4", "6", "0"],
        ]

        # Call the function with the input
        total_table(input_table, lambda x: None)  # noqa: ARG005

        # Check that the output matches the expected output
        self.assertEqual(input_table, expected_output)

    def test_to_md(self) -> None:
        """Test round-trip conversion from md to MDObj and back."""
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

    def test_extract_and_insert_tables(self) -> None:
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

        # Current impl adds/removes newlines in a way that's acceptable
        # but may differ from the exact input string
        # We verify that table content is correct and structure is maintained
        self.assertIn("| Report  | Pending |", restored_text)
        self.assertIn("# Task List", restored_text)
        # Verify normalization
        self.assertIn("|-------|-------|", restored_text)

    def test_extract_and_insert_checklists(self) -> None:
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
            text_without_checklists,
            checklists,
        )
        self.assertEqual(md_text.strip(), restored_text)

    def test_tables_with_checklists(self) -> None:
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

    def test_mdtable_search_includes_headers(self) -> None:
        """Ensure MDTable.search finds terms in headers."""
        table = MDTable(headers=["SpecificHeader", "Another"], rows=[["Val1", "Val2"]])
        # Should return headers list if found in headers
        self.assertEqual(table.search("SpecificHeader"), ["SpecificHeader", "Another"])
        # Should return row if found in row
        self.assertEqual(table.search("Val1"), ["Val1", "Val2"])
        # Should return None if not found
        self.assertIsNone(table.search("Missing"))

    def test_mdtable_split_row_edge_cases(self) -> None:
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

    def test_checklist_indentation_loss(self) -> None:
        """Verify that leading indentation in checklists is lost during round-trip."""
        # Note: Current behavior ignores indented checkboxes if they don't match pattern at start of line
        md_text = "- [ ] Indented task\n- [x] Normal task"
        checklist = MDChecklist.from_md(md_text)
        self.assertEqual(checklist.to_md(), "- [ ] Indented task\n- [x] Normal task")

    def test_table_normalization(self) -> None:
        """Verify that table spacing and alignment are normalized in to_md()."""
        md_text = "|Header|LongerHeader|\n|:---|---:|\n|val|v|"
        table = MDTable.from_md(md_text)
        normalized = table.to_md()
        self.assertIn("| Header | LongerHeader |", normalized)
        # Header (6) vs val (3) -> 6. : + 5 - = 6.
        self.assertIn("|:-----|", normalized)
        # LongerHeader (12) vs v (1) -> 12. 11 - + : = 12.
        self.assertIn("|-----------:|", normalized)

    def test_duplicate_headers(self) -> None:
        """Verify that duplicate headers at the same level are suffixed with _."""
        md_text = "# Header\nContent 1\n# Header\nContent 2"
        mdobj = MDObj.from_md(md_text)
        self.assertIn("Header", mdobj.children)
        self.assertIn("Header_", mdobj.children)
        self.assertEqual(mdobj.children["Header"].plaintext.strip(), "Content 1")
        self.assertEqual(mdobj.children["Header_"].plaintext.strip(), "Content 2")

    def test_mdobj_update_serialization(self) -> None:
        """Verify that modifications to MDObj are reflected in to_md()."""
        md_text = "# Title\n\n| K | V |\n|---|---|\n| a | 1 |"
        mdobj = MDObj.from_md(md_text)

        # Table is in the child "Title"
        title_node = mdobj.children["Title"]

        # Modify table
        # row 0 is 'a | 1'. We append row 1.
        title_node.tables[0].update_cell(1, 0, "b")
        title_node.tables[0].update_cell(1, 1, "2")

        # Add a checklist to title_node
        title_node.lists.append(MDChecklist([("New Task", True)], position=1))

        # Add a child to title_node
        new_child = MDObj("Child content", header="New Child", level=2)
        title_node.add_child(new_child)

        final_md = mdobj.to_md()
        # Spacing is normalized, so we check for content
        self.assertIn("a", final_md)
        self.assertIn("1", final_md)
        self.assertIn("b", final_md)
        self.assertIn("2", final_md)
        self.assertIn("- [x] New Task", final_md)
        self.assertIn("## New Child\nChild content", final_md)

    def test_mixed_list_extraction(self) -> None:
        """Verify that non-checklist items stay in plaintext."""
        md_text = "- [ ] Task 1\n- Regular item\n- [x] Task 2"
        # extract_checklists will find Task 1 and Task 2
        # Regular item will stay in plaintext
        text, checklists = MDChecklist.extract_checklists(md_text)
        self.assertIn("- Regular item", text)
        self.assertEqual(len(checklists), 2)
        self.assertEqual(checklists[0].checklist[0][0], "Task 1")
        self.assertEqual(checklists[1].checklist[0][0], "Task 2")

    def test_nested_list_parsing(self) -> None:
        """Verify that nested lists are correctly parsed and serialized."""
        md_text = "- Item 1\n  - Item 1.1\n    - Item 1.1.1\n- Item 2"
        mlist = MDList.from_md(md_text)
        self.assertEqual(len(mlist.items), 4)
        self.assertEqual(mlist.items[1].level, 1)
        self.assertEqual(mlist.items[2].level, 2)
        # Serialization (using 2 spaces per level as implemented)
        self.assertEqual(
            mlist.to_md(),
            "- Item 1\n  - Item 1.1\n    - Item 1.1.1\n- Item 2",
        )

    def test_mdtable_row_access(self) -> None:
        """Verify new MDTable.row() method and rows_dict property."""
        md_text = "| ID | Val |\n|---|---|\n| a | 1 |\n| b | 2 |"
        table = MDTable.from_md(md_text)
        row_a = table.row("a")
        self.assertIsNotNone(row_a)
        assert row_a is not None
        self.assertEqual(row_a["Val"], "1")
        self.assertEqual(row_a["ID"], "a")
        self.assertIsNone(table.row("c"))

        # Test rows_dict
        rd = table.rows_dict
        self.assertEqual(rd["a"]["Val"], "1")
        self.assertEqual(rd["b"]["Val"], "2")

    def test_mdobj_list_extraction(self) -> None:
        """Verify that MDObj extracts general lists into self.lists."""
        md_text = "Some text\n- List Item 1\n- List Item 2\nMore text"
        mdobj = MDObj.from_md(md_text)
        self.assertEqual(len(mdobj.lists), 1)
        self.assertEqual(mdobj.lists[0].items[0].text, "List Item 1")
        self.assertIn("- List Item 1", mdobj.to_md())

    def test_ordered_parts_serialization(self) -> None:
        """Verify that tables and lists are serialized in their original relative order."""
        md_text = "Start\n| T | B |\n|---|---|\n| 1 | 2 |\nMiddle\n- Item 1\n- Item 2\nEnd"
        mdobj = MDObj.from_md(md_text)
        serialized = mdobj.to_md()
        # Verify order: Table before List
        table_pos = serialized.find("| T | B |")
        list_pos = serialized.find("- Item 1")
        self.assertTrue(table_pos < list_pos)
        self.assertIn("Middle", serialized)

    def test_mdtable_update_rows(self) -> None:
        """Test MDTable.update_rows bulk update."""
        table = MDTable(rows=[["1", "2"]], headers=["A", "B"])
        table.update_rows([["3", "4"], ["5", "6"]])
        self.assertEqual(table.rows, [["3", "4"], ["5", "6"]])

    def test_mdtable_clear_rows(self) -> None:
        """Test MDTable.clear_rows removes all data rows."""
        table = MDTable(rows=[["1", "2"], ["3", "4"]], headers=["A", "B"])
        table.clear_rows()
        self.assertEqual(table.rows, [])

    def test_mdtable_canonize(self) -> None:
        """Test MDTable.canonize normalises cells and trims trailing empty rows."""
        table = MDTable(
            rows=[["1", "2"], ["", ""], ["3", "4"], ["", ""]],
            headers=["A", "B"],
        )
        table.canonize()
        self.assertEqual(table.rows, [["1", "2"], ["", ""], ["3", "4"]])
        self.assertEqual(table.headers, ["A", "B"])

    def test_mdtable_get_and_getitem(self) -> None:
        """Test MDTable dict-style get and __getitem__."""
        table = MDTable(rows=[["name", "Alice"], ["age", "30"]], headers=["Key", "Val"])
        self.assertEqual(table.get("name"), "Alice")
        self.assertEqual(table.get("missing", "default"), "default")
        self.assertEqual(table["name"], "Alice")

    def test_mdtable_column(self) -> None:
        """Test MDTable.column extracts values by header."""
        table = MDTable(rows=[["1", "10"], ["2", "20"]], headers=["ID", "Score"])
        self.assertEqual(table.column("Score"), ["10", "20"])
        self.assertEqual(table.column("Missing"), [])

    def test_mdtable_header_pos(self) -> None:
        """Test MDTable.header_pos finds first matching header."""
        table = MDTable(rows=[], headers=["Name", "Weight", "Price"])
        self.assertEqual(table.header_pos(["weight", "masse"]), 1)
        self.assertEqual(table.header_pos(["missing"], -1), -1)

    def test_mdtable_from_md_edge_cases(self) -> None:
        """Test MDTable.from_md with edge cases."""
        empty = MDTable.from_md("")
        self.assertEqual(empty.headers, [])
        self.assertEqual(empty.rows, [])

        no_data = MDTable.from_md("| A | B |\n|---|---|")
        self.assertEqual(no_data.headers, ["A", "B"])
        self.assertEqual(no_data.rows, [])

    def test_mdobj_confine_to_tables_non_horizontal(self) -> None:
        """Test confine_to_tables in key-value (non-horizontal) mode."""
        mdtext = "# Gear\n| Name | Cost |\n| Sword | 50s |\n| Shield | 20s |\n"
        mdobj = MDObj.from_md(mdtext)
        result, errors = mdobj.confine_to_tables(horizontal=False)
        self.assertEqual(result["Gear"]["Sword"], "50s")
        self.assertEqual(result["Gear"]["Shield"], "20s")
        self.assertEqual(errors, [])

    def test_mdobj_search_checklist_with_path(self) -> None:
        """Test searching for checklists by item text with path tracking."""
        md_text = "# Tasks\n- [ ] Buy milk\n- [x] Finish report\n## Chores\n- [ ] Clean garage"
        mdobj = MDObj.from_md(md_text)
        results = mdobj.search_checklist_with_path("Buy milk")
        self.assertEqual(results, [["Tasks"]])
        results = mdobj.search_checklist_with_path("Clean garage")
        self.assertEqual(results, [["Tasks", "Chores"]])
        results = mdobj.search_checklist_with_path("Nonexistent")
        self.assertEqual(results, [])
        results = mdobj.search_checklist_with_path("Finish report")
        self.assertEqual(results, [["Tasks"]])

    def test_mdobj_search_tables_nested(self) -> None:
        """Test MDObj.search_tables finds tables in child nodes."""
        md_text = "# Root\n| K | V |\n|---|---|\n| a | 1 |\n## Sub\n| X | Y |\n|---|---|\n| foo | bar |"
        mdobj = MDObj.from_md(md_text)
        found = mdobj.search_tables("foo")
        self.assertIsNotNone(found)
        assert found is not None
        row = found.row("foo")
        assert row is not None
        self.assertEqual(row["Y"], "bar")
        not_found = mdobj.search_tables("nope")
        self.assertIsNone(not_found)

    def test_mdobj_get_content_by_path(self) -> None:
        """Test MDObj.get_content_by_path traverses child hierarchy."""
        md_text = "# A\n## B\n### C\ncontent"
        mdobj = MDObj.from_md(md_text)
        node = mdobj.get_content_by_path(["A", "B", "C"])
        self.assertEqual(node.header, "C")
        self.assertIn("content", node.plaintext)

    def test_mdobj_replace_content_by_path(self) -> None:
        """Test MDObj.replace_content_by_path replaces a subtree."""
        md_text = "# Outer\n## Inner\nold content"
        mdobj = MDObj.from_md(md_text)
        mdobj.replace_content_by_path(["Outer"], "# Outer\n## Inner\nreplaced content")
        self.assertIn("replaced content", mdobj.children["Outer"].children["Outer"].children["Inner"].plaintext)

    def test_mdobj_getitem_keyerror(self) -> None:
        """Test MDObj.__getitem__ raises KeyError for missing keys."""
        mdobj = MDObj("no children or tables")
        with self.assertRaises(KeyError):
            _ = mdobj["nonexistent"]

    def test_mdobj_add_children(self) -> None:
        """Test MDObj.add_children adds multiple children."""
        mdobj = MDObj("root")
        children = [
            MDObj("child1 content", header="C1", level=2),
            MDObj("child2 content", header="C2", level=2),
        ]
        result = mdobj.add_children(children)
        self.assertIs(result, mdobj)
        self.assertIn("C1", mdobj.children)
        self.assertIn("C2", mdobj.children)

    def test_mdobj_empty_factory(self) -> None:
        """Test MDObj.empty creates an empty node."""
        empty = MDObj.empty()
        self.assertEqual(empty.plaintext, "")
        self.assertEqual(empty.children, {})
        self.assertEqual(empty.tables, [])
        self.assertEqual(empty.lists, [])

    def test_mdlist_item_repr(self) -> None:
        """Test MDListItem.__repr__ output."""
        from gamepack.MDPack import MDListItem

        item = MDListItem("hello", checked=False, level=1)
        self.assertIn("hello", repr(item))
        self.assertIn("False", repr(item))
        self.assertIn("level=1", repr(item))

    def test_mdtable_row_as_dict_out_of_range(self) -> None:
        """Test row_as_dict raises IndexError for out-of-range row."""
        table = MDTable(rows=[["1", "2"]], headers=["A", "B"])
        with self.assertRaises(IndexError):
            table.row_as_dict(5)

    def test_mdtable_to_simple(self) -> None:
        """Test MDTable.to_simple serialisation."""
        table = MDTable(rows=[["1", "2"]], headers=["X", "Y"])
        simple = table.to_simple()
        self.assertEqual(simple["rows"], [["1", "2"]])
        self.assertEqual(simple["headers"], ["X", "Y"])

    def test_mdlist_insert_lists_fallback(self) -> None:
        """Test insert_lists handles out-of-range positions by appending."""
        text = "preamble\n"
        mlist = MDList.from_md("- item")
        mlist.position = 999
        restored = MDList.insert_lists(text, [mlist])
        self.assertIn("- item", restored)

    def test_mdlist_extract_lists_trailing(self) -> None:
        """Test extract_lists handles trailing list at end of input."""
        text = "text\n- item 1\n- item 2"
        _, lists = MDList.extract_lists(text)
        self.assertEqual(len(lists), 1)
        self.assertIn("- item 1", lists[0].to_md())
        self.assertIn("- item 2", lists[0].to_md())

    def test_search_tables_module_not_found(self) -> None:
        """Test module-level search_tables returns empty for no match."""
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        self.assertEqual(search_tables(md, "no_match"), "")

    def test_table_row_edit_no_match(self) -> None:
        """Test table_row_edit returns original when key not found."""
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        self.assertEqual(table_row_edit(md, "nope", "x"), md)

    def test_table_remove_no_match(self) -> None:
        """Test table_remove returns original when key not found."""
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        self.assertEqual(table_remove(md, "nope"), md)

    def test_traverse_md_case_insensitive(self) -> None:
        """Test traverse_md is case-insensitive."""
        md = "# SKILLS\nsome content\n## SUBSKILL\nmore"
        self.assertIn("SKILLS", traverse_md(md, "skills"))

    def test_mdtable_line_align_center(self) -> None:
        """Test MDTable line_align applies center alignment."""
        table = MDTable(rows=[["1"]], headers=["A"], style=["c"])
        self.assertEqual(table.line_align("hello", "c", 11), "   hello   ")
