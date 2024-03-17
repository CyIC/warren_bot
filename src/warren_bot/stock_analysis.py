# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511, E1121
"""Stock Analysis functions for chatbot."""
import datetime
import logging

import discord
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from prettytable import PrettyTable

from warren_bot import alphavantage as alpha
from warren_bot import utilities as utils

YRS_LOOKBACK = 5
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)

float_formatter = "{:0.2f}".format
np.set_printoptions(formatter={"float_kind": float_formatter})


def populate_vars(old: float, new: float):
    """Generate variations between old metric number and new metric number.

    :param old: <float>
    :param new: <float>
    :return: difference and percent difference
    """
    diff = new - old
    try:
        percent_diff = diff / abs(old)
    except ZeroDivisionError:
        percent_diff = 0
    except Exception as e:  # pylint: disable=W0718
        logger.error(e)
        percent_diff = 0
    return diff, percent_diff


def past_sales_records(income_statement):
    """Build Past Sales Record section of report.

    :param income_statement:
    :return: <str> a message of the section to print
    """
    # Past Sales Records
    sales_per_year = income_statement["totalRevenue"]
    # Last year and year before sales
    recent_sales_trend = (sales_per_year[-1] + sales_per_year[-2]) / 2
    # Years 5 and 6 sales
    past_sales_trend = (sales_per_year[0] + sales_per_year[1]) / 2
    sales_increase = recent_sales_trend - past_sales_trend
    sales_percent_increase = sales_increase / past_sales_trend
    compound_annual_sales_growth_rate = pow((sales_per_year[-1] / sales_per_year[0]), 1 / YRS_LOOKBACK) - 1
    # display table
    past_sales_record_table = PrettyTable(float_format=".4")
    past_sales_record_table.header = False
    past_sales_record_table.border = False
    past_sales_record_table.add_row(["Sales for most recent year", "${:20,.0f}".format(sales_per_year[-1])])
    past_sales_record_table.add_row(["Sales for next most recent year", "${:20,.0f}".format(sales_per_year[-2])])
    past_sales_record_table.add_row(
        [
            "Sales for {} years ago".format(YRS_LOOKBACK - 1),
            "${:20,.0f}".format(sales_per_year[1]),
        ]
    )
    past_sales_record_table.add_row(
        [
            f"Sales for {YRS_LOOKBACK} years ago",
            f"${sales_per_year[0]:20,.0f}",
        ]
    )
    past_sales_record_table.add_row(["% increase in sales", f"{sales_percent_increase.round(4):.3%}"])
    past_sales_record_table.add_row(
        [
            "Compound Annual Sales Growth Rate",
            f"{compound_annual_sales_growth_rate.round(4):.3%}",
        ]
    )
    past_sales_record_table.align["Field 1"] = "l"
    past_sales_record_table.align["Field 2"] = "r"
    return f"__**Past Sales Records**__\n```{past_sales_record_table}```"


def past_eps(earnings):
    """Build Past EPS section of report.

    :param earnings:
    :return: <str> a message of the section to print
    """
    earnings = earnings[earnings.index >= datetime.datetime.now() - relativedelta(years=5)]
    # Last year and year before EPS
    recent_eps_mean = (earnings.iloc[-1] + earnings.iloc[-2]) / 2
    # Years 4 and 5 EPS
    past_eps_mean = (earnings.iloc[1] + earnings.iloc[0]) / 2
    eps_increase = recent_eps_mean - past_eps_mean
    eps_percent_increase = eps_increase / past_eps_mean
    compound_annual_eps_growth_rate = pow(earnings.iloc[-1] / earnings.iloc[0], (1 / YRS_LOOKBACK)) - 1
    # display table
    past_eps_record_table = PrettyTable()
    past_eps_record_table.align = "l"
    past_eps_record_table.align["Field 2"] = "r"
    past_eps_record_table.header = False
    past_eps_record_table.border = False
    past_eps_record_table.add_row(["EPS for most recent year", f"{earnings.iloc[-1].round(4)[0]:10.4f} "])
    past_eps_record_table.add_row(
        [
            "EPS for next most recent year",
            f"{earnings.iloc[-2].round(4)[0]:10.4f} ",
        ]
    )
    past_eps_record_table.add_row(
        [
            f"EPS for {YRS_LOOKBACK - 1} years ago",
            f"{earnings.iloc[1].round(4)[0]:10.4f} ",
        ]
    )
    past_eps_record_table.add_row(
        [
            f"EPS for {YRS_LOOKBACK} years ago",
            f"{earnings.iloc[0].round(4)[0]:10.4f}",
        ]
    )
    past_eps_record_table.add_row(["% increase in earnings", f"{eps_percent_increase.round(4)[0]:10.4%}"])
    past_eps_record_table.add_row(
        ["Compound Annual rate of EPS", f"{compound_annual_eps_growth_rate.round(4)[0]:10.4%}"]
    )
    msg = "\n__**Past EPS**__\n"
    msg += f"*EPS per year*: ```{earnings}```"
    msg += f"```{past_eps_record_table}```"
    return msg


