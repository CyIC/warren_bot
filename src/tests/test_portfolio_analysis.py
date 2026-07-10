# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Test module for portfolio analysis."""
import asyncio
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

import pandas as pd

# under test
from warren_bot import portfolio_analysis


class PortfolioAnalysisTestCase(unittest.TestCase):
    """TestCase."""

    def test_something(self):
        """Stub for unit test."""
        self.assertEqual(True, True)  # add assertion here

    def test_build_stock_stats(self):
        """_build_stock_stats aggregates cost basis, shares, weight, and avg cost per ticker."""
        # GIVEN two lots of AAA and one of BBB
        stocks = pd.DataFrame(
            {
                "ticker": ["AAA", "AAA", "BBB"],
                "shares": [10.0, 5.0, 20.0],
                "price": [2.0, 3.0, 5.0],
                "commission": [1.0, 1.0, 2.0],
            }
        )
        total_shares = stocks["shares"].sum()  # 35

        # WHEN
        result = portfolio_analysis._build_stock_stats(stocks, total_shares)

        # THEN one row per ticker with aggregated figures
        self.assertEqual(list(result.index), ["AAA", "BBB"])
        # AAA: (10*2+1) + (5*3+1) = 37 cost basis over 15 shares
        self.assertAlmostEqual(result.loc["AAA", "cost_basis"], 37.0)
        self.assertAlmostEqual(result.loc["AAA", "shares"], 15.0)
        self.assertAlmostEqual(result.loc["AAA", "weight"], 15.0 / 35.0)
        self.assertAlmostEqual(result.loc["AAA", "avg_cost"], round(37.0 / 15.0, 6))
        # BBB: 20*5+2 = 102 cost basis over 20 shares
        self.assertAlmostEqual(result.loc["BBB", "cost_basis"], 102.0)
        self.assertAlmostEqual(result.loc["BBB", "avg_cost"], 5.1)

    def test_build_meeting_valuation(self):
        """_build_meeting_valuation pulls each meeting date's close prices into rows."""
        # GIVEN a long-form price frame pivoted to date x ticker (as run() builds it)
        prices_long = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-31", "2024-01-31", "2024-02-29", "2024-02-29"]),
                "ticker": ["AAA", "BBB", "AAA", "BBB"],
                "close": [10.0, 20.0, 11.0, 19.0],
            }
        )
        close = prices_long.pivot(index="date", columns="ticker", values="close")
        meeting_dates = pd.Series(pd.to_datetime(["2024-01-31", "2024-02-29"]))

        # WHEN
        result = portfolio_analysis._build_meeting_valuation(close, meeting_dates)

        # THEN one row per meeting date (index preserved), columns per ticker
        self.assertEqual(len(result), 2)
        self.assertEqual(list(result.index), list(meeting_dates))
        self.assertAlmostEqual(result.iloc[0]["AAA"], 10.0)
        self.assertAlmostEqual(result.iloc[0]["BBB"], 20.0)
        self.assertAlmostEqual(result.iloc[1]["AAA"], 11.0)
        self.assertAlmostEqual(result.iloc[1]["BBB"], 19.0)

    def test_load_club_data_persists_when_changed(self):
        """_load_club_data writes normalized data back when verify_club_data reports a change."""
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "club_info.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"club": {}}, f)
            normalized = {"club": {"normalized": True}}
            with mock.patch.object(
                portfolio_analysis.util,
                "verify_club_data",
                new=mock.AsyncMock(return_value=(normalized, True)),
            ):
                result = asyncio.run(portfolio_analysis._load_club_data(path))
            # THEN the normalized data is returned and persisted to disk
            self.assertEqual(result, normalized)
            with open(path, encoding="utf-8") as f:
                self.assertEqual(json.load(f), normalized)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_load_club_data_tolerates_readonly_file(self):
        """_load_club_data returns data without raising when the file can't be written."""
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "club_info.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"club": {}}, f)
            normalized = {"club": {"normalized": True}}
            real_open = open

            def readonly_open(file, mode="r", *args, **kwargs):
                if "w" in mode:  # simulate a read-only mount on the write-back
                    raise OSError("Read-only file system")
                return real_open(file, mode, *args, **kwargs)

            with mock.patch.object(
                portfolio_analysis.util,
                "verify_club_data",
                new=mock.AsyncMock(return_value=(normalized, True)),
            ), mock.patch("builtins.open", side_effect=readonly_open):
                result = asyncio.run(portfolio_analysis._load_club_data(path))
            # THEN the failed write is swallowed and the normalized data still returned
            self.assertEqual(result, normalized)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
