# SEO Content Gap Analyzer

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)

A command-line tool for SEO specialists and content marketers to identify **content gaps** between their pages and top-ranking competitors. Stop guessing what to write — let the data tell you which topics you're missing.

## The Problem

You're ranking on page 2 for a high-value keyword. The top 3 results seem similar to your page — but something's missing. Manually reading 5–10 competitor pages, extracting their topics, and comparing them to yours takes hours. This tool does it in seconds.

## The Solution

`seo-content-gap-analyzer` fetches the text of your page and up to 5 competitor URLs, extracts meaningful keyword phrases using TF-IDF analysis, and produces a ranked gap report showing exactly which topics competitors cover that your page is missing.

## Features

- Scrapes and cleans body text from any public URL (respects robots.txt)
- Extracts 1-gram, 2-gram, and 3-gram keyword phrases via TF-IDF
- Calculates a **Gap Score** for each missing phrase (frequency × IDF weight)
- Outputs results as a ranked CSV report and a console summary
- Filters out boilerplate (nav, footer, ads) using content-density scoring
- Configurable minimum frequency threshold to cut noise
- Works with up to 5 competitor URLs per run

## Tech Stack

- Python 3.8+
- `requests` + `BeautifulSoup4` — fetching and parsing HTML
- `scikit-learn` — TF-IDF vectorization
- `nltk` — stopword removal and tokenization
- `pandas` — report generation and CSV export

## Installation

```bash
git clone https://github.com/mehranmoghadasi/seo-content-gap-analyzer.git
cd seo-content-gap-analyzer
pip install -r requirements.txt
python -m nltk.downloader stopwords punkt
```

## Usage

```bash
python analyzer.py \
  --target "https://yoursite.com/your-page" \
  --competitors "https://competitor1.com/page" "https://competitor2.com/page" \
  --output gap_report.csv \
  --min-freq 2
```

### Arguments

| Flag | Description | Default |
|---|---|---|
| `--target` | Your page URL | Required |
| `--competitors` | Space-separated competitor URLs (max 5) | Required |
| `--output` | CSV output filename | `gap_report.csv` |
| `--min-freq` | Minimum competitor mentions to include a phrase | `2` |
| `--top-n` | How many gap phrases to report | `50` |

## Sample Output

```
=== SEO Content Gap Report ===
Target: https://yoursite.com/best-crm-software
Competitors analyzed: 4
Phrases in competitor content NOT on your page: 38

Top 10 Content Gaps (by Gap Score):
 1. "customer data platform"     Gap Score: 8.42  | Found in 4/4 competitors
 2. "sales pipeline management"  Gap Score: 7.91  | Found in 3/4 competitors
 3. "lead scoring automation"    Gap Score: 6.88  | Found in 4/4 competitors
 4. "crm integration api"        Gap Score: 6.12  | Found in 3/4 competitors
 5. "contact segmentation"       Gap Score: 5.77  | Found in 2/4 competitors

Full report saved to: gap_report.csv
```

## Output CSV Format

| phrase | gap_score | competitor_frequency | competitor_count | ngram_type |
|---|---|---|---|---|
| customer data platform | 8.42 | 12 | 4 | 3-gram |

## Use Cases

- Pre-writing research: find every angle competitors cover before you write
- Content refresh: audit existing pages for outdated or missing topics
- Pillar page planning: identify subtopics needed for topical authority
- Client reporting: show clients exactly what's missing from their content

## License

MIT © Mehran Moghadasi
