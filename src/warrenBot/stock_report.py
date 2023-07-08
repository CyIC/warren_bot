import numpy as np
from prettytable import PrettyTable
import pandas as pd
import matplotlib.pyplot as plt
import discord

import utilities

YRS_LOOKBACK = 5
float_formatter = "{:0.2f}".format
np.set_printoptions(formatter={'float_kind': float_formatter})


def populate_vars(old, new):
    diff = new - old
    try:
        percent_diff = diff / abs(old)
    except ZeroDivisionError:
        percent_diff = 0
    return diff, percent_diff


async def send_message(msg: str, channel):
    print(type(channel))
    channel.send(msg)


# def get_finance_data(ticker):
#     # retrieve data from alphavantage
#     income_statement_json = utilities.get_alphavantage_data('INCOME_STATEMENT', ticker, KEY)
#     balance_sheet_json = utilities.get_alphavantage_data('BALANCE_SHEET', ticker, KEY)
#     stock_price_json = utilities.get_alphavantage_data('TIME_SERIES_DAILY_ADJUSTED', ticker, KEY)
#     monthly_company_price_json = utilities.get_alphavantage_data('TIME_SERIES_MONTHLY_ADJUSTED', ticker, KEY)
#     # Retrieve yearly company info
#     company_data = utilities.process_alphavantage_annual_company_info(income_statement_json, balance_sheet_json)
#     quarterly_revenue = utilities.quarterly_revenue(income_statement_json)
#     # Retrieve daily Stock Prices


async def past_sales_records(message, company_data):
    STOCK_TICKER = company_data['ticker'].unique().tolist()[0]
    # Past Sales Records
    sales_per_year = company_data.reset_index().pivot(index='date', columns='ticker', values='revenue')
    # Last year and year before sales
    recent_sales_trend = (sales_per_year[STOCK_TICKER][-1] + sales_per_year[STOCK_TICKER][-2])/2
    # Years 5 and 6 sales
    past_sales_trend = (sales_per_year[STOCK_TICKER][0] + sales_per_year[STOCK_TICKER][1])/2
    sales_increase = recent_sales_trend - past_sales_trend
    sales_percent_increase = sales_increase/past_sales_trend
    compound_annual_sales_growth_rate = pow((sales_per_year[STOCK_TICKER][-1]/sales_per_year[STOCK_TICKER][0]),1/YRS_LOOKBACK)-1
    # display table
    past_sales_record_table = PrettyTable(float_format='.4')
    past_sales_record_table.header = False
    past_sales_record_table.border = False
    past_sales_record_table.add_row(["Sales for most recent year", '${:20,.0f}'.format(sales_per_year[STOCK_TICKER][-1])])
    past_sales_record_table.add_row(["Sales for next most recent year", '${:20,.0f}'.format(sales_per_year[STOCK_TICKER][-2])])
    past_sales_record_table.add_row(["Sales for {} years ago".format(YRS_LOOKBACK-1), '${:20,.0f}'.format(sales_per_year[STOCK_TICKER][1])])
    past_sales_record_table.add_row(["Sales for {} years ago".format(YRS_LOOKBACK), '${:20,.0f}'.format(sales_per_year[STOCK_TICKER][0])])
    past_sales_record_table.add_row(["% increase in sales", '{:.3%}'.format(sales_percent_increase.round(4))])
    past_sales_record_table.add_row(["Compound Annual Sales Growth Rate", '{:.3%}'.format(compound_annual_sales_growth_rate.round(4))])
    past_sales_record_table.align['Field 1'] = 'l'
    past_sales_record_table.align['Field 2'] = 'r'
    await message.channel.send("**{}**\n```{}```".format('Past Sales Records',
                                                     past_sales_record_table))
    return


