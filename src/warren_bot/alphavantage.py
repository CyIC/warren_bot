# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Module to get and process Alphavantage information into Pandas data structures."""
from asyncio import sleep

import numpy as np
import pandas as pd
import requests


async def get_alphavantage_data(function: str, symbol: str, key: str, outputsize: str = "compact"):
    """Make https API call to Alphavantage.

    https://www.alphavantage.co/documentation

    :param function: (str) Alphavantage function (INCOME_STATEMENT, BALANCE_SHEET,
                     TIME_SERIES_MONTHLY_ADJUSTED, TIME_SERIES_WEEKLY_ADJUSTED,
                     TIME_SERIES_DAILY_ADJUSTED, EARNINGS)
    :param symbol: (str) Company stock ticker
    :param key: (str) Alphavantage api key
    :param outputsize: (str) alphavantage passed variable
    :return: <dict> json of alphavantage data
    """
    function = str.upper(function)
    url = "https://www.alphavantage.co/query?function={funct}&symbol={symbol}&apikey={key}&outputsize={outputsize}".format(  # pylint: disable=C0301
        funct=function, key=key, symbol=symbol, outputsize=outputsize
    )
    resp = requests.get(url, timeout=30).json()
    if resp.get("Note") is not None:
        await sleep(60)
        resp = requests.get(url, timeout=30).json()
    elif resp.get("Information") is not None:
        raise ConnectionError("Daily Alphavantage API Limit Reached!")
    return resp


def process_alphavantage_annual_company_info(income_statement, balance_sheet):
    """Get company fundamentals.

    Use AlphaVantage https://www.alphavantage.co/documentation/ to collect company fundamentals

    :param income_statement: (str) Income Statement json of company
    :param balance_sheet: (str) Balance Sheet json of company
    :return: company_data - Dataframe of company info {Year, ticker, revenue, eps}, current_eps
                            from last quarter filings
    """
    yrs_lookback = len(income_statement["annualReports"])
    shares_outstanding = []
    for year in balance_sheet["annualReports"]:
        shares_outstanding.append(int(year["commonStockSharesOutstanding"]))
    stock_ticker = income_statement["symbol"]
    # process company data
    date = []
    ticker = []
    revenue = []
    eps = []
    short_term_investments = []
    cash_equivalents = []
    long_term_debt = []
    shares_outstanding = []
    cash_and_short_term_investments = []
    receivables = []
    inventory = []
    other_assets = []
    payable = []
    short_term_debt = []
    other_liabilities = []
    current_assets = []
    current_liabilities = []
    count = 0
    # grab stock_ticker
    for x in range(0, yrs_lookback):  # pylint: disable=unused-variable
        ticker.append(stock_ticker)
    # process balance sheet
    for year in balance_sheet["annualReports"]:
        shares_outstanding.append(pd.to_numeric(year["commonStockSharesOutstanding"], "coerce"))
        cash_equivalents.append(pd.to_numeric(year["cashAndCashEquivalentsAtCarryingValue"], "coerce"))
        short_term_investments.append(pd.to_numeric(year["shortTermInvestments"], "coerce"))
        cash_and_short_term_investments.append(pd.to_numeric(year["cashAndShortTermInvestments"], "coerce"))
        long_term_debt.append(pd.to_numeric(year["longTermDebt"], "coerce"))
        receivables.append(pd.to_numeric(year["currentNetReceivables"], "coerce"))
        inventory.append(pd.to_numeric(year["inventory"], "coerce"))
        other_assets.append(pd.to_numeric(year["otherCurrentAssets"], "coerce"))
        payable.append(pd.to_numeric(year["currentAccountsPayable"], "coerce"))
        current_assets.append(pd.to_numeric(year["totalCurrentAssets"], "coerce"))
        current_liabilities.append(pd.to_numeric(year["totalCurrentLiabilities"], "coerce"))
        short_term_debt.append(pd.to_numeric(year["shortTermDebt"], "coerce"))
        other_liabilities.append(pd.to_numeric(year["otherCurrentLiabilities"], "coerce"))
        count += 1

    # process income statement
    count = 0
    for year in income_statement["annualReports"]:
        date.append(year["fiscalDateEnding"])
        revenue.append(int(year["totalRevenue"]))
        eps.append(int(year["netIncome"]) / shares_outstanding[count])
        count += 1
    # convert arrays to indexed Series
    tmp_info = {
        "ticker": pd.Series(ticker, index=date),
        "revenue": pd.Series(revenue, index=date),
        "eps": pd.Series(eps, index=date),
        "shortTermInvestments": pd.Series(short_term_investments, index=date),
        "cashEquivalents": pd.Series(cash_equivalents, index=date),
        "longTermDebt": pd.Series(long_term_debt, index=date),
        "shares_outstanding": pd.Series(shares_outstanding, index=date),
        "cashAndShortTermInvestments": pd.Series(cash_and_short_term_investments, index=date),
        "receivables": pd.Series(receivables, index=date),
        "inventory": pd.Series(inventory, index=date),
        "other_assets": pd.Series(other_assets, index=date),
        "payable": pd.Series(payable, index=date),
        "short_term_debt": pd.Series(short_term_debt, index=date),
        "other_liabilities": pd.Series(other_liabilities, index=date),
        "current_assets": pd.Series(current_assets, index=date),
        "current_liabilities": pd.Series(current_liabilities, index=date),
    }
    company_data = pd.DataFrame(tmp_info, index=date)
    company_data.index.name = "date"
    company_data.index = pd.to_datetime(company_data.index)
    company_data.sort_index(ascending=True, inplace=True)
    return company_data


