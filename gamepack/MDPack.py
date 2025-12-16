import logging
import re
from typing import List, Dict, Tuple, Callable, Optional, Union, Any

log = logging.Logger(__name__)


class MDChecklist:
    CHECKBOX_PATTERN = re.compile(r"-\s*\[(\s*x?\s*)] ?(.*)")

    def __init__(
        self, checklist: List[Tuple[str, bool]], position: Optional[int] = None
    ):
        """
        :param checklist: List of tuples [(item_text, checked)]
        :param position: The line number where this checklist starts/belongs
        """
        self.checklist: List[Tuple[str, bool]] = checklist or []
        self.position = position

    def to_md(self) -> str:
        """Reinserts the checkboxes back into the original text format."""
        lines = []
        for item in self.checklist:
            if isinstance(item, str):
                item_text, checked = item, False
            else:
                item_text, checked = item
            lines.append(f"- [{'x' if checked else ' '}] {item_text}")
        return "\n".join(lines)

    def insert_into(self, text: str) -> str:
        """Inserts this checklist into the given text at self.position."""
        if self.position is None:
            return text + "\n" + self.to_md()
        return (
            text[: self.position] + "\n" + self.to_md() + "\n" + text[self.position :]
        )

    def get(self, name: str, default: Any = None) -> Union[bool, Any]:
        for item_text, checked in self.checklist:
            if item_text == name:
                return checked
        return default

    @classmethod
    def from_md(cls, md_text: str, position: Optional[int] = None) -> "MDChecklist":
        """Parses a markdown string containing a checklist."""
        lines = md_text.split("\n")
        checklist = []

        for line in lines:
            match = cls.CHECKBOX_PATTERN.match(line)
            if match:
                checked = match.group(1).strip() == "x"
                item_text = match.group(2).strip()
                checklist.append((item_text, checked))

        return cls(checklist, position)

    @classmethod
    def extract_checklists(cls, plaintext: str) -> Tuple[str, List["MDChecklist"]]:
        """
        Consumes checklists from plaintext where possible.
        Checklists are extracted and removed from the text, to be restored later.
        :return: (cleaned_text, list_of_checklists)
        """
        text_lines = []
        linenr = 0
        start_line: Optional[int] = None
        checklists: List[MDChecklist] = []
        run = ""

        for line in plaintext.splitlines(True):
            if MDChecklist.CHECKBOX_PATTERN.match(line):
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
            # No need to append to text_lines as it's extracted

        return "".join(text_lines), checklists

    @classmethod
    def insert_checklists(cls, text: str, checklists: List["MDChecklist"]) -> str:
        """
        Reinsert extracted checklists back into the given text at their original positions.
        """
        if not checklists:
            return text

        checklists = sorted(
            checklists, key=lambda c: c.position if c.position is not None else -1
        )
        lines = text.splitlines(True)

        offset = 0
        for checklist in checklists:
            pos = checklist.position if checklist.position is not None else -1
            if 0 <= pos <= len(lines):
                # Offset is added because previous insertions shifted indices
                effective_pos = pos + offset
                lines.insert(effective_pos, checklist.to_md() + "\n")
                offset += 1
            else:
                lines.append(checklist.to_md() + "\n")
                offset += 1

        return "".join(lines)