async def past_eps(message, company_data):
    await message.channel.send("\n**Past EPS**")
    STOCK_TICKER = company_data['ticker'].unique().tolist()[0]
    eps_per_year = company_data.reset_index().pivot(index='date', columns='ticker', values='eps')
    # print(eps_per_year)
    # Last year and year before EPS
    recent_eps_mean = (eps_per_year[STOCK_TICKER][-1] + eps_per_year[STOCK_TICKER][-2])/2
    # Years 4 and 5 EPS
    past_eps_mean = (eps_per_year[STOCK_TICKER][1] + eps_per_year[STOCK_TICKER][0])/2
    eps_increase = recent_eps_mean - past_eps_mean
    eps_percent_increase = eps_increase/past_eps_mean
    compound_annual_eps_growth_rate = pow(eps_per_year[STOCK_TICKER][0]/eps_per_year[STOCK_TICKER][-1],(1/YRS_LOOKBACK))-1
    # display table
    past_eps_record_table = PrettyTable()
    past_eps_record_table.align = 'l'
    past_eps_record_table.align['Field 2'] = 'r'
    past_eps_record_table.header = False
    past_eps_record_table.border = False
    past_eps_record_table.add_row(["EPS for most recent year",
                                   '{:10.4f} '.format(eps_per_year[STOCK_TICKER][-1].round(4))])
    past_eps_record_table.add_row(["EPS for next most recent year",
                                   '{:10.4f} '.format(eps_per_year[STOCK_TICKER][-2].round(4))])
    past_eps_record_table.add_row(["EPS for {} years ago".format(YRS_LOOKBACK-1),
                                   '{:10.4f} '.format(eps_per_year[STOCK_TICKER][1].round(4))])
    past_eps_record_table.add_row(["EPS for {} years ago".format(YRS_LOOKBACK),
                                   '{:10.4f} '.format(eps_per_year[STOCK_TICKER][0].round(4))])
    past_eps_record_table.add_row(["% increase in earnings",
                                   '{:10.4%}'.format(eps_percent_increase.round(4))])
    past_eps_record_table.add_row(["Compound Annual rate of EPS",
                                   '{:10.4%}'.format(compound_annual_eps_growth_rate.round(4))])
    await message.channel.send("EPS per year: ```{}```".format(eps_per_year))
    await message.channel.send("```{}```".format(past_eps_record_table))
    return


