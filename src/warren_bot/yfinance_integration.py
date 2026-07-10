# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Module to get and process yfinance information into Pandas data structures."""
import logging

import numpy as np
import pandas as pd
import yfinance as yf

from warren_bot import utilities as util

LOGGER = logging.getLogger()

# Map alphavantage field names (which the report code consumes) to the candidate yfinance
# row labels. yfinance label availability varies by company, so each target lists fallbacks
# tried in order; missing labels become NaN columns so downstream access never KeyErrors.
INCOME_FIELD_MAP = {
    "totalRevenue": ["Total Revenue"],
    "netIncome": ["Net Income", "Net Income Common Stockholders"],
}

BALANCE_FIELD_MAP = {
    "cashAndCashEquivalentsAtCarryingValue": ["Cash And Cash Equivalents"],
    "shortTermInvestments": ["Other Short Term Investments", "Short Term Investments"],
    "longTermDebt": ["Long Term Debt"],
    "commonStockSharesOutstanding": ["Ordinary Shares Number", "Share Issued"],
    "currentNetReceivables": ["Receivables", "Accounts Receivable", "Net Receivables"],
    "inventory": ["Inventory"],
    "otherCurrentAssets": ["Other Current Assets"],
    "totalCurrentAssets": ["Current Assets", "Total Current Assets"],
    "currentAccountsPayable": ["Accounts Payable", "Payables"],
    "shortTermDebt": ["Current Debt", "Current Debt And Capital Lease Obligation"],
    "otherCurrentLiabilities": ["Other Current Liabilities"],
    "totalCurrentLiabilities": ["Current Liabilities", "Total Current Liabilities"],
}

CASHFLOW_FIELD_MAP = {
    "dividendPayout": ["Cash Dividends Paid", "Common Stock Dividend Paid"],
    "netIncome": ["Net Income", "Net Income From Continuing Operations"],
}


def _normalize_index(df: pd.DataFrame):
    """Coerce a statement DataFrame index to a timezone-naive DatetimeIndex.

    The report code compares the index against timezone-naive datetimes, so any tz must be
    stripped to avoid tz-naive/tz-aware comparison errors.

    :param df: (pandas.DataFrame) statement frame with date-like index
    :return: same frame with a tz-naive DatetimeIndex, sorted ascending
    """
    df.index = pd.to_datetime(df.index)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    df.sort_index(ascending=True, inplace=True)
    return df


def _remap_columns(df: pd.DataFrame, field_map: dict):
    """Translate yfinance row labels into the alphavantage column names the report expects.

    :param df: (pandas.DataFrame) transposed yfinance statement (dates as index, items as columns)
    :param field_map: (dict) {alphavantage_name: [candidate yfinance labels]}
    :return: DataFrame with alphavantage-named, numeric columns; missing source labels become NaN
    """
    if df is None or df.empty:
        return pd.DataFrame()

    remapped = pd.DataFrame(index=df.index)
    for av_name, yf_candidates in field_map.items():
        remapped[av_name] = np.nan
        for label in yf_candidates:
            if label in df.columns:
                remapped[av_name] = pd.to_numeric(df[label], errors="coerce")
                break
    return _normalize_index(remapped)


def get_finance_data(ticker: str):
    """Get stock data from yfinance.

    :param ticker: (str) Company stock ticker
    :return: yfinance Ticker object
    """
    stock = yf.Ticker(ticker)
    return stock


