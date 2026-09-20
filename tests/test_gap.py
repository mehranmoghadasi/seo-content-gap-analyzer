from content_gap.gap import Doc, gap_report
from content_gap.text import extract_text
from tests.fakepages import COMPETITORS, TARGET


def _docs():
    target = Doc.from_text("https://yoursite.example/best-crm-software", extract_text(TARGET))
    comps = [Doc.from_text(u, extract_text(h)) for u, h in COMPETITORS.items()]
    return target, comps


def test_missing_phrases_rank_by_coverage_and_density():
    target, comps = _docs()
    rows = gap_report(target, comps, min_competitors=2, top_n=50)
    by = {r["phrase"]: r for r in rows}
    assert by["lead scoring"]["gap_type"] == "missing"
    assert by["lead scoring"]["competitor_count"] == 3 and by["lead scoring"]["target_per_1k"] == 0
    assert by["workflow automation"]["gap_type"] == "missing"
    # 'customer data platform' appears on 2 competitors only, in nav on the target (ignored)
    assert by["customer data platform"]["competitor_count"] == 2
    # shorter phrase that only lives inside the 3-gram is collapsed
    assert "data platform" not in by
    # phrases the target already covers at competitor density are not gaps
    assert "contact management" not in by or by["contact management"]["gap_type"] == "underweighted"
    assert rows == sorted(rows, key=lambda r: (-r["gap_score"], -r["competitor_count"], r["phrase"]))


def test_gap_score_formula_is_reproducible():
    target, comps = _docs()
    rows = gap_report(target, comps)
    r = next(x for x in rows if x["phrase"] == "lead scoring")
    users = [d for d in comps if "lead scoring" in d.counts]
    comp_per_1k = sum(d.per_1k("lead scoring") for d in users) / len(users)
    assert abs(r["gap_score"] - round(len(users) / len(comps) * comp_per_1k * 1.0, 2)) < 0.011


def test_min_competitors_and_empty():
    target, comps = _docs()
    assert all(r["competitor_count"] >= 3 for r in gap_report(target, comps, min_competitors=3))
    assert gap_report(target, [], 2) == []
