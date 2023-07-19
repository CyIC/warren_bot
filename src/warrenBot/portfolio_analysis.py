# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Portfolio Analysis functions for chatbot."""
import os
import json
import time
import datetime as dt
import logging

import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
import mplfinance as mpf

from warrenBot.alphavantage import download_stocks
from warrenBot import utilities as util
from warrenBot import analysis

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)


async def run(club_stocks_file, club_info_file, key):
    """Execute club analysis report.

    :return:
    """
    stocks = pd.read_csv(club_stocks_file, parse_dates=True, index_col='date',
                         encoding='utf_8', encoding_errors='ignore')
    total_shares = stocks['shares'].sum()
    # get club info / check and update club info
    with open(club_info_file) as json_data:
        club_data_json = json.load(json_data)
    club_data, changed = await util.verify_club_data(club_data_json)
    if changed:
        with open(club_info_file, 'w') as f:
            json.dump(club_data, f)
    # get club meeting dates
    meeting_dates = pd.Series(pd.to_datetime(list(club_data['club']['valuation_dates'])))
    # Compare the last meeting day == today - offset to last business day
    if meeting_dates.iloc[-1].date() != (pd.to_datetime(dt.datetime.today() - BDay())).date():
        meeting_dates = pd.concat([meeting_dates, pd.Series(pd.to_datetime(dt.datetime.today() - BDay()))])
    # Read in stock prices, else get new prices from alphavantage
    try:
        # check if stocks.pkl is old data
        local_stock_price_file = 'stocks.pkl'
        if str(dt.datetime.today().date()) != time.strftime('%Y-%m-%d', time.gmtime(os.path.getmtime(local_stock_price_file))):
            prices = await download_stocks(stocks, key)
        else:
            prices = pd.read_pickle(local_stock_price_file)
    except (FileNotFoundError, KeyError):
        prices = await download_stocks(stocks, key)
    close = prices.reset_index().pivot(index='date', columns='ticker', values='close')

    # Build table for meeting valuation dates
    meeting_valuation = []
    for date in meeting_dates:
        meeting_valuation.append(close.T[str(date.date())])
    meeting_valuation = pd.DataFrame(meeting_valuation)
    # Monthly Stock Price Comparison Reporting
    last_month = meeting_valuation.iloc[-2]  # Stores last month's valuation stock prices
    this_month = meeting_valuation.iloc[-1]  # Stores this month's valuation stock prices
    percent_change = meeting_valuation.pct_change().iloc[-1]

    # Build Stock stats for each stock in portfolio
    stock_stats = pd.DataFrame()
    for x in stocks['ticker'].unique().tolist():
        df = (stocks[stocks['ticker'] == x])
        # build stock cost basis
        cost_basis = (df['shares'].round(6) * df['price'].round(4) + df['commission']).sum()
        # build weight in portfolio
        shares = df['shares'].sum()
        weight = (df['shares'].round(6) / total_shares).sum()
        avg_cost = (cost_basis / df['shares'].sum()).round(6)
        # industry = stocks['industry']
        # sector = stocks['sector']
        industry, sector = (None, None)  # TODO get company industry and sector
        # company_size = stocks['company_size']
        company_size = None  # TODO get company size util.company_size(company_revenue)
        # Build tmp Dataframe to merge into Global DataFrame
        other = pd.DataFrame([[x, avg_cost, shares, cost_basis, industry,
                               sector, weight, company_size]],
                             columns=['ticker',
                                      'avg_cost',
                                      'shares',
                                      'cost_basis',
                                      'industry',
                                      'sector',
                                      'weight',
                                      'size'])
        stock_stats = pd.concat([stock_stats, other])
    stock_stats = stock_stats.set_index(['ticker']).reindex()
    print(stock_stats)
    # For display in report
    stock_price_compare = pd.DataFrame({
        'Cost Basis': stock_stats['cost_basis'],
        'Last Month': last_month,
        'This Month': this_month,
        "% change": percent_change
    })
    print(stock_price_compare)
    # stock_price_compare['Cost Basis'] = stock_stats['cost_basis']
    stock_price_compare.style \
        .format(precision=2, thousands=',') \
        .format_index(str.upper)

    # Build stock graphs
    days_back = 180
    stock_charts = []
    for ticker in prices['ticker'].unique().tolist():
        stock = prices[prices['ticker'] == ticker].sort_index(ascending=True)
        stock = stock[-days_back:]
        other_plots = [
            mpf.make_addplot(stock[['SMA20', 'SMA50', 'SMA200']], type='line', panel=1, alpha=0.3),
            mpf.make_addplot(stock[['log_return']], type='bar', panel=0)
        ]
        meeting_days = meeting_valuation[meeting_valuation.index > pd.Timestamp.today() - pd.Timedelta(days=days_back)].index
        mpf.plot(stock, type='candle', figratio=(950, 420), datetime_format='%b-%d',
                 main_panel=1, title=ticker, style='yahoo',
                 volume=True, volume_panel=2, ylabel_lower='Volume',
                 addplot=other_plots, savefig="charts/{}_chart.png".format(ticker),
                 vlines=dict(vlines=meeting_days.tolist(), linestyle='dotted', colors='c',
                             linewidths=1, alpha=.5),
                 # hlines=dict(hlines=stock_stats['avg_cost'][ticker],linestyle='dashed',colors='r',linewidths=1)
                 )
        stock_charts.append('charts/{}_chart.png'.format(ticker))

    # Build club Performance Graph
    club_stats = pd.DataFrame()
    for meeting in club_data['club']['valuation_dates']:
        # total cost of stocks + available capital
        cost = (stocks[(stocks.index < meeting)]['shares'] * stocks[(stocks.index < meeting)]['price'] + stocks[(stocks.index < meeting)]['commission']).sum()
        other = pd.DataFrame([[meeting,
                              club_data['club']['valuation_dates'][meeting]['total_market_value'],
                              cost + club_data['club']['valuation_dates'][meeting]['available_capital']]],
                             columns=['date',
                                      'total_market_value',
                                      'stock_cost_basis'
                                      ])
        club_stats = pd.concat([club_stats, other])
    club_stats = club_stats.set_index(['date']).reindex()
    print(club_stats)  # TODO

    # Build log returns
    for x in prices['ticker'].unique().tolist():
        # Only get prices of the given ticker symbol
        price_returns = (prices[prices['ticker'] == x])
        # Build dataframe of log returns
        log_returns = np.log(price_returns['close']) - np.log(price_returns['close'].shift(1))
        returns_std = log_returns.std()
        # print("Price Return {} : {}".format(x, price_returns))
        # print("Log Return {} : {}".format(x, log_returns))
        print("{} : {}".format(x, returns_std))
        print("Est Exp Moving Avg Volatility: {}".format(
            analysis.estimate_exp_mov_avg_volatility(price_returns['close'], 0.7)))

    # Generate Report
    util.draw_club_report('CyIC.{}.EconomicsReport'.format(dt.datetime.now().strftime('%B%Y')),
                          stock_price_compare,
                          stock_charts,
                          club_data,
                          )