def record_of_stock(eps, income_statement, daily_prices, monthly_prices):
    """Build record of stock section of analysis.

    :param eps:
    :param income_statement:
    :param stock_price_json:
    :param monthly_prices:
    :return: <tuple> (<list> a list of message chunks to print, <float> max high_yield)
    """
    # pylint: disable=R0915, R0914, W0212
    msg = []
    msg.append("\n__**Record of Stock**__\n")

    # Get only last 5 years of yearly earnings
    eps_per_year = eps["annualEarnings"]
    eps_per_year = eps_per_year[eps_per_year.index >= datetime.datetime.now() - relativedelta(years=5)]
    # Get only last 5 years of quarterly earnings
    quarterly_eps = eps["quarterlyEarnings"]
    quarterly_eps = quarterly_eps[quarterly_eps.index >= datetime.datetime.now() - relativedelta(years=5)]

    # get current stock prices
    present_price = daily_prices["close"][-1]
    # get current eps
    present_eps = quarterly_eps.iloc[-1]["reportedEPS"]
    # get monthly prices
    msg.append(f"*Present Price*:\t**{present_price:.3f}**\t*Present EPS*:\t**{present_eps:.3f}**")
    # Display
    high_prices = []
    low_prices = []
    pe_high = []
    pe_low = []
    percent_payout = []
    high_yield = []
    eps_table = PrettyTable(
        [
            "List Last 5 Years",
            "High Price",
            "Low Price",
            "EPS",
            "PE Ratio at High",
            "PE Ratio at Low",
            "Dividend per Share",
            "% Payout",
            "% High Yield",
        ],
        float_format=".3",
    )
    # x.float_format = '.4'
    eps_table.align = "r"
    eps_table.align["PE Ratio at High"] = "c"
    eps_table.align["PE Ratio at Low"] = "c"
    for yr in eps_per_year.index:
        high = float(monthly_prices.loc[yr.strftime("%Y")]["high"].max())
        high_prices.append(high)
        low = float(monthly_prices.loc[yr.strftime("%Y")]["low"].min())
        low_prices.append(low)
        eps = eps_per_year.loc[yr][-1]
        pe_high.append(high / eps)
        pe_low.append(low / eps)
        div_per_share = monthly_prices.loc[yr.strftime("%Y")]["dividend_amt"].sum()
        pct_payout = (div_per_share / eps) * 100
        percent_payout.append(pct_payout)
        h_yield = (div_per_share / low) * 100
        high_yield.append(h_yield)
        eps_table.add_row(
            [
                yr,
                f"${high:15,.2f}",
                f"${low:15,.2f}",
                eps,
                f"{high / eps:15,.4f}",
                f"{low / eps:15,.4f}",
                f"{div_per_share:15,.2f}",
                f"{pct_payout:15,.2f}",
                f"{h_yield:15,.2f}",
            ]
        )
    high_prices = pd.Series(high_prices)
    low_prices = pd.Series(low_prices)
    pe_high = pd.Series(pe_high)
    pe_low = pd.Series(pe_low)
    percent_payout = pd.Series(percent_payout)
    high_yield = pd.Series(high_yield)
    eps_table.add_row(
        [
            "Averages",
            f"${high_prices.mean():15,.2f}",
            f"${low_prices.mean():15,.2f}",
            "",
            f"{pe_high.mean():15,.4f}",
            f"{pe_low.mean():15,.4f}",
            "",
            f"{percent_payout.mean():15,.2f}",
            "",
        ]
    )
    msg.append(f"```{eps_table}```")
    y = PrettyTable([], float_format=".4")
    y.header = False
    # y.border = False
    y._max_width = {
        "Field 1": 15,
        "Field 2": 20,
        "Field 3": 15,
        "Field 4": 20,
        "Field 5": 20,
        "Field 6": 20,
    }
    # Past Sales Records  ********** get sales_percent_increase  ****************
    sales_per_year = income_statement["annualReports"]["totalRevenue"]
    # Last year and year before sales
    recent_sales_trend = (sales_per_year[-1] + sales_per_year[-2]) / 2
    # Years 5 and 6 sales
    past_sales_trend = (sales_per_year[0] + sales_per_year[1]) / 2
    sales_increase = recent_sales_trend - past_sales_trend
    sales_percent_increase = sales_increase / past_sales_trend

    # Last year and year before EPS  ************** GET eps_percent_increase *************
    recent_eps_mean = (eps_per_year.iloc[-1] + eps_per_year.iloc[-2]) / 2
    # Years 4 and 5 EPS
    past_eps_mean = (eps_per_year.iloc[1] + eps_per_year.iloc[0]) / 2
    eps_increase = recent_eps_mean - past_eps_mean
    eps_percent_increase = eps_increase[0] / past_eps_mean[0]

    y.add_row(
        [
            f"Present Price % difference then high price {YRS_LOOKBACK} years ago",
            f"{((present_price - high_prices.values[-1]) / high_prices.values[-1]):.4%}",
            "% Increase in Sales",
            f"{sales_percent_increase:.4%}",
            "% Increase in Earnings",
            f"{eps_percent_increase:.4%}",
        ]
    )
    # pylint: disable-next=consider-using-f-string
    msg.append(
        "*Average PE Ratio*:\t{:20.4f}\t*Current PE Ratio*\t{:20.4f}".format(
            pd.concat([pe_high, pe_low]).mean(),
            present_price / present_eps,
        )
    )
    msg.append(f"```{y}```")
    msg.append("**% Payout** is `Dividend per share / EPS` \t**% High Yield** is `Dividend per share / Low Price`")
    return msg, high_yield.max()


