"""Content-gap scoring.

Every number in the report is defined here and reproducible by hand:

* ``per_1k``            – occurrences of the phrase per 1,000 words of a page.
* ``competitor_count``  – how many competitor pages use the phrase at all.
* ``competitor_per_1k`` – mean per_1k across the competitors that use it.
* ``target_per_1k``     – per_1k on your page (0 when missing).
* ``gap_score``         – coverage × competitor_per_1k × shortfall, where
                          coverage = competitor_count / competitors and
                          shortfall = 1 − min(1, target_per_1k / competitor_per_1k).
                          A phrase every competitor uses often and you never use scores highest;
                          a phrase you already use at competitor density scores 0 and is not reported.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from urllib.parse import urlsplit

from .text import phrase_counts, tokenize


@dataclass
class Doc:
    url: str
    words: int
    counts: Counter

    @classmethod
    def from_text(cls, url: str, text: str, max_n: int = 3) -> Doc:
        tokens = tokenize(text)
        return cls(url=url, words=len(tokens), counts=phrase_counts(tokens, max_n))

    def per_1k(self, phrase: str) -> float:
        if not self.words:
            return 0.0
        return 1000.0 * self.counts.get(phrase, 0) / self.words


def _subsumed(phrase: str, count: int, longer: dict[str, int], ratio: float = 0.8) -> bool:
    """True when *phrase* almost only occurs inside longer reported phrases (e.g. 'automation' inside
    'marketing automation' + 'workflow automation'); the longer phrases are reported instead."""
    padded = f" {phrase} "
    # a longer phrase only counts if it is a real phrase itself (>= 1/4 of the short phrase's occurrences),
    # so a handful of stray 3-grams cannot swallow a genuine 2-gram
    inside = sum(c for other, c in longer.items() if padded in f" {other} " and c >= 0.25 * count)
    return inside >= ratio * count


def gap_report(target: Doc, competitors: list[Doc], min_competitors: int = 2, top_n: int = 50,
               min_per_1k: float = 0.5) -> list[dict]:
    """Rank phrases competitors use that the target lacks or under-uses."""
    if not competitors:
        return []
    n = len(competitors)
    total: Counter = Counter()
    docs_with: Counter = Counter()
    for doc in competitors:
        for phrase, c in doc.counts.items():
            total[phrase] += c
            docs_with[phrase] += 1

    rows = []
    for phrase, count in docs_with.items():
        if count < min_competitors:
            continue
        users = [d for d in competitors if phrase in d.counts]
        comp_per_1k = sum(d.per_1k(phrase) for d in users) / len(users)
        if comp_per_1k < min_per_1k:
            continue
        target_per_1k = target.per_1k(phrase)
        shortfall = 1.0 - min(1.0, target_per_1k / comp_per_1k)
        if shortfall <= 0:
            continue
        rows.append({
            "phrase": phrase,
            "ngram": len(phrase.split()),
            "gap_type": "missing" if target_per_1k == 0 else "underweighted",
            "gap_score": round((count / n) * comp_per_1k * shortfall, 2),
            "competitor_count": count,
            "competitors": n,
            "competitor_per_1k": round(comp_per_1k, 2),
            "target_per_1k": round(target_per_1k, 2),
            "found_on": ", ".join(sorted({urlsplit(d.url).netloc for d in users})),
        })

    # Collapse shorter phrases that only live inside a longer reported phrase.
    by_len = {}
    for r in rows:
        by_len.setdefault(r["ngram"], {})[r["phrase"]] = total[r["phrase"]]
    kept = []
    for r in rows:
        longer = {}
        for n_len, phrases in by_len.items():
            if n_len > r["ngram"]:
                longer.update(phrases)
        if longer and _subsumed(r["phrase"], total[r["phrase"]], longer):
            continue
        kept.append(r)

    kept.sort(key=lambda r: (-r["gap_score"], -r["competitor_count"], r["phrase"]))
    return kept[:top_n]


def summary(target_url: str, competitors: list[Doc], rows: list[dict], shown: int = 12) -> str:
    lines = [
        "=== Content Gap Report ===",
        f"Target:        {target_url}",
        f"Competitors:   {len(competitors)}",
        f"Gap phrases:   {len(rows)} ({sum(r['gap_type'] == 'missing' for r in rows)} missing, "
        f"{sum(r['gap_type'] == 'underweighted' for r in rows)} under-weighted)",
        "",
        f"{'#':<3} {'phrase':<34} {'score':>6} {'comp':>5} {'comp/1k':>8} {'you/1k':>7}  type",
        "-" * 82,
    ]
    for i, r in enumerate(rows[:shown], 1):
        lines.append(f"{i:<3} {r['phrase'][:33]:<34} {r['gap_score']:>6} "
                     f"{r['competitor_count']}/{r['competitors']:<3} {r['competitor_per_1k']:>8} "
                     f"{r['target_per_1k']:>7}  {r['gap_type']}")
    return "\n".join(lines)
