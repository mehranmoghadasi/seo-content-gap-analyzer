"""Offline demo: runs `gap` against in-memory pages and `cluster` on examples/keywords.txt.

    python examples/demo.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from content_gap.cli import build_parser, run_cluster, run_gap  # noqa: E402
from tests.fakepages import COMPETITORS, fetch  # noqa: E402

if __name__ == "__main__":
    gap_args = build_parser().parse_args(
        ["gap", "--target", "https://yoursite.example/best-crm-software", "--competitors", *COMPETITORS,
         "--output", str(ROOT / "examples" / "gap_report.csv"), "--delay", "0"]
    )
    run_gap(gap_args, fetch=fetch)
    print("\n" + "=" * 80 + "\n")
    cl_args = build_parser().parse_args(
        ["cluster", "--input", str(ROOT / "examples" / "keywords.txt"),
         "--output", str(ROOT / "examples" / "keyword_clusters.csv")]
    )
    run_cluster(cl_args)