def trend(
    income_statement: pd.DataFrame,
    eps: pd.DataFrame,
    monthly_company_prices: pd.DataFrame,
):
    """Build Trend section of analysis.

    :param income_statement: <pandas.DatFrame>
    :param eps: <pandas.DatFrame>
    :param monthly_company_prices: <pandas.DatFrame>
    :return: <tuple> (<str> a message of the section to print, <list> of chart figure file names)
    """
    msg = "\n__**Trends**__"
    files = []
    quarterly_revenue = income_statement["quarterlyReports"]
    quarterly_revenue = quarterly_revenue["totalRevenue"]
    quarterly_revenue = quarterly_revenue[quarterly_revenue.index >= datetime.datetime.now() - relativedelta(years=5)]
    quarterly_eps = eps["quarterlyEarnings"]
    quarterly_eps = quarterly_eps[quarterly_eps.index >= datetime.datetime.now() - relativedelta(years=5)]
    # Quarterly Revenue
    fig1, revenue_fig = plt.subplots()  # pylint: disable=W0612
    revenue_fig.set_xlabel("Date")
    revenue_fig.set_ylabel("Revenue", color="tab:red")
    revenue_fig.plot(quarterly_revenue, color="tab:red")
    revenue_fig.set_title("Revenue & EPS")
    # Quarterly EPS
    eps_fig = revenue_fig.twinx()
    eps_fig.set_ylabel("EPS", color="tab:blue")
    eps_fig.plot(quarterly_eps["reportedEPS"])
    # Price high/low
    plt.savefig("./eps_fig.jpg")
    files.append("./eps_fig.jpg")

    # Plot Stock Highs and Lows
    monthly_company_prices["avg_high"] = monthly_company_prices["high"].rolling(4).mean()
    monthly_company_prices["avg_low"] = monthly_company_prices["low"].rolling(4).mean()
    monthly_company_prices.plot(
        y=["high", "low", "avg_high", "avg_low"],
        title="Stock High & Low",
        xlabel="Date",
        ylabel="USD",
    )
    plt.savefig("./stock_high_low.jpg")
    files.append("./stock_high_low.jpg")
    return msg, files