def get_yfinance_income_statement(ticker: str, years: int = 5):
    """Get income statement data from yfinance.

    Retrieves annual and quarterly income statement data from yfinance. When quarterly data
    covers periods not present in the annual data, aggregates complete fiscal years
    (4 quarters) to extend coverage beyond the default ~4 annual periods.

    :param ticker: (str) Company ticker symbol
    :param years: (int) Number of years of income statement data to retrieve (default 5)
    :return: dict of income statement data with 'annualReports' and 'quarterlyReports' DataFrames
    """
    stock = get_finance_data(ticker)

    # Get both annual and quarterly income statements
    annual_income = stock.financials  # Annual
    quarterly_income = stock.quarterly_financials  # Quarterly

    annual_reports = annual_income.T if annual_income is not None and not annual_income.empty else pd.DataFrame()
    quarterly_reports = (
        quarterly_income.T if quarterly_income is not None and not quarterly_income.empty else pd.DataFrame()
    )

    # Supplement annual data by aggregating quarterly data into fiscal years.
    # Income statement items are period totals, so summing 4 quarters gives valid annual figures.
    if not quarterly_reports.empty and not annual_reports.empty:
        annual_years = set(annual_reports.index.year)
        numeric_columns = quarterly_reports.select_dtypes(include="number").columns

        # Approximate fiscal year by shifting quarter-end dates back 2 months
        fiscal_years = (quarterly_reports.index - pd.DateOffset(months=2)).year

        for fiscal_year in sorted(set(fiscal_years)):
            if fiscal_year not in annual_years:
                year_quarters = quarterly_reports[fiscal_years == fiscal_year]
                if len(year_quarters) >= 4:
                    aggregated_row = year_quarters[numeric_columns].sum()
                    aggregated_row.name = pd.Timestamp(f"{fiscal_year}-12-31")
                    annual_reports = pd.concat([annual_reports, aggregated_row.to_frame().T])

        annual_reports.sort_index(ascending=True, inplace=True)

    # Trim to requested number of years
    if not annual_reports.empty and len(annual_reports) > years:
        annual_reports = annual_reports.iloc[-years:]

    return {
        "annualReports": _remap_columns(annual_reports, INCOME_FIELD_MAP),
        "quarterlyReports": _remap_columns(quarterly_reports, INCOME_FIELD_MAP),
    }


def get_yfinance_balance_sheet(ticker: str, years: int = 5):
    """Get balance sheet data from yfinance.

    Retrieves annual and quarterly balance sheet data from yfinance. When quarterly data
    covers fiscal years not present in the annual data, uses the latest quarter-end snapshot
    for that fiscal year to extend coverage beyond the default ~4 annual periods.

    Unlike income statement and cash flow (which are period totals), balance sheet items are
    point-in-time snapshots, so the latest quarter of each fiscal year is used rather than
    summing quarters.

    :param ticker: (str) Company ticker symbol
    :param years: (int) Number of years of balance sheet data to retrieve (default 5)
    :return: dict of balance sheet data with 'annualReports' and 'quarterlyReports' DataFrames
    """
    stock = get_finance_data(ticker)

    # Get both annual and quarterly balance sheets
    annual_balance = stock.balance_sheet  # Annual
    quarterly_balance = stock.quarterly_balance_sheet  # Quarterly

    annual_reports = annual_balance.T if annual_balance is not None and not annual_balance.empty else pd.DataFrame()
    quarterly_reports = (
        quarterly_balance.T if quarterly_balance is not None and not quarterly_balance.empty else pd.DataFrame()
    )

    # Supplement annual data using quarterly snapshots.
    # Balance sheet items are point-in-time, so take the latest quarter per fiscal year.
    if not quarterly_reports.empty and not annual_reports.empty:
        annual_years = set(annual_reports.index.year)

        # Approximate fiscal year by shifting quarter-end dates back 2 months
        fiscal_years = (quarterly_reports.index - pd.DateOffset(months=2)).year

        for fiscal_year in sorted(set(fiscal_years)):
            if fiscal_year not in annual_years:
                year_quarters = quarterly_reports[fiscal_years == fiscal_year]
                if not year_quarters.empty:
                    # Use the latest quarter-end snapshot for this fiscal year
                    latest_snapshot = year_quarters.sort_index().iloc[[-1]].copy()
                    latest_snapshot.index = [pd.Timestamp(f"{fiscal_year}-12-31")]
                    annual_reports = pd.concat([annual_reports, latest_snapshot])

        annual_reports.sort_index(ascending=True, inplace=True)

    # Trim to requested number of years
    if not annual_reports.empty and len(annual_reports) > years:
        annual_reports = annual_reports.iloc[-years:]

    return {
        "annualReports": _remap_columns(annual_reports, BALANCE_FIELD_MAP),
        "quarterlyReports": _remap_columns(quarterly_reports, BALANCE_FIELD_MAP),
    }


