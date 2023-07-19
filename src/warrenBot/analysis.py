# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Module library for quant financial analysis."""
from scipy import stats
import numpy as np


def estimate_exp_mov_avg_volatility(prices, lmda):
    """Exponential moving average model of volatility.

    Create an exponential moving average model of the volatility of a stock price, and return
    the most recent (last) volatility estimate.

    :param prices: pandas.Series
        A series of adjusted closing prices for a stock.

    :param lmda: float
        The 'lambda' parameter of the exponential moving average model. Making
        this value smaller will cause the model to weight older terms less
        relative to more recent terms.

    :return: last_vol: float
        The last element of your exponential moving averge volatility model series.
    """
    # Implement the exponential moving average volatility model and return the last value.
    log_returns = np.log(prices) - np.log(prices.shift(1))
    log_returns = log_returns.pow(2)
    ewm_returns = log_returns.ewm(alpha=(1 - lmda)).mean().pow(.5)
    return ewm_returns.iloc[-1]


def analyze_returns(net_returns, null_hypothesis=0.0):
    """Perform a t-test, with the null hypothesis being that the mean return is zero.

    :param net_returns: Pandas Series
        A Pandas Series for each date
    :param null_hypothesis: Float64
        Null Hypothesis being that the mean return is zero

    :return t_value: t-statistic from t-test
    :return p_value: Corresponding p-value
    """
    # Hint: You can use stats.ttest_1samp() to perform the test.
    #       However, this performs a two-tailed t-test.
    #       You'll need to divde the p-value by 2 to get the results of a one-tailed p-value.
    ret = stats.ttest_1samp(net_returns, null_hypothesis)
    return ret[0], ret[1] / 2


def compute_log_returns(prices):
    """Compute log returns for each ticker.

    :param prices : DataFrame
        Prices (e.g. closing stock price) for each ticker and date

    :return log_returns : DataFrame
        Log returns for each ticker and date
    """
    return np.log(prices / prices.shift(1))


def shift_returns(returns, shift_n):
    """Generate shifted returns.

    :param returns: DataFrame
        Returns for each ticker and date
    :param shift_n: int
        Number of periods to move, can be positive or negative

    :return shifted_returns: DataFrame
        Shifted returns for each ticker and date
    """
    return returns.shift(shift_n)


def resample_prices(close_prices, freq='M'):
    """Resample close prices for each ticker at specified frequency.

    :param close_prices: DataFrame
        Close prices for each ticker and date
    :param freq: str
        What frequency to sample at
        For valid freq choices, see
        http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

    :return prices_resampled: DataFrame
        Resampled prices for each ticker and date
    """
    return close_prices.resample(freq).last()


def get_most_volatile(prices):
    """Return the ticker symbol for the most volatile stock.

    :param prices: pandas.DataFrame
        a pandas.DataFrame object with columns: ['ticker', 'date', 'price']

    :return ticker: string
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


def get_top_n(prev_returns, top_n):
    """Select the top performing stocks.

    :param prev_returns: DataFrame
        Previous shifted returns for each ticker and date
    :param top_n: int
        The number of top performing stocks to get

    :return top_stocks: DataFrame
        Top stocks for each ticker and date marked with a 1
    """
    ret_top = prev_returns.copy()
    for index, row in ret_top.iterrows():
        top = row.nlargest(top_n).index

        ret_top.loc[index] = 0
        ret_top.loc[index, top] = 1
    return ret_top.astype(int)


def analyze_alpha(expected_portfolio_returns_by_date):
    """Perform a t-test with the null hypothesis being that the expected mean return is zero.

    :param expected_portfolio_returns_by_date: Pandas Series
        Expected portfolio returns for each date

    :return t_value:
        T-statistic from t-test
    :return p_value:
        Corresponding p-value
    """
    null_hypothesis = 0.0
    ret = stats.ttest_1samp(expected_portfolio_returns_by_date, null_hypothesis)
    return ret[0], ret[1] / 2


def portfolio_returns(df_long, df_short, lookahead_returns, n_stocks):
    """Compute expected returns for a portfolio, assuming equal investment in each long/short stock.

    :param df_long: DataFrame
        Top stocks for each ticker and date marked with a 1
    :param df_short: DataFrame
        Bottom stocks for each ticker and date marked with a 1
    :param lookahead_returns: DataFrame
        Lookahead returns for each ticker and date
    :param n_stocks: int
        The number of stocks chosen for each month

    :return portfolio_returns: DataFrame
        Expected portfolio returns for each ticker and date
    """
    long = (df_long * lookahead_returns) / n_stocks
    short = (df_short * lookahead_returns) / n_stocks
    #     print(long)
    return long - short
