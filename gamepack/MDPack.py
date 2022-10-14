import logging
from typing import List, Dict, Tuple, Callable

from gamepack.Item import fendeconvert, value_category, fenconvert, Item

log = logging.Logger(__name__)


class MDObj:
    def __init__(
        self,
        plaintext: str,
        children: Dict[str, "MDObj"],
        original: str,
        flash: Callable[[str], None],
        extract_tables: bool,
    ):

        self.plaintext = plaintext
        self.children = children
        self.tables = self.extract_tables() if extract_tables else []
        self.originalMD = original
        self.flash = flash

    @classmethod
    def from_md(cls, lines, level=0, flash=None, extract_tables=True) -> "MDObj":
        """
        breaks down the structure of a md text into nested tuples of a string
        of the text directly after the heading and a dictionary of all the subheadings

        @param lines: \n separated string, or a stack of lines
        (top line on top of the stack)
        @param level: the level of heading this split started and therefore should end on
        @param flash: function to call with errors
        @param extract_tables: wether or not to go through the tables and pull them out of the plaintext
        @return: a Tuple of the direct text and a dict containing recursive output

        """
        if isinstance(lines, str):
            original = lines
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
                    return cls(text, children, original, flash, extract_tables)
                else:
                    children[line.lstrip("# ").strip()] = cls.from_md(
                        lines,  # by reference
                        current_level,
                        extract_tables,
                    )
                    continue
            text += line + "\n"
        return cls(text, children, original, flash, extract_tables)

    def extract_tables(
        self, flash: Callable[[str], None] = None
    ) -> List[List[List[str]]]:
        """
        traverses the output of split_md and consumes table text where possible.
        Tables are appended to a List, at the end of each tuple
        :param flash: if given, tables are processed through
        :return: a List of Tables
        """
        text = ""
        tables = []
        run = ""
        for line in self.plaintext.splitlines(True):
            if "|" in line:
                run += line
                continue
            elif run:
                tables.append(table(run))
                run = ""
            text += line
        if run:
            tables.append(table(run))
        if flash:
            for t in tables:
                if t:
                    total_table(t, flash)
        self.plaintext = text
        return tables

    def confine_to_tables(self, headers=True) -> Tuple[Dict[str, object], List[str]]:
        """
        simplifies a mdtree into just a dictionary of dictionaries.
        Makes the assumption that either children or a table can be had, and that all leaves are key value in the end
        :param headers: if false, headers of the tables will be cut off
        :return: Dictionary that recursively always ends in ints
        """
        result = {}
        processed = False
        errors = []

        def error(msg: str):
            errors.append(msg)
            log.info(msg)

        for subtable in self.tables:
            skiprow = 0 if not not headers else 1
            for row in subtable[skiprow:]:
                if not row:
                    continue
                if len(row) != 2:
                    error(f"Malformed KeyValue at row '{'|'.join(row)}' in {subtable} ")
                    continue
                result[row[0]] = row[1]
                processed = True

        for child, content in self.children.items():
            if content.children or content.tables:
                if processed:
                    error(f"Extraneous Subheading: '{', '.join(self.children.keys())}'")
                else:
                    result[child], newerrors = content.confine_to_tables(headers)
                    errors += newerrors
            else:
                result[child] = content.plaintext
                processed = True

        if self.plaintext.strip():
            error(f"Extraneous Text: '{self.plaintext}'")
        return result, errors

    @classmethod
    def just_tables(cls, tables):
        tablesonly = cls("", {}, "", lambda x: None, False)
        tablesonly.tables = tables
        return tablesonly


def table_edit(md: str, key: str, value: str) -> str:
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


def table_add(md: str, key: str, new: str) -> str:
    intable = False
    sofar = ""
    for line in md.splitlines(True):
        if intable and "|" not in line and new:
            sofar += f"|{key}|{new}|\n"
            new = None
        if "|" in line:
            intable = True
        sofar += line
    if new:
        sofar += f"|{key}|{new}|\n"
    return sofar


def table_remove(md: str, key: str) -> str:
    old = search_tables(md, key, 0).strip()
    return md.replace(old, "", 1)


def search_tables(md: str, seek: str, surround=None) -> str:
    found = False
    curtable = []
    end = -1
    for line in md.splitlines(True):
        if "|" in line:
            curtable.append(line)
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


def table(text: str) -> List[List[str]]:
    """
    gets table from md text.
    Assumes all text is part of table and will enforce the tablewidth given in
    format row. This means non-table text will be assumed to be just the first
    column and the rest will be filled with "". Every column past the ones
    alignment was defined for will be cut.
    :param text: md text from the first to the last line of the table
    :return: list of table rows, all having uniform length
    """
    rows = [row.strip() for row in text.split("\n") if row.strip()]
    if len(rows) > 1:
        formatline = [x for x in rows[1].split("|") if "-" in x]
        length = len(formatline)
        return [split_row(rows[0], length)] + [split_row(x, length) for x in rows[2:]]
    return []


def split_row(row: str, length: int) -> List[str]:
    """
    splits the row into the given length at |, cutting and adding as needed
    :param row: md table row string
    :param length: exakt number of columns
    :return: List of the first length table cells
    """
    split = [x.strip() for x in row.split("|")]
    if len(split) > length and row.startswith("|"):
        split = split[1:]
    # fill jagged edges with empty strings and cut tolength
    return (split + [""] * (length - len(split)))[:length]


def total_table(table_input, flash):
    try:
        if table_input[-1][0].lower() in Item.table_total:
            trackers = [[0, ""] for _ in range(len(table_input[0]) - 1)]
            table_input[-1] = table_input[-1] + (
                len(table_input[0]) - len(table_input[-1])
            ) * [""]
            for row in table_input[1:-1]:
                for i in range(len(trackers)):
                    r = row[i + 1].strip().lower().replace(",", "")
                    if r:
                        # noinspection PyBroadException
                        try:
                            if not trackers[i][1]:
                                trackers[i][1] = value_category(r)
                            trackers[i][0] += fenconvert(r)
                        except Exception:
                            pass  # even text columns will get attempted, so any failure means we just skip
            for i, t in enumerate(trackers):
                table_input[-1][i + 1] = fendeconvert(t[0], t[1])
    except Exception as e:
        flash(
            "tabletotal failed for '"
            + ("\n".join("\t".join(row) for row in table_input).strip() + "':\n ")
            + str(e.args)
        )
