"""Base character module providing the base class for all character types.

This module defines the BaseCharacter class which ensures a consistent
interface for serialization and error handling across all character
implementations in GamePack.
"""

from typing import TYPE_CHECKING, Self

from gamepack.MDPack import MDObj

if TYPE_CHECKING:
    from collections.abc import Callable


class BaseCharacter:
    """Base class for all character types in GamePack.

    Ensures a consistent interface for serialization and error handling.
    """

    def __init__(self) -> None:
        """Initialize the BaseCharacter with an empty error list."""
        self.errors: list[str] = []

    @classmethod
    def from_mdobj(
        cls,
        mdobj: MDObj,
        flash_func: Callable[[str], None] | None = None,
    ) -> Self:
        """Construct a character instance from an MDObj.

        Args:
            mdobj: The markdown object to construct the character from.
            flash_func: Optional function to call for error messages.

        Returns:
            A new instance of the character class.

        Raises:
            NotImplementedError: Subclasses must implement this method.

        """
        raise NotImplementedError("Subclasses must implement from_mdobj")

    def to_mdobj(self) -> MDObj:
        """Convert the character instance to an MDObj.

        Returns:
            An MDObj representation of the character.

        Raises:
            NotImplementedError: Subclasses must implement this method.

        """
        raise NotImplementedError("Subclasses must implement to_mdobj")

    def to_md(self) -> str:
        """Convert the character instance to a Markdown string.

        Returns:
            A Markdown string representation of the character.

        """
        return self.to_mdobj().to_md()