async def record_of_stock(message,
                          company_data,
                          stock_price_json,
                          income_statement_json,
                          monthly_company_price_json
                          ):
    await message.channel.send("\n**Record of Stock**")
    STOCK_TICKER = company_data['ticker'].unique().tolist()[0]
    company_prices = utilities.process_alphavantage_company_prices(stock_price_json)
    quarterly_eps = utilities.quarterly_eps(income_statement_json, company_data['shares_outstanding'])
    # Past Sales Records
    sales_per_year = company_data.reset_index().pivot(index='date',
                                                      columns='ticker',
                                                      values='revenue')
    # Last year and year before sales
    recent_sales_trend = (sales_per_year[STOCK_TICKER][-1] + sales_per_year[STOCK_TICKER][-2])/2
    # Years 5 and 6 sales
    past_sales_trend = (sales_per_year[STOCK_TICKER][0] + sales_per_year[STOCK_TICKER][1])/2
    sales_increase = recent_sales_trend - past_sales_trend
    sales_percent_increase = sales_increase/past_sales_trend
    eps_per_year = company_data.reset_index().pivot(index='date', columns='ticker', values='eps')
    # Last year and year before EPS
    recent_eps_mean = (eps_per_year[STOCK_TICKER][-1] + eps_per_year[STOCK_TICKER][-2])/2
    # Years 4 and 5 EPS
    past_eps_mean = (eps_per_year[STOCK_TICKER][1] + eps_per_year[STOCK_TICKER][0])/2
    eps_increase = recent_eps_mean - past_eps_mean
    eps_percent_increase = eps_increase/past_eps_mean
    # get current stock price
    present_price = float(company_prices['close'][0])
    # get current eps
    present_eps = float(quarterly_eps[0])
    # get monthly prices
    monthly_company_price = utilities.process_alphavantage_company_prices(monthly_company_price_json)
    await message.channel.send("Present Price: {:.3f}".format(present_price))
    await message.channel.send("Present EPS: {:.3f}".format(present_eps))

    # Display
    high_prices = []
    low_prices = []
    pe_high = []
    pe_low = []
    eps_table = PrettyTable(['List Last 5 Years', 'High Price', 'Low Price', 'EPS', 'PE Ratio at High', 'PE Ratio at Low'],
                            float_format='.4')
    # x.float_format = '.4'
    eps_table.align = 'r'
    eps_table.align['PE Ratio at High'] = 'c'
    eps_table.align['PE Ratio at Low'] = 'c'
    for yr in eps_per_year.index.year:
        high = float(monthly_company_price.loc[str(yr)]['high'].max())
        high_prices.append(high)
        low = float(monthly_company_price.loc[str(yr)]['low'].min())
        low_prices.append(low)
        eps = eps_per_year.loc[str(yr)][STOCK_TICKER][0]
        pe_high.append(high/eps)
        pe_low.append(low/eps)
        eps_table.add_row([yr,
                           '${:20,.3f}'.format(high),
                           '${:20,.3f}'.format(low),
                           eps,
                           '{:20,.5f}'.format(high/eps),
                           '{:20,.5f}'.format(low/eps)
                           ])
    high_prices = pd.Series(high_prices)
    low_prices = pd.Series(low_prices)
    pe_high = pd.Series(pe_high)
    pe_low = pd.Series(pe_low)
    eps_table.add_row(['Averages',
                       '${:20,.3f}'.format(high_prices.mean()),
                       '${:20,.3f}'.format(low_prices.mean()),
                       '',
                       '{:20,.6f}'.format(pe_high.mean()),
                       '{:20,.6f}'.format(pe_low.mean())
                       ])
    await message.channel.send("```{}```".format(eps_table))
    y = PrettyTable([], float_format='.4')
    y.header = False
    # y.border = False
    y._max_width = {"Field 1": 15,
                    "Field 2": 20,
                    "Field 3": 15,
                    "Field 4": 20,
                    "Field 5": 20,
                    "Field 6": 20,
                    }
    y.add_row(['Present Price % difference then high price {} years ago'.format(YRS_LOOKBACK),
               '{:.4%}'.format(((present_price-high_prices.values[0])/high_prices.values[0])),
               '% Increase in Sales',
               '{:.4%}'.format(sales_percent_increase),
               '% Increase in Earnings',
               '{:.4%}'.format(eps_percent_increase)
               ])
    await message.channel.send('Average of High and Low price Earnings avg for past {} years: {:20.4f}'.format(YRS_LOOKBACK,
                                                                                                         pd.concat([pe_high, pe_low]).mean()
                                                                                                         ))
    await message.channel.send("```{}```".format(y))
    return


async def trend(message,
                income_statement_json,
                company_data,
                monthly_company_price_json):
    ticker = company_data['ticker'].unique().tolist()[0]
    await message.channel.send("\n**Trends**")
    quarterly_revenue = utilities.quarterly_revenue(income_statement_json)
    quarterly_eps = utilities.quarterly_eps(income_statement_json, company_data['shares_outstanding'])
    monthly_company_price = utilities.process_alphavantage_company_prices(monthly_company_price_json)
    # Quarterly Revenue, Quartertly EPS
    monthly_company_price_json = utilities.get_alphavantage_data('TIME_SERIES_MONTHLY_ADJUSTED',
                                                                 ticker,
                                                                 KEY)
    fig1, revenue_fig = plt.subplots()
    revenue_fig.set_xlabel('Date')
    revenue_fig.set_ylabel('Revenue', color = 'tab:red')
    revenue_fig.plot(quarterly_revenue, color = 'tab:red')
    revenue_fig.set_title('Revenue & EPS')

    eps_fig = revenue_fig.twinx()
    eps_fig.set_ylabel('EPS', color = 'tab:blue')
    eps_fig.plot(quarterly_eps)
    # trend_plot.plot(y=['Revenue', 'EPS'])
    plt.savefig('./eps_fig.jpg')
    with open('./eps_fig.jpg', 'rb') as fh:
        f = discord.File(fh, filename="eps_fig.jpg")
    await message.channel.send(file=f)
    # plt.show()

    # Plot Stock Highs and Lows
    monthly_company_price['avg_high'] = monthly_company_price['high'].rolling(4).mean()
    monthly_company_price['avg_low'] = monthly_company_price['low'].rolling(4).mean()
    monthly_company_price.plot(y=['high', 'low', 'avg_high', 'avg_low'],
                               title='Stock High & Low',
                               xlabel='Date',
                               ylabel='USD')
    plt.savefig('./stock_high_low.jpg')
    with open('./stock_high_low.jpg', "rb") as fh:
        f = discord.File(fh, filename="stock_high_low.jpg")
    await message.channel.send(file=f)
    # plt.show()
    return


