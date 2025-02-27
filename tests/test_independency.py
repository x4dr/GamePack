import importlib.util
import re
from pathlib import Path
from typing import List
from unittest import TestCase

from data import dicecache_db


class TestIndependency(TestCase):
    modules: List[Path] = []

    @classmethod
    def setUpClass(cls) -> None:
        fileblacklist = ["setup.py"]
        patternblacklist = [r".*/\.?venv/.*"]
        cls.modules = []
        candidates = list(Path(__file__).parent.glob("../Parser/**/*.py"))
        candidates += list(Path(__file__).parent.glob("../gamepack/**/*.py"))
        candidates += list(Path(__file__).parent.glob("../tests/**/*.py"))
        candidates = [x.absolute() for x in candidates if x.name not in fileblacklist]
        for pattern in patternblacklist:
            for m in candidates:
                if not re.match(pattern, m.as_posix()):
                    cls.modules.append(m.absolute())

    def test_loadability(self):
        """establish that each module is loadable and has no circular reference issues"""
        for module in TestIndependency.modules:
            with self.subTest(msg=f"Loading {module.as_posix()[3:-3]} "):
                spec = importlib.util.spec_from_file_location(
                    module.parent.stem + "." + module.stem, module
                )
                foo = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(foo)

    def test_dummy(self):
        self.assertTrue(True)

    def test_data(self):
        from data import handle

        with dicecache_db() as sut:
            self.assertEqual(sut.total_changes, 0)
        with dicecache_db() as sut:
            self.assertEqual(sut.total_changes, 0)
        sut.close()
        Path(handle("dicecache.sqlite")).unlink()