def cash_position(balance_sheet: pd.DataFrame):
    """Build Cash Position section of report.

    :param balance_sheet: <pandas.DataFrame> Balance sheet DataFrame from alphavantage
    :return: <str> a message of the section to print
    """
    # pylint: disable=R0915, R0914
    msg = []
    annual_reports = balance_sheet["annualReports"]
    annual_reports = annual_reports[annual_reports.index >= datetime.datetime.now() - relativedelta(years=5)]
    msg.append("\n__**Cash Position**__")
    cash_table = PrettyTable(
        [
            "",
            annual_reports.index[-1].year,
            annual_reports.index[-2].year,
            "Difference",
            "% Difference",
        ],
        float_format=".4",
    )
    # cash_table.border = False
    cash_table.align = "r"
    cash_table.align[""] = "l"

    new_cash = annual_reports["cashAndCashEquivalentsAtCarryingValue"][-1]
    old_cash = annual_reports["cashAndCashEquivalentsAtCarryingValue"][-2]
    diff_cash, percent_diff_cash = populate_vars(old_cash, new_cash)
    cash_table.add_row(
        [
            "Cash and Equivalents",
            f"${new_cash:20,.0f}",  # Newest cash
            f"${old_cash:20,.0f}",  # Oldest cash
            f"${diff_cash:20,.0f}",
            f"{percent_diff_cash:.4%}",
        ]
    )

    new_investments = annual_reports["shortTermInvestments"][-1]
    old_investments = annual_reports["shortTermInvestments"][-2]
    diff_investments, percent_diff_investments = populate_vars(old_investments, new_investments)
    cash_table.add_row(
        [
            "Short Term Investments",
            f"${new_investments:20,.0f}",
            f"${old_investments:20,.0f}",
            f"${diff_investments:20,.0f}",
            f"{percent_diff_investments:.4%}",
        ]
    )

    new_total_cash = new_cash + new_investments
    old_total_cash = old_cash + old_investments
    diff_total_cash, percent_diff_total_cash = populate_vars(old_total_cash, new_total_cash)
    cash_table.add_row(
        [
            "Overall Cash Positions",
            f"${new_total_cash:20,.0f}",
            f"${old_total_cash:20,.0f}",
            f"${diff_total_cash:20,.0f}",
            f"{percent_diff_total_cash:.4%}",
        ]
    )

    new_long_term_debt = annual_reports["longTermDebt"][-1]
    old_long_term_debt = annual_reports["longTermDebt"][-2]
    diff_lt_debt, percent_diff_lt_debt = populate_vars(old_long_term_debt, new_long_term_debt)
    cash_table.add_row(["", "", "", "", ""])
    cash_table.add_row(
        [
            "Long Term Debt",
            f"${new_long_term_debt:20,.0f}",
            f"${old_long_term_debt:20,.0f}",
            f"${diff_lt_debt:20,.0f}",
            f"{percent_diff_lt_debt:.4%}",
        ]
    )

    new_net_cash = new_total_cash - new_long_term_debt
    old_net_cash = old_total_cash - old_long_term_debt
    diff_net_cash, percent_diff_net_cash = populate_vars(old_net_cash, new_net_cash)
    cash_table.add_row(["", "", "", "", ""])
    cash_table.add_row(
        [
            "Net cash position",
            f"${new_net_cash:20,.0f}",
            f"${old_net_cash:20,.0f}",
            f"${diff_net_cash:20,.0f}",
            f"{percent_diff_net_cash:.4%}",
        ]
    )
    # add shares outstanding
    cash_table.add_row(["", "", "", "", ""])
    new_shares = annual_reports["commonStockSharesOutstanding"][-1]
    old_shares = annual_reports["commonStockSharesOutstanding"][-2]
    diff_shares, percent_diff_shares = populate_vars(old_shares, new_shares)
    cash_table.add_row(
        [
            "Shares outstanding",
            f"${new_shares:20,.0f}",
            f"${old_shares:20,.0f}",
            f"${diff_shares:20,.0f}",
            f"{percent_diff_shares:.4%}",
        ]
    )
    new_cash_share = new_net_cash / new_shares
    old_cash_share = old_net_cash / old_shares
    diff_cash_share, percent_diff_cash_share = populate_vars(old_cash_share, new_cash_share)

    cash_table.add_row(
        [
            "Net cash per share",
            f"${new_cash_share:20,.4f}",
            f"${old_cash_share:20,.4f}",
            f"${diff_cash_share:20,.4f}",
            f"{percent_diff_cash_share:.4%}",
        ]
    )
    msg.append(f"```{cash_table}```")

    # Assets & liabilities
    avl_table = PrettyTable(
        [
            "",
            annual_reports.index[-1].year,
            annual_reports.index[-2].year,
            "Difference",
            "% Difference",
        ],
        float_format=".4",
    )
    avl_table.align = "r"
    avl_table.align[""] = "l"

    avl_table.add_row(["---Assets---", "", "", "", ""])
    avl_table.add_row(
        [
            "Cash",
            f"${new_cash:20,.0f}",
            f"${old_cash:20,.0f}",
            f"${diff_cash:20,.0f}",
            f"{percent_diff_cash:.4%}",
        ]
    )

    old_receivables = annual_reports["currentNetReceivables"][-2]
    new_receivables = annual_reports["currentNetReceivables"][-1]
    diff_receivables, percent_diff_receivables = populate_vars(old_receivables, new_receivables)
    avl_table.add_row(
        [
            "Recievables",
            f"${new_receivables:20,.0f}",
            f"${old_receivables:20,.0f}",
            f"${diff_receivables:20,.0f}",
            f"{percent_diff_receivables:.4%}",
        ]
    )
    old_inventories = annual_reports["inventory"][-2]
    new_inventories = annual_reports["inventory"][-1]
    diff_inventories, percent_diff_inventories = populate_vars(old_inventories, new_inventories)
    avl_table.add_row(
        [
            "Inventories",
            f"${new_inventories:20,.0f}",
            f"${old_inventories:20,.0f}",
            f"${diff_inventories:20,.0f}",
            f"{percent_diff_inventories:.4%}",
        ]
    )
    old_other_assets = annual_reports["otherCurrentAssets"][-2]
    new_other_assets = annual_reports["otherCurrentAssets"][-1]
    diff_other_assets, percent_diff_other_assets = populate_vars(old_other_assets, new_other_assets)
    avl_table.add_row(
        [
            "Other Assets",
            f"${new_other_assets:20,.0f}",
            f"${old_other_assets:20,.0f}",
            f"${diff_other_assets:20,.0f}",
            f"{percent_diff_other_assets:.4%}",
        ]
    )
    old_current_assets = annual_reports["totalCurrentAssets"][-2]
    new_current_assets = annual_reports["totalCurrentAssets"][-1]
    diff_current_assets, percent_diff_current_assets = populate_vars(old_current_assets, new_current_assets)
    avl_table.add_row(
        [
            "Current Assets",
            f"${new_current_assets:20,.0f}",
            f"${old_current_assets:20,.0f}",
            f"${diff_current_assets:20,.0f}",
            f"{percent_diff_current_assets:.4%}",
        ]
    )
    msg.append(f"```{avl_table}```")

    # Reset and build Liabilities Table
    avl_table = PrettyTable(
        [
            "",
            annual_reports.index[-1].year,
            annual_reports.index[-2].year,
            "Difference",
            "% Difference",
        ],
        float_format=".3",
    )
    avl_table.align = "r"
    avl_table.align[""] = "l"
    avl_table.add_row(["---Liabilities---", "", "", "", ""])
    old_payables = annual_reports["currentAccountsPayable"][0]
    new_payables = annual_reports["currentAccountsPayable"][-1]
    diff_payables, percent_diff_payables = populate_vars(old_payables, new_payables)
    avl_table.add_row(
        [
            "Payables",
            f"${new_payables:20,.0f}",
            f"${old_payables:20,.0f}",
            f"${diff_payables:20,.0f}",
            f"{percent_diff_payables:.3%}",
        ]
    )
    old_st_debt = annual_reports["shortTermDebt"][-2]
    new_st_debt = annual_reports["shortTermDebt"][-1]
    diff_st_debt, percent_diff_st_debt = populate_vars(old_st_debt, new_st_debt)
    avl_table.add_row(
        [
            "Short Term Debt",
            f"${new_st_debt:20,.0f}",
            f"${old_st_debt:20,.0f}",
            f"${diff_st_debt:20,.0f}",
            f"{percent_diff_st_debt:.4%}",
        ]
    )
    old_other_liabilities = annual_reports["otherCurrentLiabilities"][-2]
    new_other_liabilities = annual_reports["otherCurrentLiabilities"][-1]
    diff_other_liabilities, percent_diff_other_liabilities = populate_vars(old_other_liabilities, new_other_liabilities)
    avl_table.add_row(
        [
            "Other Liabilities",
            f"${new_other_liabilities:20,.0f}",
            f"${old_other_liabilities:20,.0f}",
            f"${diff_other_liabilities:20,.0f}",
            f"{percent_diff_other_liabilities:.3%}",
        ]
    )
    old_current_liabilities = annual_reports["totalCurrentLiabilities"][-2]
    new_current_liabilities = annual_reports["totalCurrentLiabilities"][-1]
    diff_current_liabilities, percent_diff_current_liabilities = populate_vars(
        old_current_liabilities, new_current_liabilities
    )
    avl_table.add_row(
        [
            "Current Liabilities",
            f"${new_current_liabilities:20,.0f}",
            f"${old_current_liabilities:20,.0f}",
            f"${diff_current_liabilities:20,.0f}",
            f"{percent_diff_current_liabilities:.3%}",
        ]
    )

    avl_table.add_row(["", "", "", "", ""])
    old_avl = old_current_assets - old_current_liabilities
    new_avl = new_current_assets - new_current_liabilities
    diff_avl, percent_diff_avl = populate_vars(old_avl, new_avl)
    avl_table.add_row(
        [
            "Asset Vs Liabilities",
            f"${new_avl:20,.0f}",
            f"${old_avl:20,.0f}",
            f"${diff_avl:20,.0f}",
            f"{percent_diff_avl:.4%}",
        ]
    )
    avl_table.add_row(["", "", "", "", ""])
    cash_table.add_row(
        [
            "Shares outstanding",
            f"${new_shares:20,.0f}",
            f"${old_shares:20,.0f}",
            f"${diff_shares:20,.0f}",
            f"{percent_diff_shares:.3%}",
        ]
    )
    old_net_cps = old_avl / old_shares
    new_net_cps = new_avl / new_shares
    diff_net_cps, percent_diff_net_cps = populate_vars(old_net_cps, new_net_cps)
    avl_table.add_row(
        [
            "Net cash per share",
            f"${new_net_cps:20,.3f}",
            f"${old_net_cps:20,.3f}",
            f"${diff_net_cps:20,.3f}",
            f"{percent_diff_net_cps:.3%}",
        ]
    )
    # Display
    msg.append(f"```{avl_table}```")
    return msg