async def cash_position(message, company_data):
    await message.channel.send("\n**Cash Position**")
    cash_table = PrettyTable(['', company_data.index[0].year, company_data.index[1].year, 'Difference', '% Difference'], float_format='.4')
    # cash_table.border = False
    cash_table.align = 'r'
    cash_table.align[''] = 'l'

    new_cash = int(company_data['cashEquivalents'][0])
    old_cash = int(company_data['cashEquivalents'][1])
    diff_cash, percent_diff_cash = populate_vars(old_cash, new_cash)
    cash_table.add_row(['Cash and Equivalents',
                        '${:20,.0f}'.format(new_cash),
                        '${:20,.0f}'.format(old_cash),
                        '${:20,.0f}'.format(diff_cash),
                        '{:.4%}'.format(percent_diff_cash),
                        ])

    new_investments = int(company_data['shortTermInvestments'][0])
    old_investments = int(company_data['shortTermInvestments'][1])
    diff_investments, percent_diff_investments = populate_vars(old_investments, new_investments)
    cash_table.add_row(['Short Term Investments',
                        '${:20,.0f}'.format(new_investments),
                        '${:20,.0f}'.format(old_investments),
                        '${:20,.0f}'.format(diff_investments),
                        '{:.4%}'.format(percent_diff_investments)
                        ])

    new_total_cash = new_cash + new_investments
    old_total_cash = old_cash + old_investments
    diff_total_cash, percent_diff_total_cash = populate_vars(old_total_cash, new_total_cash)
    cash_table.add_row(['Overall Cash Positions',
                        '${:20,.0f}'.format(new_total_cash),
                        '${:20,.0f}'.format(old_total_cash),
                        '${:20,.0f}'.format(diff_total_cash),
                        '{:.4%}'.format(percent_diff_total_cash)
                        ])

    new_long_term_debt = int(company_data['longTermDebt'][0])
    old_long_term_debt = int(company_data['longTermDebt'][1])
    diff_lt_debt, percent_diff_lt_debt = populate_vars(old_long_term_debt, new_long_term_debt)
    cash_table.add_row(['','','','',''])
    cash_table.add_row(['Long Term Debt',
                        '${:20,.0f}'.format(new_long_term_debt),
                        '${:20,.0f}'.format(old_long_term_debt),
                        '${:20,.0f}'.format(diff_lt_debt),
                        '{:.4%}'.format(percent_diff_lt_debt)
                        ])

    new_net_cash = new_total_cash - new_long_term_debt
    old_net_cash = old_total_cash - old_long_term_debt
    diff_net_cash, percent_diff_net_cash = populate_vars(old_net_cash, new_net_cash)
    cash_table.add_row(['','','','',''])
    cash_table.add_row(['Net cash position',
                        '${:20,.0f}'.format(new_net_cash),
                        '${:20,.0f}'.format(old_net_cash),
                        '${:20,.0f}'.format(diff_net_cash),
                        '{:.4%}'.format(percent_diff_net_cash)
                        ])
    # add shares outstanding
    cash_table.add_row(['','','','',''])
    new_shares = int(company_data['shares_outstanding'][0])
    old_shares = int(company_data['shares_outstanding'][1])
    diff_shares, percent_diff_shares = populate_vars(old_shares, new_shares)
    cash_table.add_row(['Shares outstanding',
                        '${:20,.0f}'.format(new_shares),
                        '${:20,.0f}'.format(old_shares),
                        '${:20,.0f}'.format(diff_shares),
                        '{:.4%}'.format(percent_diff_shares)
                        ])
    new_cash_share = new_net_cash / new_shares
    old_cash_share = old_net_cash / old_shares
    diff_cash_share, percent_diff_cash_share = populate_vars(old_cash_share, new_cash_share)

    cash_table.add_row(['Net cash per share',
                        '${:20,.4f}'.format(new_cash_share),
                        '${:20,.4f}'.format(old_cash_share),
                        '${:20,.4f}'.format(diff_cash_share),
                        '{:.4%}'.format(percent_diff_cash_share)
                        ])
    await message.channel.send("```{}```".format(cash_table))

    # Assets & liabilities
    avl_table = PrettyTable(['', company_data.index[0].year, company_data.index[1].year, 'Difference', '% Difference'], float_format='.4')
    avl_table.align = 'r'
    avl_table.align[''] = 'l'

    avl_table.add_row(['Assets', '', '', '', ''])
    avl_table.add_row(['Cash',
                       '${:20,.4f}'.format(new_cash),
                       '${:20,.4f}'.format(old_cash),
                       '${:20,.4f}'.format(diff_cash),
                       '{:.4%}'.format(percent_diff_cash)
                       ])

    old_receivables = company_data['receivables'][1]
    new_receivables = company_data['receivables'][0]
    diff_receivables, percent_diff_receivables = populate_vars(old_receivables,
                                                               new_receivables)
    avl_table.add_row(['Recievables',
                       '${:20,.4f}'.format(new_receivables),
                       '${:20,.4f}'.format(old_receivables),
                       '${:20,.4f}'.format(diff_receivables),
                       '{:.4%}'.format(percent_diff_receivables)
                       ])
    old_inventories = company_data['inventory'][1]
    new_inventories = company_data['inventory'][0]
    diff_inventories, percent_diff_inventories = populate_vars(old_inventories, new_inventories)
    avl_table.add_row(['Inventories',
                       '${:20,.4f}'.format(new_inventories),
                       '${:20,.4f}'.format(old_inventories),
                       '${:20,.4f}'.format(diff_inventories),
                       '{:.4%}'.format(percent_diff_inventories)
                       ])
    old_other_assets = company_data['other_assets'][1]
    new_other_assets = company_data['other_assets'][0]
    diff_other_assets , percent_diff_other_assets = populate_vars(old_other_assets, new_other_assets)
    avl_table.add_row(['Other Assets',
                       '${:20,.4f}'.format(new_other_assets),
                       '${:20,.4f}'.format(old_other_assets),
                       '${:20,.4f}'.format(diff_other_assets),
                       '{:.4%}'.format(percent_diff_other_assets)
                       ])
    old_current_assets = company_data['current_assets'][1]
    new_current_assets = company_data['current_assets'][0]
    diff_current_assets, percent_diff_current_assets = populate_vars(old_current_assets, new_current_assets)
    avl_table.add_row(['Current Assets',
                       '${:20,.4f}'.format(new_current_assets),
                       '${:20,.4f}'.format(old_current_assets),
                       '${:20,.4f}'.format(diff_current_assets),
                       '{:.4%}'.format(percent_diff_current_assets)
                       ])
    await message.channel.send("```{}```".format(avl_table))

    # Reset and build Liabilities Table
    avl_table = PrettyTable(['',
                             company_data.index[0].year,
                             company_data.index[1].year,
                             'Difference',
                             '% Difference'],
                            float_format='.4')
    avl_table.align = 'r'
    avl_table.align[''] = 'l'
    avl_table.add_row(['Liabilities', '', '', '', ''])
    old_payables = company_data['payable'][1]
    new_payables = company_data['payable'][0]
    diff_payables , percent_diff_payables = populate_vars(old_payables, new_payables)
    avl_table.add_row(['Payables',
                       '${:20,.4f}'.format(new_payables),
                       '${:20,.4f}'.format(old_payables),
                       '${:20,.4f}'.format(diff_payables),
                       '{:.4%}'.format(percent_diff_payables)
                       ])
    old_st_debt = company_data['short_term_debt'][1]
    new_st_debt = company_data['short_term_debt'][0]
    diff_st_debt, percent_diff_st_debt = populate_vars(old_st_debt, new_st_debt)
    avl_table.add_row(['Short Term Debt',
                       '${:20,.4f}'.format(new_st_debt),
                       '${:20,.4f}'.format(old_st_debt),
                       '${:20,.4f}'.format(diff_st_debt),
                       '{:.4%}'.format(percent_diff_st_debt)
                       ])
    old_other_liabilities = company_data['other_liabilities'][1]
    new_other_liabilities = company_data['other_liabilities'][0]
    diff_other_liabilities, percent_diff_other_liabilities = populate_vars(old_other_liabilities,
                                                                           new_other_liabilities)
    avl_table.add_row(['Other Liabilities',
                       '${:20,.4f}'.format(new_other_liabilities),
                       '${:20,.4f}'.format(old_other_liabilities),
                       '${:20,.4f}'.format(diff_other_liabilities),
                       '{:.4%}'.format(percent_diff_other_liabilities)
                       ])
    old_current_liabilities = company_data['current_liabilities'][1]
    new_current_liabilities = company_data['current_liabilities'][0]
    diff_current_liabilities, percent_diff_current_liabilities = populate_vars(old_current_liabilities,
                                                                               new_current_liabilities)
    avl_table.add_row(['Current Liabilities',
                       '${:20,.4f}'.format(new_current_liabilities),
                       '${:20,.4f}'.format(old_current_liabilities),
                       '${:20,.4f}'.format(diff_current_liabilities),
                       '{:.4%}'.format(percent_diff_current_liabilities)
                       ])

    avl_table.add_row(['', '','','',''])
    old_avl = old_current_assets-old_current_liabilities
    new_avl = new_current_assets-new_current_liabilities
    diff_avl, percent_diff_avl = populate_vars(old_avl, new_avl)
    avl_table.add_row(['Asset Vs Liabilities',
                       '${:20,.0f}'.format(new_avl),
                       '${:20,.0f}'.format(old_avl),
                       '${:20,.0f}'.format(diff_avl),
                       '{:.4%}'.format(percent_diff_avl)
                       ])
    avl_table.add_row(['', '','','',''])
    cash_table.add_row(['Shares outstanding',
                        '${:20,.0f}'.format(new_shares),
                        '${:20,.0f}'.format(old_shares),
                        '${:20,.0f}'.format(diff_shares),
                        '{:.4%}'.format(percent_diff_shares)
                        ])
    old_net_cps = old_avl/old_shares
    new_net_cps = new_avl/new_shares
    diff_net_cps, percent_diff_net_cps = populate_vars(old_net_cps, new_net_cps)
    avl_table.add_row(['Net cash per share',
                       '${:20,.4f}'.format(new_net_cps),
                       '${:20,.4f}'.format(old_net_cps),
                       '${:20,.4f}'.format(diff_net_cps),
                       '{:.4%}'.format(percent_diff_net_cps)
                       ])
    # Display
    await message.channel.send("```{}```".format(avl_table))
    return


