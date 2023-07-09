import pandas as pd
import numpy as np
from scipy import stats
import requests
from asyncio import sleep

color_scheme = {
    'index': '#B6B2CF',
    'etf': '#2D3ECF',
    'tracking_error': '#6F91DE',
    'df_header': 'silver',
    'df_value': 'white',
    'df_line': 'silver',
    'heatmap_colorscale': [(0, '#6F91DE'), (0.5, 'grey'), (1, 'red')],
    'background_label': '#9dbdd5',
    'low_value': '#B6B2CF',
    'high_value': '#2D3ECF',
    'y_axis_2_text_color': 'grey',
    'shadow': 'rgba(0, 0, 0, 0.75)',
    'major_line': '#2D3ECF',
    'minor_line': '#B6B2CF',
    'main_line': 'black'}


def generate_config():
    return {'showLink': False, 'displayModeBar': False, 'showAxisRangeEntryBoxes': True}


def prep_pipeline(filename: str, encoding: str = 'utf_8'):
    """

    :param filename: (str) full path of the csv file to import
    :param encoding: (str) different file encoding if needed
    :return: pandas DataFrame
    """
    # Read CSV file using pandas
    data = pd.read_csv(filename, parse_dates=['date'], index_col='date', encoding=encoding, encoding_errors='ignore')
    return data


def compute_log_returns(prices):
    """
    Compute log returns for each ticker.

    Parameters
    ----------
    prices : DataFrame
        Prices (e.g. closing stock price) for each ticker and date

    Returns
    -------
    log_returns : DataFrame
        Log returns for each ticker and date
    """

    return np.log(prices/prices.shift(1))


def shift_returns(returns, shift_n):
    """
    Generate shifted returns

    Parameters
    ----------
    returns : DataFrame
        Returns for each ticker and date
    shift_n : int
        Number of periods to move, can be positive or negative

    Returns
    -------
    shifted_returns : DataFrame
        Shifted returns for each ticker and date
    """

    return returns.shift(shift_n)


async def get_alphavantage_data(function: str, symbol: str, key: str, outputsize: str = 'compact'):
    import time
    """make https API call to Alphavantage
    https://www.alphavantage.co/documentation

    :param function: (str) Alphavantage function (INCOME_STATEMENT, BALANCE_SHEET, TIME_SERIES_MONTHLY_ADJUSTED,
                     TIME_SERIES_WEEKLY_ADJUSTED, TIME_SERIES_DAILY_ADJUSTED, EARNINGS)
    :param symbol: (str) Company stock ticker
    :param key: (str) Alphavantage api key
    :return: <dict> json of alphavantage data
    """
    function = str.upper(function)
    url = 'https://www.alphavantage.co/query?function={funct}&symbol={symbol}&apikey={key}&outputsize={outputsize}'.format(funct=function,
                                                                                                                           key=key,
                                                                                                                           symbol=symbol,
                                                                                                                           outputsize=outputsize)
    r = requests.get(url).json()
    if r.get('Note') is not None:
        await sleep(60)
        r = requests.get(url).json()
    return r


def resample_prices(close_prices, freq='M'):
    """
    Resample close prices for each ticker at specified frequency.

    Parameters
    ----------
    close_prices : DataFrame
        Close prices for each ticker and date
    freq : str
        What frequency to sample at
        For valid freq choices, see http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

    Returns
    -------
    prices_resampled : DataFrame
        Resampled prices for each ticker and date
    """
    return close_prices.resample(freq).last()


def quarterly_revenue(income_statement):
    """

    :param income_statement:
    :return:
    """
    stock_ticker = income_statement['symbol']
    date = []
    ticker = []
    revenue = []
    # process income statement
    count = 0
    for year in income_statement['quarterlyReports']:
        date.append(year['fiscalDateEnding'])
        revenue.append(int(year['totalRevenue']))
        count += 1
    # convert arrays to indexed Series
    df = pd.Series(revenue, index=pd.to_datetime(date), name='quarterly_revenue')
    # df.index.name = 'date'
    # df.index = pd.to_datetime(df.index)
    return df


def quarterly_eps(income_statement, shares_outstanding):
    """

    :param income_statement:
    :param shares_outstanding:
    :return: Dataframe of quarterly EPS
    """
    eps = []
    date = []
    # process income statement
    count = 0
    for year in income_statement['quarterlyReports']:
        date.append(year['fiscalDateEnding'])
        eps.append(int(year['netIncome']) / shares_outstanding[count])
    df = pd.Series(eps, index=pd.to_datetime(date), name='quarterly_eps')
    # df.index = pd.to_datetime(df.index)
    return df


