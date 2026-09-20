from content_gap.cluster import cluster_keywords, cluster_rows, load_keywords

KWS = [
    "wordpress website design", "wordpress web design", "wordpress developer", "hire wordpress developer",
    "google ads management", "google ads agency", "google ads consultant",
    "instagram ads", "instagram marketing",
    "local seo", "local seo services",
    "the and of",  # stop-words only
    "WordPress Website Design",  # duplicate after cleaning
]


def test_clusters_are_unique_named_and_lose_no_keywords():
    clusters = cluster_keywords(KWS, min_similarity=0.3)
    names = [c.name for c in clusters]
    assert len(names) == len(set(names))
    all_kws = [kw for c in clusters for kw in c.keywords]
    assert len(all_kws) == len(set(all_kws)) == 12  # 13 inputs minus 1 duplicate
    assert "the and of" in next(c for c in clusters if c.seed == "(stop-words only)").keywords


def test_name_collision_does_not_drop_a_cluster():
    # both groups would be named "google ads" by top-2 tokens; second must get a longer, unique name
    kws = ["google ads agency", "google ads agency pricing", "google ads consultant", "google ads consultant rates"]
    clusters = cluster_keywords(kws, min_similarity=0.6)
    assert sum(len(c.keywords) for c in clusters) == 4
    assert len({c.name for c in clusters}) == len(clusters)


def test_best_match_not_first_match():
    # 'google ads consultant' is closer to the ads cluster than to a seed it merely shares 'google' with
    kws = ["google analytics setup", "google ads agency", "google ads consultant"]
    clusters = cluster_keywords(kws, min_similarity=0.3)
    ads = next(c for c in clusters if "google ads agency" in c.keywords)
    assert "google ads consultant" in ads.keywords


def test_load_keywords_and_rows(tmp_path):
    f = tmp_path / "k.csv"
    f.write_text('keyword,volume\n"local seo",100\n# comment\n\nlocal seo services,50\n')
    kws = load_keywords(str(f))
    assert kws == ["local seo", "local seo services"]
    rows = cluster_rows(cluster_keywords(kws))
    assert rows[0]["cluster"] == "local seo" and rows[0]["cluster_size"] == 2 and rows[0]["priority"] == "LOW"
