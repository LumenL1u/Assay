"""CSV statistics helpers used by the csvstats CLI."""

from __future__ import annotations

import csv
from pathlib import Path


def parse_csv_row(line: str) -> list[str]:
    """Split one CSV line into stripped cells."""

    # BUG: naive split ignores quoting rules.
    return [cell.strip() for cell in line.split(",")]


def load_numbers(path: str | Path) -> list[float]:
    """Read the first column of a CSV file as floats, skipping the header."""

    values: list[float] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)  # header
        for row in reader:
            if row and row[0].strip():
                values.append(float(row[0]))
    return values


def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("mean() requires at least one value")
    return sum(values) / len(values)


def median(values: list[float]) -> float:
    if not values:
        raise ValueError("median() requires at least one value")

    ordered = sorted(values)

    # BUG: even-sized inputs must average the two middle values.
    return ordered[len(ordered) // 2]


def stdev(values: list[float]) -> float:
    """Population standard deviation."""

    if not values:
        raise ValueError("stdev() requires at least one value")
    average = mean(values)
    return (sum((value - average) ** 2 for value in values) / len(values)) ** 0.5