async def get_alphavantage_income_statement(ticker: str, key: str):
    """Wrapper to await http get and process income statement from alphavantage.

    The download and the processing of alphavantage steps is broken apart for unittesting without
    having to download constantly.

    :param ticker: <str> Company ticker symbol
    :param key: <str> Alphavantage API Key
    :return income_statement: Pandas.DataFrame of processed income statement data
    """
    data = await get_alphavantage_data("INCOME_STATEMENT", ticker, key, outputsize="full")
    return process_alphavantage_income_statement(data)


def process_alphavantage_income_statement(data: dict):
    """Process passed income statement json from alphavantage.

    The download and the processing of alphavantage steps is broken apart for unittesting without
    having to download constantly.

    :param data: <dict> pre-downloaded JSON data
    :return: pandas.DataFrame of annual or quarterly income statement report info
    """
    ret_income = {"annualReports": None, "quarterlyReports": None}
    for time in ["annualReports", "quarterlyReports"]:
        income = pd.DataFrame(data[time])
        income.set_index("fiscalDateEnding", inplace=True)
        income = income.reindex()
        income.index = pd.to_datetime(income.index)
        income.sort_index(ascending=False, inplace=True)
        income["grossProfit"] = pd.to_numeric(income["grossProfit"], "coerce")
        income["totalRevenue"] = pd.to_numeric(income["totalRevenue"], "coerce")
        income["costOfRevenue"] = pd.to_numeric(income["costOfRevenue"], "coerce")
        income["costofGoodsAndServicesSold"] = pd.to_numeric(income["costofGoodsAndServicesSold"], "coerce")
        income["operatingIncome"] = pd.to_numeric(income["operatingIncome"], "coerce")
        income["sellingGeneralAndAdministrative"] = pd.to_numeric(income["sellingGeneralAndAdministrative"], "coerce")
        income["researchAndDevelopment"] = pd.to_numeric(income["researchAndDevelopment"], "coerce")
        income["operatingExpenses"] = pd.to_numeric(income["operatingExpenses"], "coerce")
        income["investmentIncomeNet"] = pd.to_numeric(income["investmentIncomeNet"], "coerce")
        income["netInterestIncome"] = pd.to_numeric(income["netInterestIncome"], "coerce")
        income["interestIncome"] = pd.to_numeric(income["interestIncome"], "coerce")
        income["interestExpense"] = pd.to_numeric(income["interestExpense"], "coerce")
        income["nonInterestIncome"] = pd.to_numeric(income["nonInterestIncome"], "coerce")
        income["otherNonOperatingIncome"] = pd.to_numeric(income["otherNonOperatingIncome"], "coerce")
        income["depreciation"] = pd.to_numeric(income["depreciation"], "coerce")
        income["depreciationAndAmortization"] = pd.to_numeric(income["depreciationAndAmortization"], "coerce")
        income["incomeBeforeTax"] = pd.to_numeric(income["incomeBeforeTax"], "coerce")
        income["incomeTaxExpense"] = pd.to_numeric(income["incomeTaxExpense"], "coerce")
        income["interestAndDebtExpense"] = pd.to_numeric(income["interestAndDebtExpense"], "coerce")
        income["netIncomeFromContinuingOperations"] = pd.to_numeric(
            income["netIncomeFromContinuingOperations"], "coerce"
        )
        income["comprehensiveIncomeNetOfTax"] = pd.to_numeric(income["comprehensiveIncomeNetOfTax"], "coerce")
        income["ebit"] = pd.to_numeric(income["ebit"], "coerce")
        income["ebitda"] = pd.to_numeric(income["ebitda"], "coerce")
        income["netIncome"] = pd.to_numeric(income["netIncome"], "coerce")
        ret_income[time] = income
    return ret_income


