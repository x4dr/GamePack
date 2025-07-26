from pathlib import Path
from typing import Self

from gamepack.FenCharacter import FenCharacter
from gamepack.PBTACharacter import PBTACharacter
from gamepack.WikiPage import WikiPage
from gamepack.endworld import Mecha
from gamepack.endworld.EWCharacter import EWCharacter


class WikiCharacterSheet(WikiPage):
    renderers = {}

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
        if {"mecha", "mech"} & set(x.lower() for x in self.tags):
            self.char = Mecha.from_mdobj(raw)
        elif "endworld" in self.tags:
            self.char = EWCharacter.from_mdobj(raw)
        elif "pbta" in self.tags:
            self.char = PBTACharacter.from_mdobj(raw)
        elif (
            "character" in self.tags
            or "character" in self.file.relative_to(self.wikipath()).as_posix()
        ):
            self.char = FenCharacter.from_mdobj(raw)
        else:
            self.char = None
        self.increment = 0

    @classmethod
    def renderer(cls, t: type):
        def wrapper(func):
            cls.renderers[t] = func
            return func

        return wrapper

    def render(self):
        if not type(self.char) in self.renderers:
            raise NotImplementedError(
                f"no sheet renderer registered for {type(self.char)}"
            )
        return self.renderers[type(self.char)](self)

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
        page = WikiPage.locate(page)
        p = WikiPage.load(page)
        if isinstance(p, WikiCharacterSheet):
            return p
        elif p:
            WikiPage.page_cache[page] = cls.from_wikipage(p)
            return WikiPage.page_cache[page]
        return None

    def save(self, author: str, page: Path = None, message: str = None):
        """
        warning: blocks and requires some time
        """
        self.body = self.char.to_md()
        super().save(author, page, message)

    def save_low_prio(self, message):
        self.increment += 1
        if self.char:
            self.body = self.char.to_md()
        super().save_low_prio(message + " saving charactersheet")
