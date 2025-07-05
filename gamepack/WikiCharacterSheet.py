from pathlib import Path
from typing import Self

from gamepack.FenCharacter import FenCharacter
from gamepack.Mecha import Mecha
from gamepack.PBTACharacter import PBTACharacter
from gamepack.WikiPage import WikiPage


class WikiCharacterSheet(WikiPage):
    def __init__(
        self,
        title: str,
        tags: list[str],
        body: str,
        links: list[str],
        meta: dict,
        modified: float | None,
        file: Path,
    ):
        super().__init__(title, tags, body, links, meta, modified, file)
        raw = self.md(True)
        if "mech" in self.tags:
            self.char = Mecha.from_mdobj(raw)
        elif "pbta" in self.tags:
            self.char = PBTACharacter.from_mdobj(raw)
        else:
            self.char = FenCharacter.from_mdobj(raw)
        self.sheet = {}

    @classmethod
    def from_wikipage(cls, page: WikiPage) -> Self:
        return cls(
            page.title,
            page.tags,
            page.body,
            page.links,
            page.meta,
            page.last_modified,
            page.file,
        )

    @classmethod
    def load(cls, page: Path, cache=True) -> Self:
        p = WikiPage.load(page, cache)
        if isinstance(p, WikiCharacterSheet):
            return p
        elif p:
            WikiPage.page_cache[page] = cls.from_wikipage(
                p
            )  # update cached object with sheet info
            return WikiPage.page_cache[page]
        return None

    @classmethod
    def load_locate(cls, page: str, cache=True) -> Self:
        p = WikiPage.load_locate(page, cache)
        if isinstance(p, WikiCharacterSheet):
            return p
        elif p:
            page = WikiPage.locate(page)
            WikiPage.page_cache[page] = cls.from_wikipage(p)
            return WikiPage.page_cache[page]
        return None

    def save(self, page: Path, author: str, message: str = None):
        self.body = self.char.to_md()
        super().save(page, author, message)
