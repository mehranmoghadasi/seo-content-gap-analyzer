# SEO Content Gap Analyzer

> Two CLI tools for content planning: **`gap`** finds the phrases top-ranking competitors use that your page lacks (with a score you can recompute by hand), and **`cluster`** groups a keyword export into topical clusters. Standard-library scoring — no scikit-learn, nltk downloads or pandas.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-12%20passing-brightgreen?logo=pytest&logoColor=white)](tests/)
[![Last Commit](https://img.shields.io/github/last-commit/mehranmoghadasi/seo-content-gap-analyzer)](https://github.com/mehranmoghadasi/seo-content-gap-analyzer/commits/main)

## The problem

You rank on page two. The pages above you *look* similar, but they cover something yours doesn't. Reading five competitor pages and comparing them phrase by phrase takes an afternoon; SaaS tools that do it start at $99/month and hide how the score is computed.

## Install

```bash
git clone https://github.com/mehranmoghadasi/seo-content-gap-analyzer.git
cd seo-content-gap-analyzer
pip install -e .          # or: pip install -r requirements.txt
```

Dependencies: `requests`, `beautifulsoup4`, `lxml`.

## `content-gap gap` — what competitors cover that you don't

```bash
content-gap gap \
  --target https://yoursite.com/best-crm-software \
  --competitors https://a.example/crm-guide https://b.example/best-crm https://c.example/crm-small-business \
  --output gap_report.csv
```

`python analyzer.py --target … --competitors …` still works as a legacy entry point.

| Flag | Meaning |
|---|---|
| `--min-competitors` | a phrase must appear on at least this many competitor pages (default 2) |
| `--min-per-1k` | minimum mean density, occurrences per 1,000 words, across the competitors that use it (default 0.5) |
| `--top-n` | rows to report (default 50) |
| `--max-ngram` | 1, 2 or 3-word phrases (default 3) |
| `--delay` | seconds between fetches (default 1.0) |

### How the score works

For every 1–3-word phrase on the competitor pages:

* `competitor_per_1k` — mean occurrences per 1,000 words across the competitors that use it
* `target_per_1k` — the same on your page (0 when you never use it)
* `coverage` — competitor pages using it ÷ competitor pages
* `shortfall` — `1 − min(1, target_per_1k ÷ competitor_per_1k)`
* **`gap_score = coverage × competitor_per_1k × shortfall`**

A phrase every competitor uses often and you never use scores highest. A phrase you already use at competitor density has shortfall 0 and is not reported; one you use but much less than they do is reported as `underweighted`. Shorter phrases that only occur inside a longer reported phrase ("data platform" inside "customer data platform") are collapsed into it. Phrases cannot start or end with a stop-word, and single stop-words are never counted.

Text comes from `<main>`/`<article>` when the page has one, otherwise `<body>`, with `nav`, `header`, `footer`, `aside`, `form`, scripts and styles removed. Pages disallowed by the site's `robots.txt` are skipped.

### Sample output

From `python examples/demo.py`, which runs against four in-memory pages (no network) so the numbers are reproducible:

```
=== Content Gap Report ===
Target:        https://yoursite.example/best-crm-software
Competitors:   3
Gap phrases:   10 (9 missing, 1 under-weighted)

#   phrase                              score  comp  comp/1k  you/1k  type
----------------------------------------------------------------------------------
1   lead scoring                        19.61 3/3      19.61     0.0  missing
2   marketing automation                19.61 3/3      19.61     0.0  missing
3   mobile app                          15.04 3/3      15.04     0.0  missing
4   workflow automation                 15.04 3/3      15.04     0.0  missing
5   customer data platform              14.08 2/3      21.12     0.0  missing
6   buyers                              10.09 2/3      15.14     0.0  missing
7   email sequences                     10.09 2/3      15.14     0.0  missing
8   hours                               10.09 2/3      15.14     0.0  missing
9   sales pipeline management            9.52 2/3      14.28     0.0  missing
10  sales pipeline                       7.89 3/3      25.13   17.24  underweighted
```

CSV columns: `phrase, ngram, gap_type, gap_score, competitor_count, competitors, competitor_per_1k, target_per_1k, found_on`. The demo's `examples/gap_report.csv` is committed.

## `content-gap cluster` — group a keyword export into topics

```bash
content-gap cluster --input keywords.txt --output keyword_clusters.csv --similarity 0.3
```

Input is one keyword per line, or a CSV whose first column is the keyword (a `keyword` header row is ignored). Each keyword joins the cluster whose **seed** keyword it resembles most by Jaccard similarity on content tokens — the best match, not the first that passes — and starts a new cluster if nothing reaches `--similarity`. Cluster names are the most frequent tokens across members in the seed's word order, extended until unique, so two clusters can never collide and silently drop keywords. Priority is HIGH (≥5 keywords), MEDIUM (3–4) or LOW.

```
=== Keyword clusters: 16 clusters, 38 keywords ===

[HIGH  ] google ads  (6)
    - google ads management
    - google ads agency
    - google ads campaign
    - google ads consultant
    - ecommerce google ads
    - shopify google ads

[HIGH  ] wordpress developer  (6)
    ...
[MEDIUM] local seo  (3)
    - local seo
    - local seo services
    - local business seo
```

Full run: `examples/keywords.txt` → `examples/keyword_clusters.csv` (both committed).

## Limitations

- Matching is lexical. "CRM pricing" and "cost of a CRM" are different phrases to this tool; it shortlists, you judge.
- Only server-rendered HTML is read; text injected by JavaScript is invisible.
- `robots.txt` `Disallow` rules are honoured; `Crawl-delay` is not read (use `--delay`).
- Density-based scores favour pages with focused copy. A very long competitor page dilutes its own densities.

## Project structure

```
seo-content-gap-analyzer/
├── analyzer.py            # legacy entry point → content-gap gap
├── content_gap/
│   ├── cli.py             # gap / cluster subcommands
│   ├── text.py            # HTML → text, tokens, n-gram counting, stop-words
│   ├── fetch.py           # requests + robots.txt check
│   ├── gap.py             # gap scoring (documented formula)
│   └── cluster.py         # keyword clustering + unique naming
├── tests/                 # 12 tests, in-memory pages, no network
├── examples/              # demo.py, keywords.txt, gap_report.csv, keyword_clusters.csv
├── ci/python-app.yml      # GitHub Actions workflow (copy to .github/workflows/)
├── requirements.txt
└── pyproject.toml
```

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest -q
```

## Changelog

- **2.0.0 (2026-09-19)** — Rewrite. The previous version ran TF-IDF on one document at a time (so IDF was constant and meaningless) and reported a gap score of `count × share × 2`; the README claimed robots.txt support and content-density boilerplate filtering that did not exist, required nltk downloads and scikit-learn, and referenced a `requirements.txt` that was missing. Now: documented density-based scoring, `underweighted` detection, phrase collapsing, `<main>`/`<article>` extraction, real robots.txt check, three light dependencies, 12 tests, reproducible demo. Absorbed the keyword clustering tool from `seo-keyword-research-tools` as the `cluster` subcommand, fixing a bug where two clusters with the same top-2 tokens overwrote each other and lost keywords, switching to best-match assignment, and removing unsourced client-result claims.
- **1.0.0** — single-script gap report.

## License

MIT — see [LICENSE](LICENSE).

## About the author

**Mehran Moghadasi** — Digital Marketing & Brand Manager (SEO · Google Ads · Meta Ads · Social Media), Calgary, AB.
[github.com/mehranmoghadasi](https://github.com/mehranmoghadasi) · [linkedin.com/in/mehranmoghadasi](https://www.linkedin.com/in/mehranmoghadasi)
