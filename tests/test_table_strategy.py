import os
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

os.environ.setdefault("API_TOKEN", "test-token")

import app


class TableStrategyTests(unittest.TestCase):
    def test_fast_strategy_stops_after_first_successful_extractor(self):
        df = pd.DataFrame({"A": ["one"], "B": ["two"]})

        with patch("app._run_table_extractor", return_value=[(1, df)]) as run_extractor:
            tables = app.extract_tables_fast(
                Path("dummy.pdf"),
                "all",
                ["camelot_lattice", "camelot_stream", "pdfplumber"],
            )

        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0].source, "camelot_lattice")
        run_extractor.assert_called_once_with("camelot_lattice", Path("dummy.pdf"), "all")

    def test_fast_strategy_falls_back_until_success(self):
        df = pd.DataFrame({"A": ["one"], "B": ["two"]})

        def fake_run(name, _pdf_path, _pages):
            if name == "camelot_lattice":
                return []
            return [(2, df)]

        with patch("app._run_table_extractor", side_effect=fake_run) as run_extractor:
            tables = app.extract_tables_fast(
                Path("dummy.pdf"),
                "all",
                ["camelot_lattice", "camelot_stream", "pdfplumber"],
            )

        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0].source, "camelot_stream")
        self.assertEqual(run_extractor.call_count, 2)

    def test_quality_strategy_runs_all_extractors_and_deduplicates(self):
        df = pd.DataFrame({"A": ["same"], "B": ["table"]})

        with patch("app._run_table_extractor", return_value=[(1, df)]) as run_extractor:
            tables = app.extract_tables_quality(
                Path("dummy.pdf"),
                "all",
                ["camelot_lattice", "camelot_stream"],
            )

        self.assertEqual(len(tables), 1)
        self.assertEqual(run_extractor.call_count, 2)

    def test_parse_table_extractors_ignores_unknown_and_deduplicates(self):
        with self.assertLogs("app", level="WARNING"):
            extractors = app.parse_table_extractors(
                "pdfplumber,unknown,pdfplumber,camelot_stream"
            )

        self.assertEqual(extractors, ["pdfplumber", "camelot_stream"])


if __name__ == "__main__":
    unittest.main()
