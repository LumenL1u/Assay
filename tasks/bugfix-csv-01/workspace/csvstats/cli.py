"""Command line entry point for csvstats."""

from __future__ import annotations

import sys

from .stats import load_numbers, mean, median, stdev


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    path = args[0] if args else "data/sample.csv"

    values = load_numbers(path)
    print(f"count={len(values)}")
    print(f"mean={mean(values):.2f}")
    print(f"median={median(values):.2f}")
    print(f"stdev={stdev(values):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
