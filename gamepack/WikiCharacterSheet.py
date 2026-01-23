from pathlib import Path
from typing import Self, Optional, Union, Dict, Callable, Any, cast, Generic, TypeVar

from gamepack.BaseCharacter import BaseCharacter
from gamepack.FenCharacter import FenCharacter
from gamepack.PBTACharacter import PBTACharacter
from gamepack.WikiPage import WikiPage
from gamepack.endworld.Mecha import Mecha
from gamepack.endworld.EWCharacter import EWCharacter

T = TypeVar("T", bound=BaseCharacter)


class WikiCharacterSheet(WikiPage, Generic[T]):
    def __init__(
        self,
        title: str,
        tags: list[str],
        body: str,
        links: list[str],
        meta: Union[Dict, str],
        modified: Optional[float],
        file: Optional[Path],
    ):
        super().__init__(title, tags, body, links, meta, modified, file)
        raw = self.md(True)
        self.char: Optional[T] = None

        lower_tags = [x.lower() for x in self.tags]
        if {"mecha", "mech"} & set(lower_tags):
            self.char = cast(T, Mecha.from_mdobj(raw))
        elif "endworld" in lower_tags:
            self.char = cast(T, EWCharacter.from_mdobj(raw))
        elif "pbta" in lower_tags:
            self.char = cast(T, PBTACharacter.from_mdobj(raw))
        elif "character" in lower_tags or (
            self.file
            and "character" in self.file.relative_to(self.wikipath()).as_posix()
        ):
            self.char = cast(T, FenCharacter.from_mdobj(raw))

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
    def load(cls, page: Optional[Path], cache=True) -> Optional[Self]:
        if page is None:
            return None
        p = WikiPage.load(page, cache)
        if isinstance(p, WikiCharacterSheet):
            return cast(Self, p)
        elif p:
            sheet = cls.from_wikipage(p)
            WikiPage.page_cache[page] = sheet
            return cast(Self, sheet)
        return None

    @classmethod
    def load_locate(cls, page: str, cache=True) -> Optional[Self]:
        path = WikiPage.locate(page)
        if path is None:
            return None
        p = WikiPage.load(path, cache)
        if isinstance(p, WikiCharacterSheet):
            return cast(Self, p)
        elif p:
            sheet = cls.from_wikipage(p)
            WikiPage.page_cache[path] = sheet
            return cast(Self, sheet)
        return None

    def save(
        self, author: str, page: Optional[Path] = None, message: Optional[str] = None
    ):
        """
        warning: blocks and requires some time
        """
        if self.char and hasattr(self.char, "to_md"):
            self.body = self.char.to_md()
        super().save(author, page, message)

    def save_low_prio(self, message: str):
        self.increment += 1
        if self.char and hasattr(self.char, "to_md"):
            self.body = self.char.to_md()
        super().save_low_prio(message + " saving charactersheet")