def revenue_growth(
    daily_prices: pd.DataFrame,
    cash_flow: pd.DataFrame,
    income_statement: pd.DataFrame,
    current_eps: float,
    current_shares_outstanding: int,
):
    # pylint: disable=C0209
    """Build Revenue Growth section of report.

    :param daily_prices: <pd.DataFrame> Current Daily Prices for company
    :param cash_flow: <pd.DataFrame> Current Cash Flow Statement
    :param income_statement: <pd.DataFrame> Current Income Statement
    :param current_eps: <float>
    :param current_shares_outstanding: <int>
    :return: <str> a message of the section to print
    """
    msg = "\n__**Revenue Growth**__"
    cash_flow = cash_flow["annualReports"]
    try:
        dividend_yield = cash_flow["dividendPayout"].iloc[-1] / current_shares_outstanding
    except TypeError as e:
        logger.error(e)
        dividend_yield = 0
    revenue = income_statement["annualReports"]
    revenue = pd.DataFrame(revenue["totalRevenue"])
    revenue_diff = revenue.diff()
    revenue["change"] = revenue_diff
    revenue["%_change"] = revenue["change"].div(revenue["totalRevenue"])

    pd.options.display.float_format = "{:,.3f}".format
    msg += f"```{revenue}```"
    msg += f"```Average Growth: {revenue['%_change'].mean():.3%}```"
    msg += f"```div yield: {dividend_yield:.3f}```"
    current_price = daily_prices["close"][-1]
    current_pe = current_price / current_eps
    msg += f"```Current P/E: {current_pe:.4f}```"
    msg += "```Growth Rate w/ Dividends: {:.3f}```".format(
        ((revenue["%_change"].mean() * 10) + dividend_yield) / current_pe
    )
    return msg