def get_yfinance_cash_flow(ticker: str, years: int = 5):
    """Get cash flow statement data from yfinance.

    Retrieves annual and quarterly cash flow data from yfinance. When quarterly data
    covers periods not present in the annual data, aggregates complete fiscal years
    (4 quarters) to extend coverage beyond the default ~4 annual periods.

    :param ticker: (str) Company ticker symbol
    :param years: (int) Number of years of cash flow data to retrieve (default 5)
    :return: dict of cash flow data with 'annualReports' and 'quarterlyReports' DataFrames
    """
    stock = get_finance_data(ticker)

    # Get both annual and quarterly cash flow statements
    annual_cashflow = stock.cashflow  # Annual
    quarterly_cashflow = stock.quarterly_cashflow  # Quarterly

    annual_reports = annual_cashflow.T if annual_cashflow is not None and not annual_cashflow.empty else pd.DataFrame()
    quarterly_reports = (
        quarterly_cashflow.T if quarterly_cashflow is not None and not quarterly_cashflow.empty else pd.DataFrame()
    )

    # Supplement annual data by aggregating quarterly data into fiscal years.
    # Cash flow items are period totals, so summing 4 quarters gives valid annual figures.
    if not quarterly_reports.empty and not annual_reports.empty:
        annual_years = set(annual_reports.index.year)
        numeric_columns = quarterly_reports.select_dtypes(include="number").columns

        # Approximate fiscal year by shifting quarter-end dates back 2 months
        fiscal_years = (quarterly_reports.index - pd.DateOffset(months=2)).year

        for fiscal_year in sorted(set(fiscal_years)):
            if fiscal_year not in annual_years:
                year_quarters = quarterly_reports[fiscal_years == fiscal_year]
                if len(year_quarters) >= 4:
                    aggregated_row = year_quarters[numeric_columns].sum()
                    aggregated_row.name = pd.Timestamp(f"{fiscal_year}-12-31")
                    annual_reports = pd.concat([annual_reports, aggregated_row.to_frame().T])

        annual_reports.sort_index(ascending=True, inplace=True)

    # Trim to requested number of years
    if not annual_reports.empty and len(annual_reports) > years:
        annual_reports = annual_reports.iloc[-years:]

    annual_remapped = _remap_columns(annual_reports, CASHFLOW_FIELD_MAP)
    quarterly_remapped = _remap_columns(quarterly_reports, CASHFLOW_FIELD_MAP)

    # yfinance reports dividends paid as a negative cash outflow; alphavantage's dividendPayout
    # is a positive amount, so normalize to match the value the report code expects.
    for report in (annual_remapped, quarterly_remapped):
        if "dividendPayout" in report.columns:
            report["dividendPayout"] = report["dividendPayout"].abs()

    return {
        "annualReports": annual_remapped,
        "quarterlyReports": quarterly_remapped,
    }


def _earnings_from_dates(stock, years: int) -> dict | None:
    """Build earnings dict from stock.get_earnings_dates() for extended EPS history.

    :param stock: yfinance Ticker-like object
    :param years: number of years of earnings to retrieve (fetches years * 4 quarters)
    :return: dict with annual/quarterly earnings DataFrames (annualEarnings may be an empty
        DataFrame if no complete fiscal year is available), or None if no reported EPS exists
        at all (signaling the caller to fall back to basic earnings)
    """
    earnings_dates = stock.get_earnings_dates(limit=years * 4)
    if earnings_dates is None or earnings_dates.empty:
        return None
    # Filter to rows with actual reported EPS (excludes future dates)
    reported = earnings_dates[earnings_dates["Reported EPS"].notna()].copy()
    if reported.empty:
        return None

    ret_eps = {"annualEarnings": pd.DataFrame(), "quarterlyEarnings": pd.DataFrame()}
    # Normalize index to timezone-naive for consistency
    if reported.index.tz is not None:
        reported.index = reported.index.tz_localize(None)

    # Build quarterly earnings DataFrame
    quarterly_df = pd.DataFrame(index=reported.index)
    quarterly_df.index.name = "fiscalDateEnding"
    quarterly_df["reportedEPS"] = reported["Reported EPS"].values
    if "EPS Estimate" in reported.columns:
        quarterly_df["estimatedEPS"] = reported["EPS Estimate"].values
    if "Surprise(%)" in reported.columns:
        quarterly_df["surprise"] = reported["Surprise(%)"].values
    quarterly_df.sort_index(ascending=True, inplace=True)
    ret_eps["quarterlyEarnings"] = quarterly_df

    # Approximate fiscal year by shifting announcement dates back ~2 months.
    # Earnings are typically announced 1-2 months after quarter end, so this
    # maps Q4 announcements (Jan/Feb) back to the correct fiscal year.
    fiscal_years = (quarterly_df.index - pd.DateOffset(months=2)).year

    # Sum quarterly EPS per fiscal year, only for complete years (4 quarters)
    annual_eps = quarterly_df["reportedEPS"].groupby(fiscal_years).sum()
    quarter_counts = quarterly_df["reportedEPS"].groupby(fiscal_years).count()
    complete_years = quarter_counts[quarter_counts >= 4].index
    annual_eps = annual_eps[annual_eps.index.isin(complete_years)]

    if not annual_eps.empty:
        annual_df = pd.DataFrame({"reportedEPS": annual_eps})
        annual_df.index = pd.to_datetime(annual_df.index.astype(str) + "-12-31")
        annual_df.index.name = "fiscalDateEnding"
        annual_df.sort_index(ascending=True, inplace=True)
        ret_eps["annualEarnings"] = annual_df

    return ret_eps


