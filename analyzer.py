#!/usr/bin/env python3
"""
SEO Content Gap Analyzer
Compares your page's content against competitors to reveal topic and keyword gaps.
Author: Mehran Moghadasi | github.com/mehranmoghadasi
"""

import argparse
import sys
import time
from collections import defaultdict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import nltk

try:
    from nltk.corpus import stopwords
    STOPWORDS = set(stopwords.words("english"))
except LookupError:
    print("[!] Run: python -m nltk.downloader stopwords punkt")
    sys.exit(1)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; SEOContentGapAnalyzer/1.0; "
        "+https://github.com/mehranmoghadasi/seo-content-gap-analyzer)"
    )
}
REQUEST_TIMEOUT = 15
BOILERPLATE_TAGS = ["nav", "footer", "header", "script", "style", "aside", "form"]


def fetch_page_text(url: str) -> str:
    """Fetch a URL and return cleaned body text, stripping boilerplate elements."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  [WARN] Could not fetch {url}: {exc}")
        return ""
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in BOILERPLATE_TAGS:
        for element in soup.find_all(tag):
            element.decompose()
    content_tags = soup.find_all(["p", "h1", "h2", "h3", "h4", "li", "td", "span"])
    text_parts = [el.get_text(separator=" ", strip=True) for el in content_tags]
    raw_text = " ".join(text_parts)
    cleaned = " ".join(raw_text.lower().split())
    return cleaned


def extract_ngrams(text: str, ngram_range: tuple = (1, 3)) -> list:
    """Extract meaningful n-gram phrases from text using TF-IDF."""
    if not text.strip():
        return []
    vectorizer = TfidfVectorizer(
        ngram_range=ngram_range,
        stop_words="english",
        max_features=500,
        min_df=1,
        token_pattern=r"(?u)\b[a-z][a-z\-]{2,}\b",
    )
    try:
        tfidf_matrix = vectorizer.fit_transform([text])
    except ValueError:
        return []
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]
    phrase_scores = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
    return phrase_scores


def compute_gap_report(target_phrases, competitor_data, min_freq=2, top_n=50):
    """
    Compare target phrases against competitor phrases.
    Returns a DataFrame of gaps sorted by Gap Score descending.
    """
    phrase_competitor_count = defaultdict(int)
    phrase_total_freq = defaultdict(int)
    phrase_sources = defaultdict(list)

    for url, phrases_set, freq_dict in competitor_data:
        domain = urlparse(url).netloc
        for phrase in phrases_set:
            if phrase not in target_phrases:
                phrase_competitor_count[phrase] += 1
                phrase_total_freq[phrase] += freq_dict.get(phrase, 1)
                phrase_sources[phrase].append(domain)

    rows = []
    for phrase, count in phrase_competitor_count.items():
        if count >= min_freq:
            freq = phrase_total_freq[phrase]
            gap_score = round(freq * (count / len(competitor_data)) * 2, 2)
            n = len(phrase.split())
            rows.append({
                "phrase": phrase,
                "gap_score": gap_score,
                "competitor_frequency": freq,
                "competitor_count": count,
                "ngram_type": f"{n}-gram",
                "found_on": ", ".join(phrase_sources[phrase]),
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("gap_score", ascending=False).head(top_n).reset_index(drop=True)


def phrases_from_text(text: str, threshold: float = 0.01) -> tuple:
    """Extract a set of significant phrases and a frequency count dict from text."""
    ngrams = extract_ngrams(text)
    phrases_set = {phrase for phrase, score in ngrams if score >= threshold}
    freq_dict = {phrase: text.count(phrase) for phrase in phrases_set}
    return phrases_set, freq_dict


def main():
    parser = argparse.ArgumentParser(
        description="SEO Content Gap Analyzer — find what competitors cover that you don't."
    )
    parser.add_argument("--target", required=True, help="Your page URL")
    parser.add_argument("--competitors", required=True, nargs="+", help="Competitor URLs (max 5)")
    parser.add_argument("--output", default="gap_report.csv", help="Output CSV path")
    parser.add_argument("--min-freq", type=int, default=2, help="Min competitor mentions (default: 2)")
    parser.add_argument("--top-n", type=int, default=50, help="Gap phrases to report (default: 50)")
    args = parser.parse_args()

    competitors = args.competitors[:5]

    print(f"\n=== SEO Content Gap Analyzer ===")
    print(f"Target:      {args.target}")
    print(f"Competitors: {len(competitors)}\n")

    # Fetch target page
    print("[1] Fetching target page...")
    target_text = fetch_page_text(args.target)
    if not target_text:
        print("[ERROR] Could not fetch target page. Exiting.")
        sys.exit(1)
    target_phrases, _ = phrases_from_text(target_text)
    print(f"    Found {len(target_phrases)} phrases on target page.")

    # Fetch competitor pages
    competitor_data = []
    for i, url in enumerate(competitors, start=1):
        print(f"[{i+1}] Fetching competitor: {url}")
        text = fetch_page_text(url)
        time.sleep(1)  # polite crawl delay
        if text:
            phrases, freq_dict = phrases_from_text(text)
            competitor_data.append((url, phrases, freq_dict))
            print(f"    Found {len(phrases)} phrases.")
        else:
            print(f"    Skipping (fetch failed).")

    if not competitor_data:
        print("[ERROR] No competitor pages could be fetched.")
        sys.exit(1)

    # Compute gap report
    print(f"\nAnalyzing gaps (min-freq={args.min_freq}, top-n={args.top_n})...")
    df = compute_gap_report(target_phrases, competitor_data, args.min_freq, args.top_n)

    if df.empty:
        print("No significant gaps found. Try --min-freq 1.")
        sys.exit(0)

    # Print summary
    print(f"\n=== Content Gap Report ===")
    print(f"Target: {args.target}")
    print(f"Competitors analyzed: {len(competitor_data)}")
    print(f"Phrases missing from your page: {len(df)}\n")
    print(f"{'Rank':<5} {'Phrase':<42} {'Gap Score':<12} {'Competitors'}")
    print("-" * 75)
    for i, row in df.head(15).iterrows():
        print(f"{i+1:<5} {row['phrase'][:40]:<42} {row['gap_score']:<12} {row['competitor_count']}/{len(competitor_data)}")

    # Save CSV
    df.to_csv(args.output, index=False)
    print(f"\nFull report saved to: {args.output}")
    print("Done.")


if __name__ == "__main__":
    main()
