import logging
import re
from typing import List, Dict, Tuple, Callable, Optional, Union, Any, Sequence

log = logging.Logger(__name__)


class MDListItem:
    """
    A single item in a Markdown list or checklist.
    Supports nesting via levels.
    """

    def __init__(
        self,
        text: str,
        bullet: str = "-",
        checked: Optional[bool] = None,
        level: int = 0,
    ):
        self.text = text.strip()
        self.bullet = bullet
        self.checked = checked
        self.level = level

    def __repr__(self):
        return f"MDListItem(text={self.text!r}, bullet={self.bullet!r}, checked={self.checked}, level={self.level})"


class MDList:
    """
    A class representing a Markdown list (ordered, unordered, or checklist).
    Supports nesting and round-trip serialization.
    """

    # Matches bullet, optional checkbox, and text. Group 1: indent, 2: bullet, 3: checkbox, 4: text
    LIST_PATTERN = re.compile(
        r"^(\s*)([-*+]|\d+\.)\s+(?:\[(\s*x?\s*)]\s*)?(.*)", re.MULTILINE
    )

    def __init__(self, items: List[MDListItem], position: Optional[int] = None):
        self.items = items
        self.position = position

    def to_md(self) -> str:
        """
        Convert the list back into Markdown format.
        Nesting is preserved via indentation.
        """
        lines = []
        for item in self.items:
            indent = "  " * item.level
            checkbox = ""
            if item.checked is not None:
                checkbox = f" [{'x' if item.checked else ' '}]"
            lines.append(f"{indent}{item.bullet}{checkbox} {item.text}")
        return "\n".join(lines)

    @property
    def checklist(self) -> List[Tuple[str, bool]]:
        """Compatibility property for legacy flattened checklist access."""
        return [
            (item.text, bool(item.checked))
            for item in self.items
            if item.checked is not None
        ]

    @classmethod
    def from_md(cls, md_text: str, position: Optional[int] = None) -> "MDList":
        """
        Parse a Markdown string containing a list.
        Detects nesting levels based on indentation.
        """
        lines = md_text.split("\n")
        items = []

        # We need to normalize indentation to levels
        indents = []

        for line in lines:
            match = cls.LIST_PATTERN.match(line)
            if match:
                indent_str, bullet, checkbox_str, text = match.groups()

                # Determine level
                indent_len = len(indent_str)
                if indent_len not in indents:
                    indents.append(indent_len)
                    indents.sort()
                level = indents.index(indent_len)

                checked = None
                if checkbox_str is not None:
                    checked = checkbox_str.strip().lower() == "x"

                items.append(MDListItem(text, bullet, checked, level))

        return cls(items, position)

    @classmethod
    def extract_lists(cls, plaintext: str) -> Tuple[str, List["MDList"]]:
        """
        Extract all lists (including checklists) from a block of text.
        Lists are removed from the text and returned as MDList objects.
        """
        text_lines = []
        linenr = 0
        start_line: Optional[int] = None
        lists: List[MDList] = []
        run = ""

        lines = plaintext.splitlines(True)
        for line in lines:
            if cls.LIST_PATTERN.match(line):
                if start_line is None:
                    start_line = linenr
                run += line
            else:
                if run:
                    mlist = MDList.from_md(run, position=start_line)
                    # Use MDChecklist if it contains checkboxes
                    if any(item.checked is not None for item in mlist.items):
                        lists.append(MDChecklist.from_md(run, position=start_line))
                    else:
                        lists.append(mlist)
                    start_line = None
                    run = ""
                text_lines.append(line)
                linenr += 1

        if run:
            mlist = MDList.from_md(run, position=start_line)
            if any(item.checked is not None for item in mlist.items):
                lists.append(MDChecklist.from_md(run, position=start_line))
            else:
                lists.append(mlist)

        return "".join(text_lines), lists

    @classmethod
    def insert_lists(cls, text: str, lists: Sequence["MDList"]) -> str:
        """
        Reinsert extracted lists back into the given text at their original positions.
        """
        if not lists:
            return text

        lists_sorted = sorted(
            lists,
            key=lambda mlist: mlist.position if mlist.position is not None else -1,
        )
        lines = text.splitlines(True)

        offset = 0
        for mlist in lists_sorted:
            pos = mlist.position if mlist.position is not None else -1
            if 0 <= pos <= len(lines):
                effective_pos = pos + offset
                lines.insert(effective_pos, mlist.to_md() + "\n")
                offset += 1
            else:
                lines.append(mlist.to_md() + "\n")
                offset += 1

        return "".join(lines)


