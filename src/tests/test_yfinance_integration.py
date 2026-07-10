# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Unit testing module for the yfinance_integration module."""
import asyncio
import unittest
from unittest.mock import patch, MagicMock

import pandas as pd

from warren_bot import yfinance_integration as yf_api


class YfinanceIntegrationTestCase(unittest.TestCase):
    """Test yfinance integration methods."""

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_overview(self, mock_ticker):
        """Test get_yfinance_overview method."""
        # GIVEN
        mock_stock = MagicMock()
        mock_stock.ticker = "AAPL"
        mock_stock.info = {
            "symbol": "AAPL",
            "displayName": "Apple",
            "longName": "Apple Inc.",
            "shortName": "Apple Inc.",
            "market": "us_market",
            "marketCap": 3000000000000,
            "trailingPE": 25.5,
            "dividendYield": 0.005,
        }
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.get_yfinance_overview("AAPL")

        # THEN
        self.assertIsInstance(result, pd.Series)
        mock_ticker.assert_called_once_with("AAPL")
        self.assertEqual(result["Symbol"], "AAPL")
        self.assertEqual(result["Name"], "Apple Inc.")

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_income_statement(self, mock_ticker):
        """Test get_yfinance_income_statement method."""
        # GIVEN
        mock_stock = MagicMock()

        # Create mock financials data in yfinance format (items as rows, dates as columns)
        dates = pd.to_datetime(["2023-12-31", "2022-12-31", "2021-12-31"])
        annual_data = pd.DataFrame(
            {"Total Revenue": [100000, 95000, 90000], "Net Income": [20000, 18000, 16000]}, index=dates
        ).T

        quarterly_dates = pd.to_datetime(["2023-12-31", "2023-09-30", "2023-06-30"])
        quarterly_data = pd.DataFrame(
            {"Total Revenue": [25000, 24000, 23000], "Net Income": [5000, 4800, 4600]}, index=quarterly_dates
        ).T

        mock_stock.financials = annual_data
        mock_stock.quarterly_financials = quarterly_data
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.get_yfinance_income_statement("AAPL")

        # THEN
        self.assertIsInstance(result, dict)
        self.assertIn("annualReports", result)
        self.assertIn("quarterlyReports", result)
        self.assertIsInstance(result["annualReports"], pd.DataFrame)
        # Columns are remapped to the alphavantage names the report code consumes
        self.assertIn("totalRevenue", result["annualReports"].columns)
        self.assertIn("netIncome", result["annualReports"].columns)
        self.assertEqual(result["annualReports"]["totalRevenue"].iloc[-1], 100000)

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_income_statement_quarterly_aggregation(self, mock_ticker):
        """Test that quarterly income statement is aggregated into extra annual periods."""
        # GIVEN
        mock_stock = MagicMock()

        # Annual data covers 2023 and 2022
        annual_dates = pd.to_datetime(["2023-12-31", "2022-12-31"])
        annual_data = pd.DataFrame(
            {"Total Revenue": [100000, 95000], "Net Income": [20000, 18000]}, index=annual_dates
        ).T

        # Quarterly data covers Q4 2021 through Q3 2022 — includes 4 quarters for 2021
        quarterly_dates = pd.to_datetime([
            "2022-09-30", "2022-06-30", "2022-03-31", "2021-12-31",
            "2021-09-30", "2021-06-30", "2021-03-31",
        ])
        quarterly_data = pd.DataFrame(
            {
                "Total Revenue": [26000, 25000, 24000, 23000, 22000, 21000, 20000],
                "Net Income": [5200, 5000, 4800, 4600, 4400, 4200, 4000],
            },
            index=quarterly_dates,
        ).T

        mock_stock.financials = annual_data
        mock_stock.quarterly_financials = quarterly_data
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.get_yfinance_income_statement("AAPL", years=10)

        # THEN — should have 2021 aggregated from quarterly in addition to 2022, 2023
        annual_reports = result["annualReports"]
        self.assertGreater(len(annual_reports), 2)
        annual_years = set(annual_reports.index.year)
        self.assertIn(2021, annual_years)

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_income_statement_years_limit(self, mock_ticker):
        """Test that annual reports are trimmed to the requested years."""
        # GIVEN
        mock_stock = MagicMock()

        annual_dates = pd.to_datetime(["2023-12-31", "2022-12-31", "2021-12-31", "2020-12-31"])
        annual_data = pd.DataFrame(
            {"Total Revenue": [100000, 95000, 90000, 85000]}, index=annual_dates
        ).T

        mock_stock.financials = annual_data
        mock_stock.quarterly_financials = None
        mock_ticker.return_value = mock_stock

        # WHEN — request only 2 years
        result = yf_api.get_yfinance_income_statement("AAPL", years=2)

        # THEN
        self.assertEqual(len(result["annualReports"]), 2)
        self.assertIsInstance(result["quarterlyReports"], pd.DataFrame)
        mock_ticker.assert_called_once_with("AAPL")

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_balance_sheet(self, mock_ticker):
        """Test get_yfinance_balance_sheet method."""
        # GIVEN
        mock_stock = MagicMock()

        # Create mock balance sheet data in yfinance format (items as rows, dates as columns)
        dates = pd.to_datetime(["2023-12-31", "2022-12-31"])
        balance_data = pd.DataFrame(
            {"Cash And Cash Equivalents": [500000, 450000], "Current Assets": [100000, 95000]}, index=dates
        ).T

        mock_stock.balance_sheet = balance_data
        mock_stock.quarterly_balance_sheet = balance_data
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.get_yfinance_balance_sheet("AAPL")

        # THEN
        self.assertIsInstance(result, dict)
        self.assertIn("annualReports", result)
        self.assertIn("quarterlyReports", result)
        # Columns are remapped to the alphavantage names the report code consumes
        self.assertIn("cashAndCashEquivalentsAtCarryingValue", result["annualReports"].columns)
        self.assertIn("totalCurrentAssets", result["annualReports"].columns)
        self.assertEqual(result["annualReports"]["cashAndCashEquivalentsAtCarryingValue"].iloc[-1], 500000)
        mock_ticker.assert_called_once_with("AAPL")

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_balance_sheet_quarterly_snapshot(self, mock_ticker):
        """Test that quarterly balance sheet uses latest snapshot (not sum) for extra years."""
        # GIVEN
        mock_stock = MagicMock()

        # Annual data covers 2023 and 2022
        annual_dates = pd.to_datetime(["2023-12-31", "2022-12-31"])
        annual_data = pd.DataFrame(
            {"Current Assets": [500000, 450000], "Long Term Debt": [100000, 95000]}, index=annual_dates
        ).T

        # Quarterly data includes quarters from 2021 not in annual data
        quarterly_dates = pd.to_datetime([
            "2022-09-30", "2022-06-30", "2022-03-31", "2021-12-31", "2021-09-30",
        ])
        quarterly_data = pd.DataFrame(
            {
                "Current Assets": [470000, 460000, 455000, 440000, 430000],
                "Long Term Debt": [98000, 97000, 96000, 94000, 93000],
            },
            index=quarterly_dates,
        ).T

        mock_stock.balance_sheet = annual_data
        mock_stock.quarterly_balance_sheet = quarterly_data
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.get_yfinance_balance_sheet("AAPL", years=10)

        # THEN — should have 2021 from latest quarterly snapshot, not summed
        annual_reports = result["annualReports"]
        self.assertGreater(len(annual_reports), 2)
        annual_years = set(annual_reports.index.year)
        self.assertIn(2021, annual_years)
        # The 2021 row should be a snapshot, not a sum — totalCurrentAssets should be 440000
        row_2021 = annual_reports[annual_reports.index.year == 2021]
        self.assertEqual(row_2021["totalCurrentAssets"].iloc[0], 440000)

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_balance_sheet_years_limit(self, mock_ticker):
        """Test that annual reports are trimmed to the requested years."""
        # GIVEN
        mock_stock = MagicMock()

        annual_dates = pd.to_datetime(["2023-12-31", "2022-12-31", "2021-12-31", "2020-12-31"])
        annual_data = pd.DataFrame(
            {"Current Assets": [500000, 450000, 400000, 350000]}, index=annual_dates
        ).T

        mock_stock.balance_sheet = annual_data
        mock_stock.quarterly_balance_sheet = None
        mock_ticker.return_value = mock_stock

        # WHEN — request only 2 years
        result = yf_api.get_yfinance_balance_sheet("AAPL", years=2)

        # THEN
        self.assertEqual(len(result["annualReports"]), 2)

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_cash_flow(self, mock_ticker):
        """Test get_yfinance_cash_flow method."""
        # GIVEN
        mock_stock = MagicMock()

        # Create mock cash flow data in yfinance format (items as rows, dates as columns).
        # yfinance reports dividends paid as a negative outflow.
        dates = pd.to_datetime(["2023-12-31", "2022-12-31"])
        cashflow_data = pd.DataFrame(
            {"Net Income": [80000, 75000], "Cash Dividends Paid": [-70000, -65000]}, index=dates
        ).T

        mock_stock.cashflow = cashflow_data
        mock_stock.quarterly_cashflow = cashflow_data
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.get_yfinance_cash_flow("AAPL")

        # THEN
        self.assertIsInstance(result, dict)
        self.assertIn("annualReports", result)
        self.assertIn("quarterlyReports", result)
        # Columns are remapped to the alphavantage names the report code consumes
        self.assertIn("netIncome", result["annualReports"].columns)
        self.assertIn("dividendPayout", result["annualReports"].columns)
        # dividendPayout is normalized to a positive amount to match alphavantage semantics
        self.assertEqual(result["annualReports"]["dividendPayout"].iloc[-1], 70000)
        mock_ticker.assert_called_once_with("AAPL")

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_cash_flow_quarterly_aggregation(self, mock_ticker):
        """Test that quarterly cash flow is aggregated into extra annual periods."""
        # GIVEN
        mock_stock = MagicMock()

        # Annual data covers 2023 and 2022
        annual_dates = pd.to_datetime(["2023-12-31", "2022-12-31"])
        # Columns as rows, dates as columns (yfinance raw format before .T)
        annual_cashflow = pd.DataFrame(
            {"Net Income": [80000, 75000], "Cash Dividends Paid": [-70000, -65000]}, index=annual_dates
        ).T

        # Quarterly data covers Q4 2021 through Q3 2022 — includes 4 quarters for 2021
        quarterly_dates = pd.to_datetime(["2022-09-30", "2022-06-30", "2022-03-31", "2021-12-31",
                                          "2021-09-30", "2021-06-30", "2021-03-31"])
        quarterly_cashflow = pd.DataFrame(
            {
                "Net Income": [20000, 19000, 18000, 17000, 16000, 15000, 14000],
                "Cash Dividends Paid": [-18000, -17000, -16000, -15000, -14000, -13000, -12000],
            },
            index=quarterly_dates,
        ).T

        mock_stock.cashflow = annual_cashflow
        mock_stock.quarterly_cashflow = quarterly_cashflow
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.get_yfinance_cash_flow("AAPL", years=10)

        # THEN — should have 2021 aggregated from quarterly in addition to 2022, 2023
        annual_reports = result["annualReports"]
        self.assertGreater(len(annual_reports), 2)
        annual_years = set(annual_reports.index.year)
        self.assertIn(2021, annual_years)

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_cash_flow_years_limit(self, mock_ticker):
        """Test that annual reports are trimmed to the requested years."""
        # GIVEN
        mock_stock = MagicMock()

        annual_dates = pd.to_datetime(["2023-12-31", "2022-12-31", "2021-12-31", "2020-12-31"])
        annual_cashflow = pd.DataFrame(
            {"Net Income": [80000, 75000, 70000, 65000]}, index=annual_dates
        ).T

        mock_stock.cashflow = annual_cashflow
        mock_stock.quarterly_cashflow = None
        mock_ticker.return_value = mock_stock

        # WHEN — request only 2 years
        result = yf_api.get_yfinance_cash_flow("AAPL", years=2)

        # THEN
        self.assertEqual(len(result["annualReports"]), 2)

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_earnings(self, mock_ticker):
        """Test get_yfinance_earnings uses get_earnings_dates for extended history."""
        # GIVEN
        mock_stock = MagicMock()

        # Create mock earnings_dates data (8 quarters = 2 complete years)
        announcement_dates = pd.to_datetime([
            "2024-02-01", "2023-10-26", "2023-07-27", "2023-04-27",
            "2023-02-02", "2022-10-27", "2022-07-28", "2022-04-28",
        ])
        earnings_dates_data = pd.DataFrame(
            {
                "EPS Estimate": [2.10, 1.39, 1.19, 1.52, 1.94, 1.27, 1.16, 1.43],
                "Reported EPS": [2.18, 1.46, 1.26, 1.52, 1.88, 1.29, 1.20, 1.52],
                "Surprise(%)": [3.8, 5.0, 5.9, 0.0, -3.1, 1.6, 3.4, 6.3],
            },
            index=announcement_dates,
        )

        mock_stock.get_earnings_dates.return_value = earnings_dates_data
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.get_yfinance_earnings("AAPL")

        # THEN
        self.assertIsInstance(result, dict)
        self.assertIn("annualEarnings", result)
        self.assertIn("quarterlyEarnings", result)
        self.assertIsNotNone(result["quarterlyEarnings"])
        self.assertEqual(len(result["quarterlyEarnings"]), 8)
        self.assertIn("reportedEPS", result["quarterlyEarnings"].columns)
        # Annual earnings should aggregate 4 quarters per year
        self.assertIsNotNone(result["annualEarnings"])
        self.assertIn("reportedEPS", result["annualEarnings"].columns)
        mock_stock.get_earnings_dates.assert_called_once_with(limit=20)

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_earnings_custom_years(self, mock_ticker):
        """Test get_yfinance_earnings with custom years parameter."""
        # GIVEN
        mock_stock = MagicMock()
        mock_stock.get_earnings_dates.return_value = pd.DataFrame()
        mock_stock.earnings = None
        mock_stock.quarterly_earnings = None
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.get_yfinance_earnings("AAPL", years=10)

        # THEN — no data available yields empty DataFrames (matching sibling get_yfinance_* helpers)
        mock_stock.get_earnings_dates.assert_called_once_with(limit=40)
        self.assertTrue(result["annualEarnings"].empty)
        self.assertTrue(result["quarterlyEarnings"].empty)

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_earnings_fallback(self, mock_ticker):
        """Test get_yfinance_earnings falls back to stock.earnings on failure."""
        # GIVEN
        mock_stock = MagicMock()
        mock_stock.get_earnings_dates.side_effect = Exception("API error")

        dates = pd.to_datetime(["2023-12-31", "2022-12-31"])
        earnings_data = pd.DataFrame({"Revenue": [100000, 95000], "Earnings": [20000, 18000]}, index=dates)
        mock_stock.earnings = earnings_data
        mock_stock.quarterly_earnings = earnings_data
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.get_yfinance_earnings("AAPL")

        # THEN
        self.assertIsInstance(result, dict)
        self.assertIn("annualEarnings", result)
        self.assertIn("quarterlyEarnings", result)
        self.assertIsNotNone(result["annualEarnings"])
        self.assertIn("reportedEPS", result["annualEarnings"].columns)

    def test_earnings_from_dates_builds_quarterly_and_annual(self):
        """_earnings_from_dates builds quarterly rows and aggregates complete fiscal years."""
        # GIVEN 8 quarters spanning two complete fiscal years
        stock = MagicMock()
        announcement_dates = pd.to_datetime([
            "2024-02-01", "2023-10-26", "2023-07-27", "2023-04-27",
            "2023-02-02", "2022-10-27", "2022-07-28", "2022-04-28",
        ])
        stock.get_earnings_dates.return_value = pd.DataFrame(
            {
                "EPS Estimate": [2.10, 1.39, 1.19, 1.52, 1.94, 1.27, 1.16, 1.43],
                "Reported EPS": [2.18, 1.46, 1.26, 1.52, 1.88, 1.29, 1.20, 1.52],
                "Surprise(%)": [3.8, 5.0, 5.9, 0.0, -3.1, 1.6, 3.4, 6.3],
            },
            index=announcement_dates,
        )

        # WHEN
        result = yf_api._earnings_from_dates(stock, 5)

        # THEN
        stock.get_earnings_dates.assert_called_once_with(limit=20)
        self.assertEqual(len(result["quarterlyEarnings"]), 8)
        self.assertIn("reportedEPS", result["quarterlyEarnings"].columns)
        self.assertIsNotNone(result["annualEarnings"])
        self.assertIn("reportedEPS", result["annualEarnings"].columns)
        # Two complete fiscal years, summed per year (announcements shifted back ~2 months):
        # FY2022 = 1.88+1.29+1.20+1.52 = 5.89, FY2023 = 2.18+1.46+1.26+1.52 = 6.42
        self.assertEqual(len(result["annualEarnings"]), 2)
        self.assertAlmostEqual(result["annualEarnings"]["reportedEPS"].iloc[0], 5.89)
        self.assertAlmostEqual(result["annualEarnings"]["reportedEPS"].iloc[1], 6.42)

    def test_earnings_from_dates_no_annual_when_year_incomplete(self):
        """_earnings_from_dates sets quarterly but leaves annual empty when a year lacks 4 quarters."""
        # GIVEN only 3 quarters (one incomplete fiscal year); also no EPS Estimate/Surprise columns
        stock = MagicMock()
        dates = pd.to_datetime(["2023-10-26", "2023-07-27", "2023-04-27"])
        stock.get_earnings_dates.return_value = pd.DataFrame(
            {"Reported EPS": [1.46, 1.26, 1.52]}, index=dates,
        )

        # WHEN
        result = yf_api._earnings_from_dates(stock, 5)

        # THEN quarterly is populated but annual aggregation is skipped (empty, not None)
        self.assertIsNotNone(result)
        self.assertEqual(len(result["quarterlyEarnings"]), 3)
        self.assertTrue(result["annualEarnings"].empty)

    def test_earnings_from_dates_returns_none_when_empty(self):
        """_earnings_from_dates returns None when get_earnings_dates yields no rows."""
        stock = MagicMock()
        stock.get_earnings_dates.return_value = pd.DataFrame()
        self.assertIsNone(yf_api._earnings_from_dates(stock, 5))

    def test_earnings_from_dates_returns_none_when_no_reported_eps(self):
        """_earnings_from_dates returns None when no row has a reported EPS."""
        stock = MagicMock()
        dates = pd.to_datetime(["2024-05-01", "2024-08-01"])
        stock.get_earnings_dates.return_value = pd.DataFrame(
            {"EPS Estimate": [1.0, 1.1], "Reported EPS": [float("nan"), float("nan")]},
            index=dates,
        )
        self.assertIsNone(yf_api._earnings_from_dates(stock, 5))

    def test_earnings_from_basic_builds_from_earnings(self):
        """_earnings_from_basic maps the Earnings column onto reportedEPS."""
        # GIVEN basic annual and quarterly earnings frames
        stock = MagicMock()
        dates = pd.to_datetime(["2023-12-31", "2022-12-31"])
        earnings = pd.DataFrame({"Revenue": [100000, 95000], "Earnings": [20000, 18000]}, index=dates)
        stock.earnings = earnings
        stock.quarterly_earnings = earnings

        # WHEN
        result = yf_api._earnings_from_basic(stock)

        # THEN
        self.assertIsNotNone(result["annualEarnings"])
        self.assertIn("reportedEPS", result["annualEarnings"].columns)
        self.assertIsNotNone(result["quarterlyEarnings"])
        self.assertIn("reportedEPS", result["quarterlyEarnings"].columns)

    def test_earnings_from_basic_returns_empty_values_when_missing(self):
        """_earnings_from_basic leaves values as empty DataFrames when no basic earnings exist."""
        stock = MagicMock()
        stock.earnings = None
        stock.quarterly_earnings = None

        result = yf_api._earnings_from_basic(stock)

        self.assertTrue(result["annualEarnings"].empty)
        self.assertTrue(result["quarterlyEarnings"].empty)

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_yfinance_company_prices(self, mock_ticker):
        """Test get_yfinance_company_prices method."""
        # GIVEN
        mock_stock = MagicMock()

        # Create mock price data
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        price_data = pd.DataFrame(
            {
                "Open": [150.0, 151.0, 152.0, 153.0, 154.0],
                "High": [152.0, 153.0, 154.0, 155.0, 156.0],
                "Low": [149.0, 150.0, 151.0, 152.0, 153.0],
                "Close": [151.0, 152.0, 153.0, 154.0, 155.0],
                "Volume": [1000000, 1100000, 1200000, 1300000, 1400000],
                "Dividends": [0, 0, 0, 0, 0],
                "Stock Splits": [0, 0, 0, 0, 0],
            },
            index=dates,
        )

        mock_stock.history.return_value = price_data
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.get_yfinance_company_prices("AAPL")

        # THEN
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("open", result.columns)
        self.assertIn("high", result.columns)
        self.assertIn("low", result.columns)
        self.assertIn("close", result.columns)
        self.assertIn("volume", result.columns)
        self.assertIn("ticker", result.columns)
        self.assertIn("SMA20", result.columns)
        self.assertIn("log_return", result.columns)
        mock_ticker.assert_called_once_with("AAPL")

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_get_daily_yfinance_company_prices(self, mock_ticker):
        """Test get_daily_yfinance_company_prices method."""
        # GIVEN
        mock_stock = MagicMock()

        # Create mock price data
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        price_data = pd.DataFrame(
            {
                "Open": [150.0, 151.0, 152.0, 153.0, 154.0],
                "High": [152.0, 153.0, 154.0, 155.0, 156.0],
                "Low": [149.0, 150.0, 151.0, 152.0, 153.0],
                "Close": [151.0, 152.0, 153.0, 154.0, 155.0],
                "Volume": [1000000, 1100000, 1200000, 1300000, 1400000],
                "Dividends": [0, 0, 0, 0, 0],
                "Stock Splits": [0, 0, 0, 0, 0],
            },
            index=dates,
        )

        mock_stock.history.return_value = price_data
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.get_daily_yfinance_company_prices("AAPL")

        # THEN
        self.assertIsInstance(result, pd.DataFrame)
        mock_ticker.assert_called_once_with("AAPL")
        # Verify history was called with correct parameters
        mock_stock.history.assert_called_once_with(period="5y", interval="1d")

    def test_get_yfinance_data(self):
        """Test get_yfinance_data method."""
        # WHEN
        result = yf_api.get_finance_data("AAPL")

        # THEN
        # This should return a yfinance Ticker object
        # We're just testing that it doesn't raise an exception
        self.assertIsNotNone(result)

    @patch("warren_bot.yfinance_integration.pd.DataFrame.to_pickle")
    @patch("warren_bot.yfinance_integration.get_daily_yfinance_company_prices")
    def test_download_stocks(self, mock_get_prices, mock_to_pickle):
        """Test download_stocks method."""
        # GIVEN
        mock_price_data = pd.DataFrame(
            {
                "open": [150.0, 151.0],
                "high": [152.0, 153.0],
                "low": [149.0, 150.0],
                "close": [151.0, 152.0],
                "volume": [1000000, 1100000],
                "ticker": ["AAPL", "AAPL"],
            }
        )
        mock_get_prices.return_value = mock_price_data

        stocks = ["AAPL", "GOOGL"]

        # WHEN
        result = asyncio.run(yf_api.download_stocks(stocks))

        # THEN
        self.assertIsInstance(result, pd.DataFrame)
        # Should be called for each ticker
        self.assertEqual(mock_get_prices.call_count, 2)
        mock_to_pickle.assert_called_once()

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_process_yfinance_annual_company_info(self, mock_ticker):
        """Test process_yfinance_annual_company_info method."""
        # GIVEN
        mock_stock = MagicMock()

        annual_dates = pd.to_datetime(["2023-12-31", "2022-12-31"])
        income_data = pd.DataFrame(
            {"Total Revenue": [100000, 95000], "Net Income": [20000, 18000]}, index=annual_dates
        ).T
        balance_data = pd.DataFrame(
            {"Ordinary Shares Number": [10000, 10000]}, index=annual_dates
        ).T

        mock_stock.financials = income_data
        mock_stock.balance_sheet = balance_data
        mock_stock.quarterly_financials = None
        mock_stock.quarterly_balance_sheet = None
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.process_yfinance_annual_company_info("AAPL")

        # THEN
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("ticker", result.columns)
        self.assertIn("revenue", result.columns)
        self.assertIn("eps", result.columns)
        self.assertIn("shares_outstanding", result.columns)
        self.assertEqual(len(result), 2)
        # EPS should be Net Income / Shares Outstanding
        self.assertAlmostEqual(result["eps"].iloc[-1], 20000 / 10000)

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_process_yfinance_annual_company_info_quarterly_extension(self, mock_ticker):
        """Test that quarterly data extends annual company info beyond ~4 years."""
        # GIVEN
        mock_stock = MagicMock()

        # Annual data covers 2023 and 2022
        annual_dates = pd.to_datetime(["2023-12-31", "2022-12-31"])
        income_data = pd.DataFrame(
            {"Total Revenue": [100000, 95000], "Net Income": [20000, 18000]}, index=annual_dates
        ).T
        balance_data = pd.DataFrame(
            {"Ordinary Shares Number": [10000, 10000]}, index=annual_dates
        ).T

        # Quarterly data covers 4 quarters of 2021
        quarterly_dates = pd.to_datetime([
            "2022-09-30", "2022-06-30", "2022-03-31", "2021-12-31",
            "2021-09-30", "2021-06-30", "2021-03-31",
        ])
        quarterly_income = pd.DataFrame(
            {"Total Revenue": [26000, 25000, 24000, 23000, 22000, 21000, 20000],
             "Net Income": [5200, 5000, 4800, 4600, 4400, 4200, 4000]},
            index=quarterly_dates,
        ).T
        quarterly_balance = pd.DataFrame(
            {"Ordinary Shares Number": [10000, 10000, 10000, 9500, 9500, 9500, 9500]},
            index=quarterly_dates,
        ).T

        mock_stock.financials = income_data
        mock_stock.balance_sheet = balance_data
        mock_stock.quarterly_financials = quarterly_income
        mock_stock.quarterly_balance_sheet = quarterly_balance
        mock_ticker.return_value = mock_stock

        # WHEN
        result = yf_api.process_yfinance_annual_company_info("AAPL", years=10)

        # THEN — should have 2021 in addition to 2022, 2023
        self.assertGreater(len(result), 2)
        result_years = set(result.index.year)
        self.assertIn(2021, result_years)

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_process_yfinance_annual_company_info_years_limit(self, mock_ticker):
        """Test that company info is trimmed to the requested years."""
        # GIVEN
        mock_stock = MagicMock()

        annual_dates = pd.to_datetime(["2023-12-31", "2022-12-31", "2021-12-31", "2020-12-31"])
        income_data = pd.DataFrame(
            {"Total Revenue": [100000, 95000, 90000, 85000], "Net Income": [20000, 18000, 16000, 14000]},
            index=annual_dates,
        ).T
        balance_data = pd.DataFrame(
            {"Ordinary Shares Number": [10000, 10000, 10000, 10000]}, index=annual_dates
        ).T

        mock_stock.financials = income_data
        mock_stock.balance_sheet = balance_data
        mock_stock.quarterly_financials = None
        mock_stock.quarterly_balance_sheet = None
        mock_ticker.return_value = mock_stock

        # WHEN — request only 2 years
        result = yf_api.process_yfinance_annual_company_info("AAPL", years=2)

        # THEN
        self.assertEqual(len(result), 2)

    def test_supplement_income_with_quarters_adds_complete_year(self):
        """_supplement_income_with_quarters sums 4 quarters for a fiscal year missing from annual."""
        # GIVEN annual covers 2023/2022; quarterly provides a complete 2021
        income_stmt = pd.DataFrame(
            {"Total Revenue": [100000, 95000], "Net Income": [20000, 18000]},
            index=pd.to_datetime(["2023-12-31", "2022-12-31"]),
        )
        q_dates = pd.to_datetime(["2021-12-31", "2021-09-30", "2021-06-30", "2021-03-31"])
        quarterly_income = pd.DataFrame(
            {"Total Revenue": [23000, 22000, 21000, 20000], "Net Income": [4600, 4400, 4200, 4000]},
            index=q_dates,
        ).T

        # WHEN
        result = yf_api._supplement_income_with_quarters(income_stmt, quarterly_income)

        # THEN 2021 is appended with summed quarterly figures
        self.assertIn(pd.Timestamp("2021-12-31"), result.index)
        self.assertAlmostEqual(result.loc[pd.Timestamp("2021-12-31"), "Total Revenue"], 86000)
        self.assertAlmostEqual(result.loc[pd.Timestamp("2021-12-31"), "Net Income"], 17200)

    def test_supplement_income_with_quarters_skips_incomplete_year(self):
        """_supplement_income_with_quarters ignores a fiscal year with fewer than 4 quarters."""
        income_stmt = pd.DataFrame(
            {"Total Revenue": [100000], "Net Income": [20000]},
            index=pd.to_datetime(["2023-12-31"]),
        )
        q_dates = pd.to_datetime(["2021-09-30", "2021-06-30", "2021-03-31"])  # only 3 quarters
        quarterly_income = pd.DataFrame(
            {"Total Revenue": [22000, 21000, 20000], "Net Income": [4400, 4200, 4000]},
            index=q_dates,
        ).T

        result = yf_api._supplement_income_with_quarters(income_stmt, quarterly_income)

        self.assertNotIn(pd.Timestamp("2021-12-31"), result.index)
        self.assertEqual(len(result), 1)

    def test_supplement_income_with_quarters_skips_year_already_annual(self):
        """_supplement_income_with_quarters does not re-add a fiscal year already in the annual data."""
        income_stmt = pd.DataFrame(
            {"Total Revenue": [100000], "Net Income": [20000]},
            index=pd.to_datetime(["2023-12-31"]),
        )
        # 4 complete quarters for 2023 — but 2023 is already covered by the annual statement
        q_dates = pd.to_datetime(["2023-12-31", "2023-09-30", "2023-06-30", "2023-03-31"])
        quarterly_income = pd.DataFrame(
            {"Total Revenue": [26000, 25000, 24000, 23000], "Net Income": [5200, 5000, 4800, 4600]},
            index=q_dates,
        ).T

        result = yf_api._supplement_income_with_quarters(income_stmt, quarterly_income)

        # THEN the existing 2023 row is left as-is, not duplicated or overwritten with the quarterly sum
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result.loc[pd.Timestamp("2023-12-31"), "Total Revenue"], 100000)

    def test_supplement_income_with_quarters_none_returns_unchanged(self):
        """_supplement_income_with_quarters returns the input untouched when no quarterly data."""
        income_stmt = pd.DataFrame({"Total Revenue": [100000]}, index=pd.to_datetime(["2023-12-31"]))
        self.assertIs(yf_api._supplement_income_with_quarters(income_stmt, None), income_stmt)

    def test_supplement_balance_with_quarters_adds_latest_snapshot(self):
        """_supplement_balance_with_quarters uses the most recent quarter snapshot for a missing year."""
        balance_sheet = pd.DataFrame(
            {"Ordinary Shares Number": [10000, 10000]},
            index=pd.to_datetime(["2023-12-31", "2022-12-31"]),
        )
        q_dates = pd.to_datetime(["2021-12-31", "2021-09-30", "2021-06-30", "2021-03-31"])
        quarterly_balance = pd.DataFrame(
            {"Ordinary Shares Number": [9500, 9400, 9300, 9200]},
            index=q_dates,
        ).T

        result = yf_api._supplement_balance_with_quarters(balance_sheet, quarterly_balance)

        # THEN the latest 2021 quarter (2021-12-31 → 9500) is used, not a sum
        self.assertIn(pd.Timestamp("2021-12-31"), result.index)
        self.assertEqual(result.loc[pd.Timestamp("2021-12-31"), "Ordinary Shares Number"], 9500)

    def test_supplement_balance_with_quarters_none_returns_unchanged(self):
        """_supplement_balance_with_quarters returns the input untouched when no quarterly data."""
        balance_sheet = pd.DataFrame({"Ordinary Shares Number": [10000]}, index=pd.to_datetime(["2023-12-31"]))
        self.assertIs(yf_api._supplement_balance_with_quarters(balance_sheet, None), balance_sheet)

    def test_extract_financial_metrics_computes_eps(self):
        """_extract_financial_metrics returns revenue, shares, and EPS = net income / shares."""
        dates = pd.to_datetime(["2023-12-31", "2022-12-31"])
        income_stmt = pd.DataFrame(
            {"Total Revenue": [100000, 95000], "Net Income": [20000, 18000]}, index=dates,
        )
        balance_sheet = pd.DataFrame({"Ordinary Shares Number": [10000, 9000]}, index=dates)

        revenue, eps, shares = yf_api._extract_financial_metrics(income_stmt, balance_sheet, dates)

        self.assertAlmostEqual(revenue[0], 100000)
        self.assertAlmostEqual(shares[1], 9000)
        self.assertAlmostEqual(eps[0], 20000 / 10000)
        self.assertAlmostEqual(eps[1], 18000 / 9000)

    def test_extract_financial_metrics_missing_columns_yield_nan(self):
        """_extract_financial_metrics yields NaN when required columns are absent."""
        dates = pd.to_datetime(["2023-12-31"])
        income_stmt = pd.DataFrame({"Some Other Field": [1]}, index=dates)  # no Total Revenue/Net Income
        balance_sheet = pd.DataFrame({"Some Field": [1]}, index=dates)  # no shares columns

        revenue, eps, shares = yf_api._extract_financial_metrics(income_stmt, balance_sheet, dates)

        self.assertTrue(pd.isna(revenue[0]))
        self.assertTrue(pd.isna(eps[0]))
        self.assertTrue(pd.isna(shares[0]))

    @patch("warren_bot.yfinance_integration.yf.Ticker")
    def test_empty_data_handling(self, mock_ticker):
        """Test handling of empty data from yfinance."""
        # GIVEN
        mock_stock = MagicMock()
        mock_stock.info = None
        mock_stock.financials = None
        mock_stock.balance_sheet = None
        mock_stock.cashflow = None
        mock_stock.earnings = None
        mock_stock.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_stock

        # WHEN & THEN
        overview = yf_api.get_yfinance_overview("INVALID")
        self.assertIsInstance(overview, pd.Series)
        self.assertTrue(overview.empty)

        income = yf_api.get_yfinance_income_statement("INVALID")
        self.assertIn("annualReports", income)
        self.assertIn("quarterlyReports", income)
        self.assertTrue(income["annualReports"].empty)
        self.assertTrue(income["quarterlyReports"].empty)

        prices = yf_api.get_yfinance_company_prices("INVALID")
        self.assertTrue(prices.empty)


if __name__ == "__main__":
    unittest.main()
