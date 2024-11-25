import logging
import os.path
import time
from functools import lru_cache
from pathlib import Path
from typing import Self

import bleach
import yaml
from git import Repo

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
        meta: dict,
        modified: float = None,
        file: Path = None,
    ):
        if Item.item_cache is None:
            WikiPage.cache_items()
        self.title = title
        self.tags = tags
        self.body = body
        self.links = links
        if isinstance(meta, str):
            meta = yaml.safe_load(meta)
        self.meta: dict = meta
        self.last_modified = modified
        self.file = file

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

        def lineloader(file):
            for readline in file.readlines():
                yield readline

        try:
            p = page if page.is_absolute() else cls.wikipath() / page
            filetime = p.stat().st_mtime
            res = cls.page_cache.get(page, None) if cache else None
            if res is not None:
                if res.last_modified != filetime:
                    cls.refresh_cache(page)
                    res = cls.page_cache.get(page, None)
                return res
            with p.open() as f:
                lines = lineloader(f)
                for line in lines:
                    if line.strip().startswith("---"):
                        break
                    # consume everything until preamble start and discard
                preamble = ""
                for line in lines:
                    if not line.strip():
                        continue
                    if line.strip().startswith("---"):
                        break
                    preamble += line

                    # consume everything until preamble end into preamble
                if not preamble:
                    preamble = ""
                body = ""
                try:
                    preamble = yaml.safe_load(preamble) or {}
                except yaml.YAMLError:
                    body = f"???\n{preamble}\n???"

                body += "".join(lines)

                loaded_page = cls(
                    title=preamble.get("title") or page.stem,
                    tags=preamble.get("tags") or [],
                    body=body,
                    links=preamble.get("outgoing links") or [],
                    modified=filetime,
                    meta=preamble,
                    file=p,
                )
                cls.page_cache[page] = loaded_page
                return loaded_page
        except FileNotFoundError:
            raise DescriptiveError(str(page) + " not found in wiki.")

    def save(self, page: Path, author: str, message=None):
        if page.suffix != ".md":
            raise DescriptiveError("page must be a .md file")
        print(f"saving '{self.title}' as {page} ...")
        self.meta["title"] = self.title
        self.meta["tags"] = self.tags
        self.meta["outgoing links"] = self.links
        with (self.wikipath() / page).open("w+") as f:
            f.write("---\n")
            f.write(
                yaml.dump(
                    self.meta,
                    default_flow_style=False,
                    encoding=None,
                    allow_unicode=True,
                )
            )
            f.write("---\n")
            f.write(self.body.replace("\r", ""))
        self.cacheclear(page)

        commit_and_push(
            self.wikipath(), page, message or f"{page} edited by {author}\n"
        )

    def save_overwrite(self, author, message=None):
        print(f"overwriting '{self.title}' at {self.file} ...")
        self.meta["title"] = self.title
        self.meta["tags"] = self.tags
        self.meta["outgoing links"] = self.links
        with self.file.open("w+") as f:
            f.write("---\n")
            f.write(
                yaml.dump(
                    self.meta,
                    default_flow_style=False,
                    encoding=None,
                    allow_unicode=True,
                )
            )
            f.write("---\n")
            f.write(self.body.replace("\r", ""))
        self.cacheclear(self.file)

        commit_and_push(
            self.wikipath(), self.file, message or f"{self.file} edited by {author}\n"
        )

    @classmethod
    def cacheclear(cls, page: Path):
        if not page.is_absolute():
            page = cls.wikipath() / page
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
            mds.append(p)
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
    def refresh_cache(cls, page: Path = None) -> list[Path]:
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


def commit_and_push(repo, file, commit_message: str):
    repo = Repo(os.path.expanduser(repo))
    # Check for changes
    if not repo.is_dirty():
        return
    # Stage all changes
    repo.git.add(file)

    # Commit changes
    repo.index.commit(commit_message)

    # Push changes
    # origin = repo.remote(name="origin")
    # origin.push()
    log.info(f"Committed and pushed changes with message: '{commit_message}'")