async def get_alphavantage_earnings(ticker: str, key: str):
    """Wrapper to await http get and process earnings statement from Alphavantage.

    The download and the processing of alphavantage steps is broken apart for unittesting without
    having to download constantly.

    :param ticker: <str> Company ticker symbol
    :param key: <str> Alphavantage API Key
    :return income_statement: Pandas.DataFrame of processed Earnings statement data
    """
    data = await get_alphavantage_data("EARNINGS", ticker, key, outputsize="full")
    return process_alphavantage_earnings(data)


def process_alphavantage_earnings(data: dict):
    """Process Earnings per share from alphavantage data.

    The download and the processing of alphavantage steps is broken apart for unittesting without
    having to download constantly.

    annualEarnings, quarterlyEarnings

    from warren_bot import utilities as util
    import pandas as pd
    data = await util.get_alphavantage_earnings('MSFT')

    :param data: <dict> pre-downloaded JSON data from Alphavantage
    :return: pandas.DataFrame of annual and quarterly earnings report info
    """
    ret_eps = {"annualEarnings": None, "quarterlyEarnings": None}
    for time in ["quarterlyEarnings", "annualEarnings"]:
        eps = pd.DataFrame(data[time])
        eps.set_index("fiscalDateEnding", inplace=True)
        eps.sort_index(ascending=True, inplace=True)
        eps = eps.reindex()
        eps.index = pd.to_datetime(eps.index)
        eps["reportedEPS"] = pd.to_numeric(eps["reportedEPS"], "coerce")
        if time == "quarterlyEarnings":
            eps["reportedDate"] = pd.to_datetime(eps["reportedDate"])
            eps["estimatedEPS"] = pd.to_numeric(eps["estimatedEPS"], "coerce")
            eps["surprise"] = pd.to_numeric(eps["surprise"], "coerce")
            eps["surprisePercentage"] = pd.to_numeric(eps["surprisePercentage"], "coerce")
        ret_eps[time] = eps
    return ret_eps


async def get_alphavantage_cash_flow(ticker: str, key: str):
    """Wrapper to await http get and process cash flow statement from Alphavantage.

    The download and the processing of alphavantage steps is broken apart for unittesting without
    having to download constantly.

    :param ticker: <str> Company ticker symbol
    :param key: <str> Alphavantage API Key
    :return cash_flow: Pandas.DataFrame of processed cash flow statement data
    """
    data = await get_alphavantage_data("CASH_FLOW", ticker, key, outputsize="full")
    return process_alphavantage_cash_flow(data)


