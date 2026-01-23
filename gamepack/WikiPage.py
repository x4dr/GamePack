import logging
import os.path
import re
import threading
import time
from datetime import timedelta, datetime, timezone
from pathlib import Path
from typing import Self, List, Optional, Union

import bleach
import yaml
from git import Repo, GitCommandError

from gamepack.Dice import DescriptiveError
from gamepack.Item import Item
from gamepack.MDPack import MDObj
from gamepack.PBTAItem import PBTAItem

log = logging.getLogger(__name__)


class WikiPage:
    """
    Class to represent a wiki page.
    """

    live = False
    page_cache: dict[Path, Self] = {}
    wikicache: dict[str, dict[str, list[str]]] = {}
    _wikipath: Optional[Path] = None
    wikistamp = 0
    clock_re = re.compile(
        r"\[clock\|(?P<name>.*?)\|(?P<current>.*?)\|(?P<maximum>.*?)]"
    )

    def __init__(
        self,
        title: str,
        tags: list[str],
        body: str,
        links: list[str],
        meta: Union[dict, str],
        modified: Optional[float] = None,
        file: Optional[Path] = None,
    ):
        self.save_msg_queue: List[str] = []
        if Item.item_cache is None:
            WikiPage.cache_items()
        self.title = title
        self.tags = set(tags)
        self.body = body
        self.links = links
        if isinstance(meta, str):
            meta_dict = yaml.safe_load(meta) or {}
        else:
            meta_dict = meta
        self.meta: dict = meta_dict
        self.last_modified = modified
        self.file = file

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
    def locate(cls, pagename: Union[str, Path, None]) -> Optional[Path]:
        """
        Finds a page in the wiki. Accepts full or stem name.
        Returns path relative to wiki root if found, else None.
        """
        if pagename is None:
            return None
        if isinstance(pagename, str):
            pagename = Path(pagename)
        if pagename.as_posix() == ".":
            return None
        root = cls.wikipath()
        pagename = Path(pagename).with_suffix(".md")

        if "/" in pagename.as_posix():
            full = root / pagename
            return full.relative_to(root) if full.exists() else None
        else:
            for path in root.rglob(pagename.name):
                if not any(part.startswith(".") for part in path.parts):
                    return path.relative_to(root)
            return None

    @classmethod
    def load_locate(cls, page: str, cache=True) -> Optional[Self]:
        path = cls.locate(page)
        if path is None:
            return None
        return cls.load(path, cache)

    @classmethod
    def load(cls, page: Optional[Path], cache=True) -> Optional[Self]:
        """
        loads page from wiki
        :param page: path of page
        :param cache: whether to retrieve from cache
        :return: WikiPage object or None
        """
        if page is None:
            return None
        result = cls.page_cache.get(page) if cache else None
        if (
            result
            and result.file
            and result.file.stat().st_mtime == result.last_modified
        ):
            return result

        def lineloader(file_obj):
            for readline in file_obj.readlines():
                yield readline

        try:
            if page.is_absolute():
                try:
                    rel = page.relative_to(cls.wikipath())
                    p = cls.wikipath() / rel
                except ValueError:
                    raise ValueError(f"Absolute path {page} is outside of the wiki!")
            else:
                p = cls.wikipath() / page
            filetime = p.stat().st_mtime
            with p.open() as f:
                lines = lineloader(f)
                first_line = next(lines, "").strip()
                preamble_text = None
                if first_line.startswith("---"):
                    preamble_text = ""
                    for line in lines:
                        if line.strip().startswith("---"):
                            break
                        preamble_text += line
                else:
                    f.seek(0)
                    lines = lineloader(f)

                body = ""
                preamble = {}
                if preamble_text:
                    try:
                        preamble = yaml.safe_load(preamble_text) or {}
                    except yaml.YAMLError:
                        body = f"???\n{preamble_text}\n???"

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
                cls.page_cache[p] = loaded_page
                return loaded_page
        except FileNotFoundError:
            raise DescriptiveError(str(page) + " not found in wiki.")

    def save(self, author: str, page: Optional[Path] = None, message=None):
        if not page:
            page = self.file
        if not page:
            raise DescriptiveError("No file path set for saving.")
        if page.suffix != ".md":
            raise DescriptiveError("page must be a .md file")

        target_path = self.wikipath() / page if not page.is_absolute() else page
        print(f"saving '{self.title}' as {target_path} ...")
        self.meta["title"] = self.title
        self.meta["tags"] = list(self.tags)
        self.meta["outgoing links"] = self.links
        with target_path.open("w+") as f:
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
        self.reload_cache(page)

        commit_and_push(
            self.wikipath(), target_path, message or f"{page} edited by {author}\n"
        )

    def save_overwrite(self, author, message=None):
        if not self.file:
            raise DescriptiveError("No file path set for overwriting.")
        log.info(f"overwriting '{self.title}' at {self.file} ...")
        self.meta["title"] = self.title
        self.meta["tags"] = list(self.tags)
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
        self.cacheupdate()

        commit_and_push(
            self.wikipath(), self.file, message or f"{self.file} edited by {author}\n"
        )

    def save_low_prio(self, message):
        if message and message not in self.save_msg_queue:
            self.save_msg_queue.append(message)
        self.cacheupdate()

    @classmethod
    def reload_cache(cls, page: Path):
        canonical_name = page.as_posix().replace(page.name, page.stem)
        cls.wikicache.pop(canonical_name, None)
        cls.page_cache.pop(page, None)
        cls.updatewikicache()

    def cacheupdate(self):
        page = self.file
        if not page:
            return
        canonical_name = page.as_posix().replace(page.name, page.stem)
        self.wikicache[canonical_name] = {"tags": list(self.tags), "links": self.links}
        target_path = page if page.is_absolute() else self.wikipath() / page
        self.last_modified = time.time()
        self.page_cache[target_path] = self

    @classmethod
    def wikindex(cls) -> list[Path]:
        mds = []
        root = cls.wikipath()
        for p in root.glob("**/*.md"):
            if p.relative_to(root).as_posix().startswith("."):
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
        log.info(f"it has been {message} since the last wiki indexing")
        cls.wikistamp = time.time()
        for m in cls.wikindex():
            canonical_name = m.as_posix().replace(m.name, m.stem)
            if canonical_name not in cls.wikicache:
                p = cls.load(m)
                if p:
                    cls.wikicache[canonical_name] = {
                        "tags": list(p.tags),
                        "links": p.links,
                    }

        log.info(
            f"index took: {str(1000 * (time.time() - cls.wikistamp))} milliseconds"
        )

    @classmethod
    def cache_items(cls):
        for itemclass in [Item, PBTAItem]:
            itemclass.item_cache = {}
            # cls.__caching = True # Unused?

            home_page = cls.load_locate(itemclass.home_md)
            if home_page:
                items, _ = itemclass.process_tree(home_page.md(), print)
            else:
                items = []

            prices_page = cls.load_locate("prices")
            if prices_page:
                item_from_prices, _ = itemclass.process_tree(prices_page.md(), print)
                items += item_from_prices

            cache = {}
            for x in items:
                cache[x.name] = x

            itemclass.item_cache = cache

    def get_clock(self, name) -> Optional[re.Match]:
        for candidate in self.clock_re.finditer(self.body):
            if candidate.group("name") == name:
                return candidate
        return None

    def change_clock(self, name, delta) -> Self:
        c = self.get_clock(name)
        if not c:
            return self
        try:
            current = int(c.group("current"))
        except ValueError:
            current = 0
        current += delta
        self.body = (
            self.body[: c.start()]
            + f"[clock|{c.group('name')}|{current}|{c.group('maximum')}]"
            + self.body[c.end() :]
        )
        return self

    def tagcheck(self, tag):
        for t in self.tags:
            if t.lower() == tag.lower():
                return True
        return False


