import importlib
import pytest
from gamepack import dicecache_db, handle
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
BLACKLIST = [".venv"]


def all_module_names():
    """Scan directories and return importable module names (dot notation)."""
    modules = []
    for subdir in ["Parser", "gamepack"]:
        for py_file in (ROOT / subdir).rglob("*.py"):
            if any(b in py_file.parts for b in BLACKLIST):
                continue
            if py_file.name == "__init__.py":
                # Use parent package as module name
                module_name = ".".join(py_file.parent.relative_to(ROOT).parts)
            else:
                module_name = ".".join(py_file.with_suffix("").relative_to(ROOT).parts)
            modules.append(module_name)
    return modules


@pytest.mark.parametrize("module_name", all_module_names())
def test_module_importable(module_name):
    """Each module should import successfully."""
    importlib.import_module(module_name)


def test_dicecache_db_cleanup():
    """Verify dicecache_db can be opened twice and file is cleaned up."""
    with dicecache_db() as sut:
        assert sut.total_changes == 0
    with dicecache_db() as sut:
        assert sut.total_changes == 0
    sut.close()
    Path(handle("dicecache.sqlite")).unlink()
