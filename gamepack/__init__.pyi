import sqlite3
from pathlib import Path

from _typeshed import Incomplete

cache: Incomplete

def handle(res) -> Path: ...
def dicecache_db() -> sqlite3.Connection: ...
