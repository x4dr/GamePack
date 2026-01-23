import re
from typing import Optional, Callable, Self

from gamepack.FenCharacter import FenCharacter
from gamepack.MDPack import MDObj
from gamepack.WikiPage import WikiPage
from gamepack.endworld.Mecha import Mecha


class EWCharacter(FenCharacter):
    mech_headings = ["mech", "mecha"]

    def __init__(self):
        super().__init__()
        self.mecha: Mecha | None = None

    @classmethod
    def from_mdobj(
        cls, mdobj: MDObj, flash_func: Optional[Callable[[str], None]] = None
    ) -> Self:
        self = super().from_mdobj(mdobj, flash_func)
        if not flash_func:

            def default_flash(err):
                self.errors.append(err)

            flash_func = default_flash

        for heading, section in mdobj.children.items():
            if heading.lower() in cls.mech_headings:
                link_pattern = re.compile(r"\((.*?)\)")
                match = link_pattern.search(section.plaintext)
                if match:
                    link = match.group(1)
                    p = WikiPage.locate(link)
                    if p:
                        page = WikiPage.load(p)
                        if page:
                            self.mecha = Mecha.from_mdobj(page.md())
                else:
                    if any(x.lower() == "systems" for x in section.children.keys()):
                        self.mecha = Mecha.from_mdobj(section)
        return self