def earnings_growth(cash_flow: pd.DataFrame):
    """Build Earnings growth section of stock analysis.

    :param cash_flow: <dict> json of cash flow
    :return: <str> a message of the analysis to print
    """
    msg = "__**Earnings Growth**__"
    earnings_table = PrettyTable(["Year", "Net Income", "Change", "% Change"], float_format=".4")
    earnings_table.align = "r"
    earning_growth = cash_flow["annualReports"]
    earning_growth = pd.DataFrame(earning_growth["netIncome"])
    # earnings_growth['Change'] = earnings_growth.diff()
    # earnings_growth['% Change'] = earnings_growth['Change'].div(earnings_growth['netIncome'])
    last_year = None
    date = earning_growth.index
    change = 0
    percent_change = 0
    count = 0
    for year in earning_growth["netIncome"]:
        if last_year is not None:
            change = year - last_year
            percent_change = change / abs(last_year)
        earnings_table.add_row(
            [
                f"{date[count].year}",
                f"${year:20,.0f}",
                f"${change:20,.0f}",
                f"{percent_change:.3%}",
            ]
        )
        last_year = year
        count += 1
        # date.append(year[0])
    msg += f"```{earnings_table}```"
    return msg


def predict_low(high: float, low: float, current_price: float):
    """Build out the table for buy/maybe/sell options.

    :param high: <float> Predicted stock high
    :param low: <float> Predicted stock low
    :param current_price: <float> Current price of a stock
    :return: <str> a message of the prediction to print
    """
    # pylint: disable=C0209
    assert high > low
    quarter_range = (high - low) / 3
    if current_price < (low + quarter_range):
        decision = "BUY"
    elif current_price > (high - quarter_range):
        decision = "SELL"
    else:
        decision = "Maybe"
    msg = """```Lower 1/3 = {low_low:,.2f} to {low_high:,.2f} (Buy)
Middle 1/3 = {mid_low:,.2f} to {mid_high:,.2f} (Maybe)
Upper 1/3 = {high_low:,.2f} to {high_high:,.2f} (Sell)```
*Present Market Price of {present_price:,.2f} is in the **{decision}** range*
""".format(
        low_low=low,
        low_high=low + quarter_range,
        mid_low=low + quarter_range,
        mid_high=low + quarter_range * 2,
        high_low=high - quarter_range,
        high_high=high,
        present_price=current_price,
        decision=decision,
    )
    return msg