async def revenue_growth(message,
                         company_data,
                         stock_price_json,
                         income_statement_json,
                         cash_flow_json):
    await message.channel.send('\n**Revenue Growth**')
    eps_per_year = company_data.reset_index().pivot(index='date', columns='ticker', values='eps')
    quarterly_revenue = utilities.quarterly_revenue(income_statement_json)
    company_prices = utilities.process_alphavantage_company_prices(stock_price_json)
    STOCK_TICKER = company_data['ticker'].unique().tolist()[0]
    cash_flow = pd.DataFrame(cash_flow_json['annualReports']).set_index('fiscalDateEnding').reindex()
    try:
        dividend_yield = cash_flow['dividendPayout'].div(company_data['shares_outstanding'])
    except TypeError:
        dividend_yield = 0
    revenue = pd.DataFrame(company_data.sort_index()['revenue'])
    revenue.index = pd.to_datetime(revenue.index)
    revenue_diff = pd.Series(pd.to_numeric(company_data.sort_index()['revenue']).diff(), index=pd.to_datetime(revenue.index))
    revenue['change'] = revenue_diff
    revenue['%_change'] = revenue['change'].div(pd.to_numeric(revenue['revenue']))
    await message.channel.send("```{}```".format(revenue))
    await message.channel.send('Average Growth: {:.4%}'.format(revenue['%_change'].mean()))
    await message.channel.send("div yield: {:.4f}".format(dividend_yield))
    current_price = company_prices['close'][0]
    current_eps = eps_per_year[STOCK_TICKER][0]
    current_pe = current_price / current_eps
    await message.channel.send('Current P/E: {:.4f}'.format( current_pe ))
    await message.channel.send('Growth Rate w/ Dividends: {:.4f}'.format(((revenue['%_change'].mean()*10)+dividend_yield)/current_pe))
    # Display plot
    pd.to_numeric(quarterly_revenue).plot(title='Revenue',
                                          xlabel='Date',
                                          ylabel='USD')
    # plt.show()
    filename = 'quarterly_revenue.jpg'
    plt.savefig(filename)
    with open(filename, "rb") as fh:
        f = discord.File(fh, filename=filename)
    await message.channel.send(file=f)
    return