def delayed_push(repo, pushtime: datetime):
    pushtime_utc = pushtime.astimezone(timezone.utc)
    now_utc = datetime.now(timezone.utc)
    threading.Event().wait(max(0, int((pushtime_utc - now_utc).total_seconds())))
    try:
        commitfile = Path("commit_tmp")
        with commitfile.open() as f:
            commit_message = "\n".join(line.strip() for line in f if line.strip())
        commitfile.unlink()
    except FileNotFoundError:
        commit_message = "general update"

    repo.index.commit(commit_message)

    # Push changes
    origin = repo.remote(name="origin")
    try:
        origin.push()
        log.info(f"Committed and pushed changes with message: '{commit_message}'")
    except GitCommandError:
        log.error("Failed to push changes.")


saveat = None


def commit_and_push(wikipath_val, file, commit_message: str):
    global saveat
    if not WikiPage.live:
        log.info("Not live, not pushing.")
        return
    repo = Repo(os.path.expanduser(str(wikipath_val)))
    # Check for changes
    if not repo.is_dirty():
        return
    # Stage all changes
    repo.git.add(str(file))
    with Path("commit_tmp").open("a") as f:
        f.write(commit_message + "\n")
    if not saveat or not saveat.is_alive():
        last_commit = next(repo.iter_commits(max_count=1)).committed_datetime
        next_push_time = last_commit + timedelta(hours=1)
        print("next push", next_push_time)
        saveat = threading.Thread(
            target=delayed_push, args=(repo, next_push_time), daemon=True
        )
        saveat.start()


def savequeue():
    log.info("starting save queue thread")
    while True:
        time.sleep(5)
        for w in WikiPage.page_cache.values():
            if w.save_msg_queue:
                msgs = w.save_msg_queue[:]
                w.save_msg_queue.clear()
                log.info(
                    f"queued overwriting {w.file} with message: '{' '.join(msgs)}'"
                )
                w.save_overwrite("system", "\n".join(msgs))


def start_savequeue():
    t = threading.Thread(target=savequeue)
    t.daemon = True
    t.start()
