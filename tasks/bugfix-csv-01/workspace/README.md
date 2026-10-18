# csvstats

Small CSV statistics CLI. The project uses only the Python standard library.

## Run

```bash
python3 -m csvstats.cli data/sample.csv
```

## Test

```bash
python3 -m unittest discover -s tests -v
```

## Public API

The following names are exported from `csvstats.stats` and must keep their
existing signatures:

- `parse_csv_row(line: str) -> list[str]`
- `load_numbers(path: str | Path) -> list[float]`
- `mean(values: list[float]) -> float`
- `median(values: list[float]) -> float`
- `stdev(values: list[float]) -> float`
