#!/usr/bin/env python3
"""Strict tuner audit including source/UI/test registration assertions."""

from __future__ import annotations

import argparse
from tuner_audit import run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inject-failure", action="store_true",
                        help=argparse.SUPPRESS)
    args = parser.parse_args()
    return run(include_source=True, inject_failure=args.inject_failure)


if __name__ == "__main__":
    raise SystemExit(main())
