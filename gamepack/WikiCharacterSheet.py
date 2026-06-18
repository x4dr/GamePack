from typing import TYPE_CHECKING, Self, TypeVar, cast

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
    def __init__(
        self,
        title: str,
        tags: list[str],
        body: str,
        links: list[str],
        meta: dict | str,
        modified: float | None,
        file: Path | None,
    ):
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
            self.file
            and "character" in self.file.relative_to(self.wikipath()).as_posix()
        ):
            self.char = cast("T", FenCharacter.from_mdobj(raw))

        self.increment = 0

    @classmethod
    def from_wikipage(cls, page: WikiPage) -> Self:
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
            return cast("Self", sheet)
        return None

    @classmethod
    def load_locate(cls, page: str, *, cache: bool = True) -> Self | None:
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
            return cast("Self", sheet)
        return None

    def save(self, author: str, page: Path | None = None, message: str | None = None):
        """warning: blocks and requires some time."""
        if self.char and hasattr(self.char, "to_md"):
            self.body = self.char.to_md()
        super().save(author, page, message)

    def save_low_prio(self, message: str):
        self.increment += 1
        if self.char and hasattr(self.char, "to_md"):
            self.body = self.char.to_md()
        super().save_low_prio(message + " saving charactersheet")