def process_alphavantage_annual_company_info(income_statement, balance_sheet):
    """Get company fundamentals
    Use AlphaVantage https://www.alphavantage.co/documentation/ to collect company fundamentals

    :param income_statement: (str) Income Statement json of company
    :param balance_sheet: (str) Balance Sheet json of company
    :return: company_data - Dataframe of company info {Year, ticker, revenue, eps}, current_eps from last quarter
                           filings
    """
    yrs_lookback = len(income_statement['annualReports'])
    shares_outstanding = []
    for year in balance_sheet['annualReports']:
        shares_outstanding.append(int(year['commonStockSharesOutstanding']))
    stock_ticker = income_statement['symbol']
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
    for x in range(0, yrs_lookback):
        ticker.append(stock_ticker)
    # process balance sheet
    for year in balance_sheet['annualReports']:
        shares_outstanding.append(pd.to_numeric(year['commonStockSharesOutstanding'], 'coerce'))
        cash_equivalents.append(pd.to_numeric(year['cashAndCashEquivalentsAtCarryingValue'], 'coerce'))
        short_term_investments.append(pd.to_numeric(year['shortTermInvestments'], 'coerce'))
        cash_and_short_term_investments.append(pd.to_numeric(year['cashAndShortTermInvestments'], 'coerce'))
        long_term_debt.append(pd.to_numeric(year['longTermDebt'], 'coerce'))
        receivables.append(pd.to_numeric(year['currentNetReceivables'], 'coerce'))
        inventory.append(pd.to_numeric(year['inventory'], 'coerce'))
        other_assets.append(pd.to_numeric(year['otherCurrentAssets'], 'coerce'))
        payable.append(pd.to_numeric(year['currentAccountsPayable'], 'coerce'))
        current_assets.append(pd.to_numeric(year['totalCurrentAssets'], 'coerce'))
        current_liabilities.append(pd.to_numeric(year['totalCurrentLiabilities'], 'coerce'))
        short_term_debt.append(pd.to_numeric(year['shortTermDebt'], 'coerce'))
        other_liabilities.append(pd.to_numeric(year['otherCurrentLiabilities'], 'coerce'))
        count += 1

    # process income statement
    count = 0
    for year in income_statement['annualReports']:
        date.append(year['fiscalDateEnding'])
        revenue.append(int(year['totalRevenue']))
        eps.append(int(year['netIncome']) / shares_outstanding[count])
        count += 1
    # convert arrays to indexed Series
    tmp_info = {
        'ticker': pd.Series(ticker, index=date),
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
    company_data.index.name = 'date'
    company_data.index = pd.to_datetime(company_data.index)
    # current_eps = int(income_statement['quarterlyReports'][0]['netIncome']) / shares
    return company_data


def process_alphavantage_eps(data, period: str = 'annualEarnings'):
    """
    annualEarnings, quarterlyEarnings

    :param data: (dict)
    :param period: (str)
    :return:
    """
    eps = pd.DataFrame(data[period])
    eps = eps.set_index('fiscalDateEnding')
    eps = eps.rename({'fiscalDateEnding': 'date'})
    return eps


def process_alphavantage_company_prices(data):
    """Get company stock data from alphavantage
    Use AlphaVantage https://www.alphavantage.co/documentation/ to collect company stock data

    :param data: (Dict) JSON Time series prices from alphavantage
    :return: Dataframe of company stock prices
    """
    if 'Time Series (Daily)' in data.keys():
        function = 'TIME_SERIES_DAILY_ADJUSTED'
        pivot = 'Time Series (Daily)'
    elif 'Monthly Adjusted Time Series' in data.keys():
        function = 'TIME_SERIES_MONTHLY_ADJUSTED'
        pivot = 'Monthly Adjusted Time Series'
    elif 'Weekly Adjusted Time Series' in data.keys():
        function = 'TIME_SERIES_WEEKLY_ADJUSTED'
        pivot = 'Weekly Adjusted Time Series'
    else:
        raise KeyError

    prices = pd.DataFrame(data[pivot]).T
    prices = prices.rename(columns={'1. open': 'open',
                                    '2. high': 'high',
                                    '3. low': 'low',
                                    '4. close': 'close',
                                    '5. adjusted close': 'adjusted close',
                                    '6. volume': 'volume',
                                    '7. dividend amount': 'dividend amount',
                                    '8. split coefficient': 'split coefficient'
                                    })
    prices.index.name = 'date'
    prices.index = pd.to_datetime(prices.index)
    prices['open'] = pd.to_numeric(prices['open'])
    prices['high'] = pd.to_numeric(prices['high'])
    prices['low'] = pd.to_numeric(prices['low'])
    prices['close'] = pd.to_numeric(prices['close'])
    prices['adj_close'] = pd.to_numeric(prices['adjusted close'])
    prices['volume'] = pd.to_numeric(prices['volume'])
    prices['dividend_amt'] = pd.to_numeric(prices['dividend amount'])
    prices['ticker'] = data['Meta Data']['2. Symbol']
    try:
        prices['split coefficient'] = pd.to_numeric(prices['split coefficient'])
    except KeyError:
        pass
    return prices


def get_most_volatile(prices):
    """Return the ticker symbol for the most volatile stock.

    Parameters
    ----------
    prices : pandas.DataFrame
        a pandas.DataFrame object with columns: ['ticker', 'date', 'price']

    Returns
    -------
    ticker : string
        ticker symbol for the most volatile stock
    """
    volatile_stock = ()
    for x in prices['ticker'].unique().tolist():
        price_returns = (prices[prices['ticker'] == x])
        log_returns = np.log(price_returns['price']) - np.log(price_returns['price'].shift(1))
        returns_std = log_returns.std()
        print("{} : {}".format(x, returns_std))
        if volatile_stock == ():
            volatile_stock = (x, returns_std)
        else:
            if volatile_stock[1] < returns_std:
                volatile_stock = (x, returns_std)
    return volatile_stock[0]


def resample_prices(close_prices, freq='M'):
    """
    Resample close prices for each ticker at specified frequency.

    Parameters
    ----------
    close_prices : DataFrame
        Close prices for each ticker and date
            column names: Ticker date, stock_tickers
            data is EoD ticker prices
        ticker date 	A 	AAL 	AAP 	AAPL 	ABBV 	ABC 	ABT 	ACN 	ADBE 	ADI 	... 	XL 	XLNX 	XOM 	XRAY 	XRX 	XYL 	YUM 	ZBH 	ZION 	ZTS
        2013-07-01 	29.99418563 	16.17609308 	81.13821681 	53.10917319 	34.92447839 	50.86319750 	31.42538772 	64.69409505 	46.23500000 	39.91336014 	... 	27.66879066 	35.28892781 	76.32080247 	40.02387348 	22.10666494 	25.75338607 	45.48038323 	71.89882693 	27.85858718 	29.44789315
        2013-07-02 	29.65013670 	15.81983388 	80.72207258 	54.31224742 	35.42807578 	50.69676639 	31.27288084 	64.71204071 	46.03000000 	39.86057632 	... 	27.54228410 	35.05903252 	76.60816761 	39.96552964 	22.08273998 	25.61367511 	45.40266113 	72.93417195 	28.03893238 	28.57244125

    freq : str
        What frequency to sample at
        For valid freq choices, see http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

    Returns
    -------
    prices_resampled : DataFrame
        Resampled prices for each ticker and date
    """
    return close_prices.resample(freq).last()


def compute_log_returns(prices):
    """
    Compute log returns for each ticker.

    Parameters
    ----------
    prices : DataFrame
        Prices for each ticker and date

    Returns
    -------
    log_returns : DataFrame
        Log returns for each ticker and date
    """

    return np.log(prices/prices.shift(1))


def get_top_n(prev_returns, top_n):
    """
    Select the top performing stocks

    Parameters
    ----------
    prev_returns : DataFrame
        Previous shifted returns for each ticker and date
    top_n : int
        The number of top performing stocks to get

    Returns
    -------
    top_stocks : DataFrame
        Top stocks for each ticker and date marked with a 1
    """
    ret_top = prev_returns.copy()
    for index, row in ret_top.iterrows():
        top = row.nlargest(top_n).index

        ret_top.loc[index] = 0
        ret_top.loc[index, top] = 1
    return ret_top.astype(int)


def analyze_alpha(expected_portfolio_returns_by_date):
    """
    Perform a t-test with the null hypothesis being that the expected mean return is zero.

    Parameters
    ----------
    expected_portfolio_returns_by_date : Pandas Series
        Expected portfolio returns for each date

    Returns
    -------
    t_value
        T-statistic from t-test
    p_value
        Corresponding p-value
    """
    null_hypothesis = 0.0
    ret = stats.ttest_1samp(expected_portfolio_returns_by_date, null_hypothesis)
    return ret[0], ret[1]/2


def portfolio_returns(df_long, df_short, lookahead_returns, n_stocks):
    """
    Compute expected returns for the portfolio, assuming equal investment in each long/short stock.

    Parameters
    ----------
    df_long : DataFrame
        Top stocks for each ticker and date marked with a 1
    df_short : DataFrame
        Bottom stocks for each ticker and date marked with a 1
    lookahead_returns : DataFrame
        Lookahead returns for each ticker and date
    n_stocks: int
        The number of stocks chosen for each month

    Returns
    -------
    portfolio_returns : DataFrame
        Expected portfolio returns for each ticker and date
    """
    long = (df_long * lookahead_returns) / n_stocks
    short = (df_short * lookahead_returns) / n_stocks
    #     print(long)
    return long - short


def analyze_alpha(expected_portfolio_returns_by_date):
    """
    Perform a t-test with the null hypothesis being that the expected mean return is zero.

    Parameters
    ----------
    expected_portfolio_returns_by_date : Pandas Series
        Expected portfolio returns for each date

    Returns
    -------
    t_value
        T-statistic from t-test
    p_value
        Corresponding p-value
    """
    # TODO: Implement Function
    null_hypothesis = 0.0
    ret = stats.ttest_1samp(expected_portfolio_returns_by_date, null_hypothesis)
    return ret[0], ret[1]/2
