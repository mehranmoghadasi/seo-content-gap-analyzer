from content_gap.cli import build_parser, run_gap
from content_gap.fetch import fetch_page, robots_allows
from tests.fakepages import COMPETITORS, fetch


def test_robots_is_respected():
    assert robots_allows("https://beta.example/best-crm", fetch)
    assert not robots_allows("https://beta.example/private/secret", fetch)
    assert fetch_page("https://beta.example/private/secret", fetch) is None
    assert fetch_page("https://alpha.example/crm-guide", fetch) is not None


def test_gap_end_to_end(tmp_path, capsys):
    out = tmp_path / "gap.csv"
    args = build_parser().parse_args(["gap", "--target", "https://yoursite.example/best-crm-software",
                                      "--competitors", *COMPETITORS, "https://beta.example/private/secret",
                                      "--output", str(out), "--delay", "0"])
    assert run_gap(args, fetch=fetch) == 0
    text = capsys.readouterr().out
    assert "[skip] robots.txt disallows" in text
    assert "Competitors:   3" in text
    assert "lead scoring" in out.read_text()
