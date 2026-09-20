"""Keyword clustering by token overlap (Jaccard), with stable, unique cluster names."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .text import keyword_tokens


@dataclass
class Cluster:
    seed: str
    seed_tokens: set[str]
    keywords: list[str] = field(default_factory=list)
    name: str = ""

    @property
    def priority(self) -> str:
        n = len(self.keywords)
        return "HIGH" if n >= 5 else "MEDIUM" if n >= 3 else "LOW"


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def clean_keyword(kw: str) -> str:
    return " ".join(kw.lower().split())


def cluster_keywords(keywords: list[str], min_similarity: float = 0.3) -> list[Cluster]:
    """Each keyword joins the cluster whose *seed* it resembles most (not the first that passes),
    so cluster membership does not depend on input order drifting the seed."""
    clusters: list[Cluster] = []
    seen: set[str] = set()
    unclustered: list[str] = []
    for raw in keywords:
        kw = clean_keyword(raw)
        if not kw or kw in seen:
            continue
        seen.add(kw)
        tokens = keyword_tokens(kw)
        if not tokens:
            unclustered.append(kw)
            continue
        best, best_sim = None, 0.0
        for c in clusters:
            sim = jaccard(tokens, c.seed_tokens)
            if sim > best_sim:
                best, best_sim = c, sim
        if best is not None and best_sim >= min_similarity:
            best.keywords.append(kw)
        else:
            clusters.append(Cluster(seed=kw, seed_tokens=tokens, keywords=[kw]))
    if unclustered:
        clusters.append(Cluster(seed="(stop-words only)", seed_tokens=set(), keywords=unclustered))
    _name_clusters(clusters)
    clusters.sort(key=lambda c: (-len(c.keywords), c.name))
    return clusters


def _in_seed_order(tokens: list[str], seed_words: list[str]) -> str:
    """Keep the seed keyword's natural word order ("local seo", not "seo local")."""
    return " ".join(sorted(tokens, key=lambda t: seed_words.index(t) if t in seed_words else 99))


def _name_clusters(clusters: list[Cluster]) -> None:
    """Name = most frequent tokens across members; extended until unique so no cluster is lost."""
    used: set[str] = set()
    for c in clusters:
        if not c.seed_tokens:
            c.name = c.seed
            used.add(c.name)
            continue
        freq = Counter(t for kw in c.keywords for t in keyword_tokens(kw))
        ordered = [t for t, _ in freq.most_common()]
        name = ""
        for k in range(min(2, len(ordered)), len(ordered) + 1):
            name = _in_seed_order(ordered[:k], c.seed.split())
            if name not in used:
                break
        if name in used:
            name = c.seed
        c.name = name
        used.add(name)


def load_keywords(path: str) -> list[str]:
    """One keyword per line; CSV lines use the first column; '#' lines are comments."""
    keywords = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            kw = line.split(",")[0].strip().strip('"')
            if kw and kw.lower() not in ("keyword", "keywords"):
                keywords.append(kw)
    return keywords


def cluster_rows(clusters: list[Cluster]) -> list[dict]:
    rows = []
    for c in clusters:
        for kw in c.keywords:
            rows.append({"cluster": c.name, "keyword": kw, "cluster_size": len(c.keywords), "priority": c.priority})
    return rows


def cluster_summary(clusters: list[Cluster]) -> str:
    total = sum(len(c.keywords) for c in clusters)
    lines = [f"=== Keyword clusters: {len(clusters)} clusters, {total} keywords ==="]
    for c in clusters:
        lines.append(f"\n[{c.priority:<6}] {c.name}  ({len(c.keywords)})")
        lines.extend(f"    - {kw}" for kw in c.keywords)
    lines.append("\nOne page or ad group per HIGH/MEDIUM cluster; fold LOW clusters into the nearest page.")
    return "\n".join(lines)
