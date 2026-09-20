"""HTTP fetching with a robots.txt check."""

from __future__ import annotations

import urllib.robotparser
from collections.abc import Callable
from urllib.parse import urlsplit

import requests

USER_AGENT = "SEOContentGapAnalyzer/2.0 (+https://github.com/mehranmoghadasi/seo-content-gap-analyzer)"
TIMEOUT = 15

Fetch = Callable[[str], tuple[int, bytes]]


def robots_allows(url: str, fetch: Fetch) -> bool:
    """True unless the site's robots.txt disallows *url* for our user-agent (or '*')."""
    parts = urlsplit(url)
    status, body = fetch(f"{parts.scheme}://{parts.netloc}/robots.txt")
    if status != 200:
        return True
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(body.decode("utf-8", "replace").splitlines())
    return rp.can_fetch(USER_AGENT, url)


def requests_fetch(session: requests.Session | None = None) -> Fetch:
    s = session or requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})

    def fetch(url: str) -> tuple[int, bytes]:
        try:
            r = s.get(url, timeout=TIMEOUT)
            return r.status_code, r.content
        except requests.RequestException as exc:
            print(f"  [warn] {url}: {exc.__class__.__name__}")
            return 0, b""

    return fetch


def fetch_page(url: str, fetch: Fetch) -> bytes | None:
    """Return HTML bytes, or None if robots.txt disallows or the request fails."""
    if not robots_allows(url, fetch):
        print(f"  [skip] robots.txt disallows {url}")
        return None
    status, body = fetch(url)
    if status != 200 or not body:
        print(f"  [warn] {url} returned HTTP {status}")
        return None
    return body
