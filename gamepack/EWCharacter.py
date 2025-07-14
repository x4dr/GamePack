import re

from gamepack.FenCharacter import FenCharacter
from gamepack.MDPack import MDObj
from gamepack.Mecha import Mecha
from gamepack.WikiPage import WikiPage


class EWCharacter(FenCharacter):
    mech_headings = ["mech", "mecha"]

    def __init__(self):
        super().__init__()
        self.mecha: Mecha | None = None

    @classmethod
    def from_mdobj(cls, mdobj: MDObj, flash=None):
        self = super().from_mdobj(mdobj, flash)
        if not flash:

            def flash(err):
                self.errors.append(err)

        for heading, section in mdobj.children.items():
            if heading.lower() in cls.mech_headings:
                links = re.compile(r"\((.*?)\)")
                for link in links.match(section.plaintext):
                    p = WikiPage.locate(link[0])
                    if p:
                        self.mecha = Mecha.from_mdobj(WikiPage.load(p).md())
                        break
                else:
                    if any(x.lower() == "systems" for x in section.children.keys()):
                        self.mecha = Mecha.from_mdobj(section)
        return self
