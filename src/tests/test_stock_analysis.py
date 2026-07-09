# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Test stock_report module for stock analysis."""
import asyncio
import datetime
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from warren_bot import alphavantage as alv
# under test
from warren_bot import stock_analysis


# pylint: disable=E1136


class StockAnalysisTestCase(unittest.TestCase):
    """Test Stock Analysis methods."""

    def test_record_of_stock(self):
        """Test successfull execution of record of stock method."""
        # GIVEN
        # Prepare files
        with open("./src/tests/IBM.earnings.json", encoding="utf-8") as file:
            eps_data = json.load(file)
        with open("./src/tests/IBM.income_statement.json", encoding="utf-8") as file:
            income_data = json.load(file)
        with open("./src/tests/IBM.daily_adjusted.json", encoding="utf-8") as file:
            daily_data = json.load(file)
        with open("./src/tests/IBM.monthly_adjusted.json", encoding="utf-8") as file:
            monthly_data = json.load(file)
        # Prepare data sources
        eps = alv.process_alphavantage_earnings(eps_data)
        income_statement = alv.process_alphavantage_income_statement(income_data)
        daily_prices = alv.process_alphavantage_company_prices(daily_data)
        monthly_prices = alv.process_alphavantage_company_prices(monthly_data)

        # WHEN
        msg, high_yield = stock_analysis.record_of_stock(eps, income_statement, daily_prices, monthly_prices)

        # THEN
        self.assertIsInstance(high_yield, float)
        self.assertIsInstance(msg, list)
        for chunk in msg:
            self.assertIsInstance(chunk, str)

    def test_trend(self):
        """Test successfull execution of trend method."""
        # GIVEN
        # Prepare files
        with open("./src/tests/IBM.income_statement.json", encoding="utf-8") as file:
            income_data = json.load(file)
        with open("./src/tests/IBM.monthly_adjusted.json", encoding="utf-8") as file:
            monthly_data = json.load(file)
        with open("./src/tests/IBM.earnings.json", encoding="utf-8") as file:
            eps_data = json.load(file)
        # Prepare data sources
        eps = alv.process_alphavantage_earnings(eps_data)
        income_statement = alv.process_alphavantage_income_statement(income_data)
        monthly_prices = alv.process_alphavantage_company_prices(monthly_data)

        # WHEN
        msg, files = stock_analysis.trend(income_statement, eps, monthly_prices)

        # THEN
        self.assertIsInstance(msg, str)
        self.assertIsInstance(files, list)
        for file in files:
            self.assertIsInstance(file, str)

    def test_cash_position(self):
        """Test cash position printing module."""
        # GIVEN
        # Prepare files
        with open("./src/tests/IBM.balance_sheet.json", encoding="utf-8") as file:
            balance_data = json.load(file)
        # Prepare data sources
        balance_sheet = alv.process_alphavantage_balance_sheet(balance_data)

        # WHEN
        msg = stock_analysis.cash_position(balance_sheet)

        # THEN
        self.assertIsInstance(msg, list)
        for chunk in msg:
            self.assertIsInstance(chunk, str)

    def test_revenue_growth(self):
        """Test cash position revenue_growth module."""
        # GIVEN
        # Prepare files
        with open("./src/tests/IBM.income_statement.json", encoding="utf-8") as file:
            income_data = json.load(file)
        with open("./src/tests/IBM.daily_adjusted.json", encoding="utf-8") as file:
            daily_data = json.load(file)
        with open("./src/tests/IBM.cash_flow.json", encoding="utf-8") as file:
            cash_data = json.load(file)
        with open("./src/tests/IBM.earnings.json", encoding="utf-8") as file:
            eps_data = json.load(file)
        with open("./src/tests/IBM.balance_sheet.json", encoding="utf-8") as file:
            balance_data = json.load(file)

        # Prepare data sources
        income_statement = alv.process_alphavantage_income_statement(income_data)
        daily_prices = alv.process_alphavantage_company_prices(daily_data)
        cash_flow = alv.process_alphavantage_cash_flow(cash_data)
        earnings = alv.process_alphavantage_earnings(eps_data)
        balance_sheet = alv.process_alphavantage_balance_sheet(balance_data)

        # WHEN
        msg = stock_analysis.revenue_growth(
            daily_prices,
            cash_flow,
            income_statement,
            earnings["quarterlyEarnings"]["reportedEPS"][-1],
            balance_sheet["annualReports"]["commonStockSharesOutstanding"][-1],
        )

        # THEN
        self.assertIsInstance(msg, str)

    def test_risk_reward(self):
        """Test cash position risk_reward module."""
        # GIVEN
        # Prepare files
        with open("./src/tests/IBM.income_statement.json", encoding="utf-8") as file:
            income_data = json.load(file)
        with open("./src/tests/IBM.daily_adjusted.json", encoding="utf-8") as file:
            daily_data = json.load(file)
        with open("./src/tests/IBM.monthly_adjusted.json", encoding="utf-8") as file:
            monthly_data = json.load(file)
        with open("./src/tests/IBM.earnings.json", encoding="utf-8") as file:
            eps_data = json.load(file)
        # with open("./src/tests/IBM.balance_sheet.json", encoding="utf-8") as file:
        #     balance_data = json.load(file)

        # Prepare data sources
        income_statement = alv.process_alphavantage_income_statement(income_data)
        daily_prices = alv.process_alphavantage_company_prices(daily_data)
        monthly_prices = alv.process_alphavantage_company_prices(monthly_data)
        earnings = alv.process_alphavantage_earnings(eps_data)
        # balance_sheet = alv.process_alphavantage_balance_sheet(balance_data)

        # WHEN
        msg, charts = stock_analysis.risk_reward(
            daily_prices,
            earnings,
            monthly_prices,
            income_statement,
            earnings["quarterlyEarnings"]["reportedEPS"][-1],  # stand in for highest EPS
            # balance_sheet["annualReports"]["commonStockSharesOutstanding"][-1],
        )
        # THEN
        self.assertIsInstance(msg, str)
        self.assertIsInstance(charts, list)
        for fig in charts:
            self.assertIsInstance(fig, str)

    def test_run_calls_risk_reward_with_matching_signature(self):
        """run() must call risk_reward with an argument list its signature accepts.

        Regression: run() passed a 6th (shares-outstanding) argument to risk_reward(),
        which accepts only 5 parameters. Patching risk_reward with autospec=True enforces
        the real signature, so a mismatched call raises TypeError.
        """
        # GIVEN a message and every collaborator run() touches mocked out (no network)
        message = MagicMock()
        message.channel.send = AsyncMock()

        alpha_mock = MagicMock()
        for getter in (
            "get_alphavantage_income_statement",
            "get_alphavantage_balance_sheet",
            "get_alphavantage_earnings",
            "get_alphavantage_cash_flow",
            "get_monthly_alphavantage_company_prices",
            "get_daily_alphavantage_company_prices",
        ):
            setattr(alpha_mock, getter, AsyncMock(return_value=MagicMock()))

        utils_mock = MagicMock()
        utils_mock.send_message_in_chunks = AsyncMock()

        # WHEN / THEN run() completes without a signature TypeError
        with patch.object(stock_analysis, "alpha", alpha_mock), patch.object(
            stock_analysis, "utils", utils_mock
        ), patch.object(stock_analysis, "past_sales_records", MagicMock()), patch.object(
            stock_analysis, "past_eps", MagicMock()
        ), patch.object(
            stock_analysis, "record_of_stock", MagicMock(return_value=(["msg"], 5.0))
        ), patch.object(
            stock_analysis, "trend", MagicMock(return_value=("trend", []))
        ), patch.object(
            stock_analysis, "cash_position", MagicMock()
        ), patch.object(
            stock_analysis, "revenue_growth", MagicMock()
        ), patch.object(
            stock_analysis, "earnings_growth", MagicMock()
        ), patch.object(
            stock_analysis, "risk_reward", autospec=True
        ) as risk_reward_mock:
            risk_reward_mock.return_value = ("risk_reward", [])
            asyncio.run(stock_analysis.run(message, "IBM"))

        risk_reward_mock.assert_called_once()

    def test_epoch_seconds(self):
        """_epoch_seconds converts each datetime to its UNIX epoch seconds."""
        # GIVEN
        times = [datetime.datetime(2020, 1, 1), datetime.datetime(2021, 6, 15, 12, 30)]

        # WHEN
        result = stock_analysis._epoch_seconds(times)

        # THEN
        self.assertEqual(result, [moment.timestamp() for moment in times])

    def test_epoch_seconds_empty(self):
        """_epoch_seconds returns an empty list for empty input."""
        self.assertEqual(stock_analysis._epoch_seconds([]), [])

    def test_predict_values(self):
        """_predict_values evaluates the prediction at each time's epoch seconds."""
        # GIVEN a prediction that marks its input so we can prove it saw epoch seconds
        def prediction(seconds):
            return seconds + 1

        times = [datetime.datetime(2020, 1, 1), datetime.datetime(2022, 3, 10)]

        # WHEN
        result = stock_analysis._predict_values(prediction, times)

        # THEN
        self.assertEqual(result, [moment.timestamp() + 1 for moment in times])

    def test_zone_analysis_success(self):
        """_zone_analysis returns the predict_low fragment and the up/down ratio."""
        # WHEN high > low and prices are numeric
        fragment, ratio = stock_analysis._zone_analysis(100.0, 40.0, 60.0)

        # THEN
        self.assertIsInstance(fragment, str)
        self.assertTrue(fragment.startswith("```Lower"))
        self.assertAlmostEqual(ratio, (100.0 - 60.0) / (60.0 - 40.0))

    def test_zone_analysis_type_error_returns_zero_ratio(self):
        """A None projected_low makes predict_low raise TypeError -> error fragment, 0 ratio."""
        # WHEN
        fragment, ratio = stock_analysis._zone_analysis(100.0, None, 60.0)

        # THEN
        self.assertIsInstance(fragment, str)
        self.assertTrue(fragment.startswith("```"))
        self.assertEqual(ratio, 0)

    def test_zone_analysis_assertion_error_returns_nan(self):
        """When high <= low predict_low asserts -> NaN fragment, 0 ratio."""
        # WHEN forcast high is below the projected low
        fragment, ratio = stock_analysis._zone_analysis(40.0, 100.0, 60.0)

        # THEN
        self.assertEqual(fragment, "```NaN```")
        self.assertEqual(ratio, 0)


if __name__ == "__main__":
    unittest.main()