def _earnings_from_basic(stock) -> dict:
    """Build earnings dict from stock.earnings / stock.quarterly_earnings (~4 year limit).

    :param stock: yfinance Ticker-like object
    :return: dict with annual/quarterly earnings DataFrames (empty DataFrames when unavailable)
    """
    ret_eps = {"annualEarnings": pd.DataFrame(), "quarterlyEarnings": pd.DataFrame()}
    annual_earnings = stock.earnings
    quarterly_earnings = stock.quarterly_earnings

    if annual_earnings is not None and not annual_earnings.empty:
        annual_df = annual_earnings.copy()
        annual_df.index.name = "fiscalDateEnding"
        annual_df = annual_df.reset_index()
        annual_df["fiscalDateEnding"] = pd.to_datetime(annual_df["fiscalDateEnding"])
        annual_df.set_index("fiscalDateEnding", inplace=True)
        annual_df.sort_index(ascending=True, inplace=True)
        if "Earnings" in annual_df.columns:
            annual_df["reportedEPS"] = annual_df["Earnings"]
        ret_eps["annualEarnings"] = annual_df

    if quarterly_earnings is not None and not quarterly_earnings.empty:
        quarterly_df = quarterly_earnings.copy()
        quarterly_df.index.name = "fiscalDateEnding"
        quarterly_df = quarterly_df.reset_index()
        quarterly_df["fiscalDateEnding"] = pd.to_datetime(quarterly_df["fiscalDateEnding"])
        quarterly_df.set_index("fiscalDateEnding", inplace=True)
        quarterly_df.sort_index(ascending=True, inplace=True)
        if "Earnings" in quarterly_df.columns:
            quarterly_df["reportedEPS"] = quarterly_df["Earnings"]
        ret_eps["quarterlyEarnings"] = quarterly_df

    return ret_eps


def get_yfinance_earnings(ticker: str, years: int = 5):
    """Get earnings data from yfinance.

    Uses get_earnings_dates() to retrieve extended historical EPS data beyond the
    default ~4 years available from stock.earnings. Falls back to stock.earnings
    if the extended method fails.

    :param ticker: (str) Company ticker symbol
    :param years: (int) Number of years of earnings data to retrieve (default 5)
    :return: dict with exactly two keys, each a pandas.DataFrame (never None):

        {
            "annualEarnings":    <DataFrame>,  # one row per fiscal year
            "quarterlyEarnings": <DataFrame>,  # one row per fiscal quarter
        }

        When populated, each DataFrame is indexed by "fiscalDateEnding" (tz-naive
        datetime, sorted ascending) and contains a "reportedEPS" column:
            - annualEarnings["reportedEPS"]:    EPS summed per fiscal year (YYYY-12-31 index)
            - quarterlyEarnings["reportedEPS"]: EPS per quarter
        The extended path may add "estimatedEPS" and "surprise" columns; the fallback
        path also carries through yfinance's original columns (e.g. "Earnings").
        Either DataFrame is EMPTY when that series is unavailable (unknown ticker or no
        reported EPS), matching the other get_yfinance_* helpers; callers should check
        `.empty` rather than `is None`.
    """
    stock = get_finance_data(ticker)

    try:
        # Use get_earnings_dates for extended historical EPS data
        extended = _earnings_from_dates(stock, years)
        if extended is not None:
            return extended
    except Exception as exc:  # pylint:disable=W0718
        LOGGER.warning("Failed to get extended earnings data for %s: %s, falling back to basic earnings", ticker, exc)

    # Fallback to basic earnings data (limited to ~4 years)
    return _earnings_from_basic(stock)


