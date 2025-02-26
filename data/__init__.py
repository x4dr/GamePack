import importlib.resources
import pathlib
import sqlite3


cache = []


def handle(res):
    try:
        with importlib.resources.files("gamepack.data").joinpath(res) as path:
            return path.as_posix()
    except FileNotFoundError as e:
        path = pathlib.Path(e.filename)
        path.touch()
        return path.as_posix()


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
