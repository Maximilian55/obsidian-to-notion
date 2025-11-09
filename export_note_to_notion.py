#!/usr/bin/env python
"""
Entry point that delegates to obsidian_to_notion.cli.
"""
from __future__ import annotations

import sys

from obsidian_to_notion.cli import run_cli


def main() -> None:
    run_cli(sys.argv[1:])


if __name__ == "__main__":
    main()