def get_yfinance_overview(ticker: str):
    """Get company overview data from yfinance.

    :param ticker: (str) Company ticker symbol
    :return: pandas.Series of company information
    """
    LOGGER.debug("Ticker to lookup: %s", ticker)
    stock = get_finance_data(ticker)
    info = stock.info

    if info is None:
        return pd.Series()

    # Convert to pandas Series and standardize field names to match alphavantage format
    overview = pd.Series(info)

    # Map yfinance fields to alphavantage-style names where possible
    field_mapping = {
        "symbol": "Symbol",
        "longName": "Name",
        "sector": "Sector",
        "industry": "Industry",
        "marketCap": "MarketCapitalization",
        "ebitda": "EBITDA",
        "trailingPE": "PERatio",
        "pegRatio": "PEGRatio",
        "bookValue": "BookValue",
        "dividendYield": "DividendYield",
        "trailingEps": "EPS",
        "revenuePerShare": "RevenuePerShareTTM",
        "profitMargins": "ProfitMargin",
        "operatingMargins": "OperatingMarginTTM",
        "returnOnAssets": "ReturnOnAssetsTTM",
        "returnOnEquity": "ReturnOnEquityTTM",
        "totalRevenue": "RevenueTTM",
        "grossProfits": "GrossProfitTTM",
        "earningsQuarterlyGrowth": "QuarterlyEarningsGrowthYOY",
        "revenueQuarterlyGrowth": "QuarterlyRevenueGrowthYOY",
        "targetHighPrice": "AnalystTargetPrice",
        "forwardPE": "ForwardPE",
        "priceToSalesTrailing12Months": "PriceToSalesRatioTTM",
        "priceToBook": "PriceToBookRatio",
        "enterpriseToRevenue": "EVToRevenue",
        "enterpriseToEbitda": "EVToEBITDA",
        "beta": "Beta",
        "fiftyTwoWeekHigh": "52WeekHigh",
        "fiftyTwoWeekLow": "52WeekLow",
        "fiftyDayAverage": "50DayMovingAverage",
        "twoHundredDayAverage": "200DayMovingAverage",
        "sharesOutstanding": "SharesOutstanding",
        "dividendDate": "DividendDate",
        "exDividendDate": "ExDividendDate",
    }

    # Create new series with mapped field names
    mapped_overview = pd.Series()
    for yf_field, av_field in field_mapping.items():
        if yf_field in overview:
            mapped_overview[av_field] = overview[yf_field]

    # Add any unmapped fields from original
    for field, value in overview.items():
        if field not in field_mapping:
            mapped_overview[field] = value

    return mapped_overview


def get_yfinance_company_prices(ticker: str, period: str = "5y", interval: str = "1d"):
    """Get historical stock price data from yfinance.

    :param ticker: (str) Company ticker symbol
    :param period: (str) Period for historical data
    :param interval: (str) Data interval
    :return: pandas.DataFrame of stock price data
    """
    stock = get_finance_data(ticker)
    hist = stock.history(period=period, interval=interval)

    if hist.empty:
        return pd.DataFrame()

    # Rename columns to match alphavantage format
    hist = hist.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Dividends": "dividend_amt",
            "Stock Splits": "split_coefficient",
        }
    )

    # Add adjusted close if not present (yfinance Close is already adjusted)
    if "adj_close" not in hist.columns:
        hist["adj_close"] = hist["close"]

    # Add ticker column
    hist["ticker"] = ticker

    # Calculate technical indicators
    hist["SMA20"] = hist["close"].rolling(20).mean()
    hist["SMA50"] = hist["close"].rolling(50).mean()
    hist["SMA200"] = hist["close"].rolling(200).mean()
    hist["log_return"] = np.log(hist["close"]) - np.log(hist["close"].shift(1))

    # Ensure index is a tz-naive DatetimeIndex named 'date'. yfinance history returns a
    # tz-aware index, which would break the report's comparisons against tz-naive datetimes.
    if hist.index.tz is not None:
        hist.index = hist.index.tz_localize(None)
    hist.index.name = "date"
    hist.sort_index(ascending=True, inplace=True)

    return hist


