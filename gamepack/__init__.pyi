import sqlite3
from pathlib import Path

cache: list[sqlite3.Connection]

def handle(res: str) -> Path: ...
def dicecache_db() -> sqlite3.Connection: ...
