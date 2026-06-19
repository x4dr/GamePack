from pathlib import Path
from typing import Any, Self, TypeVar

from _typeshed import Incomplete

from gamepack.BaseCharacter import BaseCharacter
from gamepack.WikiPage import WikiPage

T = TypeVar("T", bound=BaseCharacter)

class WikiCharacterSheet[T: BaseCharacter](WikiPage):
    char: T | None
    increment: int
    def __init__(
        self,
        title: str,
        tags: list[str],
        body: str,
        links: list[str],
        meta: dict[str, Any] | str,
        modified: float | None,
        file: Path | None,
    ) -> None: ...
    @classmethod
    def from_wikipage(cls, page: WikiPage) -> Self: ...
    @classmethod
    def load(cls, page: Path | None, *, cache: bool = True) -> Self | None: ...
    @classmethod
    def load_locate(cls, page: str, *, cache: bool = True) -> Self | None: ...
    body: Incomplete
    def save(self, author: str, page: Path | None = None, message: str | None = None) -> None: ...
    def save_low_prio(self, message: str) -> None: ...
