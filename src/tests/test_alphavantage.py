# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Unit testing module for the alphavantage module."""
import unittest
import pandas as pd
import json

from warren_bot import alphavantage as alpha


class AlphavantageTestCase(unittest.TestCase):
    """Test Alphavantage methods."""

    def test_process_income_statement(self):
        """Test process income_statement method."""
        # GIVEN
        # Build IBM JSON from file
        with open('./src/tests/IBM.income_statement.json') as file:
            data = json.load(file)

        # WHEN
        ic_statement = alpha.process_alphavantage_income_statement(data)

        # THEN
        self.assertIsInstance(ic_statement, dict)
        self.assertIsInstance(ic_statement['annualReports'], pd.DataFrame)
        self.assertIsInstance(ic_statement['quarterlyReports'], pd.DataFrame)
        # Check oldest date is first record
        self.assertGreater(ic_statement['annualReports'].index[-1],
                           ic_statement['annualReports'].index[0])
        # Check oldest date is first record
        self.assertGreater(ic_statement['quarterlyReports'].index[-1],
                           ic_statement['quarterlyReports'].index[0])
        # Check structure of annualReports
        self.assertIn('grossProfit', ic_statement['annualReports'].keys())
        self.assertIn('totalRevenue', ic_statement['annualReports'].keys())
        self.assertIn('costOfRevenue', ic_statement['annualReports'].keys())
        self.assertIn('costofGoodsAndServicesSold', ic_statement['annualReports'].keys())
        self.assertIn('operatingIncome', ic_statement['annualReports'].keys())
        self.assertIn('sellingGeneralAndAdministrative', ic_statement['annualReports'].keys())
        self.assertIn('researchAndDevelopment', ic_statement['annualReports'].keys())
        self.assertIn('operatingExpenses', ic_statement['annualReports'].keys())
        self.assertIn('investmentIncomeNet', ic_statement['annualReports'].keys())
        self.assertIn('netInterestIncome', ic_statement['annualReports'].keys())
        self.assertIn('interestIncome', ic_statement['annualReports'].keys())
        self.assertIn('interestExpense', ic_statement['annualReports'].keys())
        self.assertIn('nonInterestIncome', ic_statement['annualReports'].keys())
        self.assertIn('otherNonOperatingIncome', ic_statement['annualReports'].keys())
        self.assertIn('depreciation', ic_statement['annualReports'].keys())
        self.assertIn('depreciationAndAmortization', ic_statement['annualReports'].keys())
        self.assertIn('incomeBeforeTax', ic_statement['annualReports'].keys())
        self.assertIn('incomeTaxExpense', ic_statement['annualReports'].keys())
        self.assertIn('interestAndDebtExpense', ic_statement['annualReports'].keys())
        self.assertIn('netIncomeFromContinuingOperations', ic_statement['annualReports'].keys())
        self.assertIn('comprehensiveIncomeNetOfTax', ic_statement['annualReports'].keys())
        self.assertIn('ebit', ic_statement['annualReports'].keys())
        self.assertIn('ebitda', ic_statement['annualReports'].keys())
        self.assertIn('netIncome', ic_statement['annualReports'].keys())
        # Check structure of quarterlyReports
        self.assertIn('grossProfit', ic_statement['quarterlyReports'].keys())
        self.assertIn('totalRevenue', ic_statement['quarterlyReports'].keys())
        self.assertIn('costOfRevenue', ic_statement['quarterlyReports'].keys())
        self.assertIn('costofGoodsAndServicesSold', ic_statement['quarterlyReports'].keys())
        self.assertIn('operatingIncome', ic_statement['quarterlyReports'].keys())
        self.assertIn('sellingGeneralAndAdministrative', ic_statement['quarterlyReports'].keys())
        self.assertIn('researchAndDevelopment', ic_statement['quarterlyReports'].keys())
        self.assertIn('operatingExpenses', ic_statement['quarterlyReports'].keys())
        self.assertIn('investmentIncomeNet', ic_statement['quarterlyReports'].keys())
        self.assertIn('netInterestIncome', ic_statement['quarterlyReports'].keys())
        self.assertIn('interestIncome', ic_statement['quarterlyReports'].keys())
        self.assertIn('interestExpense', ic_statement['quarterlyReports'].keys())
        self.assertIn('nonInterestIncome', ic_statement['quarterlyReports'].keys())
        self.assertIn('otherNonOperatingIncome', ic_statement['quarterlyReports'].keys())
        self.assertIn('depreciation', ic_statement['quarterlyReports'].keys())
        self.assertIn('depreciationAndAmortization', ic_statement['quarterlyReports'].keys())
        self.assertIn('incomeBeforeTax', ic_statement['quarterlyReports'].keys())
        self.assertIn('incomeTaxExpense', ic_statement['quarterlyReports'].keys())
        self.assertIn('interestAndDebtExpense', ic_statement['quarterlyReports'].keys())
        self.assertIn('netIncomeFromContinuingOperations', ic_statement['quarterlyReports'].keys())
        self.assertIn('comprehensiveIncomeNetOfTax', ic_statement['quarterlyReports'].keys())
        self.assertIn('ebit', ic_statement['quarterlyReports'].keys())
        self.assertIn('ebitda', ic_statement['quarterlyReports'].keys())
        self.assertIn('netIncome', ic_statement['quarterlyReports'].keys())

    def test_process_earnings(self):
        """Test process earnings method."""
        # GIVEN
        # Build IBM JSON from file
        with open('./src/tests/IBM.earnings.json') as file:
            data = json.load(file)

        # WHEN
        earnings = alpha.process_alphavantage_earnings(data)

        # THEN
        self.assertIsInstance(earnings, dict)
        self.assertIsInstance(earnings['annualEarnings'], pd.DataFrame)
        self.assertIsInstance(earnings['quarterlyEarnings'], pd.DataFrame)
        # Check oldest date is first record
        self.assertGreater(earnings['annualEarnings'].index[-1],
                           earnings['annualEarnings'].index[0])
        # Check oldest date is first record
        self.assertGreater(earnings['quarterlyEarnings'].index[-1],
                           earnings['quarterlyEarnings'].index[0])
        # Check structure of annualEarnings
        self.assertIn('reportedEPS', earnings['annualEarnings'].keys())
        self.assertTrue(len(earnings['annualEarnings'].keys()) == 1)
        # Check structure of quarterlyEarnings
        self.assertIn('reportedEPS', earnings['quarterlyEarnings'].keys())
        self.assertIn('reportedDate', earnings['quarterlyEarnings'].keys())
        self.assertIn('estimatedEPS', earnings['quarterlyEarnings'].keys())
        self.assertIn('surprise', earnings['quarterlyEarnings'].keys())
        self.assertIn('surprisePercentage', earnings['quarterlyEarnings'].keys())

    def test_process_cash_flow(self):
        """Test process cash_flow method."""
        # GIVEN
        # Build IBM JSON from file
        with open('./src/tests/IBM.cash_flow.json') as file:
            data = json.load(file)

        # WHEN
        cash_flow = alpha.process_alphavantage_cash_flow(data)

        # THEN
        self.assertIsInstance(cash_flow, dict)
        self.assertIsInstance(cash_flow['annualReports'], pd.DataFrame)
        self.assertIsInstance(cash_flow['quarterlyReports'], pd.DataFrame)
        # Check oldest date is first record
        self.assertGreater(cash_flow['annualReports'].index[-1],
                           cash_flow['annualReports'].index[0])
        # Check oldest date is first record
        self.assertGreater(cash_flow['quarterlyReports'].index[-1],
                           cash_flow['quarterlyReports'].index[0])
        # Check structure of annualReports
        self.assertIn('operatingCashflow', cash_flow['annualReports'].keys())
        self.assertIn('paymentsForOperatingActivities', cash_flow['annualReports'].keys())
        self.assertIn('proceedsFromOperatingActivities', cash_flow['annualReports'].keys())
        self.assertIn('changeInOperatingLiabilities', cash_flow['annualReports'].keys())
        self.assertIn('changeInOperatingAssets', cash_flow['annualReports'].keys())
        self.assertIn('depreciationDepletionAndAmortization', cash_flow['annualReports'].keys())
        self.assertIn('capitalExpenditures', cash_flow['annualReports'].keys())
        self.assertIn('changeInReceivables', cash_flow['annualReports'].keys())
        self.assertIn('changeInInventory', cash_flow['annualReports'].keys())
        self.assertIn('profitLoss', cash_flow['annualReports'].keys())
        self.assertIn('cashflowFromInvestment', cash_flow['annualReports'].keys())
        self.assertIn('cashflowFromFinancing', cash_flow['annualReports'].keys())
        self.assertIn('proceedsFromRepaymentsOfShortTermDebt', cash_flow['annualReports'].keys())
        self.assertIn('paymentsForRepurchaseOfCommonStock', cash_flow['annualReports'].keys())
        self.assertIn('paymentsForRepurchaseOfEquity', cash_flow['annualReports'].keys())
        self.assertIn('paymentsForRepurchaseOfPreferredStock', cash_flow['annualReports'].keys())
        self.assertIn('dividendPayout', cash_flow['annualReports'].keys())
        self.assertIn('dividendPayoutCommonStock', cash_flow['annualReports'].keys())
        self.assertIn('dividendPayoutPreferredStock', cash_flow['annualReports'].keys())
        self.assertIn('proceedsFromIssuanceOfCommonStock', cash_flow['annualReports'].keys())
        self.assertIn('proceedsFromIssuanceOfLongTermDebtAndCapitalSecuritiesNet', cash_flow['annualReports'].keys())
        self.assertIn('proceedsFromIssuanceOfPreferredStock', cash_flow['annualReports'].keys())
        self.assertIn('proceedsFromRepurchaseOfEquity', cash_flow['annualReports'].keys())
        self.assertIn('proceedsFromSaleOfTreasuryStock', cash_flow['annualReports'].keys())
        self.assertIn('changeInCashAndCashEquivalents', cash_flow['annualReports'].keys())
        self.assertIn('changeInExchangeRate', cash_flow['annualReports'].keys())
        self.assertIn('netIncome', cash_flow['annualReports'].keys())
        # Check structure of quarterlyReports
        self.assertIn('operatingCashflow', cash_flow['quarterlyReports'].keys())
        self.assertIn('paymentsForOperatingActivities', cash_flow['quarterlyReports'].keys())
        self.assertIn('proceedsFromOperatingActivities', cash_flow['quarterlyReports'].keys())
        self.assertIn('changeInOperatingLiabilities', cash_flow['quarterlyReports'].keys())
        self.assertIn('changeInOperatingAssets', cash_flow['quarterlyReports'].keys())
        self.assertIn('depreciationDepletionAndAmortization', cash_flow['quarterlyReports'].keys())
        self.assertIn('capitalExpenditures', cash_flow['quarterlyReports'].keys())
        self.assertIn('changeInReceivables', cash_flow['quarterlyReports'].keys())
        self.assertIn('changeInInventory', cash_flow['quarterlyReports'].keys())
        self.assertIn('profitLoss', cash_flow['quarterlyReports'].keys())
        self.assertIn('cashflowFromInvestment', cash_flow['quarterlyReports'].keys())
        self.assertIn('cashflowFromFinancing', cash_flow['quarterlyReports'].keys())
        self.assertIn('proceedsFromRepaymentsOfShortTermDebt', cash_flow['quarterlyReports'].keys())
        self.assertIn('paymentsForRepurchaseOfCommonStock', cash_flow['quarterlyReports'].keys())
        self.assertIn('paymentsForRepurchaseOfEquity', cash_flow['quarterlyReports'].keys())
        self.assertIn('paymentsForRepurchaseOfPreferredStock', cash_flow['quarterlyReports'].keys())
        self.assertIn('dividendPayout', cash_flow['quarterlyReports'].keys())
        self.assertIn('dividendPayoutCommonStock', cash_flow['quarterlyReports'].keys())
        self.assertIn('dividendPayoutPreferredStock', cash_flow['quarterlyReports'].keys())
        self.assertIn('proceedsFromIssuanceOfCommonStock', cash_flow['quarterlyReports'].keys())
        self.assertIn('proceedsFromIssuanceOfLongTermDebtAndCapitalSecuritiesNet', cash_flow['quarterlyReports'].keys())
        self.assertIn('proceedsFromIssuanceOfPreferredStock', cash_flow['quarterlyReports'].keys())
        self.assertIn('proceedsFromRepurchaseOfEquity', cash_flow['quarterlyReports'].keys())
        self.assertIn('proceedsFromSaleOfTreasuryStock', cash_flow['quarterlyReports'].keys())
        self.assertIn('changeInCashAndCashEquivalents', cash_flow['quarterlyReports'].keys())
        self.assertIn('changeInExchangeRate', cash_flow['quarterlyReports'].keys())
        self.assertIn('netIncome', cash_flow['quarterlyReports'].keys())

    def test_process_balance_sheet(self):
        """Test process balance sheet method."""
        # GIVEN
        # Build IBM JSON from file
        with open('./src/tests/IBM.balance_sheet.json') as file:
            data = json.load(file)

        # WHEN
        balance_sheet = alpha.process_alphavantage_balance_sheet(data)

        # THEN
        self.assertIsInstance(balance_sheet, dict)
        self.assertIsInstance(balance_sheet['annualReports'], pd.DataFrame)
        self.assertIsInstance(balance_sheet['quarterlyReports'], pd.DataFrame)
        # Check oldest date is first record
        self.assertGreater(balance_sheet['annualReports'].index[-1],
                           balance_sheet['annualReports'].index[0])
        # Check oldest date is first record
        self.assertGreater(balance_sheet['quarterlyReports'].index[-1],
                           balance_sheet['quarterlyReports'].index[0])
        # Check structure of annualReports
        self.assertIn('reportedCurrency', balance_sheet['annualReports'].keys())
        self.assertIn('totalAssets', balance_sheet['annualReports'].keys())
        self.assertIn('totalCurrentAssets', balance_sheet['annualReports'].keys())
        self.assertIn('cashAndCashEquivalentsAtCarryingValue', balance_sheet['annualReports'].keys())
        self.assertIn('cashAndShortTermInvestments', balance_sheet['annualReports'].keys())
        self.assertIn('inventory', balance_sheet['annualReports'].keys())
        self.assertIn('currentNetReceivables', balance_sheet['annualReports'].keys())
        self.assertIn('totalNonCurrentAssets', balance_sheet['annualReports'].keys())
        self.assertIn('propertyPlantEquipment', balance_sheet['annualReports'].keys())
        self.assertIn('accumulatedDepreciationAmortizationPPE', balance_sheet['annualReports'].keys())
        self.assertIn('intangibleAssets', balance_sheet['annualReports'].keys())
        self.assertIn('intangibleAssetsExcludingGoodwill', balance_sheet['annualReports'].keys())
        self.assertIn('goodwill', balance_sheet['annualReports'].keys())
        self.assertIn('investments', balance_sheet['annualReports'].keys())
        self.assertIn('longTermInvestments', balance_sheet['annualReports'].keys())
        self.assertIn('shortTermInvestments', balance_sheet['annualReports'].keys())
        self.assertIn('otherCurrentAssets', balance_sheet['annualReports'].keys())
        self.assertIn('otherNonCurrentAssets', balance_sheet['annualReports'].keys())
        self.assertIn('totalLiabilities', balance_sheet['annualReports'].keys())
        self.assertIn('totalCurrentLiabilities', balance_sheet['annualReports'].keys())
        self.assertIn('currentAccountsPayable', balance_sheet['annualReports'].keys())
        self.assertIn('deferredRevenue', balance_sheet['annualReports'].keys())
        self.assertIn('currentDebt', balance_sheet['annualReports'].keys())
        self.assertIn('shortTermDebt', balance_sheet['annualReports'].keys())
        self.assertIn('totalNonCurrentLiabilities', balance_sheet['annualReports'].keys())
        self.assertIn('capitalLeaseObligations', balance_sheet['annualReports'].keys())
        self.assertIn('longTermDebt', balance_sheet['annualReports'].keys())
        self.assertIn('currentLongTermDebt', balance_sheet['annualReports'].keys())
        self.assertIn('longTermDebtNoncurrent', balance_sheet['annualReports'].keys())
        self.assertIn('shortLongTermDebtTotal', balance_sheet['annualReports'].keys())
        self.assertIn('otherCurrentLiabilities', balance_sheet['annualReports'].keys())
        self.assertIn('otherNonCurrentLiabilities', balance_sheet['annualReports'].keys())
        self.assertIn('totalShareholderEquity', balance_sheet['annualReports'].keys())
        self.assertIn('treasuryStock', balance_sheet['annualReports'].keys())
        self.assertIn('retainedEarnings', balance_sheet['annualReports'].keys())
        self.assertIn('commonStock', balance_sheet['annualReports'].keys())
        self.assertIn('commonStockSharesOutstanding', balance_sheet['annualReports'].keys())
        # Check structure of quarterlyReports
        self.assertIn('reportedCurrency', balance_sheet['quarterlyReports'].keys())
        self.assertIn('totalAssets', balance_sheet['quarterlyReports'].keys())
        self.assertIn('totalCurrentAssets', balance_sheet['quarterlyReports'].keys())
        self.assertIn('cashAndCashEquivalentsAtCarryingValue', balance_sheet['quarterlyReports'].keys())
        self.assertIn('cashAndShortTermInvestments', balance_sheet['quarterlyReports'].keys())
        self.assertIn('inventory', balance_sheet['quarterlyReports'].keys())
        self.assertIn('currentNetReceivables', balance_sheet['quarterlyReports'].keys())
        self.assertIn('totalNonCurrentAssets', balance_sheet['quarterlyReports'].keys())
        self.assertIn('propertyPlantEquipment', balance_sheet['quarterlyReports'].keys())
        self.assertIn('accumulatedDepreciationAmortizationPPE', balance_sheet['quarterlyReports'].keys())
        self.assertIn('intangibleAssets', balance_sheet['quarterlyReports'].keys())
        self.assertIn('intangibleAssetsExcludingGoodwill', balance_sheet['quarterlyReports'].keys())
        self.assertIn('goodwill', balance_sheet['quarterlyReports'].keys())
        self.assertIn('investments', balance_sheet['quarterlyReports'].keys())
        self.assertIn('longTermInvestments', balance_sheet['quarterlyReports'].keys())
        self.assertIn('shortTermInvestments', balance_sheet['quarterlyReports'].keys())
        self.assertIn('otherCurrentAssets', balance_sheet['quarterlyReports'].keys())
        self.assertIn('otherNonCurrentAssets', balance_sheet['quarterlyReports'].keys())
        self.assertIn('totalLiabilities', balance_sheet['quarterlyReports'].keys())
        self.assertIn('totalCurrentLiabilities', balance_sheet['quarterlyReports'].keys())
        self.assertIn('currentAccountsPayable', balance_sheet['quarterlyReports'].keys())
        self.assertIn('deferredRevenue', balance_sheet['quarterlyReports'].keys())
        self.assertIn('currentDebt', balance_sheet['quarterlyReports'].keys())
        self.assertIn('shortTermDebt', balance_sheet['quarterlyReports'].keys())
        self.assertIn('totalNonCurrentLiabilities', balance_sheet['quarterlyReports'].keys())
        self.assertIn('capitalLeaseObligations', balance_sheet['quarterlyReports'].keys())
        self.assertIn('longTermDebt', balance_sheet['quarterlyReports'].keys())
        self.assertIn('currentLongTermDebt', balance_sheet['quarterlyReports'].keys())
        self.assertIn('longTermDebtNoncurrent', balance_sheet['quarterlyReports'].keys())
        self.assertIn('shortLongTermDebtTotal', balance_sheet['quarterlyReports'].keys())
        self.assertIn('otherCurrentLiabilities', balance_sheet['quarterlyReports'].keys())
        self.assertIn('otherNonCurrentLiabilities', balance_sheet['quarterlyReports'].keys())
        self.assertIn('totalShareholderEquity', balance_sheet['quarterlyReports'].keys())
        self.assertIn('treasuryStock', balance_sheet['quarterlyReports'].keys())
        self.assertIn('retainedEarnings', balance_sheet['quarterlyReports'].keys())
        self.assertIn('commonStock', balance_sheet['quarterlyReports'].keys())
        self.assertIn('commonStockSharesOutstanding', balance_sheet['quarterlyReports'].keys())

    def test_process_overview(self):
        """Test process overview method."""
        # GIVEN
        # Build IBM JSON from file
        with open('./src/tests/IBM.company_overview.json') as file:
            data = json.load(file)

        # WHEN
        overview = alpha.process_alphavantage_overview(data)

        # THEN
        self.assertIsInstance(overview, pd.Series)
        # Check structure of quarterlyReports
        self.assertIn('CIK', overview.keys())
        self.assertIn('LatestQuarter', overview.keys())
        self.assertIn('MarketCapitalization', overview.keys())
        self.assertIn('EBITDA', overview.keys())
        self.assertIn('PERatio', overview.keys())
        self.assertIn('PEGRatio', overview.keys())
        self.assertIn('BookValue', overview.keys())
        self.assertIn('DividendPerShare', overview.keys())
        self.assertIn('DividendYield', overview.keys())
        self.assertIn('EPS', overview.keys())
        self.assertIn('RevenuePerShareTTM', overview.keys())
        self.assertIn('ProfitMargin', overview.keys())
        self.assertIn('OperatingMarginTTM', overview.keys())
        self.assertIn('ReturnOnAssetsTTM', overview.keys())
        self.assertIn('ReturnOnEquityTTM', overview.keys())
        self.assertIn('RevenueTTM', overview.keys())
        self.assertIn('GrossProfitTTM', overview.keys())
        self.assertIn('DilutedEPSTTM', overview.keys())
        self.assertIn('QuarterlyEarningsGrowthYOY', overview.keys())
        self.assertIn('QuarterlyRevenueGrowthYOY', overview.keys())
        self.assertIn('AnalystTargetPrice', overview.keys())
        self.assertIn('TrailingPE', overview.keys())
        self.assertIn('ForwardPE', overview.keys())
        self.assertIn('PriceToSalesRatioTTM', overview.keys())
        self.assertIn('PriceToBookRatio', overview.keys())
        self.assertIn('EVToRevenue', overview.keys())
        self.assertIn('EVToEBITDA', overview.keys())
        self.assertIn('Beta', overview.keys())
        self.assertIn('52WeekHigh', overview.keys())
        self.assertIn('52WeekLow', overview.keys())
        self.assertIn('50DayMovingAverage', overview.keys())
        self.assertIn('200DayMovingAverage', overview.keys())
        self.assertIn('SharesOutstanding', overview.keys())
        self.assertIn('DividendDate', overview.keys())
        self.assertIn('ExDividendDate', overview.keys())

    def test_process_prices(self):
        """Test process prices method."""
        # GIVEN
        # Build IBM JSON from file
        with open('./src/tests/IBM.daily_adjusted.json') as file:
            data = json.load(file)

        # WHEN
        prices = alpha.process_alphavantage_company_prices(data)

        # THEN
        self.assertIsInstance(prices, pd.DataFrame)
        # Check oldest date is first record
        self.assertGreater(prices.index[-1],
                           prices.index[0])
        # Check structure of prices
        self.assertGreater(len(prices), 2)
        self.assertIn('open', prices.keys())
        self.assertIn('high', prices.keys())
        self.assertIn('low', prices.keys())
        self.assertIn('close', prices.keys())
        self.assertIn('adj_close', prices.keys())
        self.assertIn('volume', prices.keys())
        self.assertIn('dividend_amt', prices.keys())
        self.assertIn('ticker', prices.keys())
        self.assertIn('SMA20', prices.keys())
        self.assertIn('SMA50', prices.keys())
        self.assertIn('SMA200', prices.keys())
        self.assertIn('log_return', prices.keys())


if __name__ == '__main__':
    unittest.main()