def risk_reward(
    daily_prices: pd.DataFrame,
    eps: pd.DataFrame,
    monthly_company_prices: pd.DataFrame,
    income_statement: pd.DataFrame,
    high_yield: float,
):
    # pylint: disable=R0915, R0912, R0914, C0209
    """Build Risk/Reward analysis of stock report.

    :param company_data:
    :param stock_price_json:
    :param cash_flow_json:
    :param monthly_company_price_json:
    :param income_statement_json:
    :param high_yield:
    :return:
    """
    msg = "\n__**Evaluating Risk & Reward**__"
    present_price = float(daily_prices["close"][-1])
    files = []
    # Build PE High
    yearly_eps = eps["annualEarnings"]
    yearly_eps = yearly_eps[yearly_eps.index >= datetime.datetime.now() - relativedelta(years=5)]
    quarterly_eps = eps["quarterlyEarnings"]
    quarterly_eps = quarterly_eps[quarterly_eps.index >= datetime.datetime.now() - relativedelta(years=5)]
    pe_high = []
    div_per_share = []
    for yr in yearly_eps.index:
        high = float(monthly_company_prices.loc[yr.strftime("%Y")]["high"].max())
        newest_eps = yearly_eps.loc[yr.strftime("%Y")]["reportedEPS"][-1]
        div_per_share.append(monthly_company_prices.loc[yr.strftime("%Y")]["dividend_amt"].sum())
        pe_high.append(high / newest_eps)
    pe_high = pd.Series(pe_high, index=yearly_eps.index)
    div_per_share = pd.Series(div_per_share, index=yearly_eps.index)
    # filter daily_prices to last 5 years
    daily_prices = daily_prices[daily_prices.index >= datetime.datetime.now() - relativedelta(years=5)]
    future_five_years = datetime.datetime.now() + relativedelta(years=5)

    # Build EPS prediction
    time = quarterly_eps.index.tolist()
    # convert time to UNIX Epoch time for x values
    tmp_time = []
    eps_pred = []
    for y in time:
        tmp_time.append(y.timestamp())
    eps_prediction = np.polynomial.polynomial.Polynomial.fit(tmp_time, quarterly_eps["reportedEPS"], 1)
    for y in time:
        eps_pred.append(eps_prediction(y.timestamp()))
    est_high_eps = eps_prediction(future_five_years.timestamp())
    eps_pred = pd.Series(pd.to_numeric(eps_pred), index=pd.to_datetime(time))
    # convert arrays to DataFrame for plotting
    tmp_info = {"eps": quarterly_eps["reportedEPS"], "eps_pred": eps_pred}
    quarterly_eps = pd.DataFrame(tmp_info, index=time)
    quarterly_eps.index.name = "date"
    quarterly_eps.index = pd.to_datetime(time)
    quarterly_eps.sort_index(ascending=True, inplace=True)
    quarterly_eps.plot()
    plt.savefig("./eps_pred_fig.jpg")
    files.append("./eps_pred_fig.jpg")
    forcast_high = pe_high.mean() * est_high_eps

    # Build High Revenue Prediction
    revenue = income_statement["quarterlyReports"]
    revenue = revenue["totalRevenue"].tolist()
    time = income_statement["quarterlyReports"].index.tolist()
    # Build prediction
    # Convert times to Unix Epoch time for x vars for prediction
    tmp_time = []
    for y in time:
        tmp_time.append(y.timestamp())
    revenue_prediction = np.polynomial.polynomial.Polynomial.fit(tmp_time, revenue, 1)
    # Build revenue & prediction DataFrame
    revenue = pd.Series(revenue, index=time)
    revenue_pred = []
    for y in time:
        revenue_pred.append(revenue_prediction(y.timestamp()))
    revenue_pred = pd.Series(revenue_pred, index=time)
    tmp_info = {"revenue": revenue, "revenue_pred": revenue_pred}
    quarterly_revenue = pd.DataFrame(tmp_info, index=time)
    quarterly_revenue.index.name = "date"
    quarterly_revenue.index = pd.to_datetime(time)
    quarterly_revenue.sort_index(ascending=True, inplace=True)
    # Plot revenue and prediction
    quarterly_revenue.plot()
    plt.savefig("./revenue_pred_fig.jpg")
    files.append("./revenue_pred_fig.jpg")

    # Sales to EPS Prediction
    # print('PE High Mean: {}'.format(pe_high.mean()))
    # print('Predicted Revenue: {}'.format(revenue_prediction(future_five_years.timestamp())))
    # print('shares_outstanding: {}'.format(current_stocks_outstanding))
    # print('forcast_pe_high: {}'.format(est_high_eps))
    # forcast_high = pe_high.mean() * (revenue_prediction(future_five_years.timestamp()) /
    #                                  pd.to_numeric(company_data['shares_outstanding'].iloc[-1]))

    # Build High Price Prediction
    msg += f"""\n**HIGH PRICE - NEXT 5 YEARS**
```Linear Regression of Highs: {forcast_high}```\n"""

    # Build Low Price Predictions
    # Calculate linear regression low
    low_prices = daily_prices["low"].values.tolist()
    time = daily_prices.index.tolist()
    tmp_time = []
    for y in time:
        tmp_time.append(y.timestamp())
    low_price_prediction = np.polynomial.polynomial.Polynomial.fit(tmp_time, low_prices, 1)
    lr_low = low_price_prediction(future_five_years.timestamp())

    # Plot Low Prices and Prediction
    low_prices = pd.Series(low_prices, index=time)
    low_price_pred = []
    for y in time:
        low_price_pred.append(low_price_prediction(y.timestamp()))
    low_price_pred = pd.Series(low_price_pred, index=time)
    tmp_info = {"low": low_prices, "low_price_pred": low_price_pred}
    low_prices = pd.DataFrame(tmp_info, index=time)
    low_prices.index.name = "date"
    low_prices.index = pd.to_datetime(time)
    low_prices.sort_index(ascending=True, inplace=True)
    low_prices.plot()
    plt.savefig("./low_price_pred_fig.jpg")
    files.append("./low_price_pred_fig.jpg")

    # Build High Price Predictions
    # Calculate linear regression high
    high_prices = daily_prices["high"].values.tolist()
    time = daily_prices.index.tolist()
    tmp_time = []
    for y in time:
        tmp_time.append(y.timestamp())
    high_price_prediction = np.polynomial.polynomial.Polynomial.fit(tmp_time, high_prices, 1)

    # Plot Low Prices and Prediction
    high_prices = pd.Series(high_prices, index=time)
    high_price_pred = []
    for y in time:
        high_price_pred.append(high_price_prediction(y.timestamp()))
    high_price_pred = pd.Series(high_price_pred, index=time)
    tmp_info = {"high": high_prices, "high_price_pred": high_price_pred}
    high_prices = pd.DataFrame(tmp_info, index=time)
    high_prices.index.name = "date"
    high_prices.index = pd.to_datetime(time)
    high_prices.sort_index(ascending=True, inplace=True)
    high_prices.plot()
    plt.savefig("./high_price_pred_fig.jpg")
    files.append("./high_price_pred_fig.jpg")

    # Calculate severe low
    severe_low = daily_prices["low"].min()
    # Calculate avg low
    avg_low = daily_prices["low"].mean()
    # Calculate Dividend low
    try:
        price_dividend = pd.to_numeric(div_per_share.iloc[-1]) / (high_yield / 100)
    except ValueError as e:
        logger.error(e)
        price_dividend = None
    msg += """**LOW PRICE - NEXT 5 YEARS**
```(a) Linear Regression of Lows: {a}
(b) Avg Low Price of Last 5 Years: {b}
(c) Recent Severe Market Low Price: {c}
(d) Price Dividend will Support: {d}```
""".format(
        a=lr_low, b=avg_low, c=severe_low, d=price_dividend
    )
    # Build Zoning
    msg += "**ZONING**"
    # Predict A
    msg += "\n(a - Linear Regression)"
    try:
        msg += predict_low(forcast_high, lr_low, present_price)
        lr_low = (forcast_high - present_price) / (present_price - lr_low)
    except TypeError as e:
        msg += f"```{e}```"
        lr_low = 0
    except AssertionError:
        msg += "```NaN```"
        lr_low = 0
    # Predict B
    msg += "\n(b - Avg Low Price of Last 5 Years)"
    try:
        msg += predict_low(forcast_high, avg_low, present_price)
        avg_low = (forcast_high - present_price) / (present_price - avg_low)
    except TypeError as e:
        msg += f"```{e}```"
        avg_low = 0
    except AssertionError:
        msg += "```NaN```"
        avg_low = 0
    # Predict C
    msg += "\n(c - Recent Severe Market Low)"
    try:
        msg += predict_low(forcast_high, severe_low, present_price)
        severe_low = (forcast_high - present_price) / (present_price - severe_low)
    except TypeError as e:
        msg += f"```{e}```"
        severe_low = 0
    except AssertionError:
        msg += "```NaN```"
        severe_low = 0
    # Predict D
    msg += "\n(d - Price Dividend Support)"
    try:
        msg += predict_low(forcast_high, price_dividend, present_price)
        dividend_low = (forcast_high - present_price) / (present_price - price_dividend)
    except TypeError as e:
        msg += f"```{e}```"
        dividend_low = 0
    except AssertionError:
        msg += "```NaN```"
        dividend_low = 0
    # Build UP-SIDE DOWN-SIDE Ration
    msg += """\n**UP-SIDE / DOWN-SIDE RATIO (Potential Gain vs Risk of Loss)**"""
    msg += """```a) {lr_low:.4f} to 1
b) {avg_low:.4f} to 1
c) {severe_low:.4f} to 1
d) {dividend_low:.4f} to 1```""".format(
        lr_low=lr_low, avg_low=avg_low, severe_low=severe_low, dividend_low=dividend_low
    )
    # TODO Build Price Targe
    msg += """\n**PRICE TARGET**
```${:,.2f} 5yr predicted stock price drives {:,.4f}% appreciation```""".format(
        forcast_high, (forcast_high / present_price) * 100 - 100
    )
    return msg, files


