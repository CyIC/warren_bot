# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Test analysis module for financial analysis."""
import math
import unittest

import numpy as np
import pandas as pd

from warren_bot import analysis


class ComputeLogReturnsTestCase(unittest.TestCase):
    """Tests for compute_log_returns."""

    def test_matches_manual_log_ratio(self):
        # Given
        prices = pd.Series([100.0, 110.0, 121.0])

        # When
        log_returns = analysis.compute_log_returns(prices)

        # Then - first value is NaN (no prior price), rest are log ratios
        self.assertTrue(math.isnan(log_returns.iloc[0]))
        self.assertAlmostEqual(log_returns.iloc[1], math.log(110.0 / 100.0))
        self.assertAlmostEqual(log_returns.iloc[2], math.log(121.0 / 110.0))


class EstimateExpMovAvgVolatilityTestCase(unittest.TestCase):
    """Tests for estimate_exp_mov_avg_volatility."""

    def test_returns_non_negative_float(self):
        # Given
        prices = pd.Series([10.0, 10.5, 10.2, 10.8, 11.1, 10.9])

        # When
        last_vol = analysis.estimate_exp_mov_avg_volatility(prices, 0.7)

        # Then
        self.assertIsInstance(float(last_vol), float)
        self.assertGreaterEqual(last_vol, 0.0)

    def test_constant_prices_have_zero_volatility(self):
        # Given - no price movement => zero volatility
        prices = pd.Series([5.0, 5.0, 5.0, 5.0])

        # When
        last_vol = analysis.estimate_exp_mov_avg_volatility(prices, 0.9)

        # Then
        self.assertAlmostEqual(last_vol, 0.0)


class AnalyzeReturnsTestCase(unittest.TestCase):
    """Tests for analyze_returns and analyze_alpha (one-tailed t-test)."""

    def test_returns_t_and_half_p_value(self):
        # Given
        net_returns = pd.Series([0.01, 0.02, -0.005, 0.015, 0.008])

        # When
        t_value, p_value = analysis.analyze_returns(net_returns)

        # Then - p is half the two-tailed p-value and within [0, 0.5]
        self.assertTrue(np.isfinite(t_value))
        self.assertGreaterEqual(p_value, 0.0)
        self.assertLessEqual(p_value, 0.5)

    def test_analyze_alpha_matches_analyze_returns(self):
        # Given
        series = pd.Series([0.03, 0.01, 0.02, -0.01, 0.04])

        # When
        t_returns, p_returns = analysis.analyze_returns(series)
        t_alpha, p_alpha = analysis.analyze_alpha(series)

        # Then
        self.assertAlmostEqual(t_returns, t_alpha)
        self.assertAlmostEqual(p_returns, p_alpha)


class ShiftReturnsTestCase(unittest.TestCase):
    """Tests for shift_returns."""

    def test_positive_shift_moves_values_forward(self):
        # Given
        returns = pd.Series([1.0, 2.0, 3.0])

        # When
        shifted = analysis.shift_returns(returns, 1)

        # Then
        self.assertTrue(math.isnan(shifted.iloc[0]))
        self.assertEqual(shifted.iloc[1], 1.0)
        self.assertEqual(shifted.iloc[2], 2.0)

    def test_negative_shift_moves_values_backward(self):
        # Given
        returns = pd.Series([1.0, 2.0, 3.0])

        # When
        shifted = analysis.shift_returns(returns, -1)

        # Then
        self.assertEqual(shifted.iloc[0], 2.0)
        self.assertTrue(math.isnan(shifted.iloc[2]))


class ResamplePricesTestCase(unittest.TestCase):
    """Tests for resample_prices."""

    def test_resamples_to_month_end_last_value(self):
        # Given - daily prices spanning two months
        idx = pd.date_range("2024-01-30", periods=4, freq="D")
        close_prices = pd.Series([1.0, 2.0, 3.0, 4.0], index=idx)

        # When - month-end resample takes the last observation in each month
        resampled = analysis.resample_prices(close_prices, freq="ME")

        # Then
        self.assertEqual(resampled.loc["2024-01-31"], 2.0)
        self.assertEqual(resampled.loc["2024-02-29"], 4.0)


class GetMostVolatileTestCase(unittest.TestCase):
    """Tests for get_most_volatile."""

    def test_identifies_higher_variance_ticker(self):
        # Given - AAA is calm, BBB swings wildly
        prices = pd.DataFrame(
            {
                "ticker": ["AAA", "AAA", "AAA", "BBB", "BBB", "BBB"],
                "date": pd.to_datetime(
                    ["2024-01-01", "2024-01-02", "2024-01-03"] * 2
                ),
                "price": [100.0, 101.0, 100.5, 50.0, 80.0, 40.0],
            }
        )

        # When
        most_volatile = analysis.get_most_volatile(prices)

        # Then
        self.assertEqual(most_volatile, "BBB")


class GetTopNTestCase(unittest.TestCase):
    """Tests for get_top_n."""

    def test_marks_top_performers_with_one(self):
        # Given - per row, the two largest columns should be marked 1
        prev_returns = pd.DataFrame(
            {
                "AAA": [0.05, 0.01],
                "BBB": [0.02, 0.09],
                "CCC": [0.10, 0.03],
            },
            index=pd.to_datetime(["2024-01-31", "2024-02-29"]),
        )

        # When
        top = analysis.get_top_n(prev_returns, 2)

        # Then - row 1: AAA & CCC are top-2; row 2: BBB & CCC are top-2
        self.assertEqual(list(top.iloc[0]), [1, 0, 1])
        self.assertEqual(list(top.iloc[1]), [0, 1, 1])
        self.assertTrue((top.dtypes == int).all())


class PortfolioReturnsTestCase(unittest.TestCase):
    """Tests for portfolio_returns."""

    def test_long_minus_short_divided_by_n(self):
        # Given
        df_long = pd.DataFrame({"AAA": [1, 0], "BBB": [0, 1]})
        df_short = pd.DataFrame({"AAA": [0, 1], "BBB": [1, 0]})
        lookahead = pd.DataFrame({"AAA": [0.10, 0.20], "BBB": [0.30, 0.40]})

        # When
        result = analysis.portfolio_returns(df_long, df_short, lookahead, 2)

        # Then - (long*look - short*look)/n
        self.assertAlmostEqual(result.loc[0, "AAA"], (0.10 - 0.0) / 2)
        self.assertAlmostEqual(result.loc[0, "BBB"], (0.0 - 0.30) / 2)
        self.assertAlmostEqual(result.loc[1, "AAA"], (0.0 - 0.20) / 2)
        self.assertAlmostEqual(result.loc[1, "BBB"], (0.40 - 0.0) / 2)


if __name__ == "__main__":
    unittest.main()
