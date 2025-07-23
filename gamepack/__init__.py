import sqlite3
from pathlib import Path

cache = []


def handle(res) -> Path:
    p = Path(__file__).parent.parent / "data" / res
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.is_file():
        p.touch()
    return p


def dicecache_db() -> sqlite3.Connection:
    """db connection singleton"""
    if cache:
        return cache[0]
    dbpath = handle("dicecache.sqlite")
    cache.append(sqlite3.connect(dbpath))
    cache[0].cursor().executescript(
        "create table if not exists occurences (sel TEXT, mod INT, res INT, occ INT, unique (sel, mod, res));"
        "create index if not exists sel on occurences (sel, mod);"
        "create table if not exists versus (sel1 TEXT, sel2 TEXT, mod1 INT, mod2 INT, res INT, occ BLOB, "
        "unique (sel1, sel2, mod1, mod2, res));"
        "create index if not exists sel1 on versus (sel1, sel2, mod1, mod2);"
    )
    cache[0].commit()

    return cache[0]
