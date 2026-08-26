"""Polite fetching: robots.txt gate, honest UA, per-domain rate limit, HTML cache
with content-hash drift detection (docs/04 §2, §9.2).

Compliance rules implemented here (§9.5):
- robots.txt respected (cached once per host; disallowed URLs raise RobotsDisallowed)
- ChurneyBot/1.0 user agent
- <= 1 request / 5s per domain
- content cached on disk; callers can skip re-parsing unchanged pages via PageResult.status
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

USER_AGENT = "ChurneyBot/1.0 (+about/contact)"
MIN_INTERVAL_SECONDS = 5.0


class RobotsDisallowed(RuntimeError):
    pass


class FetchError(RuntimeError):
    def __init__(self, status: int, url: str) -> None:
        super().__init__(f"HTTP {status} for {url}")
        self.status = status


@dataclass
class PageResult:
    url: str
    html: str
    status: Literal["new", "unchanged"]
    content_hash: str


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Fetcher:
    """HTTPX-backed fetcher; also the base class for alternate engines
    (e.g., PlaywrightFetcher overrides `_get`)."""

    def __init__(
        self,
        cache_dir: Path,
        *,
        transport: httpx.BaseTransport | None = None,
        min_interval: float = MIN_INTERVAL_SECONDS,
        respect_robots: bool = True,
        clock: Callable[[], float] = time.monotonic,
        timeout: float = 30.0,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.min_interval = min_interval
        self.respect_robots = respect_robots
        self._clock = clock
        self._last_hit: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser | None] = {}
        self._index_path = self.cache_dir / "index.json"
        self._index: dict[str, dict] = self._load_index()
        self.client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            transport=transport,
            timeout=timeout,
            follow_redirects=True,
        )

    # -- public API ---------------------------------------------------------

    def fetch(self, url: str) -> PageResult:
        if self.respect_robots and not self._robots_allows(url):
            raise RobotsDisallowed(url)
        host = urlparse(url).netloc
        self._throttle(host)
        status_code, html = self._get(url)
        if status_code >= 400:
            raise FetchError(status_code, url)
        digest = sha256_hex(html)
        status: Literal["new", "unchanged"] = "new"
        prev = self._index.get(url)
        if prev and prev.get("hash") == digest:
            status = "unchanged"
        self._write_cache(url, html, digest)
        return PageResult(url=url, html=html, status=status, content_hash=digest)

    def known_hash(self, url: str) -> str | None:
        entry = self._index.get(url)
        return entry.get("hash") if entry else None

    def close(self) -> None:
        self.client.close()

    # -- engine hook ----------------------------------------------------------

    def _get(self, url: str) -> tuple[int, str]:
        resp = self.client.get(url)
        return resp.status_code, resp.text

    # -- internals ----------------------------------------------------------

    def _load_index(self) -> dict[str, dict]:
        try:
            return json.loads(self._index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_cache(self, url: str, html: str, digest: str) -> None:
        parsed = urlparse(url)
        host_dir = self.cache_dir / re.sub(r"[^a-z0-9.-]", "_", parsed.netloc.lower())
        host_dir.mkdir(parents=True, exist_ok=True)
        body_path = host_dir / f"{digest}.html"
        if not body_path.exists():
            body_path.write_text(html, encoding="utf-8")
        self._index[url] = {
            "hash": digest,
            "body": str(body_path),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._index_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._index, indent=2), encoding="utf-8")
        tmp.replace(self._index_path)

    def _throttle(self, host: str) -> None:
        last = self._last_hit.get(host)
        now = self._clock()
        if last is not None:
            wait = self.min_interval - (now - last)
            if wait > 0:
                time.sleep(wait)  # real sleep even with fake clock deltas < interval
                now = self._clock()
        self._last_hit[host] = now

    def _robots_for(self, scheme_host: str) -> RobotFileParser | None:
        """Returns a parser, an empty-allow sentinel (None), or raises-free fallback.

        RFC 9309 semantics:
        - 2xx            -> parse rules
        - 4xx (no robots)-> unrestricted
        - 5xx (unreachable) -> conservative: treat as complete disallow
        We encode 'complete disallow' by returning a parser whose fetch of any URL
        fails via _disallow_all.
        """
        if scheme_host in self._robots:
            return self._robots[scheme_host]
        rp = RobotFileParser()
        robots_url = f"{scheme_host}/robots.txt"
        try:
            resp = self.client.get(robots_url)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
            elif 500 <= resp.status_code < 600:
                rp.disallow_all = True  # RFC 9309: unreachable => complete disallow
                rp.parse([])
            else:
                rp.parse([])  # 4xx/no robots => unrestricted (empty rules allow all)
            self._robots[scheme_host] = rp
        except httpx.HTTPError:
            rp.disallow_all = True  # unreachable transport => conservative
            self._robots[scheme_host] = rp
        return self._robots[scheme_host]

    def _robots_allows(self, url: str) -> bool:
        parsed = urlparse(url)
        scheme_host = f"{parsed.scheme}://{parsed.netloc}"
        rp = self._robots_for(scheme_host)
        if rp is None:
            return True
        return rp.can_fetch(USER_AGENT, url)
