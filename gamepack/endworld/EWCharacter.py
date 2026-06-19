"""Endworld character module for mecha-piloting characters.

This module defines the EWCharacter class which extends FenCharacter
with mecha integration capabilities for the Endworld game system.
"""

import re
from typing import TYPE_CHECKING, ClassVar, Self

from gamepack.endworld.Mecha import Mecha
from gamepack.FenCharacter import FenCharacter
from gamepack.MDPack import MDObj
from gamepack.WikiPage import WikiPage

if TYPE_CHECKING:
    from collections.abc import Callable


class EWCharacter(FenCharacter):
    """A character in the Endworld game system that can pilot mecha.

    Extends FenCharacter with support for mecha integration, including
    parsing mecha references from markdown character sheets.
    """

    mech_headings: ClassVar[list[str]] = ["mech", "mecha"]

    def __init__(self) -> None:
        """Initialize an EWCharacter with no mecha assigned."""
        super().__init__()
        self.mecha: Mecha | None = None

    @classmethod
    def from_mdobj(
        cls,
        mdobj: MDObj,
        flash_func: Callable[[str], None] | None = None,
    ) -> Self:
        """Construct an EWCharacter from an MDObj, parsing mecha references.

        Scans the markdown object for mecha-related headings (e.g. "Mech",
        "Mecha") and attempts to locate and load the referenced mecha from
        the wiki.

        Args:
            mdobj: The markdown object to construct the character from.
            flash_func: Optional function to call for error messages.

        Returns:
            A new EWCharacter instance with parsed mecha data.

        """
        self = super().from_mdobj(mdobj, flash_func)
        if not flash_func:

            def default_flash(err: str) -> None:
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
