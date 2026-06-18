from typing import TYPE_CHECKING, Self

from gamepack.MDPack import MDObj

if TYPE_CHECKING:
    from collections.abc import Callable


class BaseCharacter:
    """Base class for all character types in GamePack.
    Ensures a consistent interface for serialization and error handling.
    """

    def __init__(self):
        self.errors: list[str] = []

    @classmethod
    def from_mdobj(
        cls,
        mdobj: MDObj,
        flash_func: Callable[[str], None] | None = None,
    ) -> Self:
        """Construct a character instance from an MDObj."""
        raise NotImplementedError("Subclasses must implement from_mdobj")

    def to_mdobj(self) -> MDObj:
        """Convert the character instance to an MDObj."""
        raise NotImplementedError("Subclasses must implement to_mdobj")

    def to_md(self) -> str:
        """Convert the character instance to a Markdown string."""
        return self.to_mdobj().to_md()