def get_daily_yfinance_company_prices(ticker: str):
    """Get daily historical stock price data from yfinance.

    :param ticker: (str) Company ticker symbol
    :return: pandas.DataFrame of daily stock price data
    """
    return get_yfinance_company_prices(ticker, period="5y", interval="1d")


def get_weekly_yfinance_company_prices(ticker: str):
    """Get weekly historical stock price data from yfinance.

    :param ticker: (str) Company ticker symbol
    :return: pandas.DataFrame of weekly stock price data
    """
    return get_yfinance_company_prices(ticker, period="5y", interval="1wk")


def get_monthly_yfinance_company_prices(ticker: str):
    """Get monthly historical stock price data from yfinance.

    :param ticker: (str) Company ticker symbol
    :return: pandas.DataFrame of monthly stock price data
    """
    return get_yfinance_company_prices(ticker, period="5y", interval="1mo")


def _supplement_income_with_quarters(
    income_stmt: pd.DataFrame, quarterly_income: pd.DataFrame | None
) -> pd.DataFrame:
    """Append summed quarterly income for fiscal years missing from the annual statement.

    Income items are summed across the quarters of each missing fiscal year (only years with
    at least 4 quarters are included). Fiscal year is approximated by shifting quarter-end
    dates back ~2 months.

    :param income_stmt: transposed annual income statement (dates as index)
    :param quarterly_income: raw quarterly financials (fields as index), or None
    :return: income_stmt with supplemental annual rows appended
    """
    if quarterly_income is None or quarterly_income.empty:
        return income_stmt
    quarterly_income_t = quarterly_income.T
    annual_years = set(income_stmt.index.year)
    fiscal_years = (quarterly_income_t.index - pd.DateOffset(months=2)).year
    for fiscal_year in sorted(set(fiscal_years)):
        if fiscal_year in annual_years:
            continue
        year_quarters = quarterly_income_t[fiscal_years == fiscal_year]
        if len(year_quarters) >= 4:
            numeric_columns = year_quarters.select_dtypes(include="number").columns
            aggregated_row = year_quarters[numeric_columns].sum()
            aggregated_row.name = pd.Timestamp(f"{fiscal_year}-12-31")
            income_stmt = pd.concat([income_stmt, aggregated_row.to_frame().T])
    return income_stmt


def _supplement_balance_with_quarters(
    balance_sheet: pd.DataFrame, quarterly_balance: pd.DataFrame | None
) -> pd.DataFrame:
    """Append the latest quarterly snapshot for fiscal years missing from the annual balance sheet.

    Balance sheet items use the most recent quarter-end snapshot of each missing fiscal year.

    :param balance_sheet: transposed annual balance sheet (dates as index)
    :param quarterly_balance: raw quarterly balance sheet (fields as index), or None
    :return: balance_sheet with supplemental annual rows appended
    """
    if quarterly_balance is None or quarterly_balance.empty:
        return balance_sheet
    quarterly_balance_t = quarterly_balance.T
    annual_years = set(balance_sheet.index.year)
    fiscal_years = (quarterly_balance_t.index - pd.DateOffset(months=2)).year
    for fiscal_year in sorted(set(fiscal_years)):
        if fiscal_year in annual_years:
            continue
        year_quarters = quarterly_balance_t[fiscal_years == fiscal_year]
        if not year_quarters.empty:
            latest_snapshot = year_quarters.sort_index().iloc[[-1]].copy()
            latest_snapshot.index = [pd.Timestamp(f"{fiscal_year}-12-31")]
            balance_sheet = pd.concat([balance_sheet, latest_snapshot])
    return balance_sheet


