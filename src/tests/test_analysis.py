# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Test analysis module for financial analysis."""
import unittest

import numpy as np
import pandas as pd

from warren_bot.analysis import get_most_volatile, compute_log_returns, get_top_n, analyze_returns


class TestGetMostVolatile(unittest.TestCase):
    """Test cases for get_most_volatile function."""

    def setUp(self):
        """Set up test fixtures for get_most_volatile tests."""
        # Create basic test data with known volatility characteristics
        np.random.seed(42)  # For reproducible tests

        # Create test data with different volatility levels
        dates = pd.date_range("2023-01-01", periods=100, freq="D")

        # Low volatility stock (small price changes)
        low_vol_prices = 100 + np.cumsum(np.random.normal(0, 0.5, 100))

        # Medium volatility stock
        med_vol_prices = 100 + np.cumsum(np.random.normal(0, 1.5, 100))

        # High volatility stock (large price changes)
        high_vol_prices = 100 + np.cumsum(np.random.normal(0, 3.0, 100))

        # Create DataFrame with multiple tickers
        self.test_data = pd.DataFrame(
            {
                "ticker": ["LOW"] * 100 + ["MED"] * 100 + ["HIGH"] * 100,
                "date": list(dates) + list(dates) + list(dates),
                "price": list(low_vol_prices) + list(med_vol_prices) + list(high_vol_prices),
            }
        )

        # Create minimal valid data
        self.minimal_data = pd.DataFrame(
            {
                "ticker": ["A", "A", "B", "B"],
                "date": pd.date_range("2023-01-01", periods=2).tolist() * 2,
                "price": [100, 101, 100, 110],  # B is more volatile
            }
        )

        # Create single ticker data
        self.single_ticker = pd.DataFrame(
            {
                "ticker": ["SINGLE"] * 10,
                "date": pd.date_range("2023-01-01", periods=10),
                "price": [100, 102, 98, 105, 95, 108, 92, 110, 88, 115],
            }
        )

    def test_basic_functionality(self):
        """Test that function returns the most volatile ticker."""
        result = get_most_volatile(self.test_data)

        # HIGH should be the most volatile stock based on our test data generation
        self.assertEqual(result, "HIGH")
        self.assertIsInstance(result, str)

    def test_minimal_data(self):
        """Test with minimal valid data (2 prices per ticker)."""
        result = get_most_volatile(self.minimal_data)

        # With only 2 data points, both tickers will have NaN volatility
        # Function should still return a ticker (the first one encountered)
        self.assertIn(result, ["A", "B"])

    def test_single_ticker(self):
        """Test with single ticker (should return that ticker)."""
        result = get_most_volatile(self.single_ticker)
        self.assertEqual(result, "SINGLE")

    def test_equal_volatility(self):
        """Test when tickers have equal volatility."""
        equal_vol_data = pd.DataFrame(
            {
                "ticker": ["A"] * 3 + ["B"] * 3,
                "date": pd.date_range("2023-01-01", periods=3).tolist() * 2,
                "price": [100, 102, 98] * 2,  # Same price pattern
            }
        )

        result = get_most_volatile(equal_vol_data)

        # Should return one of the tickers (depends on processing order)
        self.assertIn(result, ["A", "B"])

    def test_empty_dataframe(self):
        """Test that empty DataFrame raises ValueError."""
        empty_df = pd.DataFrame(columns=["ticker", "date", "price"])

        with self.assertRaises(ValueError) as context:
            get_most_volatile(empty_df)

        self.assertIn("cannot be None or empty", str(context.exception))

    def test_none_input(self):
        """Test that None input raises ValueError."""
        with self.assertRaises(ValueError) as context:
            get_most_volatile(None)

        self.assertIn("cannot be None or empty", str(context.exception))

    def test_missing_required_columns(self):
        """Test that missing required columns raises ValueError."""
        # Missing 'ticker' column
        missing_ticker = pd.DataFrame(
            {"date": pd.date_range("2023-01-01", periods=5), "price": [100, 101, 102, 103, 104]}
        )

        with self.assertRaises(ValueError) as context:
            get_most_volatile(missing_ticker)

        self.assertIn("Missing required columns", str(context.exception))
        self.assertIn("ticker", str(context.exception))

        # Missing 'price' column
        missing_price = pd.DataFrame({"ticker": ["A"] * 5, "date": pd.date_range("2023-01-01", periods=5)})

        with self.assertRaises(ValueError) as context:
            get_most_volatile(missing_price)

        self.assertIn("Missing required columns", str(context.exception))
        self.assertIn("price", str(context.exception))

    def test_single_price_point(self):
        """Test with single price point per ticker (should handle gracefully)."""
        single_point = pd.DataFrame(
            {"ticker": ["A", "B"], "date": pd.date_range("2023-01-01", periods=2), "price": [100, 200]}
        )

        # This should work but may return NaN volatility
        # The function should handle this gracefully
        result = get_most_volatile(single_point)
        self.assertIn(result, ["A", "B"])

    def test_constant_prices(self):
        """Test with constant prices (zero volatility)."""
        constant_prices = pd.DataFrame(
            {
                "ticker": ["A"] * 5 + ["B"] * 5,
                "date": pd.date_range("2023-01-01", periods=5).tolist() * 2,
                "price": [100] * 5 + [200] * 5,  # Constant prices
            }
        )

        # Should handle zero volatility gracefully
        result = get_most_volatile(constant_prices)
        self.assertIn(result, ["A", "B"])

    def test_nan_prices(self):
        """Test handling of NaN prices."""
        nan_data = pd.DataFrame(
            {
                "ticker": ["A"] * 5 + ["B"] * 5,
                "date": pd.date_range("2023-01-01", periods=5).tolist() * 2,
                "price": [100, np.nan, 102, 103, 104, 200, 201, np.nan, 203, 204],
            }
        )

        # Should handle NaN values gracefully
        result = get_most_volatile(nan_data)
        self.assertIn(result, ["A", "B"])

    def test_negative_prices(self):
        """Test with negative prices (unusual but should handle)."""
        negative_data = pd.DataFrame(
            {
                "ticker": ["A"] * 3 + ["B"] * 3,
                "date": pd.date_range("2023-01-01", periods=3).tolist() * 2,
                "price": [-100, -102, -98, -50, -55, -45],  # Negative prices cause log(negative) = NaN
            }
        )

        # Negative prices will cause NaN in log calculations
        # Function should handle this and return a ticker (likely the first encountered)
        result = get_most_volatile(negative_data)
        self.assertIn(result, ["A", "B"])

    def test_very_large_numbers(self):
        """Test with very large price numbers."""
        large_data = pd.DataFrame(
            {
                "ticker": ["A"] * 3 + ["B"] * 3,
                "date": pd.date_range("2023-01-01", periods=3).tolist() * 2,
                "price": [1e10, 1.01e10, 0.99e10, 1e10, 1.1e10, 0.9e10],  # B more volatile
            }
        )

        result = get_most_volatile(large_data)
        self.assertEqual(result, "B")

    def test_many_tickers(self):
        """Test performance with many tickers."""
        # Create data with 100 tickers
        tickers = [f"TICK_{i:03d}" for i in range(100)]
        all_data = []

        for i, ticker in enumerate(tickers):
            # Create different volatility for each ticker
            volatility = 0.5 + i * 0.01  # Increasing volatility
            prices = 100 + np.cumsum(np.random.normal(0, volatility, 50))

            ticker_data = pd.DataFrame(
                {"ticker": [ticker] * 50, "date": pd.date_range("2023-01-01", periods=50), "price": prices}
            )
            all_data.append(ticker_data)

        many_tickers_data = pd.concat(all_data, ignore_index=True)

        result = get_most_volatile(many_tickers_data)

        # Should return one of the higher-numbered tickers (higher volatility)
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("TICK_"))

    def test_data_types(self):
        """Test that function handles different data types correctly."""
        # Test with string ticker and float prices
        mixed_data = pd.DataFrame(
            {"ticker": ["AAPL", "GOOGL"], "date": pd.date_range("2023-01-01", periods=2), "price": [150.5, 2500.75]}
        )

        result = get_most_volatile(mixed_data)
        self.assertIn(result, ["AAPL", "GOOGL"])

    def test_duplicate_dates_per_ticker(self):
        """Test handling of duplicate dates for same ticker."""
        duplicate_dates = pd.DataFrame(
            {
                "ticker": ["A", "A", "B", "B"],
                "date": ["2023-01-01", "2023-01-01", "2023-01-01", "2023-01-02"],
                "price": [100, 105, 200, 220],  # A has duplicate date
            }
        )

        # Should handle gracefully
        result = get_most_volatile(duplicate_dates)
        self.assertIn(result, ["A", "B"])

    def test_mathematical_correctness(self):
        """Test mathematical correctness of volatility calculation."""
        # Create data with known volatility characteristics
        known_data = pd.DataFrame(
            {
                "ticker": ["LOW_VOL"] * 4 + ["HIGH_VOL"] * 4,
                "date": pd.date_range("2023-01-01", periods=4).tolist() * 2,
                "price": [
                    100,
                    100.1,
                    100.2,
                    100.1,  # Low volatility: ~0.1% changes
                    100,
                    110,
                    90,
                    105,
                ],  # High volatility: ~10% changes
            }
        )

        result = get_most_volatile(known_data)
        self.assertEqual(result, "HIGH_VOL")

    def test_clear_volatility_difference(self):
        """Test with data that has clear volatility differences."""
        # Create data with sufficient points and clear volatility differences
        clear_diff_data = pd.DataFrame(
            {
                "ticker": ["STABLE"] * 5 + ["VOLATILE"] * 5,
                "date": pd.date_range("2023-01-01", periods=5).tolist() * 2,
                "price": [
                    100,
                    100.5,
                    101,
                    100.5,
                    101,  # Very stable: 0.5% max change
                    100,
                    120,
                    80,
                    150,
                    70,
                ],  # Very volatile: 50% swings
            }
        )

        result = get_most_volatile(clear_diff_data)
        self.assertEqual(result, "VOLATILE")


class AnalysisTestCase(unittest.TestCase):
    """General test cases for analysis module."""

    def test_module_imports(self):
        """Test that required functions can be imported."""

        # Test that functions are callable
        self.assertTrue(callable(get_most_volatile))
        self.assertTrue(callable(compute_log_returns))
        self.assertTrue(callable(get_top_n))
        self.assertTrue(callable(analyze_returns))


if __name__ == "__main__":
    unittest.main()
