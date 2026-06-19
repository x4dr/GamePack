"""GamePack — game mechanics library for tabletop RPG systems.

Provides dice rolling, character management, item handling, and
wiki/Markdown parsing functionality.
"""

import sqlite3
from pathlib import Path

cache: list[sqlite3.Connection] = []


def handle(res: str) -> Path:
    """Resolve a relative data path under the project's data/ directory.

    Ensures the parent directory exists and the file is created if
    it does not already exist.

    Args:
        res: Relative path to a file under the data/ directory.

    Returns:
        Resolved absolute Path to the file.

    """
    p = Path(__file__).parent.parent / "data" / res
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.is_file():
        p.touch()
    return p


def dicecache_db() -> sqlite3.Connection:
    """Db connection singleton."""
    if cache:
        return cache[0]
    dbpath = handle("dicecache.sqlite")
    cache.append(sqlite3.connect(dbpath))
    cache[0].cursor().executescript(
        "create table if not exists occurences (sel TEXT, mod INT, res INT, occ INT, unique (sel, mod, res));"
        "create index if not exists sel on occurences (sel, mod);"
        "create table if not exists versus (sel1 TEXT, sel2 TEXT, mod1 INT, mod2 INT, res INT, occ BLOB, "
        "unique (sel1, sel2, mod1, mod2, res));"
        "create index if not exists sel1 on versus (sel1, sel2, mod1, mod2);",
    )
    cache[0].commit()

    return cache[0]
