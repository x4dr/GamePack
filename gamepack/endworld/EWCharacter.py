import re
from typing import TYPE_CHECKING, ClassVar, Self

from gamepack.endworld.Mecha import Mecha
from gamepack.FenCharacter import FenCharacter
from gamepack.MDPack import MDObj
from gamepack.WikiPage import WikiPage

if TYPE_CHECKING:
    from collections.abc import Callable


class EWCharacter(FenCharacter):
    mech_headings: ClassVar[list[str]] = ["mech", "mecha"]

    def __init__(self):
        super().__init__()
        self.mecha: Mecha | None = None

    @classmethod
    def from_mdobj(
        cls,
        mdobj: MDObj,
        flash_func: Callable[[str], None] | None = None,
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
                elif any(x.lower() == "systems" for x in section.children):
                    self.mecha = Mecha.from_mdobj(section)
        return self