def _extract_financial_metrics(
    income_stmt: pd.DataFrame, balance_sheet: pd.DataFrame, dates: pd.Index
) -> tuple[list, list, list]:
    """Extract per-date revenue, EPS, and shares outstanding aligned to income statement dates.

    EPS is Net Income / Shares Outstanding, using the balance sheet snapshot on the matching
    date. Missing inputs yield NaN.

    :param income_stmt: supplemented income statement (dates as index)
    :param balance_sheet: supplemented balance sheet (dates as index)
    :param dates: income statement dates to extract metrics for
    :return: tuple of (revenue, eps, shares_outstanding) lists parallel to dates
    """
    revenue = []
    eps = []
    shares_outstanding = []

    for date in dates:
        # Revenue (Total Revenue)
        if "Total Revenue" in income_stmt.columns:
            revenue.append(income_stmt.loc[date, "Total Revenue"])
        else:
            revenue.append(np.nan)

        # Shares outstanding (use balance sheet date closest to income statement date)
        shares_out = np.nan
        if date in balance_sheet.index:
            if "Ordinary Shares Number" in balance_sheet.columns:
                shares_out = balance_sheet.loc[date, "Ordinary Shares Number"]
            elif "Share Issued" in balance_sheet.columns:
                shares_out = balance_sheet.loc[date, "Share Issued"]
        shares_outstanding.append(shares_out)

        # Calculate EPS from Net Income and Shares Outstanding
        if "Net Income" in income_stmt.columns and not pd.isna(shares_out) and shares_out != 0:
            net_income = income_stmt.loc[date, "Net Income"]
            eps_calc = net_income / shares_out if not pd.isna(net_income) else np.nan
        else:
            eps_calc = np.nan
        eps.append(eps_calc)

    return revenue, eps, shares_outstanding


def process_yfinance_annual_company_info(ticker: str, years: int = 5):
    """Get company fundamentals from yfinance and process into format similar to alphavantage.

    Retrieves annual income statement and balance sheet data, supplementing with quarterly
    data to extend coverage beyond the default ~4 annual periods. Income statement items
    (revenue, net income) are summed across 4 quarters; balance sheet items (shares outstanding)
    use the latest quarter-end snapshot.

    :param ticker: (str) Company ticker symbol
    :param years: (int) Number of years of company data to retrieve (default 5)
    :return: company_data - DataFrame of company info {Year, ticker, revenue, eps}
    """
    stock = get_finance_data(ticker)

    # Get annual financial statements
    income_stmt = stock.financials  # Annual income statement
    balance_sheet = stock.balance_sheet  # Annual balance sheet

    if income_stmt is None or income_stmt.empty or balance_sheet is None or balance_sheet.empty:
        return pd.DataFrame()

    # Transpose to get dates as index
    income_stmt = income_stmt.T
    balance_sheet = balance_sheet.T

    # Supplement with quarterly data for fiscal years not covered by annual data
    income_stmt = _supplement_income_with_quarters(income_stmt, stock.quarterly_financials)
    balance_sheet = _supplement_balance_with_quarters(balance_sheet, stock.quarterly_balance_sheet)

    income_stmt.sort_index(ascending=True, inplace=True)
    balance_sheet.sort_index(ascending=True, inplace=True)

    # Align dates across both statements
    dates = income_stmt.index
    tickers = [ticker] * len(dates)

    # Extract key financial metrics
    revenue, eps, shares_outstanding = _extract_financial_metrics(income_stmt, balance_sheet, dates)

    # Create DataFrame
    company_data = pd.DataFrame(
        {"ticker": tickers, "revenue": revenue, "eps": eps, "shares_outstanding": shares_outstanding}, index=dates
    )

    company_data.index.name = "date"
    company_data.index = pd.to_datetime(company_data.index)
    company_data.sort_index(ascending=True, inplace=True)

    # Trim to requested number of years
    if len(company_data) > years:
        company_data = company_data.iloc[-years:]

    return company_data


async def download_stocks(stocks: list):
    """Download a collection of stocks from yfinance.

    :param stocks: <list> a list of stocks to lookup (or DataFrame with 'ticker' column)
    :return: pandas.DataFrame of combined stock price data
    """
    prices = pd.DataFrame()

    # Handle both list and DataFrame input
    if hasattr(stocks, "unique"):  # DataFrame case
        tickers = stocks["ticker"].unique().tolist()
    else:  # List case
        tickers = stocks

    for ticker in tickers:
        tmp_stock = get_daily_yfinance_company_prices(ticker)
        if not tmp_stock.empty:
            prices = pd.concat([tmp_stock, prices])

    # Save to pickle for compatibility
    prices.to_pickle(util.data_path("stocks.pkl"))
    return prices