def process_alphavantage_cash_flow(data: dict):
    """Process cash flow from alphavantage data.

    The download and the processing of alphavantage steps is broken apart for unittesting without
    having to download constantly.

    :param data: <dict> pre-downloaded JSON data from Alphavantage
    :return: pandas.DataFrame of annual and quarterly cash flow report info
    """
    ret_cash = {"annualReports": None, "quarterlyReports": None}

    for time in ["annualReports", "quarterlyReports"]:
        cash = pd.DataFrame(data[time])
        cash.set_index("fiscalDateEnding", inplace=True)
        cash = cash.reindex()
        cash.index = pd.to_datetime(cash.index)
        cash.sort_index(ascending=True, inplace=True)
        cash["operatingCashflow"] = pd.to_numeric(cash["operatingCashflow"], "coerce")
        cash["paymentsForOperatingActivities"] = pd.to_numeric(cash["paymentsForOperatingActivities"], "coerce")
        cash["proceedsFromOperatingActivities"] = pd.to_numeric(cash["proceedsFromOperatingActivities"], "coerce")
        cash["changeInOperatingLiabilities"] = pd.to_numeric(cash["changeInOperatingLiabilities"], "coerce")
        cash["changeInOperatingAssets"] = pd.to_numeric(cash["changeInOperatingAssets"], "coerce")
        cash["depreciationDepletionAndAmortization"] = pd.to_numeric(
            cash["depreciationDepletionAndAmortization"], "coerce"
        )
        cash["capitalExpenditures"] = pd.to_numeric(cash["capitalExpenditures"], "coerce")
        cash["changeInReceivables"] = pd.to_numeric(cash["changeInReceivables"], "coerce")
        cash["changeInInventory"] = pd.to_numeric(cash["changeInInventory"], "coerce")
        cash["profitLoss"] = pd.to_numeric(cash["profitLoss"], "coerce")
        cash["cashflowFromInvestment"] = pd.to_numeric(cash["cashflowFromInvestment"], "coerce")
        cash["cashflowFromFinancing"] = pd.to_numeric(cash["cashflowFromFinancing"], "coerce")
        cash["proceedsFromRepaymentsOfShortTermDebt"] = pd.to_numeric(
            cash["proceedsFromRepaymentsOfShortTermDebt"], "coerce"
        )
        cash["paymentsForRepurchaseOfCommonStock"] = pd.to_numeric(cash["paymentsForRepurchaseOfCommonStock"], "coerce")
        cash["paymentsForRepurchaseOfEquity"] = pd.to_numeric(cash["paymentsForRepurchaseOfEquity"], "coerce")
        cash["paymentsForRepurchaseOfPreferredStock"] = pd.to_numeric(
            cash["paymentsForRepurchaseOfPreferredStock"], "coerce"
        )
        cash["dividendPayout"] = pd.to_numeric(cash["dividendPayout"], "coerce")
        cash["dividendPayoutCommonStock"] = pd.to_numeric(cash["dividendPayoutCommonStock"], "coerce")
        cash["dividendPayoutPreferredStock"] = pd.to_numeric(cash["dividendPayoutPreferredStock"], "coerce")
        cash["proceedsFromIssuanceOfCommonStock"] = pd.to_numeric(cash["proceedsFromIssuanceOfCommonStock"], "coerce")
        cash["proceedsFromIssuanceOfLongTermDebtAndCapitalSecuritiesNet"] = pd.to_numeric(
            cash["proceedsFromIssuanceOfLongTermDebtAndCapitalSecuritiesNet"],
            "coerce",
        )
        cash["proceedsFromIssuanceOfPreferredStock"] = pd.to_numeric(
            cash["proceedsFromIssuanceOfPreferredStock"], "coerce"
        )
        cash["proceedsFromRepurchaseOfEquity"] = pd.to_numeric(cash["proceedsFromRepurchaseOfEquity"], "coerce")
        cash["proceedsFromSaleOfTreasuryStock"] = pd.to_numeric(cash["proceedsFromSaleOfTreasuryStock"], "coerce")
        cash["changeInCashAndCashEquivalents"] = pd.to_numeric(cash["changeInCashAndCashEquivalents"], "coerce")
        cash["changeInExchangeRate"] = pd.to_numeric(cash["changeInExchangeRate"], "coerce")
        cash["netIncome"] = pd.to_numeric(cash["netIncome"], "coerce")
        ret_cash[time] = cash
    return ret_cash


async def get_alphavantage_balance_sheet(ticker: str, key: str):
    """Wrapper to await http get and process balance sheet from Alphavantage.

    The download and the processing of alphavantage steps is broken apart for unittesting without
    having to download constantly.

    :param ticker: <str> Company ticker symbol
    :param key: <str> Alphavantage API Key
    :return cash_flow: Pandas.DataFrame of processed balance sheet statement data
    """
    data = await get_alphavantage_data("BALANCE_SHEET", ticker, key, outputsize="full")
    return process_alphavantage_balance_sheet(data)


