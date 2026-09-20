"""CLI: `content-gap gap ...` and `content-gap cluster ...`."""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

from . import __version__
from .cluster import cluster_keywords, cluster_rows, cluster_summary, load_keywords
from .fetch import fetch_page, requests_fetch
from .gap import Doc, gap_report, summary
from .text import extract_text


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        if not rows:
            fh.write("")
            return
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="content-gap", description="SEO content-gap analysis and keyword clustering.")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("gap", help="phrases competitors use that your page lacks")
    g.add_argument("--target", required=True, help="your page URL")
    g.add_argument("--competitors", required=True, nargs="+", help="competitor page URLs (up to 10)")
    g.add_argument("--output", default="gap_report.csv")
    g.add_argument("--min-competitors", type=int, default=2, help="phrase must appear on this many competitors (2)")
    g.add_argument("--min-per-1k", type=float, default=0.5, help="min mean density per 1,000 words (0.5)")
    g.add_argument("--top-n", type=int, default=50)
    g.add_argument("--max-ngram", type=int, default=3, choices=(1, 2, 3))
    g.add_argument("--delay", type=float, default=1.0, help="seconds between fetches (1.0)")

    c = sub.add_parser("cluster", help="group a keyword list into topical clusters")
    c.add_argument("--input", required=True, help="keywords file (txt, one per line, or CSV first column)")
    c.add_argument("--output", default="keyword_clusters.csv")
    c.add_argument("--similarity", type=float, default=0.3, help="Jaccard threshold 0-1 (0.3)")
    return p


def run_gap(args: argparse.Namespace, fetch=None) -> int:
    fetch = fetch or requests_fetch()
    urls = args.competitors[:10]
    print(f"[gap] target: {args.target}")
    html = fetch_page(args.target, fetch)
    if html is None:
        print("[error] could not fetch target page", file=sys.stderr)
        return 1
    target = Doc.from_text(args.target, extract_text(html), args.max_ngram)
    print(f"      {target.words} words")

    competitors: list[Doc] = []
    for url in urls:
        if args.delay:
            time.sleep(args.delay)
        html = fetch_page(url, fetch)
        if html is None:
            continue
        doc = Doc.from_text(url, extract_text(html), args.max_ngram)
        print(f"[gap] competitor: {url}  ({doc.words} words)")
        competitors.append(doc)
    if not competitors:
        print("[error] no competitor page could be fetched", file=sys.stderr)
        return 1

    rows = gap_report(target, competitors, args.min_competitors, args.top_n, args.min_per_1k)
    print()
    print(summary(args.target, competitors, rows))
    write_csv(rows, Path(args.output))
    print(f"\n[saved] {args.output} ({len(rows)} rows)")
    return 0


def run_cluster(args: argparse.Namespace) -> int:
    keywords = load_keywords(args.input)
    if not keywords:
        print("[error] no keywords found", file=sys.stderr)
        return 1
    clusters = cluster_keywords(keywords, args.similarity)
    print(cluster_summary(clusters))
    write_csv(cluster_rows(clusters), Path(args.output))
    print(f"\n[saved] {args.output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "gap":
        return run_gap(args)
    return run_cluster(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
