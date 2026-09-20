"""Text extraction and phrase counting. Pure functions, no network."""

from __future__ import annotations

import re
from collections import Counter

from bs4 import BeautifulSoup

STOPWORDS = frozenset("""
a about above after again against all am an and any are as at be because been before being below between
both but by can could did do does doing down during each few for from further had has have having he her here
hers herself him himself his how i if in into is it its itself just me more most my myself no nor not now of
off on once only or other our ours ourselves out over own same she should so some such than that the their
theirs them themselves then there these they this those through to too under until up very was we were what
when where which while who whom why will with would you your yours yourself yourselves
also however therefore thus via per etc one two three first second next last new get got make made use used
using like well much many even still yet already always often sometimes never every another back way ways
things thing something anything nothing may might must shall
""".split())

_NO_INTERIOR = frozenset({"and", "or", "but", "nor", "yet", "than", "then"})
_WORD = re.compile(r"[a-z][a-z0-9'-]*[a-z0-9]|[a-z]")
_BOILERPLATE = ("nav", "footer", "header", "aside", "form", "script", "style", "noscript", "template", "svg",
                "iframe", "button")


def extract_text(html: str | bytes) -> str:
    """Visible body text. Prefers <main>/<article> when present; strips nav/footer/aside/etc."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(_BOILERPLATE):
        tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    return " ".join(root.get_text(" ", strip=True).split())


def tokenize(text: str) -> list[str]:
    """Lower-cased word tokens in order (stop-words kept so that n-grams keep their shape)."""
    return _WORD.findall(text.lower())


def phrase_counts(tokens: list[str], max_n: int = 3) -> Counter:
    """Count 1..max_n-grams. An n-gram may contain a stop-word inside but not at either end,
    and single stop-words are never counted."""
    counts: Counter = Counter()
    n_tokens = len(tokens)
    for i, first in enumerate(tokens):
        if first in STOPWORDS or len(first) < 3:
            continue
        for n in range(1, max_n + 1):
            j = i + n
            if j > n_tokens:
                break
            last = tokens[j - 1]
            if last in STOPWORDS or (n > 1 and len(last) < 2):
                continue
            if n == 3 and tokens[i + 1] in _NO_INTERIOR:
                continue
            counts[" ".join(tokens[i:j])] += 1
    return counts


def keyword_tokens(keyword: str) -> set[str]:
    """Token set used for keyword clustering (stop-words and very short tokens removed)."""
    return {t for t in tokenize(keyword) if t not in STOPWORDS and len(t) >= 2}