class MDChecklist(MDList):
    """
    Legacy compatibility class for MDChecklist.
    Now wraps MDList functionality.
    """

    CHECKBOX_PATTERN = re.compile(r"-\s*\[(\s*x?\s*)] ?(.*)")

    def __init__(
        self, checklist: List[Tuple[str, bool]], position: Optional[int] = None
    ):
        items = [MDListItem(text, "-", checked, 0) for text, checked in checklist]
        super().__init__(items, position)

    @classmethod
    def from_md(cls, md_text: str, position: Optional[int] = None) -> "MDChecklist":
        mlist = MDList.from_md(md_text, position)
        checklist_items = []
        for item in mlist.items:
            if item.checked is not None:
                checklist_items.append((item.text, item.checked))
        return cls(checklist_items, position)

    @classmethod
    def extract_checklists(cls, plaintext: str) -> Tuple[str, List["MDChecklist"]]:
        """
        Maintains legacy behavior: extracts only items with checkboxes.
        """
        # We use MDList to find all lists, then filter for checklists
        # Actually, better to just use the original logic but return MDChecklist
        # to ensure we don't extract regular lists if only checklists were requested.
        text_lines = []
        linenr = 0
        start_line: Optional[int] = None
        checklists: List[MDChecklist] = []
        run = ""

        for line in plaintext.splitlines(True):
            if cls.CHECKBOX_PATTERN.match(line):
                if start_line is None:
                    start_line = linenr
                run += line
            else:
                if run:
                    checklists.append(cls.from_md(run, position=start_line))
                    start_line = None
                    run = ""
                text_lines.append(line)
                linenr += 1

        if run:
            checklists.append(cls.from_md(run, position=start_line))

        return "".join(text_lines), checklists

    @classmethod
    def insert_checklists(cls, text: str, checklists: List["MDChecklist"]) -> str:
        """
        Maintains legacy behavior: reinserts checklists.
        """
        return cls.insert_lists(text, checklists)