# print("## Earnings Growth")
async def earnings_growth(message, cash_flow_json):
    await message.channel.send('\n**Earnings Growth**')
    cash_flow = pd.DataFrame(cash_flow_json['annualReports']).set_index('fiscalDateEnding').reindex()
    earnings_table = PrettyTable(['Year', 'Net Income', 'Change', '% Change'], float_format='.4')
    earnings_table.align = 'r'
    earnings_growth = pd.DataFrame(pd.to_numeric(cash_flow['netIncome'])).set_index(pd.to_datetime(cash_flow.index)).reindex()
    earnings_growth = earnings_growth.sort_index()
    earnings_growth['Change'] = pd.Series(earnings_growth['netIncome'].diff(), index=earnings_growth.index)
    last_year = None
    date = earnings_growth.index
    change = 0
    percent_change = 0
    count = 0
    for year in earnings_growth['netIncome']:
        if last_year is not None:
            change = year - last_year
            percent_change = change/abs(last_year)
        earnings_table.add_row(['{}'.format(date[count].year),
                               '${:20,.0f}'.format(year),
                               '${:20,.0f}'.format(change),
                               '{:.3%}'.format(percent_change)])
        last_year = year
        count += 1
        # date.append(year[0])
    await message.channel.send("```{}```".format(earnings_table))
    earnings_growth['% Change'] = earnings_growth['Change'].div(earnings_growth['netIncome'])

    # Display plot
    quarterly_cash_flow = pd.DataFrame(cash_flow_json['quarterlyReports']).set_index('fiscalDateEnding').reindex()
    quarterly_cash_flow.index = pd.to_datetime(quarterly_cash_flow.index)
    quarterly_cash_flow['netIncome'] = pd.to_numeric(quarterly_cash_flow['netIncome'])
    pd.to_numeric(quarterly_cash_flow['netIncome']).plot(title='Earnings Growth',
                                                         xlabel='Date',
                                                         ylabel='Net Income (USD)')
    # plt.show()
    filename = 'earnings_growth.jpg'
    plt.savefig(filename)
    with open(filename, "rb") as fh:
        f = discord.File(fh, filename=filename)
    await message.channel.send(file=f)
    return
