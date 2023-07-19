# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Test stock_report module for stock analysis."""
import unittest
import json
from warrenBot import alphavantage as alv

# under test
from warrenBot import stock_analysis


class StockAnalysisTestCase(unittest.TestCase):
    """Test Stock Analysis methods."""

    def test_record_of_stock(self):
        """Test successfull execution of record of stock method."""
        # GIVEN
        # Prepare files
        with open('./src/warrenBot/tests/IBM.earnings.json') as file:
            eps_data = json.load(file)
        with open('./src/warrenBot/tests/IBM.income_statement.json') as file:
            income_data = json.load(file)
        with open('./src/warrenBot/tests/IBM.daily_adjusted.json') as file:
            daily_data = json.load(file)
        with open('./src/warrenBot/tests/IBM.monthly_adjusted.json') as file:
            monthly_data = json.load(file)
        # Prepare data sources
        eps = alv.process_alphavantage_earnings(eps_data)
        income_statement = alv.process_alphavantage_income_statement(income_data)
        daily_prices = alv.process_alphavantage_company_prices(daily_data)
        monthly_prices = alv.process_alphavantage_company_prices(monthly_data)

        # WHEN
        msg, high_yield = stock_analysis.record_of_stock(eps,
                                                         income_statement,
                                                         daily_prices,
                                                         monthly_prices
                                                         )

        # THEN
        self.assertIsInstance(high_yield, float)
        self.assertIsInstance(msg, list)
        for chunk in msg:
            self.assertIsInstance(chunk, str)

    def test_trend(self):
        """Test successfull execution of trend method."""
        # GIVEN
        # Prepare files
        with open('./src/warrenBot/tests/IBM.income_statement.json') as file:
            income_data = json.load(file)
        with open('./src/warrenBot/tests/IBM.monthly_adjusted.json') as file:
            monthly_data = json.load(file)
        with open('./src/warrenBot/tests/IBM.earnings.json') as file:
            eps_data = json.load(file)
        # Prepare data sources
        eps = alv.process_alphavantage_earnings(eps_data)
        income_statement = alv.process_alphavantage_income_statement(income_data)
        monthly_prices = alv.process_alphavantage_company_prices(monthly_data)

        # WHEN
        msg, files = stock_analysis.trend(income_statement,
                                          eps,
                                          monthly_prices
                                          )

        # THEN
        self.assertIsInstance(msg, str)
        self.assertIsInstance(files, list)
        for file in files:
            self.assertIsInstance(file, str)

    def test_cash_position(self):
        """Test cash position printing module."""
        # GIVEN
        # Prepare files
        with open('./src/warrenBot/tests/IBM.balance_sheet.json') as file:
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
        with open('./src/warrenBot/tests/IBM.income_statement.json') as file:
            income_data = json.load(file)
        with open('./src/warrenBot/tests/IBM.daily_adjusted.json') as file:
            daily_data = json.load(file)
        with open('./src/warrenBot/tests/IBM.cash_flow.json') as file:
            cash_data = json.load(file)
        with open('./src/warrenBot/tests/IBM.earnings.json') as file:
            eps_data = json.load(file)
        with open('./src/warrenBot/tests/IBM.balance_sheet.json') as file:
            balance_data = json.load(file)

        # Prepare data sources
        income_statement = alv.process_alphavantage_income_statement(income_data)
        daily_prices = alv.process_alphavantage_company_prices(daily_data)
        cash_flow = alv.process_alphavantage_cash_flow(cash_data)
        earnings = alv.process_alphavantage_earnings(eps_data)
        balance_sheet = alv.process_alphavantage_balance_sheet(balance_data)

        # WHEN
        msg = stock_analysis.revenue_growth(daily_prices,
                                            cash_flow,
                                            income_statement,
                                            earnings['quarterlyEarnings']['reportedEPS'][-1],
                                            balance_sheet['annualReports']['commonStockSharesOutstanding'][-1])

        # THEN
        self.assertIsInstance(msg, str)

    def test_risk_reward(self):
        """Test cash position risk_reward module."""
        # GIVEN
        # Prepare files
        with open('./src/warrenBot/tests/IBM.income_statement.json') as file:
            income_data = json.load(file)
        with open('./src/warrenBot/tests/IBM.daily_adjusted.json') as file:
            daily_data = json.load(file)
        with open('./src/warrenBot/tests/IBM.monthly_adjusted.json') as file:
            monthly_data = json.load(file)
        with open('./src/warrenBot/tests/IBM.earnings.json') as file:
            eps_data = json.load(file)
        with open('./src/warrenBot/tests/IBM.balance_sheet.json') as file:
            balance_data = json.load(file)

        # Prepare data sources
        income_statement = alv.process_alphavantage_income_statement(income_data)
        daily_prices = alv.process_alphavantage_company_prices(daily_data)
        monthly_prices = alv.process_alphavantage_company_prices(monthly_data)
        earnings = alv.process_alphavantage_earnings(eps_data)
        balance_sheet = alv.process_alphavantage_balance_sheet(balance_data)

        # WHEN
        msg, charts = stock_analysis.risk_reward(daily_prices,
                                                 earnings,
                                                 monthly_prices,
                                                 income_statement,
                                                 earnings['quarterlyEarnings']['reportedEPS'][-1],  # stand in for highest EPS
                                                 balance_sheet['annualReports']['commonStockSharesOutstanding'][-1])
        # THEN
        self.assertIsInstance(msg, str)
        self.assertIsInstance(charts, list)
        for fig in charts:
            self.assertIsInstance(fig, str)


if __name__ == '__main__':
    unittest.main()