async def run(message, ticker, alphavantage_key=None):
    """Run stock analysis.

    :param message: <discord.message> Discord message object to make replys to
    :param ticker: Company stock ticker
    :param alphavantage_key: Alphavantage API key
    :return:
    """
    # Get Company Data
    income_statement = await alpha.get_alphavantage_income_statement(ticker, alphavantage_key)
    balance_sheet = await alpha.get_alphavantage_balance_sheet(ticker, alphavantage_key)
    earnings = await alpha.get_alphavantage_earnings(ticker, alphavantage_key)
    cash_flow = await alpha.get_alphavantage_cash_flow(ticker, alphavantage_key)
    # Get company stock prices
    monthly_company_prices = await alpha.get_monthly_alphavantage_company_prices(ticker, alphavantage_key)
    daily_company_prices = await alpha.get_daily_alphavantage_company_prices(ticker, alphavantage_key)

    # Build and send report components
    await utils.send_message_in_chunks(message.channel, past_sales_records(income_statement["annualReports"]))
    await message.channel.send(past_eps(earnings["annualEarnings"]))
    msg, high_yield = record_of_stock(earnings, income_statement, daily_company_prices, monthly_company_prices)
    await utils.send_message_in_chunks(message.channel, msg)
    msg, charts = trend(income_statement, earnings, monthly_company_prices)
    await message.channel.send(msg)
    for fig in charts:
        with open(fig, "rb") as fh:
            f = discord.File(fh, filename=fig)
            await message.channel.send(file=f)
    await utils.send_message_in_chunks(message.channel, cash_position(balance_sheet))
    await message.channel.send(
        revenue_growth(
            daily_company_prices,
            cash_flow,
            income_statement,
            earnings["quarterlyEarnings"]["reportedEPS"][-1],
            balance_sheet["annualReports"]["commonStockSharesOutstanding"][-1],
        )
    )
    await message.channel.send(earnings_growth(cash_flow))
    # TODO management
    # Risk Reward
    msg, charts = risk_reward(
        daily_company_prices,
        earnings,
        monthly_company_prices,
        income_statement,
        high_yield,  # high yield from EPS chart
        balance_sheet["annualReports"]["commonStockSharesOutstanding"][-1],
    )
    await message.channel.send(msg)
    for fig in charts:
        with open(fig, "rb") as fh:
            f = discord.File(fh, filename=fig)
            await message.channel.send(file=f)