def process_alphavantage_balance_sheet(data: dict):
    """Process balance sheet from alphavantage data.

    The download and the processing of alphavantage steps is broken apart for unittesting without
    having to download constantly.

    :param data: <dict> pre-downloaded JSON data from Alphavantage
    :return: pandas.DataFrame of annual and quarterly cash flow report info
    """
    ret_bal = {"annualReports": None, "quarterlyReports": None}
    for time in ["annualReports", "quarterlyReports"]:
        bal = pd.DataFrame(data[time])
        bal.set_index("fiscalDateEnding", inplace=True)
        bal = bal.reindex()
        bal.index = pd.to_datetime(bal.index)
        bal.sort_index(ascending=True, inplace=True)
        bal["reportedCurrency"] = pd.to_numeric(bal["reportedCurrency"], "coerce")
        bal["totalAssets"] = pd.to_numeric(bal["totalAssets"], "coerce")
        bal["totalCurrentAssets"] = pd.to_numeric(bal["totalCurrentAssets"], "coerce")
        bal["cashAndCashEquivalentsAtCarryingValue"] = pd.to_numeric(
            bal["cashAndCashEquivalentsAtCarryingValue"], "coerce"
        )
        bal["cashAndShortTermInvestments"] = pd.to_numeric(bal["cashAndShortTermInvestments"], "coerce")
        bal["inventory"] = pd.to_numeric(bal["inventory"], "coerce")
        bal["currentNetReceivables"] = pd.to_numeric(bal["currentNetReceivables"], "coerce")
        bal["totalNonCurrentAssets"] = pd.to_numeric(bal["totalNonCurrentAssets"], "coerce")
        bal["propertyPlantEquipment"] = pd.to_numeric(bal["propertyPlantEquipment"], "coerce")
        bal["accumulatedDepreciationAmortizationPPE"] = pd.to_numeric(
            bal["accumulatedDepreciationAmortizationPPE"], "coerce"
        )
        bal["intangibleAssets"] = pd.to_numeric(bal["intangibleAssets"], "coerce")
        bal["intangibleAssetsExcludingGoodwill"] = pd.to_numeric(bal["intangibleAssetsExcludingGoodwill"], "coerce")
        bal["goodwill"] = pd.to_numeric(bal["goodwill"], "coerce")
        bal["investments"] = pd.to_numeric(bal["investments"], "coerce")
        bal["longTermInvestments"] = pd.to_numeric(bal["longTermInvestments"], "coerce")
        bal["shortTermInvestments"] = pd.to_numeric(bal["shortTermInvestments"], "coerce")
        bal["otherCurrentAssets"] = pd.to_numeric(bal["otherCurrentAssets"], "coerce")
        bal["otherNonCurrentAssets"] = pd.to_numeric(bal["otherNonCurrentAssets"], "coerce")
        bal["totalLiabilities"] = pd.to_numeric(bal["totalLiabilities"], "coerce")
        bal["totalCurrentLiabilities"] = pd.to_numeric(bal["totalCurrentLiabilities"], "coerce")
        bal["currentAccountsPayable"] = pd.to_numeric(bal["currentAccountsPayable"], "coerce")
        bal["deferredRevenue"] = pd.to_numeric(bal["deferredRevenue"], "coerce")
        bal["currentDebt"] = pd.to_numeric(bal["currentDebt"], "coerce")
        bal["shortTermDebt"] = pd.to_numeric(bal["shortTermDebt"], "coerce")
        bal["totalNonCurrentLiabilities"] = pd.to_numeric(bal["totalNonCurrentLiabilities"], "coerce")
        bal["capitalLeaseObligations"] = pd.to_numeric(bal["capitalLeaseObligations"], "coerce")
        bal["longTermDebt"] = pd.to_numeric(bal["longTermDebt"], "coerce")
        bal["currentLongTermDebt"] = pd.to_numeric(bal["currentLongTermDebt"], "coerce")
        bal["longTermDebtNoncurrent"] = pd.to_numeric(bal["longTermDebtNoncurrent"], "coerce")
        bal["shortLongTermDebtTotal"] = pd.to_numeric(bal["shortLongTermDebtTotal"], "coerce")
        bal["otherCurrentLiabilities"] = pd.to_numeric(bal["otherCurrentLiabilities"], "coerce")
        bal["otherNonCurrentLiabilities"] = pd.to_numeric(bal["otherNonCurrentLiabilities"], "coerce")
        bal["totalShareholderEquity"] = pd.to_numeric(bal["totalShareholderEquity"], "coerce")
        bal["treasuryStock"] = pd.to_numeric(bal["treasuryStock"], "coerce")
        bal["retainedEarnings"] = pd.to_numeric(bal["retainedEarnings"], "coerce")
        bal["commonStock"] = pd.to_numeric(bal["commonStock"], "coerce")
        bal["commonStockSharesOutstanding"] = pd.to_numeric(bal["commonStockSharesOutstanding"], "coerce")
        ret_bal[time] = bal
    return ret_bal


