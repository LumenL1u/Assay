import tempfile
import unittest
from pathlib import Path

from csvstats.stats import load_numbers, mean, median, parse_csv_row, stdev


class ParseCsvRowTests(unittest.TestCase):
    def test_plain_cells(self):
        self.assertEqual(parse_csv_row("a, b ,c"), ["a", "b", "c"])

    def test_quoted_comma(self):
        self.assertEqual(parse_csv_row('a,"b,c",d'), ["a", "b,c", "d"])

    def test_escaped_quotes(self):
        self.assertEqual(parse_csv_row('"say ""hi""",x'), ['say "hi"', "x"])


class StatsTests(unittest.TestCase):
    def test_mean(self):
        self.assertAlmostEqual(mean([1, 2, 3]), 2.0)

    def test_median_odd(self):
        self.assertEqual(median([3, 1, 2]), 2)

    def test_median_even(self):
        self.assertEqual(median([4, 1, 3, 2]), 2.5)

    def test_stdev(self):
        self.assertAlmostEqual(stdev([2, 4, 4, 4, 5, 5, 7, 9]), 2.0)


class LoadNumbersTests(unittest.TestCase):
    def test_skips_header_and_reads_first_column(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "values.csv"
            path.write_text("value,label\n1,a\n2,b\n\n3,c\n", encoding="utf-8")
            self.assertEqual(load_numbers(path), [1.0, 2.0, 3.0])


if __name__ == "__main__":
    unittest.main()