class MDTable:
    """
    A class representing a Markdown table.
    Provides methods for parsing, manipulating, and serializing tables.
    """

    def __init__(
        self,
        rows: List[List[str]],
        headers: List[str],
        style: Optional[List[Optional[str]]] = None,
    ):
        """
        Initialize an MDTable.

        :param rows: 2D list of strings (data rows).
        :param headers: List of header strings.
        :param style: List of alignment styles ('l', 'r', 'c', or None).
        :raises ValueError: If a row length doesn't match the number of headers.
        """
        for row in rows:
            if len(row) != len(headers):
                raise ValueError(
                    f"Row length {len(row)} does not match headers' length {len(headers)}: {row}"
                )
        self.rows: List[List[str]] = rows
        self.headers: List[str] = headers
        self.style: List[Optional[str]] = (
            list(style) if style else [None] * len(headers)
        )
        self.prev_line_nr: Optional[int] = None  # For reconstruction

    @staticmethod
    def split_row(row: str, length: int) -> List[str]:
        """
        Split a Markdown table row into individual cells.
        Handles optional outer pipes and missing leading empty cells.

        :param row: The row string to split.
        :param length: Expected number of columns.
        :return: List of cell contents, padded/truncated to length.
        """
        row = row.strip()
        first_cell_potentially_missing = False
        if row.startswith("|"):
            first_cell_potentially_missing = True
            row = row[1:]
        if row.endswith("|"):
            row = row[:-1]

        cells = [x.strip() for x in row.split("|")]

        if len(cells) < length and first_cell_potentially_missing:
            # Handle cases where the first empty cell before | is omitted in split
            cells = [""] + cells

        # Pad or truncate to exact length
        if len(cells) < length:
            cells += [""] * (length - len(cells))
        return cells[:length]

    def row_as_dict(self, row_idx: int) -> Dict[str, str]:
        """
        Get a row as a dictionary mapping headers to cell values.

        :param row_idx: Index of the data row.
        :return: Dictionary of {header: value}.
        :raises IndexError: If row_idx is out of range.
        """
        if 0 <= row_idx < len(self.rows):
            return {
                header: self.rows[row_idx][i] for i, header in enumerate(self.headers)
            }
        raise IndexError("Row index out of range")

    @staticmethod
    def extract_styles(row: List[str]) -> List[Optional[str]]:
        """
        Extract alignment styles from a separator row (e.g., |:---|---:|).

        :param row: List of cell contents from the separator row.
        :return: List of styles ('l', 'r', 'c', or None).
        """
        styles = []
        for cell in row:
            if cell.startswith(":") and cell.endswith(":"):
                styles.append("c")
            elif cell.startswith(":"):
                styles.append("l")
            elif cell.endswith(":"):
                styles.append("r")
            else:
                styles.append(None)
        return styles

    def row(self, key: str) -> Optional[Dict[str, str]]:
        """
        Get a full row as a dictionary, using the first column as the key.

        :param key: Key to look for in the first column.
        :return: Dictionary of {header: value} for the matching row, or None.
        """
        for i, r in enumerate(self.rows):
            if r and r[0] == key:
                return self.row_as_dict(i)
        return None

    @classmethod
    def from_md(cls, md: str) -> "MDTable":
        """
        Parse a Markdown string into an MDTable.
        Attempts to be robust against various human-generated formats.

        :param md: The Markdown table string.
        :return: An MDTable instance.
        """
        lines = [line.strip() for line in md.splitlines() if line.strip()]
        if not lines:
            return cls([], [])

        def parse_line(line: str) -> List[str]:
            # Remove outer pipes if present
            content = line
            if content.startswith("|"):
                content = content[1:]
            if content.endswith("|"):
                content = content[:-1]
            return [cell.strip() for cell in content.split("|")]

        # Header processing
        headers = parse_line(lines.pop(0))

        if not lines:
            return cls([], headers)

        # Style row detection
        styles: List[Optional[str]] = [None] * len(headers)
        if lines and all(c in "- |:" for c in lines[0]):
            style_row = parse_line(lines.pop(0))
            # If style row has different number of columns, it might not be a style row
            # or the table is malformed.
            if len(style_row) == len(headers):
                styles = cls.extract_styles(style_row)
            else:
                # Put it back, it might be a data row that just looks like a style row
                # (unlikely but possible in some weird MD variants)
                # Actually, standard MD REQUIRES it to match.
                # If it doesn't match, we might want to warn or just ignore it.
                pass

        rows = []
        for line in lines:
            cells = parse_line(line)
            # Robustness: pad or truncate to match headers
            if len(cells) < len(headers):
                cells += [""] * (len(headers) - len(cells))
            elif len(cells) > len(headers):
                cells = cells[: len(headers)]
            rows.append(cells)

        return cls(rows, headers, styles)

    def to_md(self) -> str:
        """
        Serialize the table back to Markdown.
        Normalization occurs here: column widths are standardized and alignment is applied.

        :return: Markdown string.
        """
        self.canonize()
        columns = len(self.headers)
        if not self.rows and not self.headers:
            return ""  # empty table

        display_rows = self.rows if self.rows else [[""] * columns]

        # Calculate column widths
        column_widths = [len(h) for h in self.headers]
        for row in display_rows:
            for i in range(columns):
                if i < len(row):
                    column_widths[i] = max(column_widths[i], len(row[i]))

        # Ensure min width for separator
        column_widths = [max(w, 3) for w in column_widths]

        def format_row(r):
            return (
                "| "
                + " | ".join(
                    self.line_align(r[i], self.style[i], column_widths[i])
                    for i in range(columns)
                )
                + " |"
            )

        result = format_row(self.headers) + "\n"

        # Separator line
        sep_parts = []
        for i in range(columns):
            s = self.style[i]
            width = column_widths[i]
            # Compact style
            if s == "c":
                sep = ":" + "-" * (width - 2) + ":"
            elif s == "r":
                sep = "-" * (width - 1) + ":"
            elif s == "l":
                sep = ":" + "-" * (width - 1)
            else:
                sep = "-" * width
            sep_parts.append(sep)

        result += "|" + "|".join(sep_parts) + "|"

        if self.rows:
            for row in self.rows:
                result += "\n" + format_row(row)

        return result

    @property
    def rows_dict(self) -> Dict[str, Dict[str, str]]:
        """
        Returns a dictionary where keys are the first column values
        and values are dictionaries mapping headers to cell contents.
        """
        return {r[0]: self.row_as_dict(i) for i, r in enumerate(self.rows) if r}

    def __repr__(self):
        return f"MDTable(headers={self.headers}, rows={len(self.rows)})"

    @staticmethod
    def line_align(line: str, align: Optional[str], length: int) -> str:
        """
        Align a cell's content string.

        :param line: Cell content.
        :param align: 'l', 'r', 'c', or None.
        :param length: Target width.
        :return: Aligned string.
        """
        line = line if line is not None else ""
        if align == "l":
            return line.ljust(length)
        if align == "r":
            return line.rjust(length)
        if align == "c":
            return line.center(length)
        return line.ljust(length)

    def search(self, searchterm: str) -> Optional[List[str]]:
        """
        Find the first row containing the searchterm.

        :param searchterm: String to search for.
        :return: The matching row (list of cells) or None.
        """
        if any(searchterm in h for h in self.headers):
            return self.headers

        for row in self.rows:
            if any(searchterm in cell for cell in row):
                return row
        return None

    def to_simple(self) -> Dict[str, Any]:
        """Convert table data to a simple dictionary."""
        return {"styles": self.style, "headers": self.headers, "rows": self.rows}

    def update_cell(self, row: int, col: int, data: str):
        """
        Update a specific cell value. Expands the table if indices are out of bounds.

        :param row: Data row index.
        :param col: Column index.
        :param data: New cell value.
        """
        while row >= len(self.rows):
            self.rows.append([""] * len(self.headers))
        while col >= len(self.rows[row]):
            self.rows[row].append("")
        self.rows[row][col] = data

    def update_rows(self, data: List[List[str]]):
        """Update multiple rows of data."""
        for i, r in enumerate(data):
            for h, d in enumerate(r):
                self.update_cell(i, h, d)

    def clear_rows(self):
        """Remove all data rows."""
        self.rows = []

    def canonize(self):
        """Ensure all cells are strings and trim trailing empty rows."""
        self.rows = [[str(x) for x in row] for row in self.rows]
        self.headers = [str(x) for x in self.headers]
        # Pad styles if missing
        if len(self.style) < len(self.headers):
            self.style += [None] * (len(self.headers) - len(self.style))

        # Delete empty rows at the end
        while self.rows and not any(x.strip() for x in self.rows[-1]):
            self.rows.pop()

    def __getitem__(self, key: str) -> Optional[str]:
        """Dictionary-like access: treats first column as key and second as value."""
        return self.get(key)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Treat the table as a dictionary where the first column is the key
        and the second column is the value.

        :param key: Key to look for in the first column.
        :param default: Value if key not found.
        :return: Value from the second column or default.
        """
        for row in self.rows:
            if len(row) > 1 and row[0] == key:
                return row[1]
        return default

    def column(self, key: str, default: Optional[List[str]] = None) -> List[str]:
        """
        Get all values in a specific column by header name.

        :param key: Header name.
        :param default: Value if header not found.
        :return: List of column values.
        """
        try:
            position = [x.lower() for x in self.headers].index(key.lower())
            return [row[position] for row in self.rows if len(row) > position]
        except ValueError:
            return default or []

    def header_pos(self, possible_headers: List[str], default: int = -1) -> int:
        """
        Find the index of the first matching header from a list of candidates.

        :param possible_headers: List of candidate header names.
        :param default: Value if no candidate found.
        :return: Column index.
        """
        lowercase = [x.lower() for x in self.headers]
        for candidate in possible_headers:
            if candidate.lower() in lowercase:
                return lowercase.index(candidate.lower())
        return default

    @classmethod
    def extract_tables(cls, plaintext: str) -> Tuple[str, List["MDTable"]]:
        """
        Extract all tables from a block of text.

        :param plaintext: Input text.
        :return: Tuple of (text_without_tables, list_of_extracted_tables).
        """
        text_lines = []
        linenr = 0
        start_line: Optional[int] = None
        tables: List[MDTable] = []
        run = ""

        for line in plaintext.splitlines(True):
            if "|" in line:
                if start_line is None:
                    start_line = linenr
                run += line
            else:
                if run:
                    t = MDTable.from_md(run)
                    t.prev_line_nr = start_line
                    tables.append(t)
                    run = ""
                    start_line = None
                text_lines.append(line)
                linenr += 1

        if run:
            t = MDTable.from_md(run)
            t.prev_line_nr = start_line
            tables.append(t)

        return "".join(text_lines), tables

    @classmethod
    def insert_tables(cls, text: str, tables: List["MDTable"]) -> str:
        """
        Reinsert extracted tables back into text at their original positions.

        :param text: Text without tables.
        :param tables: List of MDTable objects.
        :return: Reconstructed text.
        """
        if not tables:
            return text

        lines = text.splitlines(False)

        # We must insert from bottom up to preserve indices or use offset logic
        tables_sorted = sorted(
            tables, key=lambda t: t.prev_line_nr if t.prev_line_nr is not None else -1
        )

        offset = 0
        for table in tables_sorted:
            pos = table.prev_line_nr if table.prev_line_nr is not None else 0
            md = table.to_md()
            if 0 <= pos + offset <= len(lines):
                lines.insert(pos + offset, md)
                offset += 1
            else:
                lines.append(md)
                offset += 1

        return "\n".join(lines)


class MDObj:
    """
    A tree-like representation of a Markdown document based on headers.
    Automatically extracts tables, checklists, and general lists from the text content of each node.
    """

    def __init__(
        self,
        plaintext: str,
        children: Optional[Dict[str, "MDObj"]] = None,
        flash: Optional[Callable[[str], None]] = None,
        tables: Optional[List[MDTable]] = None,
        level: int = 0,
        header: str = "",
        original: Optional[str] = None,
        lists: Optional[List[MDList]] = None,
        checklists: Optional[List[MDChecklist]] = None,
    ):
        """
        Initialize an MDObj.

        :param plaintext: Content of this node.
        :param children: Dictionary of child nodes {header: MDObj}.
        :param flash: Function to call for reporting errors.
        :param tables: List of tables in this node (extracted if None).
        :param level: Header level (1 for #, 2 for ##, etc.).
        :param header: Header text.
        :param original: Original Markdown source (if available).
        :param lists: List of lists/checklists in this node (extracted if None).
        :param checklists: Legacy parameter for checklists (alias for lists).
        """
        self.originalMD: str = original or plaintext

        # Initial extraction
        if tables is None:
            self.plaintext, self.tables = MDTable.extract_tables(plaintext)
        else:
            self.plaintext = plaintext
            self.tables = tables

        if lists is None:
            if checklists is not None:
                self.lists = [
                    mlist for mlist in checklists if isinstance(mlist, MDList)
                ]  # ensure correct type
                # Clean plaintext if checklists were provided but tables extracted from plaintext
                # This is tricky because we don't know where checklists were.
                # But legacy code usually passed empty plaintext if providing parts.
            else:
                self.plaintext, self.lists = MDList.extract_lists(self.plaintext)
        else:
            self.lists = lists

        self.children: Dict[str, "MDObj"] = children or {}
        self.level = level
        self.header = header
        self.errors: List[str] = []
        self.flash = flash or self.add_to_error

    @property
    def checklists(self) -> List[MDChecklist]:
        """Compatibility property for legacy checklist access."""
        return [mlist for mlist in self.lists if isinstance(mlist, MDChecklist)]

    def add_to_error(self, error: str):
        """Default error reporter: appends to self.errors."""
        self.errors.append(error)

    @property
    def all_checklists(self) -> List[Tuple[str, bool]]:
        """Flattened list of all checklist items in this node."""
        return [item for mlist in self.lists for item in mlist.checklist]

    def search_checklist_with_path(
        self, name: str, path: Optional[List[str]] = None
    ) -> List[List[str]]:
        """
        Find the path to a checklist item by its name.

        :param name: Item text to find.
        :param path: Current accumulation path (internal recursion).
        :return: List of paths (lists of header names).
        """
        if path is None:
            path = []
        results = []

        for mlist in self.lists:
            for item in mlist.items:
                if item.text == name and item.checked is not None:
                    results.append(path[:])

        for heading, child in self.children.items():
            results.extend(child.search_checklist_with_path(name, path + [heading]))

        return results

    def __repr__(self):
        return (
            f"{self.header or 'MDObj'}(len={len(self.plaintext)}, "
            f"tables={len(self.tables)}, lists={len(self.lists)}, children={list(self.children.keys())})"
        )

    def __getitem__(self, key: str) -> Any:
        """
        Access children or table values using square bracket notation.
        Priority: 1. Children, 2. Tables (in order of appearance).
        """
        # Search through children
        if key in self.children:
            return self.children[key]

        # Search through tables
        for t in self.tables:
            value = t.get(key)
            if value is not None:
                return value

        raise KeyError(f"'{key}' not found in {self.header or 'MDObj'}")

    @classmethod
    def from_md(
        cls,
        lines: Union[str, List[str]],
        level: int = 0,
        header: str = "",
        flash: Optional[Callable[[str], None]] = None,
    ) -> "MDObj":
        """
        Recursively parse Markdown source into a tree of MDObj nodes.

        :param lines: Markdown string or stack of lines.
        :param level: Current header level being parsed.
        :param header: Current header text.
        :param flash: Error reporting function.
        :return: Root MDObj of the parsed tree.
        """
        if isinstance(lines, str):
            original = lines[:]
            lines = list(reversed(lines.split("\n")))
        else:
            original = "\n".join(reversed(lines))

        text_accumulated = ""
        children = {}

        while lines:
            line = lines[-1]  # Peek

            # Check for header
            if line.strip().startswith("#"):
                current_header_level = len(line.strip()) - len(line.strip().lstrip("#"))

                if current_header_level > 0:
                    if level >= current_header_level and level != 0:
                        # Sibling or parent header found, stop recursion for this level.
                        break

                    if current_header_level > level:
                        # Found a child (or deeper descendant).
                        # Consume the line
                        header_line = lines.pop()
                        header_title = header_line.lstrip("# ").strip()

                        # Handle duplicates
                        k = header_title
                        while k in children:
                            k += "_"

                        # Parse child
                        children[k] = cls.from_md(
                            lines=lines,  # Pass reference to stack
                            level=current_header_level,
                            header=header_title,
                            flash=flash,
                        )
                        continue

            # If not a relevant header, consume line as text
            text_accumulated += lines.pop() + "\n"

        return cls(
            text_accumulated,
            children,
            flash,
            level=level,
            header=header,
            original=original,
        )

    def confine_to_tables(
        self, horizontal: bool = False
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Simplify the MDTree into a nested dictionary of data.
        Assumes the document is primarily structured data (tables/checklists/subheaders).

        :param horizontal: If True, treats tables as having headers in the first row.
        :return: Tuple of (data_dict, list_of_errors).
        """
        result = {}
        errors = []

        def error(msg: str):
            errors.append(msg)
            log.info(msg)

        if horizontal:
            for subtable in self.tables:
                for row in subtable.rows:
                    if not row:
                        continue
                    key = row[0]
                    result[key] = {}
                    # Headers skip the first one (key col)
                    for i, heading in enumerate(subtable.headers[1:]):
                        if i + 1 < len(row):
                            result[key][heading] = row[i + 1]
        else:
            for subtable in self.tables:
                for row in subtable.rows:
                    if not row:
                        continue
                    if len(row) != 2:
                        error(
                            f"Malformed KeyValue at row '{'|'.join(row)}' in {subtable} "
                        )
                        continue
                    result[row[0]] = row[1]

        for child_name, child_obj in self.children.items():
            if child_obj.children or child_obj.tables:
                child_data, newerrors = child_obj.confine_to_tables(horizontal)
                result[child_name] = child_data
                errors += newerrors
            else:
                result[child_name] = child_obj.plaintext.strip()
                if (
                    not child_obj.children
                    and not child_obj.plaintext.strip()
                    and not child_obj.tables
                ):
                    error(f"Extraneous Subheading: '{child_name}'")

        if self.plaintext.strip():
            error(f"Extraneous Text: '{self.plaintext.strip()}'")

        return result, errors

    def search_children(self, name: str) -> Optional["MDObj"]:
        """
        Search for an MDObj node by its header name (case-insensitive).

        :param name: Header name to search for.
        :return: Found MDObj or None.
        """
        # Search direct children first
        for child_name in self.children:
            if name.lower().strip() == child_name.lower().strip():
                return self.children[child_name]

        # Search tables
        for t in self.tables:
            if t.search(name):
                return self

        # Depth first search
        for child in self.children.values():
            if result := child.search_children(name):
                return result
        return None

    def set_levels(self, newlevel: Optional[int] = None):
        """Recursively set header levels for the tree."""
        if newlevel is not None:
            self.level = newlevel
        for child in self.children.values():
            if not child.level:
                child.set_levels(self.level + 1)

    def add_child(self, child: "MDObj") -> "MDObj":
        """Add a child node. Returns self for chaining."""
        if self.is_ancestor(child):
            raise Exception(
                "Cannot add child, it is already a descendant of this object"
            )
        name = child.header.strip()
        self.children[name] = child
        return self

    def is_ancestor(self, child: "MDObj") -> bool:
        """Check if child is already a descendant of this node."""
        for candidate in self.children.values():
            if candidate == child or candidate.is_ancestor(child):
                return True
        return False

    def add_children(self, children: List["MDObj"]) -> "MDObj":
        """Add multiple child nodes."""
        for child in children:
            self.add_child(child)
        return self

    def to_md(self, do_header: bool = True) -> str:
        """
        Serialize the tree back to Markdown in a canonical, optimal format.
        Maintains order of tables and lists based on their stored positions.

        :param do_header: Whether to include the header of this node.
        :return: Markdown string.
        """
        if not self.level:
            self.set_levels(0)

        # Reconstruct body from cleaned plaintext and parts
        lines = self.plaintext.splitlines(True)
        parts: List[Tuple[int, Union[MDTable, MDList]]] = []
        for t in self.tables:
            parts.append(
                (t.prev_line_nr if t.prev_line_nr is not None else len(lines), t)
            )
        for mlist in self.lists:
            parts.append(
                (mlist.position if mlist.position is not None else len(lines), mlist)
            )

        parts.sort(key=lambda x: x[0])

        # Reinsert parts into the body
        offset = 0
        for pos, part in parts:
            md_text = part.to_md()
            if not md_text.endswith("\n"):
                md_text += "\n"
            effective_pos = pos + offset
            if 0 <= effective_pos <= len(lines):
                lines.insert(effective_pos, md_text)
                offset += 1
            else:
                lines.append(md_text)
                offset += 1

        full_body = "".join(lines).rstrip()
        if full_body:
            full_body += "\n"

        result = ""
        if do_header and self.header.strip() and self.level > 0:
            result += f"{'#' * self.level} {self.header}\n"

        if full_body:
            result += full_body

        for child in self.children.values():
            child_md = child.to_md().strip("\n")
            if child_md:
                # Add separation between sections
                if result and not result.endswith("\n\n"):
                    if not result.endswith("\n"):
                        result += "\n"
                    result += "\n"
                result += child_md + "\n"

        return result

    def search_tables(self, searchterm: str) -> Optional[MDTable]:
        """Search all nodes for a table containing the searchterm."""
        for t in self.tables:
            if t.search(searchterm):
                return t
        for child in self.children.values():
            if (
                child.header.strip().lower() == searchterm.strip().lower()
                and len(child.tables) == 1
            ):
                return child.tables[0]
            r = child.search_tables(searchterm)
            if r:
                return r
        return None

    def replace_content_by_path(self, path: List[str], new_content: str):
        """Replace the content of a node at a specific path."""
        focus = self
        for p in path[:-1]:
            focus = focus.children[p]
        focus.children[path[-1]] = MDObj.from_md(new_content)

    def get_content_by_path(self, path: List[str]) -> "MDObj":
        """Get an MDObj node at a specific path."""
        focus = self
        for p in path:
            focus = focus.children[p]
        return focus

    def with_header(self, header_text: str) -> "MDObj":
        """Set the header text. Returns self for chaining."""
        self.header = header_text
        return self

    @classmethod
    def empty(cls) -> "MDObj":
        """Create an empty MDObj."""
        return cls("")


# Utilities


def table_row_edit(md: str, key: str, value: str) -> str:
    """
    Find a table row by its first column (key) and update its subsequent columns.

    :param md: Markdown source.
    :param key: Key to match in the first column.
    :param value: New cell values (as '|' delimited string).
    :return: Modified Markdown string.
    """
    old = search_tables(md, key, 0).strip()
    if not old:
        return md

    start = "|" if old.startswith("|") else ""
    end = "|" if old.endswith("|") else ""
    new = f"{start} {key} | {value} {end}"
    return md.replace(old, new, 1)


def table_md(t: List[List[str]]) -> str:
    """Simple converter for 2D list to Markdown table (no headers)."""
    return "\n".join(["|".join([x for x in row if x is not None]) for row in t if row])


def table_add(md: str, key: str, new_val: str) -> str:
    """
    Manually insert a row into a Markdown table in a string.

    :param md: Markdown source.
    :param key: Key for the first column.
    :param new_val: Value for the subsequent columns.
    :return: Modified Markdown string.
    """
    intable = False
    sofar = ""
    lines = md.splitlines(True)
    new_inserted = False

    for line in lines:
        if intable and "|" not in line and not new_inserted:
            # End of table
            prev_line = sofar.splitlines()[-1] if sofar else ""
            indent = len(prev_line) - len(prev_line.lstrip())

            sofar += " " * indent + f"| {key} | {new_val} |\n"
            new_inserted = True

        if "|" in line:
            intable = True
        else:
            intable = False

        sofar += line

    if not new_inserted:
        # Check if we ended inside table
        if intable:
            prev_line = sofar.splitlines()[-1] if sofar else ""
            indent = len(prev_line) - len(prev_line.lstrip())
            sofar += " " * indent + f"| {key} | {new_val} |\n"

    return sofar


def table_remove(md: str, key: str) -> str:
    """Remove a table row by its key."""
    old = search_tables(md, key, 0).strip()
    if not old:
        return md
    # We replace old row + newline with empty
    return md.replace(old + "\n", "", 1)


def search_tables(md: str, seek: str, surround: Optional[int] = None) -> str:
    """
    Search for a table row in Markdown text.

    :param md: Markdown source.
    :param seek: Term to search for.
    :param surround: If set, returns a block of rows around the match.
    :return: Matching table row or block.
    """
    found = False
    curtable = []
    end = -1

    for line in md.splitlines(True):
        if "|" in line:
            curtable.append(line)
            if not found and seek.lower() in line.lower():
                if line.strip(" |").lower().startswith(seek.strip(" |").lower()):
                    if surround is not None:
                        end = surround * 2 + 1
                        curtable = curtable[-surround - 1 :]
                    found = True

            if end != -1 and len(curtable) >= end:
                curtable = curtable[:end]
                break
        else:
            if found:
                break
            else:
                curtable = []

    if found:
        return "".join(curtable)
    else:
        return ""


def traverse_md(md: str, seek: str) -> str:
    """
    Extract all lines under a specific header level.

    :param md: Markdown source.
    :param seek: Header name to search for.
    :return: Extracted block of text.
    """
    result = ""
    level = 0
    seek = seek.strip(": ").upper()

    for line in md.split("\n"):
        if line.strip().startswith("#") or level:
            # Determine level of current line
            current_level = 0
            if line.strip().startswith("#"):
                current_level = len(line.strip()) - len(line.strip().lstrip("#"))

            if current_level and level >= current_level and level != 0:
                # Close section
                level = 0
                continue

            # Check if this is the start
            header_content = line.strip().lstrip("#").strip(": ").upper()
            if level or header_content == seek:
                if not level:
                    level = current_level

                result += line + "\n"
    return result
