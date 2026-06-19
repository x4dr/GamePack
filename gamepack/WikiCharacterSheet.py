"""Character sheet wiki page integration.

Provides WikiCharacterSheet, which extends WikiPage with automatic
character parsing from wiki page content based on tags.
"""

from typing import TYPE_CHECKING, Any, Self, TypeVar, cast

from gamepack.BaseCharacter import BaseCharacter
from gamepack.endworld.EWCharacter import EWCharacter
from gamepack.endworld.Mecha import Mecha
from gamepack.FenCharacter import FenCharacter
from gamepack.PBTACharacter import PBTACharacter
from gamepack.WikiPage import WikiPage

if TYPE_CHECKING:
    from pathlib import Path

T = TypeVar("T", bound=BaseCharacter)


class WikiCharacterSheet[T: BaseCharacter](WikiPage):
    """A wiki page that parses its content into a character sheet.

    Automatically detects the character type from page tags and
    deserializes the character from the page's markdown body.
    """

    def __init__(
        self,
        title: str,
        tags: list[str],
        body: str,
        links: list[str],
        meta: dict[str, Any] | str,
        modified: float | None,
        file: Path | None,
    ):
        """Initialize a WikiCharacterSheet.

        Parses the page markdown into a character object based on tags.

        Args:
            title: The page title.
            tags: List of tags used to determine character type.
            body: The markdown body of the page.
            links: List of outgoing links from the page.
            meta: Metadata dictionary or YAML front-matter string.
            modified: Last modified timestamp, if available.
            file: Path to the page file, if available.

        """
        super().__init__(title, tags, body, links, meta, modified, file)
        raw = self.md(sanitize=True)
        self.char: T | None = None

        lower_tags = [x.lower() for x in self.tags]
        if {"mecha", "mech"} & set(lower_tags):
            self.char = cast("T", Mecha.from_mdobj(raw))
        elif "endworld" in lower_tags:
            self.char = cast("T", EWCharacter.from_mdobj(raw))
        elif "pbta" in lower_tags:
            self.char = cast("T", PBTACharacter.from_mdobj(raw))
        elif "character" in lower_tags or (
            self.file and "character" in self.file.relative_to(self.wikipath()).as_posix()
        ):
            self.char = cast("T", FenCharacter.from_mdobj(raw))

        self.increment = 0

    @classmethod
    def from_wikipage(cls, page: WikiPage) -> Self:
        """Create a WikiCharacterSheet from an existing WikiPage.

        Args:
            page: The WikiPage instance to convert.

        Returns:
            A new WikiCharacterSheet instance.

        """
        return cls(
            page.title,
            list(page.tags),
            page.body,
            page.links,
            page.meta,
            page.last_modified,
            page.file,
        )

    @classmethod
    def load(cls, page: Path | None, *, cache: bool = True) -> Self | None:
        """Load a character sheet from a wiki page path.

        If the cached WikiPage is already a WikiCharacterSheet, it is
        returned directly. Otherwise, a new WikiCharacterSheet is
        created from the loaded WikiPage.

        Args:
            page: The page path relative to the wiki root.
            cache: Whether to use the page cache.

        Returns:
            A WikiCharacterSheet instance, or None if the page
            is not found.

        """
        if page is None:
            return None

        abs_path = (cls.wikipath() / page).resolve()
        if abs_path.suffix != ".md":
            abs_path = abs_path.with_suffix(".md")

        p = WikiPage.load(page, cache=cache)
        if isinstance(p, WikiCharacterSheet):
            return cast("Self", p)
        if p:
            if not isinstance(p, WikiPage):
                msg = f"Expected WikiPage instance, got {type(p)}"
                raise TypeError(msg)

            sheet = cls.from_wikipage(p)
            WikiPage.page_cache[abs_path] = sheet
            return sheet
        return None

    @classmethod
    def load_locate(cls, page: str, *, cache: bool = True) -> Self | None:
        """Locate and load a character sheet by page name.

        Args:
            page: The page name to locate.
            cache: Whether to use the page cache.

        Returns:
            A WikiCharacterSheet instance, or None if not found.

        """
        path = WikiPage.locate(page)
        if path is None:
            return None

        abs_path = (cls.wikipath() / path).resolve()
        if abs_path.suffix != ".md":
            abs_path = abs_path.with_suffix(".md")

        p = WikiPage.load(path, cache=cache)
        if isinstance(p, WikiCharacterSheet):
            return cast("Self", p)
        if p:
            if not isinstance(p, WikiPage):
                msg = f"Expected WikiPage instance, got {type(p)}"
                raise TypeError(msg)

            sheet = cls.from_wikipage(p)
            WikiPage.page_cache[abs_path] = sheet
            return sheet
        return None

    def save(self, author: str, page: Path | None = None, message: str | None = None) -> None:
        """warning: blocks and requires some time."""
        if self.char and hasattr(self.char, "to_md"):
            self.body = self.char.to_md()
        super().save(author, page, message)

    def save_low_prio(self, message: str) -> None:
        """Queue a low-priority save with character data.

        Converts the character to markdown before queuing the save.

        Args:
            message: The save message to queue.

        """
        self.increment += 1
        if self.char and hasattr(self.char, "to_md"):
            self.body = self.char.to_md()
        super().save_low_prio(message + " saving charactersheet")