async def get_alphavantage_overview(ticker: str, key: str):
    """Wrapper to await http get and process company overview data  from Alphavantage.

    The download and the processing of alphavantage steps is broken apart for unittesting without
    having to download constantly.

    :param ticker: <str> Company ticker symbol
    :param key: <str> Alphavantage API Key
    :return cash_flow: Pandas.DataFrame of processed company overview data
    """
    data = await get_alphavantage_data("OVERVIEW", ticker, key, outputsize="full")
    return process_alphavantage_overview(data)


def process_alphavantage_overview(data: dict):
    """Get company overview from alphavantage.

    Get alphavantage json and return a pandas.Series

    :param data: <dict> pre-downloaded JSON data from Alphavantage
    :return: pandas.DataFrame of company overview report info
    """
    view = pd.Series(data)
    view["CIK"] = pd.to_numeric(view["CIK"], "coerce")
    view["LatestQuarter"] = pd.to_datetime(view["LatestQuarter"])
    view["MarketCapitalization"] = pd.to_numeric(view["MarketCapitalization"], "coerce")
    view["EBITDA"] = pd.to_numeric(view["EBITDA"], "coerce")
    view["PERatio"] = pd.to_numeric(view["PERatio"], "coerce")
    view["PEGRatio"] = pd.to_numeric(view["PEGRatio"], "coerce")
    view["BookValue"] = pd.to_numeric(view["BookValue"], "coerce")
    view["DividendPerShare"] = pd.to_numeric(view["DividendPerShare"], "coerce")
    view["DividendYield"] = pd.to_numeric(view["DividendYield"], "coerce")
    view["EPS"] = pd.to_numeric(view["EPS"], "coerce")
    view["RevenuePerShareTTM"] = pd.to_numeric(view["RevenuePerShareTTM"], "coerce")
    view["ProfitMargin"] = pd.to_numeric(view["ProfitMargin"], "coerce")
    view["OperatingMarginTTM"] = pd.to_numeric(view["OperatingMarginTTM"], "coerce")
    view["ReturnOnAssetsTTM"] = pd.to_numeric(view["ReturnOnAssetsTTM"], "coerce")
    view["ReturnOnEquityTTM"] = pd.to_numeric(view["ReturnOnEquityTTM"], "coerce")
    view["RevenueTTM"] = pd.to_numeric(view["RevenueTTM"], "coerce")
    view["GrossProfitTTM"] = pd.to_numeric(view["GrossProfitTTM"], "coerce")
    view["DilutedEPSTTM"] = pd.to_numeric(view["DilutedEPSTTM"], "coerce")
    view["QuarterlyEarningsGrowthYOY"] = pd.to_numeric(view["QuarterlyEarningsGrowthYOY"], "coerce")
    view["QuarterlyRevenueGrowthYOY"] = pd.to_numeric(view["QuarterlyRevenueGrowthYOY"], "coerce")
    view["AnalystTargetPrice"] = pd.to_numeric(view["AnalystTargetPrice"], "coerce")
    view["TrailingPE"] = pd.to_numeric(view["TrailingPE"], "coerce")
    view["ForwardPE"] = pd.to_numeric(view["ForwardPE"], "coerce")
    view["PriceToSalesRatioTTM"] = pd.to_numeric(view["PriceToSalesRatioTTM"], "coerce")
    view["PriceToBookRatio"] = pd.to_numeric(view["PriceToBookRatio"], "coerce")
    view["EVToRevenue"] = pd.to_numeric(view["EVToRevenue"], "coerce")
    view["EVToEBITDA"] = pd.to_numeric(view["EVToEBITDA"], "coerce")
    view["Beta"] = pd.to_numeric(view["Beta"], "coerce")
    view["52WeekHigh"] = pd.to_numeric(view["52WeekHigh"], "coerce")
    view["52WeekLow"] = pd.to_numeric(view["52WeekLow"], "coerce")
    view["50DayMovingAverage"] = pd.to_numeric(view["50DayMovingAverage"], "coerce")
    view["200DayMovingAverage"] = pd.to_numeric(view["200DayMovingAverage"], "coerce")
    view["SharesOutstanding"] = pd.to_numeric(view["SharesOutstanding"], "coerce")
    view["DividendDate"] = pd.to_datetime(view["DividendDate"])
    view["ExDividendDate"] = pd.to_datetime(view["ExDividendDate"])
    return view


