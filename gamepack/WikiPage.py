import logging
import subprocess
import time
from functools import lru_cache
from pathlib import Path
from typing import Self

import bleach

from gamepack.Dice import DescriptiveError
from gamepack.Item import Item
from gamepack.MDPack import MDObj

log = logging.getLogger(__name__)


class WikiPage:
    """
    Class to represent a wiki page.
    """

    page_cache: dict[Path, Self] = {}
    wikicache: dict[str, dict[str, list[str]]] = {}
    _wikipath: Path = None
    wikistamp = 0

    def __init__(
        self,
        title: str,
        tags: list[str],
        body: str,
        links: list[str],
        meta: list[str],
        modified: float = None,
    ):
        if Item.item_cache is None:
            WikiPage.cache_items()
        self.title = title
        self.tags = tags
        self.body = body
        self.links = links
        self.meta = meta
        self.last_modified = modified

    @lru_cache(maxsize=2)
    def md(self, sanitize: bool = False) -> MDObj:
        """
        :param sanitize: whether to sanitize the markdown
        :return: markdown of page
        """
        if sanitize:
            return MDObj.from_md(bleach.clean(self.body))
        return MDObj.from_md(self.body)

    @classmethod
    def wikipath(cls) -> Path:
        """
        :return: path to wiki directory
        """
        if cls._wikipath is None:
            raise DescriptiveError("wikipath not set")
        return cls._wikipath

    @classmethod
    def set_wikipath(cls, path: Path):
        if cls._wikipath is not None:
            raise DescriptiveError("wikipath already set")
        cls._wikipath = path

    @classmethod
    def locate(cls, pagename: [str | Path]) -> Path:
        """
        finds page in wiki
        :param pagename: name of page
        :return: path to page
        """
        if isinstance(pagename, Path):
            pagename = pagename.stem
        if pagename.endswith(".md"):
            pagename = pagename[:-3]
        matching_mds = (
            path
            for path in cls.wikipath().rglob(pagename + ".md")
            if not any(part.startswith(".") for part in path.parts)  # no hidden files
        )
        p = (
            next(matching_mds, None)
            if "/" not in pagename
            else cls.wikipath() / (pagename + ".md")
        )
        if not p:
            p = cls.wikipath() / (pagename + ".md")
        p = p.relative_to(cls.wikipath())
        return p

    @classmethod
    def load_str(cls, page: str, cache=True) -> Self:
        return cls.load(cls.locate(page), cache)

    @classmethod
    def load(cls, page: Path, cache=True) -> Self:
        """
        loads page from wiki
        :param page: name of page
        :param cache: whether to retrieve from cache
        :return: title, tags, body
        """
        res = cls.page_cache.get(page, None) if cache else None
        if res is not None:
            return res
        try:
            p = cls.wikipath() / page
            with p.open() as f:
                mode = "init"
                title = ""
                tags = []
                body = ""
                meta = []
                links = []
                for line in f.readlines():
                    if mode == "init" and line.strip().startswith("---"):
                        mode = "preamble"
                        continue
                    if mode and line.startswith("tags:"):
                        tags += [t for t in line[5:].strip().split(" ") if t]
                        continue
                    if mode and line.startswith("title:"):
                        title = line[6:].strip()
                        continue
                    if mode and line.startswith("outgoing links:"):
                        links = [
                            x.strip("' ")
                            for x in line[len("outgoing links:") :].strip().split("',")
                        ]
                        continue
                    if mode == "meta" and not line.strip():
                        mode = ""
                        continue
                    if mode == "preamble":
                        if line.strip().startswith("---"):
                            mode = ""
                            continue
                        meta.append(line.strip())
                        continue
                    body += line
                loaded_page = cls(
                    title=title,
                    tags=tags,
                    body=body,
                    links=links,
                    meta=meta,
                    modified=p.stat().st_mtime,
                )
                cls.page_cache[page] = loaded_page
                return loaded_page
        except FileNotFoundError:
            raise DescriptiveError(str(page) + " not found in wiki.")

    def save(self, page: Path, author: str):
        if page.suffix != ".md":
            raise DescriptiveError("page must be a .md file")
        print(f"saving '{self.title}' as {page} ...")
        with (self.wikipath() / page).open("w+") as f:
            f.write("---\n")
            f.write("title: " + self.title + "  \n")
            f.write("tags: " + " ".join(self.tags) + "  \n")
            f.write("outgoing links: '" + "', '".join(self.links) + "'  \n")
            for x in self.meta:
                f.write(x + "\n")
            f.write("---\n")
            f.write(self.body.replace("\r", ""))
        with (self.wikipath() / "control").open("a+") as h:
            h.write(f"{page} edited by {author}\n")
        self.cacheclear(page)
        if subprocess.run(
            [Path("~").expanduser() / "bin/wikiupdate"], shell=True
        ).returncode:
            raise DescriptiveError("wikiupdate failed")

    @classmethod
    def cacheclear(cls, page: Path):
        canonical_name = page.as_posix().replace(page.name, page.stem)
        cls.wikicache.pop(canonical_name, None)
        cls.page_cache.pop(page, None)
        cls.updatewikicache()

    @classmethod
    def wikindex(cls) -> [Path]:
        mds = []
        for p in cls.wikipath().glob("**/*.md"):
            if p.relative_to(cls.wikipath()).as_posix().startswith("."):
                continue  # skip hidden files
            mds.append(p.relative_to(cls.wikipath()))
        return sorted(mds)

    @classmethod
    def gettags(cls):
        if not cls.wikicache:
            cls.updatewikicache()
        return {k: v["tags"] for k, v in cls.wikicache.items()}

    @classmethod
    def getlinks(cls):
        if not cls.wikicache:
            cls.updatewikicache()
        return {k: v["links"] for k, v in cls.wikicache.items()}

    @classmethod
    def updatewikicache(cls):
        dt = time.time() - cls.wikistamp
        if dt > 6e4:
            cls.wikicache.clear()
            message = "a while"
        else:
            message = f"{dt} seconds"
        print(f"it has been {message} since the last wiki indexing")
        cls.wikistamp = time.time()
        changed = cls.refresh_cache()
        for m in cls.wikindex():
            if m in changed or m not in cls.wikicache:
                p = cls.load(m)
                canonical_name = m.as_posix().replace(m.name, m.stem)
                cls.wikicache[canonical_name] = {}
                cls.wikicache[canonical_name]["tags"] = p.tags
                cls.wikicache[canonical_name]["links"] = p.links

        print(f"index took: {str(1000 * (time.time() - cls.wikistamp))} milliseconds")

    @classmethod
    def refresh_cache(cls, page: Path = None):
        changed = []
        if page is None:
            for key in list(cls.page_cache.keys()):
                p = cls.page_cache.get(key, None)
                if p is None:
                    continue
                n = cls.wikipath() / key
                if not n.exists() or p.last_modified != n.stat().st_mtime:
                    del cls.page_cache[key]
                    if n.exists():
                        cls.load(key)
                    changed.append(key)
        else:
            if page in cls.page_cache:
                del cls.page_cache[page]
                cls.load(page)
                changed.append(page)

        if "items" in changed or "prices" in changed:
            cls.cache_items()
        return changed

    @classmethod
    def cache_items(cls):
        Item.item_cache = {}
        cls.__caching = True
        items, _ = Item.process_tree(cls.load_str("items").md(), print)
        item_from_prices, _ = Item.process_tree(cls.load_str("prices").md(), print)
        items += item_from_prices

        cache = {}
        for x in items:
            cache[x.name] = x

        Item.item_cache = cache
