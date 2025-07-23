import importlib.util
import re
import warnings
from pathlib import Path
from typing import List
from unittest import TestCase

from gamepack import dicecache_db, handle

ROOT = Path(__file__).parent.parent.resolve()


class TestIndependency(TestCase):
    modules: List[Path] = []

    @classmethod
    def setUpClass(cls) -> None:
        patternblacklist = [r".*/\.?venv/.*"]
        cls.modules = []
        candidates = list(Path(__file__).parent.glob("../Parser/**/*.py"))
        candidates += list(Path(__file__).parent.glob("../gamepack/**/*.py"))
        candidates += list(Path(__file__).parent.glob("../tests/**/*.py"))
        candidates = [x.absolute() for x in candidates]
        for pattern in patternblacklist:
            for m in candidates:
                if not re.match(pattern, m.as_posix()):
                    cls.modules.append(m.absolute())

    def test_loadability(self):
        """establish that each module is loadable and has no circular reference issues"""
        warnings.filterwarnings("ignore", category=ImportWarning)
        for module_full_path in TestIndependency.modules:
            with self.subTest(msg=f"Loading {module_full_path.as_posix()[3:-3]} "):
                spec = importlib.util.spec_from_file_location(
                    module_full_path.parent.stem + "." + module_full_path.stem,
                    module_full_path,
                )
                actual_module = importlib.util.module_from_spec(spec)

                path = module_full_path.resolve().parent.relative_to(ROOT).parts
                depth = len(path)
                if depth > 1:
                    # submodule: set __package__ to full dotted parent path relative to ROOT
                    actual_module.__package__ = ".".join(path)
                else:
                    # top-level module
                    actual_module.__package__ = ""

                spec.loader.exec_module(actual_module)

    def test_dummy(self):
        self.assertTrue(True)

    def test_data(self):
        with dicecache_db() as sut:
            self.assertEqual(sut.total_changes, 0)
        with dicecache_db() as sut:
            self.assertEqual(sut.total_changes, 0)
        sut.close()
        Path(handle("dicecache.sqlite")).unlink()