async def get_daily_alphavantage_company_prices(ticker: str, key: str):
    """Wrapper to await http get and process company stock price data from Alphavantage.

    The download and the processing of alphavantage steps is broken apart for unittesting without
    having to download constantly.

    :param ticker: <str> Company ticker symbol
    :param key: <str> Alphavantage API Key
    :return cash_flow: Pandas.DataFrame of processed company stock price data
    """
    data = await get_alphavantage_data("TIME_SERIES_DAILY_ADJUSTED", ticker, key, outputsize="full")
    return process_alphavantage_company_prices(data)


async def get_weekly_alphavantage_company_prices(ticker: str, key: str):
    """Wrapper to await http get and process company stock price data from Alphavantage.

    The download and the processing of alphavantage steps is broken apart for unittesting without
    having to download constantly.

    :param ticker: <str> Company ticker symbol
    :param key: <str> Alphavantage API Key
    :return cash_flow: Pandas.DataFrame of processed company stock price data
    """
    data = await get_alphavantage_data("TIME_SERIES_WEEKLY_ADJUSTED", ticker, key, outputsize="full")
    return process_alphavantage_company_prices(data)


async def get_monthly_alphavantage_company_prices(ticker: str, key: str):
    """Wrapper to await http get and process company stock price data from Alphavantage.

    The download and the processing of alphavantage steps is broken apart for unittesting without
    having to download constantly.

    :param ticker: <str> Company ticker symbol
    :param key: <str> Alphavantage API Key
    :return cash_flow: Pandas.DataFrame of processed company stock price data
    """
    data = await get_alphavantage_data("TIME_SERIES_MONTHLY_ADJUSTED", ticker, key, outputsize="full")
    return process_alphavantage_company_prices(data)


def process_alphavantage_company_prices(data):
    """Get company stock data from alphavantage Core Stock API.

    Use AlphaVantage https://www.alphavantage.co/documentation/ to collect company stock data

    :param data: (Dict) JSON Time series prices from alphavantage
    :return: Dataframe of company stock prices
    """
    if "Time Series (Daily)" in data.keys():
        pivot = "Time Series (Daily)"
    elif "Monthly Adjusted Time Series" in data.keys():
        pivot = "Monthly Adjusted Time Series"
    elif "Weekly Adjusted Time Series" in data.keys():
        pivot = "Weekly Adjusted Time Series"
    else:
        raise KeyError

    prices = pd.DataFrame(data[pivot]).T
    prices = prices.rename(
        columns={
            "1. open": "open",
            "2. high": "high",
            "3. low": "low",
            "4. close": "close",
            "5. adjusted close": "adj_close",
            "6. volume": "volume",
            "7. dividend amount": "dividend_amt",
            "8. split coefficient": "split coefficient",
        }
    )
    prices.index.name = "date"
    prices.index = pd.to_datetime(prices.index)
    prices = prices.reindex()
    prices.sort_index(ascending=True, inplace=True)
    prices["open"] = pd.to_numeric(prices["open"])
    prices["high"] = pd.to_numeric(prices["high"])
    prices["low"] = pd.to_numeric(prices["low"])
    prices["close"] = pd.to_numeric(prices["close"])
    prices["adj_close"] = pd.to_numeric(prices["adj_close"])
    prices["volume"] = pd.to_numeric(prices["volume"])
    prices["dividend_amt"] = pd.to_numeric(prices["dividend_amt"])
    prices["ticker"] = data["Meta Data"]["2. Symbol"]
    prices["SMA20"] = prices["close"].rolling(20).mean()
    prices["SMA50"] = prices["close"].rolling(50).mean()
    prices["SMA200"] = prices["close"].rolling(200).mean()
    prices["log_return"] = np.log(prices["close"]) - np.log(prices["close"].shift(1))
    try:
        prices["split coefficient"] = pd.to_numeric(prices["split coefficient"], errors="coerce")
    except KeyError:
        prices["split coefficient"] = None
    return prices


async def download_stocks(stocks: list, key: str):
    """Download a collection of stocks from Alphavantage.

    :param stocks: <list> a list of stocks to lookup
    :param key: Alphavantage API key
    :return:
    """
    prices = pd.DataFrame()
    for ticker in stocks["ticker"].unique().tolist():
        tmp_stock = await get_daily_alphavantage_company_prices(ticker, key)
        prices = pd.concat([tmp_stock, prices])
    prices.to_pickle("stocks.pkl")
    return prices
