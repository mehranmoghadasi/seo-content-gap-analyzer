#!/usr/bin/env python3
"""Legacy entry point: `python analyzer.py --target ... --competitors ...` == `content-gap gap ...`."""

import sys

from content_gap.cli import main

if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv and argv[0] not in ("gap", "cluster", "-h", "--help", "--version"):
        argv = ["gap", *argv]
    sys.exit(main(argv))
