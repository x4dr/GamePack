import logging
from typing import List, Dict, Tuple, Callable, Self, Optional

log = logging.Logger(__name__)


class MDTable:
    def __init__(
        self, rows: List[List[str]], headers: List[str], style: List[str] | None = None
    ):
        for row in rows:
            if len(row) != len(headers):
                raise ValueError(
                    f"Row length {len(row)} does not match headers' length {len(headers)} "
                )
        self.rows = rows
        self.headers = headers
        self.style = style or [None] * len(headers)
        self.prev_line_nr = None  # To help with placing the table back into context

    @staticmethod
    def split_row(row: str, length: int) -> List[str]:
        """
        splits a md table row into a list of cells, using the length to decide if the row was missing
        the initial
        :param row: md table row string
        :param length: exact number of columns
        :return: List of the first length table cells
        """
        row = row.strip()
        first_cell_potentially_missing = False
        if row.startswith("|"):
            first_cell_potentially_missing = True
            row = row[1:]
        if row.endswith("|"):
            row = row[:-1]
        rows = [x.strip() for x in row.split("|")]
        if len(rows) < length and first_cell_potentially_missing:
            rows = [""] + rows
        return (rows + [""] * (length - len(rows)))[:length]

    @staticmethod
    def extract_styles(row: List[str]) -> List[str]:
        """
        extracts the styles from a md table row
        :param row: md table row string
        :return: List of the styles
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

    @classmethod
    def from_md(cls, md: str) -> "MDTable":
        """
        gets table from md text.
        Assumes all text is part of table and will enforce the tablewidth given in
        format row. This means non-table text will be assumed to be just the first
        column and the rest will be filled with "". Every column past the ones
        alignment was defined for will be cut.
        :param md: md text from the first to the last line of the table
        :return: list of table rows, all having uniform length
        """
        lines = md.splitlines()
        headers = lines.pop(0).split("|")
        # remove first and last cell if they are empty
        if not headers[0].strip():
            headers = headers[1:]
        if not headers[-1].strip():
            headers = headers[:-1]
        headers = [x.strip() for x in headers]

        rows = [cls.split_row(row, len(headers)) for row in lines]
        if not rows:
            return cls([], headers)
        # remove the separator
        if all(x in "- |:" for x in "".join(rows[0])):
            styles = cls.extract_styles(rows.pop(0))
        else:
            styles = [None] * len(headers)
        # ensure all rows have the same length
        for row in rows:
            row += [""] * (len(headers) - len(row))
        # ensure no row is longer than headers
        rows = [row[: len(headers)] for row in rows]
        return cls(rows, headers, styles)

    def to_md(self):
        """
        converts the table back to markdown
        :return: markdown
        """
        self.canonize()
        columns = len(self.headers)
        if not self.rows:
            self.rows = [[""] * columns]

        column_widths = [len(self.headers[i]) for i in range(columns)]
        for row in self.rows:
            for i in range(columns):
                if len(row) > i:
                    column_widths[i] = max(column_widths[i], len(row[i]))

        result = "| "
        result += " | ".join(
            self.line_align(self.headers[h], self.style[h], column_widths[h])
            for h in range(columns)
        )
        result += " |\n"
        for i in range(len(self.headers)):
            s = self.style[i] or "x"
            stylebegin = ":" if s in "lc" else ""
            styleend = ":" if s in "rc" else ""
            lesser = len(stylebegin + styleend) - 1
            result += f"|{stylebegin}-{'-' * (column_widths[i] - lesser)}{styleend}"
        result += "|\n"
        for row in self.rows:
            if len(row) < columns:  # pad empty cells
                row.extend([""] * (columns - len(row)))
            result += "| "
            result += " | ".join(
                self.line_align(row[i], self.style[i], column_widths[i])
                for i in range(columns)
            )
            result += " |\n"
        return result

    def __repr__(self):
        return f"MDTable{self.to_md()}"

    @staticmethod
    def line_align(line: str, align: str, length: int) -> str:
        """
        aligns a line according to the table's alignment
        :param line: the line to align
        :param align: the alignment of the line
        :param length: the length to align to
        :return: the aligned line
        """
        if align == "l":
            return line.ljust(length)
        elif align == "r":
            return line.rjust(length)
        elif align == "c":
            return line.center(length)
        return line.ljust(length)

    def search(self, searchterm) -> List[str] | None:
        """
        searches the table for a searchterm
        :param searchterm: the term to search for
        :return: True if the searchterm is found
        """
        for row in self.rows + self.headers:
            for cell in row:
                if searchterm in cell:
                    return row
        return None

    def to_simple(self):
        return {"styles": self.style, "headers": self.headers, "rows": self.rows}

    def update_cell(self, row: int, col: int, data: str):
        while row >= len(self.rows):
            self.rows.append([])
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
        # make all cells str
        self.rows = [[str(x) for x in row] for row in self.rows]
        self.headers = [str(x) for x in self.headers]
        self.style += [None] * (len(self.headers) - len(self.style))

        # delete empty rows at the end
        while self.rows and not any(x for x in self.rows[-1] if x.strip()):
            self.rows.pop()

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError(f"Key '{key}' not found in table")
        return value

    def get(
        self, key, default=None
    ):  # treat as dictionary, with rows past 1 being optional data (see search)
        for row in self.rows:
            if len(row) > 1 and row[0] == key:
                return row[1]
        return default

    def header_pos(self, possible_headers: list[str], default: int) -> int:
        lowercase = [x.lower() for x in self.headers]
        for candidate in possible_headers:
            if candidate.lower() in lowercase:
                return lowercase.index(candidate.lower())
        return default


class MDObj:
    def __init__(
        self,
        plaintext: str,
        children: Dict[str, "MDObj"] = None,
        flash: Callable[[str], None] = None,
        tables: List[MDTable] = None,
        level: int = 0,
        header: str = "",
        original=None,
    ):
        self.originalMD = original or plaintext
        self.plaintext = plaintext
        self.children: Dict[str, "MDObj"] = children or {}
        self.tables: List[MDTable] = tables or self.extract_tables()
        self.level = level
        self.header = header
        self.errors = []
        self.flash = flash or self.add_to_error

    def add_to_error(self, error):
        self.errors.append(error)

    def __repr__(self):
        return (
            f"{self.header or 'MDObj'}({self.plaintext}, {self.tables} {self.children})"
        )

    def __getitem__(self, key):
        # Search through children
        if key in self.children:
            return self.children[key]
        for t in self.tables:
            value = t.get(key)
            if value:
                return value
        raise KeyError(f"{key} not found in {self.header or 'MDObj'}")

    @classmethod
    def from_md(
        cls,
        lines: str | list[str],
        level=0,
        header="",
        flash=None,
    ) -> "MDObj":
        """
        breaks down the structure of a md text into nested tuples of a string
        of the text directly after the heading and a dictionary of all the subheadings

        @param lines: \n separated string, or a stack of lines
        (top line on top of the stack)
        @param level: the level of heading this split started and therefore should end on
        @param flash: function to call with errors

        @return: a Tuple of the direct text and a dict containing recursive output

        """
        if isinstance(lines, str):
            original = lines[:]
            lines = list(reversed(lines.split("\n")))  # build stack of lines
        else:
            original = "\n".join(
                reversed(lines)
            )  # saving the original was an idea introduced later
        text = ""
        children = {}
        while len(lines):
            line = lines.pop()
            if line.strip().startswith("#"):
                current_level = len(line.strip()) - len(line.strip().lstrip("#"))
                # easy way to only count # on the left
                if current_level and level >= current_level:
                    # we moved out of our subtree
                    lines.append(line)  # push the current line back
                    # and remove them from the OriginalMD which represents the parsed MD of the subtree
                    return cls(
                        text,
                        children,
                        flash,
                        level=level,
                        header=header,
                        original=original,
                    )
                else:
                    k = line.lstrip("# ").strip()
                    while k in children:
                        k += "_"  # duplicate keys would have been inaccessible anyway
                    children[k] = cls.from_md(
                        lines=lines,  # by reference
                        level=current_level,
                        header=k,
                        flash=flash,
                    )
                    continue
            text += line + "\n"
        return cls(text, children, flash, header=header, level=level, original=original)

    def search_all(self, searchterm: str) -> [(str, str)]:
        """
        searches all children and tables for a searchterm
        :param searchterm: the term to search for
        :return: a list of tuples of the form (heading, text)
        """
        results = []
        for k, v in self.children.items():
            if k.strip().startswith(searchterm):
                results.append((k, v.originalMD))
            results += [(k, r) for r in v.search_all(searchterm)]
        for subtable in self.tables:
            for row in subtable.headers + subtable.rows:
                if row[0].strip().startswith(searchterm):
                    results.append((row[0], "|".join(row[1:])))
        return results

    def extract_tables(self) -> List[MDTable]:
        """
        traverses the output of split_md and consumes table text where possible.
        Tables are appended to a List, at the end of each tuple
        :return: a List of Tables
        """
        text = ""
        linenr = 0
        tables = []
        run = ""
        for line in self.plaintext.splitlines(True):
            linenr += 1
            if "|" in line:
                run += line
                continue
            elif run:
                tables.append(MDTable.from_md(run))
                tables[-1].prev_line_nr = linenr
                run = ""
            text += line
        if run:
            tables.append(MDTable.from_md(run))
            tables[-1].prev_line_nr = linenr
        self.plaintext = text
        return tables

    def confine_to_tables(self) -> Tuple[Dict[str, str | dict], List[str]]:
        """
        simplifies a mdtree into just a dictionary of dictionaries.
        Makes the assumption that either children or a table can be had, and that all leaves are key value in the end
        :return: A Tuple of adictionary that recursively always ends in values, and a list of errors
        """
        result = {}
        errors = []

        def error(msg: str):
            errors.append(msg)
            log.info(msg)

        for subtable in self.tables:
            for row in subtable.rows:
                if not row:
                    continue
                if len(row) != 2:
                    error(f"Malformed KeyValue at row '{'|'.join(row)}' in {subtable} ")
                    continue
                result[row[0]] = row[1]

        for child, content in self.children.items():
            if content.children or content.tables:
                result[child], newerrors = content.confine_to_tables()
                errors += newerrors
            else:
                result[child] = content.plaintext.strip()
                if (
                    not content.children
                    and not content.plaintext.strip()
                    and not content.tables
                ):
                    error(f"Extraneous Subheading: '{', '.join(self.children.keys())}'")

        if self.plaintext.strip():
            error(f"Extraneous Text: '{self.plaintext.strip()}'")
        return result, errors

    @staticmethod
    def from_dict(cls, inp: Dict[str, str | dict]) -> "MDObj":
        """
        inverse of confine_to_tables
        """
        children = {}
        plaintext = ""
        for k, v in inp.items():
            if isinstance(v, str):
                children[k] = cls(v, {}, "", lambda x: None)
            elif isinstance(v, MDTable):
                children[k] = v
            elif isinstance(v, dict):
                children[k] = cls.from_dict(v)
        return cls(plaintext, children, "", lambda x: None)

    @classmethod
    def just_tables(cls, tables: [MDTable]) -> "MDObj":
        tablesonly = cls("", {}, lambda x: None)
        tablesonly.tables = tables
        return tablesonly

    def search_children(self, name: str) -> Optional["MDObj"]:
        # search direct children first
        for child_name in self.children:
            if name.lower().strip() == child_name.lower().strip():
                return self.children[child_name]
        for t in self.tables:
            if t.search(name):
                return self
        # then do a depth first search for the first matching entry
        for _, child in self.children.items():
            if result := child.search_children(name):
                return result
        return None

    def set_levels(self, newlevel=None):
        """
        sets all children's levels if unset
        """
        if newlevel is not None:
            self.level = newlevel
        for child in self.children.values():
            if not child.level:
                child.set_levels(self.level + 1)

    def add_child(self, child: "MDObj") -> Self:
        """
        adds a child to the object
        :param child: child MDObj to add
        """
        if self.is_ancestor(child):
            raise Exception(
                "cannot add child, it is already a descendant of this object"
            )
        name = child.header.strip()
        self.children[name] = child
        return self

    def is_ancestor(self, child):
        for candidate in self.children.values():
            if candidate == child or candidate.is_ancestor(child):
                return True
        return False

    def add_children(self, children: List["MDObj"]) -> Self:
        for child in children:
            self.add_child(child)
        return self

    def to_md(self) -> str:
        """
        reconstructs the original markdown from the object
        """
        result = ""
        if not self.level:
            self.set_levels(0)
        if self.header.strip():
            result += f"\n{'#' * self.level} {self.header}\n"
        if self.plaintext.strip():
            result += self.plaintext.rstrip() + "\n"
        if self.tables:
            result += "\n"
        for t in self.tables:
            if t.prev_line_nr:
                lines = result.splitlines(True)
                result = (
                    "".join(
                        lines[: t.prev_line_nr]
                        + t.to_md().splitlines(True)
                        + lines[t.prev_line_nr :]
                    )
                    + "\n"
                )
            else:
                result += t.to_md() + "\n"
        for v in self.children.values():
            result += v.to_md()

        return result

    def search_tables(self, searchterm: str) -> MDTable | None:
        """
        searches all tables in the MD and its children, returning the first matching table
        """
        for t in self.tables:
            if t.search(searchterm):
                return t
        for n, c in self.children.items():
            if searchterm.strip().lower() == n.strip().lower() and len(c.tables) == 1:
                return c.tables[0]
            r = c.search_tables(searchterm)
            if r:
                return r
        return None

    def replace_content_by_path(self, path: [str], new: str):
        focus = self
        for p in path[:-1]:
            focus = focus.children[p]
        focus.children[path[-1]] = MDObj.from_md(new)

    def get_content_by_path(self, path: [str]):
        focus = self
        for p in path:
            focus = focus.children[p]
        return focus

    def with_header(self, header_text: str) -> Self:
        """
        adds a header to the object
        :param header_text: text of header
        :return: self
        """
        self.header = header_text
        return self


def table_row_edit(md: str, key: str, value: str) -> str:
    """
    changes everything but the leftmost column in a table the first time key is encountered
    :param md: markdown to operate on
    :param key: first column value
    :param value: all subsequent values to change to, | delimited
    """
    old = search_tables(md, key, 0).strip()
    start = "|" if old.startswith("|") else ""
    end = "|" if old.endswith("|") else ""
    new = f"{start} {key} | {value} {end}"
    return md.replace(old, new, 1)


def table_md(t: List[List[str]]) -> str:
    """
    converts a table to markdown
    :param t: table
    :return: markdown
    """
    return "\n".join(["|".join([x for x in row if x is not None]) for row in t if row])


def table_add(md: str, key: str, new: str) -> str:
    intable = False
    sofar = ""
    for line in md.splitlines(True):
        if intable and "|" not in line and new:
            sofar += (
                " "
                * (len(sofar.splitlines()[-2]) - len(sofar.splitlines()[-2].lstrip()))
                + f"| {key} | {new} |\n"
            )
            new = None
        if "|" in line:
            intable = True
        sofar += line
    if new:
        if sofar and not sofar.endswith("\n"):
            sofar += "\n"
        sofar += " " * (
            len(sofar.splitlines()[-2]) - len(sofar.splitlines()[-2].lstrip())
        )
        sofar += f"| {key} | {new} |\n"
    return sofar


def table_remove(md: str, key: str) -> str:
    old = search_tables(md, key, 0).strip()
    return md.replace(old + "\n", "", 1)


def search_tables(md: str, seek: str, surround=None) -> str:
    found = False
    curtable = []
    end = -1
    for line in md.splitlines(True):
        if "|" in line:
            curtable.append(line)
            if not found and line.strip(" |").lower().startswith(
                seek.strip(" |").lower()
            ):
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
    returns all lines under a heading
    :param md: markdown to operate on, expects no trailing newline
    :param seek: heading to search for
    """
    result = ""
    level = 0
    for line in md.split("\n"):
        if line.strip().startswith("#") or level:
            current_level = len(line.strip()) - len(line.strip().lstrip("#"))
            if current_level and level >= current_level:
                level = 0
                continue
            if (
                level
                or line.strip().lstrip("#").strip(": ").upper()
                == seek.strip(": ").upper()
            ):
                if not level:
                    level = current_level
                result += line + "\n"
    return result
