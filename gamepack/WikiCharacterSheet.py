from pathlib import Path
from typing import Self, Optional, Union, Dict, Callable, cast

from gamepack.FenCharacter import FenCharacter
from gamepack.PBTACharacter import PBTACharacter
from gamepack.WikiPage import WikiPage
from gamepack.endworld import Mecha
from gamepack.endworld.EWCharacter import EWCharacter


class WikiCharacterSheet(WikiPage):
    renderers: Dict[type, Callable] = {}

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
        if {"mecha", "mech"} & set(x.lower() for x in self.tags):
            self.char = Mecha.from_mdobj(raw)
        elif "endworld" in [x.lower() for x in self.tags]:
            self.char = EWCharacter.from_mdobj(raw)
        elif "pbta" in [x.lower() for x in self.tags]:
            self.char = PBTACharacter.from_mdobj(raw)
        elif "character" in [x.lower() for x in self.tags] or (
            self.file
            and "character" in self.file.relative_to(self.wikipath()).as_posix()
        ):
            self.char = FenCharacter.from_mdobj(raw)
        else:
            self.char = None
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
        if self.char:
            self.body = self.char.to_md()
        super().save(author, page, message)

    def save_low_prio(self, message):
        self.increment += 1
        if self.char:
            self.body = self.char.to_md()
        super().save_low_prio(message + " saving charactersheet")
