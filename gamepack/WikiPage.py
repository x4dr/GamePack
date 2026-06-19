"""Wiki page representation and management for wiki-based content.

Provides the WikiPage class for loading, caching, saving, and rendering
wiki pages from a git-backed markdown wiki directory.
"""

import logging
import os.path
import re
import threading
import time
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, ClassVar, Self, TextIO, cast

import bleach
import yaml
from git import GitCommandError, Repo

from gamepack.Dice import DescriptiveError
from gamepack.Item import Item
from gamepack.ItemBase import ItemBase
from gamepack.MDPack import MDObj, traverse_md
from gamepack.PBTAItem import PBTAItem

log = logging.getLogger(__name__)

__all__ = ["DescriptiveError", "WikiPage"]


class WikiPage:
    """Class to represent a wiki page."""

    live = False
    page_cache: ClassVar[dict[Path, WikiPage]] = {}
    wikicache: ClassVar[dict[str, dict[str, list[str]]]] = {}
    _wikipath: Path | None = None
    wikistamp: float = 0.0
    clock_re = re.compile(
        r"\[clock\|(?P<name>.*?)\|(?P<current>.*?)\|(?P<maximum>.*?)]",
    )

    def __init__(
        self,
        title: str,
        tags: list[str],
        body: str,
        links: list[str],
        meta: dict[str, Any] | str,
        modified: float | None = None,
        file: Path | None = None,
    ) -> None:
        """Initialize a WikiPage instance.

        Args:
            title: The page title.
            tags: List of tags associated with the page.
            body: The markdown body of the page.
            links: List of outgoing links from the page.
            meta: Metadata dictionary or YAML front-matter string.
            modified: Last modified timestamp, if available.
            file: Path to the page file, if available.

        """
        self.save_msg_queue: list[str] = []
        if Item.item_cache is None:
            WikiPage.cache_items()
        self.title = title
        self.tags = set(tags)
        self.body = body
        self.links = links
        meta_dict = yaml.safe_load(meta) or {} if isinstance(meta, str) else meta
        self.meta: dict[str, Any] = meta_dict
        self.last_modified = modified
        self.file = file

    def md(self, *, sanitize: bool = False) -> MDObj:
        """Parse the page body into an MDObj.

        Args:
            sanitize: Whether to sanitize the markdown.

        Returns:
            The parsed MDObj representation.

        """
        if sanitize:
            return MDObj.from_md(bleach.clean(self.body))
        return MDObj.from_md(self.body)

    @classmethod
    def wikipath(cls) -> Path:
        """:return: path to wiki directory"""
        if cls._wikipath is None:
            raise DescriptiveError("wikipath not set")
        return cls._wikipath

    @classmethod
    def set_wikipath(cls, path: Path) -> None:
        """Set the wiki root directory path.

        Args:
            path: The filesystem path to the wiki root.

        Raises:
            DescriptiveError: If the wiki path has already been set.

        """
        if cls._wikipath is not None:
            raise DescriptiveError("wikipath already set")
        cls._wikipath = path

    @classmethod
    def locate(cls, pagename: str | Path | None) -> Path | None:
        """Find a page in the wiki.

        Accepts full or stem name.

        Returns:
            Path relative to wiki root if found, else None.

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
        for path in root.rglob(pagename.name):
            if not any(part.startswith(".") for part in path.parts):
                return path.relative_to(root)
        return None

    @classmethod
    def load_locate(cls, page: str, *, cache: bool = True) -> Self | None:
        """Load a page by name, locating it first.

        Args:
            page: The page name to locate and load.
            cache: Whether to use the page cache.

        Returns:
            The loaded WikiPage, or None if not found.

        """
        path = cls.locate(page)
        if path is None:
            return None
        return cls.load(path, cache=cache)

    @classmethod
    def load(cls, page: Path | None, *, cache: bool = True) -> Self | None:
        """Load a page from the wiki.

        Args:
            page: Path of the page.
            cache: Whether to retrieve from cache.

        Returns:
            WikiPage object or None.

        """
        if page is None:
            return None
        if page.is_absolute():
            try:
                rel = page.relative_to(cls.wikipath())
                p = cls.wikipath() / rel
            except ValueError:
                msg = f"Absolute path {page} is outside of the wiki!"
                raise ValueError(msg) from None
        else:
            p = cls.wikipath() / page
        result = cls.page_cache.get(p) if cache else None
        if result and result.file and result.file.stat().st_mtime == result.last_modified:
            return cast(Self, result)

        def lineloader(file_obj: TextIO) -> Iterator[str]:
            yield from file_obj.readlines()

        try:
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
                preamble: dict[str, Any] = {}
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
            raise DescriptiveError(str(page) + " not found in wiki.") from None

    def save(self, author: str, page: Path | None = None, message: str | None = None) -> None:
        """Save the page to disk and commit to the git repository.

        Writes the page body with YAML front-matter to a markdown file,
        updates the cache, and triggers a git commit and push.

        Args:
            author: The author name for the commit.
            page: The target file path. Defaults to the stored file path.
            message: The commit message. Generated from page and author if
                not provided.

        Raises:
            DescriptiveError: If no file path is set or the file is not
                a .md file.

        """
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
                ),
            )
            f.write("---\n")
            f.write(self.body.replace("\r", ""))
        self.reload_cache(page)

        commit_and_push(
            self.wikipath(),
            target_path,
            message or f"{page} edited by {author}\n",
        )

    def save_overwrite(self, author: str, message: str | None = None) -> None:
        """Overwrite the current file and commit changes.

        Differs from save() by always writing to the existing file path
        and using a simpler commit flow.

        Args:
            author: The author name for the commit.
            message: The commit message. Generated from file path and
                author if not provided.

        Raises:
            DescriptiveError: If no file path is set.

        """
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
                ),
            )
            f.write("---\n")
            f.write(self.body.replace("\r", ""))
        self.cacheupdate()

        commit_and_push(
            self.wikipath(),
            self.file,
            message or f"{self.file} edited by {author}\n",
        )

    def save_low_prio(self, message: str) -> None:
        """Queue a low-priority save message.

        Adds the message to the save queue and updates the cache.
        Actual saving is deferred to the save queue thread.

        Args:
            message: The save message to queue.

        """
        if message and message not in self.save_msg_queue:
            self.save_msg_queue.append(message)
        self.cacheupdate()

    @classmethod
    def reload_cache(cls, page: Path) -> None:
        """Reload the cache for a specific page.

        Removes the page from both wikicache and page_cache, then
        triggers a full wiki cache update.

        Args:
            page: Path of the page to reload.

        """
        canonical_name = page.as_posix().replace(page.name, page.stem)
        cls.wikicache.pop(canonical_name, None)
        cls.page_cache.pop(page, None)
        cls.updatewikicache()

    def cacheupdate(self) -> None:
        """Update the cache entry for this page.

        Refreshes the wikicache entry with current tags and links, and
        updates the page_cache with the latest modification timestamp.
        """
        page = self.file
        if not page:
            return
        canonical_name = page.as_posix().replace(page.name, page.stem)
        self.wikicache[canonical_name] = {"tags": list(self.tags), "links": self.links}
        target_path = page if page.is_absolute() else self.wikipath() / page
        self.last_modified = page.stat().st_mtime
        self.page_cache[target_path] = self

    @classmethod
    def wikindex(cls) -> list[Path]:
        """List all markdown files in the wiki directory.

        Excludes hidden files (those whose relative path starts with
        a dot).

        Returns:
            Sorted list of Paths to markdown files.

        """
        mds = []
        root = cls.wikipath()
        for p in root.glob("**/*.md"):
            if p.relative_to(root).as_posix().startswith("."):
                continue  # skip hidden files
            mds.append(p)
        return sorted(mds)

    @classmethod
    def gettags(cls) -> dict[str, list[str]]:
        """Get all tags indexed in the wiki cache.

        Returns:
            A dict mapping canonical page names to their tag lists.

        """
        if not cls.wikicache:
            cls.updatewikicache()
        return {k: v["tags"] for k, v in cls.wikicache.items()}

    @classmethod
    def getlinks(cls) -> dict[str, list[str]]:
        """Get all outgoing links indexed in the wiki cache.

        Returns:
            A dict mapping canonical page names to their link lists.

        """
        if not cls.wikicache:
            cls.updatewikicache()
        return {k: v["links"] for k, v in cls.wikicache.items()}

    @classmethod
    def updatewikicache(cls) -> None:
        """Rebuild the wiki cache index.

        Clears the cache if more than 60 seconds have elapsed since
        the last index, then reloads all wiki pages and populates the
        cache with tags and links.
        """
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

        log.info(f"index took: {1000 * (time.time() - cls.wikistamp)!s} milliseconds")

    @classmethod
    def cache_items(cls) -> None:
        """Cache all items from the wiki into the item cache.

        Loads the home page and prices page for each item class
        (Item and PBTAItem), processes them, and populates the
        class-level item_cache.
        """
        for itemclass in (Item, PBTAItem):
            itemclass.item_cache = {}
            # cls.__caching = True # Unused?

            home_page = cls.load_locate(itemclass.home_md)
            if home_page:
                items: list[ItemBase] = [*itemclass.process_tree(home_page.md(), print)[0]]
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

    def get_clock(self, name: str) -> re.Match[str] | None:
        """Find a clock marker in the page body by name.

        Args:
            name: The clock name to search for.

        Returns:
            A regex Match object if found, or None.

        """
        for candidate in self.clock_re.finditer(self.body):
            if candidate.group("name") == name:
                return candidate
        return None

    def change_clock(self, name: str, delta: int) -> Self:
        """Change a clock's current value by a delta.

        Args:
            name: The clock name to modify.
            delta: The amount to add to the clock's current value
                (can be negative).

        Returns:
            Self, for method chaining.

        """
        c = self.get_clock(name)
        if not c:
            return self
        try:
            current = int(c.group("current"))
        except ValueError:
            current = 0
        current += delta
        self.body = (
            self.body[: c.start()] + f"[clock|{c.group('name')}|{current}|{c.group('maximum')}]" + self.body[c.end() :]
        )
        return self

    def tagcheck(self, tag: str) -> bool:
        """Check if the page has a specific tag (case-insensitive).

        Args:
            tag: The tag to check for.

        Returns:
            True if the tag exists, False otherwise.

        """
        return any(t.lower() == tag.lower() for t in self.tags)

    def render(self) -> Any:
        """Render the page. Base implementation returns None.

        Override this method in subclasses to provide custom rendering.

        Returns:
            The rendered output, or None by default.

        """
        return None

    @classmethod
    def resolve_address(cls, address: str) -> str | None:
        """Resolve a wiki address to page content.

        Supports page names and fragment navigation
        (e.g. "Page#Section").

        Args:
            address: The address string, optionally containing a
                # fragment separator.

        Returns:
            The resolved page body (or fragment), or None if the page
            is not found.

        """
        parts = address.split("#", 1)
        page_name = parts[0]

        page = cls.load_locate(page_name)
        if page is None:
            return None

        body = page.body

        if len(parts) < 2:
            return body

        body = re.sub(r"^(#+)\s*!\s*", r"\1 ", body, flags=re.MULTILINE)

        fragments = parts[1].split(":")
        for fragment in fragments:
            if not fragment.strip():
                continue
            body = traverse_md(body, fragment.strip())
            if not body.strip():
                return None

        return body


def delayed_push(repo: Repo, pushtime: datetime) -> None:
    """Push repository changes after a delay.

    Waits until the specified push time, then commits staged changes
    and pushes to the remote origin.

    Args:
        repo: The git repository object.
        pushtime: The datetime at which to perform the push.

    """
    pushtime_utc = pushtime.astimezone(UTC)
    now_utc = datetime.now(UTC)
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
        log.exception("Failed to push changes.")


saveat = None


def commit_and_push(wikipath_val: Path | str, file: Path | str, commit_message: str) -> None:
    """Stage, commit, and push changes to the wiki repository.

    If WikiPage.live is False, the operation is skipped. Stages the
    file, writes the commit message to a temporary file, and schedules
    a delayed push.

    Args:
        wikipath_val: Path to the wiki repository.
        file: The file to stage.
        commit_message: The commit message.

    """
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
            target=delayed_push,
            args=(repo, next_push_time),
            daemon=True,
        )
        saveat.start()


def savequeue() -> None:
    """Background thread that periodically flushes queued saves.

    Every 5 seconds, iterates over cached pages and saves any that
    have pending save messages.
    """
    log.info("starting save queue thread")
    while True:
        time.sleep(5)
        for w in WikiPage.page_cache.values():
            if w.save_msg_queue:
                msgs = w.save_msg_queue[:]
                w.save_msg_queue.clear()
                log.info(
                    f"queued overwriting {w.file} with message: '{' '.join(msgs)}'",
                )
                w.save_overwrite("system", "\n".join(msgs))


def start_savequeue() -> None:
    """Start the background save queue thread as a daemon."""
    t = threading.Thread(target=savequeue)
    t.daemon = True
    t.start()