class MDTable:
    def __init__(
        self,
        rows: List[List[str]],
        headers: List[str],
        style: Optional[List[Optional[str]]] = None,
    ):
        for row in rows:
            if len(row) != len(headers):
                raise ValueError(
                    f"Row length {len(row)} does not match headers' length {len(headers)}: {row}"
                )
        self.rows: List[List[str]] = rows
        self.headers: List[str] = headers
        self.style: List[Optional[str]] = style or [None] * len(headers)
        self.prev_line_nr: Optional[int] = None  # For reconstruction

    @staticmethod
    def split_row(row: str, length: int) -> List[str]:
        """
        Splits a markdown table row into cells.
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
        if 0 <= row_idx < len(self.rows):
            return {
                header: self.rows[row_idx][i] for i, header in enumerate(self.headers)
            }
        raise IndexError("Row index out of range")

    @staticmethod
    def extract_styles(row: List[str]) -> List[Optional[str]]:
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

    @classmethod
    def from_md(cls, md: str) -> "MDTable":
        lines = md.splitlines()
        if not lines:
            return cls([], [])

        # Header processing
        headers_raw = lines.pop(0)
        # Handle outer pipes for header
        if headers_raw.strip().startswith("|"):
            headers_raw = headers_raw.strip()[1:]
        if headers_raw.strip().endswith("|"):
            headers_raw = headers_raw.strip()[:-1]

        headers = [x.strip() for x in headers_raw.split("|")]

        if not lines:
            return cls([], headers)

        # Style row detection
        # Check if the next row is a separator row (---)
        rows_raw = lines
        styles = [None] * len(headers)

        if rows_raw and all(c in "- |:" for c in rows_raw[0].strip()):
            style_row = cls.split_row(rows_raw.pop(0), len(headers))
            styles = cls.extract_styles(style_row)

        rows = [cls.split_row(row, len(headers)) for row in rows_raw]

        return cls(rows, headers, styles)

    def to_md(self) -> str:
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

    def __repr__(self):
        return f"MDTable({len(self.rows)} rows)"

    @staticmethod
    def line_align(line: str, align: Optional[str], length: int) -> str:
        line = line if line is not None else ""
        if align == "l":
            return line.ljust(length)
        if align == "r":
            return line.rjust(length)
        if align == "c":
            return line.center(length)
        return line.ljust(length)

    def search(self, searchterm: str) -> Optional[List[str]]:
        """Returns the first row containing the searchterm."""
        if any(searchterm in h for h in self.headers):
            return self.headers

        for row in self.rows:
            if any(searchterm in cell for cell in row):
                return row
        return None

    def to_simple(self) -> Dict[str, Any]:
        return {"styles": self.style, "headers": self.headers, "rows": self.rows}

    def update_cell(self, row: int, col: int, data: str):
        while row >= len(self.rows):
            self.rows.append([""] * len(self.headers))
        while col >= len(self.rows[row]):
            self.rows[row].append("")
        self.rows[row][col] = data

    def update_rows(self, data: List[List[str]]):
        for i, r in enumerate(data):
            for h, d in enumerate(r):
                self.update_cell(i, h, d)

    def clear_rows(self):
        self.rows = []

    def canonize(self):
        """Ensures all cells are strings and cleans up empty rows."""
        self.rows = [[str(x) for x in row] for row in self.rows]
        self.headers = [str(x) for x in self.headers]
        # Pad styles if missing
        if len(self.style) < len(self.headers):
            self.style += [None] * (len(self.headers) - len(self.style))

        # Delete empty rows at the end
        while self.rows and not any(x.strip() for x in self.rows[-1]):
            self.rows.pop()

    def __getitem__(self, key: str) -> Optional[str]:
        return self.get(key)

    def get(self, key: str, default: Any = None) -> Any:
        """Treat table as dictionary where first col is key, second col is value."""
        for row in self.rows:
            if len(row) > 1 and row[0] == key:
                return row[1]
        return default

    def column(self, key: str, default: List[str] = None) -> List[str]:
        try:
            position = [x.lower() for x in self.headers].index(key.lower())
            return [row[position] for row in self.rows if len(row) > position]
        except ValueError:
            return default or []

    def header_pos(self, possible_headers: List[str], default: int = -1) -> int:
        lowercase = [x.lower() for x in self.headers]
        for candidate in possible_headers:
            if candidate.lower() in lowercase:
                return lowercase.index(candidate.lower())
        return default

    @classmethod
    def extract_tables(cls, plaintext: str) -> Tuple[str, List["MDTable"]]:
        """
        Consumes tables from plaintext where possible.
        :return: (cleaned_text, list_of_tables)
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
        if not tables:
            return text

        lines = text.splitlines(False)

        # We must insert from bottom up to preserve indices
        tables.sort(key=lambda t: t.prev_line_nr if t.prev_line_nr is not None else -1)

        # Offset logic similar to checklists
        offset = 0
        for table in tables:
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
    def __init__(
        self,
        plaintext: str,
        children: Optional[Dict[str, "MDObj"]] = None,
        flash: Optional[Callable[[str], None]] = None,
        tables: Optional[List[MDTable]] = None,
        level: int = 0,
        header: str = "",
        original: Optional[str] = None,
        checklists: Optional[List[MDChecklist]] = None,
    ):
        self.originalMD: str = original or plaintext

        # Self.plaintext will hold the text content of *this* node
        # (excluding children headers content, extracting tables and checklists)
        self.plaintext: str = plaintext
        self.children: Dict[str, "MDObj"] = children or {}

        if tables is None:
            self.plaintext, self.tables = MDTable.extract_tables(self.plaintext)
        else:
            self.tables = tables

        self.level = level
        self.header = header
        self.errors: List[str] = []

        if checklists is None:
            self.plaintext, self.checklists = MDChecklist.extract_checklists(
                self.plaintext
            )
        else:
            self.checklists = checklists

        self.flash = flash or self.add_to_error

    def add_to_error(self, error: str):
        self.errors.append(error)

    @property
    def all_checklists(self) -> List[Tuple[str, bool]]:
        return [item for checklist in self.checklists for item in checklist.checklist]

    def search_checklist_with_path(
        self, name: str, path: Optional[List[str]] = None
    ) -> List[List[str]]:
        if path is None:
            path = []
        results = []

        for mdchecklist in self.checklists:
            for item, checked in mdchecklist.checklist:
                if item == name:
                    results.append(path[:])

        for heading, child in self.children.items():
            results.extend(child.search_checklist_with_path(name, path + [heading]))

        return results

    def __repr__(self):
        return (
            f"{self.header or 'MDObj'}(len={len(self.plaintext)}, "
            f"tables={len(self.tables)}, children={list(self.children.keys())})"
        )

    def __getitem__(self, key: str) -> Any:
        # Search through children
        if key in self.children:
            return self.children[key]
        for t in self.tables:
            value = t.get(key)
            if value:
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
        Recursively parses markdown into a tree of MDObjects based on headers.
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

                # Check for "Empty headers" or accidental #?
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
        Simplifies a MDTree into a dictionary of dictionaries/values.
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
            # Are we the root or a leaf that shouldn't have text?
            # confine_to_tables assumes structure is data. Loose text is "error".
            error(f"Extraneous Text: '{self.plaintext.strip()}'")

        return result, errors

    def search_children(self, name: str) -> Optional["MDObj"]:
        # Search direct children first
        for child_name in self.children:
            if name.lower().strip() == child_name.lower().strip():
                return self.children[child_name]

        # Search tables
        for t in self.tables:
            # t.search returns a row. But this function returns MDObj?
            # Original code: `if t.search(name): return self`
            # Meaning "I contain the term in my table, so return Me".
            if t.search(name):
                return self

        # Depth first search
        for child in self.children.values():
            if result := child.search_children(name):
                return result
        return None

    def set_levels(self, newlevel: Optional[int] = None):
        if newlevel is not None:
            self.level = newlevel
        for child in self.children.values():
            if not child.level:
                child.set_levels(self.level + 1)

    def add_child(self, child: "MDObj") -> "MDObj":
        if self.is_ancestor(child):
            raise Exception(
                "Cannot add child, it is already a descendant of this object"
            )
        name = child.header.strip()
        self.children[name] = child
        return self

    def is_ancestor(self, child: "MDObj") -> bool:
        for candidate in self.children.values():
            if candidate == child or candidate.is_ancestor(child):
                return True
        return False

    def add_children(self, children: List["MDObj"]) -> "MDObj":
        for child in children:
            self.add_child(child)
        return self

    def to_md(self, do_header: bool = True) -> str:
        if not self.level:
            self.set_levels(0)

        if self.plaintext.strip():
            body = self.plaintext.rstrip() + "\n"
        else:
            body = ""

        body = MDChecklist.insert_checklists(body, self.checklists)

        if self.tables:
            body += "\n"

        body = MDTable.insert_tables(body, self.tables)

        children_md = ""
        for child in self.children.values():
            children_md += child.to_md()

        # Ensure separation between body and children
        if body and children_md and not body.endswith("\n"):
            body += "\n"

        full_body = body + children_md

        if full_body and not full_body.endswith("\n"):
            full_body += "\n"

        if do_header and self.header.strip() and self.level > 0:
            return f"\n{'#' * self.level} {self.header}\n" + full_body

        return full_body

    def search_tables(self, searchterm: str) -> Optional[MDTable]:
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
        focus = self
        for p in path[:-1]:
            focus = focus.children[p]
        focus.children[path[-1]] = MDObj.from_md(new_content)

    def get_content_by_path(self, path: List[str]) -> "MDObj":
        focus = self
        for p in path:
            focus = focus.children[p]
        return focus

    def with_header(self, header_text: str) -> "MDObj":
        self.header = header_text
        return self

    @classmethod
    def empty(cls) -> "MDObj":
        return cls("")


# Utilities


def table_row_edit(md: str, key: str, value: str) -> str:
    """
    Changes everything but the leftmost column in a table the first time key is encountered.
    """
    old = search_tables(md, key, 0).strip()
    if not old:
        return md

    start = "|" if old.startswith("|") else ""
    end = "|" if old.endswith("|") else ""
    new = f"{start} {key} | {value} {end}"
    return md.replace(old, new, 1)


def table_md(t: List[List[str]]) -> str:
    return "\n".join(["|".join([x for x in row if x is not None]) for row in t if row])


def table_add(md: str, key: str, new_val: str) -> str:
    """Inserts a row into a markdown table manually."""
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
    old = search_tables(md, key, 0).strip()
    if not old:
        return md
    # We replace old row + newline with empty
    return md.replace(old + "\n", "", 1)


def search_tables(md: str, seek: str, surround: Optional[int] = None) -> str:
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
