from content_gap.text import extract_text, keyword_tokens, phrase_counts, tokenize
from tests.fakepages import COMPETITORS, TARGET


def test_extract_text_prefers_main_and_drops_boilerplate():
    text = extract_text(TARGET)
    assert "nav-noise" not in text and "footer-noise" not in text and "var a=1" not in text
    assert text.startswith("Best CRM Software for Small Business")
    # page without <main> still drops nav/footer
    text2 = extract_text(COMPETITORS["https://beta.example/best-crm"])
    assert "nav-noise" not in text2 and "We tested ten CRM tools" in text2


def test_phrase_counts_respect_stopword_edges():
    counts = phrase_counts(tokenize("The sales pipeline of the team. Sales pipeline management."))
    assert counts["sales pipeline"] == 2
    assert counts["sales pipeline management"] == 1
    assert "pipeline of" not in counts and "of the" not in counts and "the" not in counts
    assert "pipeline of the team" not in counts  # 4-gram not generated
    conj = phrase_counts(tokenize("automation and email sequences; cost per click"))
    assert "automation and email" not in conj and "cost per click" in conj


def test_keyword_tokens():
    assert keyword_tokens("How to get the best CRM for my business") == {"best", "crm", "business"}
    assert keyword_tokens("the and of") == set()
