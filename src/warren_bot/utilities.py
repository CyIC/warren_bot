# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Collection of useful utilities for warren_bot including getting data from alphavantage and processing
data structures. Also includes secure configuration management."""
import datetime
import logging
import os
from asyncio import sleep
from typing import Dict, Any, Optional

import pandas as pd
import requests
from jinja2 import Environment, select_autoescape, FileSystemLoader
from xhtml2pdf import pisa

# noqa: W503
color_scheme = {
    "index": "#B6B2CF",
    "etf": "#2D3ECF",
    "tracking_error": "#6F91DE",
    "df_header": "silver",
    "df_value": "white",
    "df_line": "silver",
    "heatmap_colorscale": [(0, "#6F91DE"), (0.5, "grey"), (1, "red")],
    "background_label": "#9dbdd5",
    "low_value": "#B6B2CF",
    "high_value": "#2D3ECF",
    "y_axis_2_text_color": "grey",
    "shadow": "rgba(0, 0, 0, 0.75)",
    "major_line": "#2D3ECF",
    "minor_line": "#B6B2CF",
    "main_line": "black",
}
MAX_MESSAGE_LENGTH = 2000  # Maximum message length allowed by Discord
LOGGER = logging.getLogger()


def prep_pipeline(filename: str, encoding: str = "utf_8"):
    """Prepare the analysis pipeline.

    :param filename: (str) full path of the csv file to import
    :param encoding: (str) different file encoding if needed
    :return: pandas DataFrame
    """
    # Read CSV file using pandas
    data = pd.read_csv(
        filename,
        parse_dates=["date"],
        index_col="date",
        encoding=encoding,
        encoding_errors="ignore",
    )
    return data


async def send_message_in_chunks(channel, content):
    """Split a long message into Discord allowed chunks.

    :param channel: Discord message channel
    :param content: Message to break into chunks
    :return:
    """
    # split the message into chunks
    if isinstance(content, list):
        for msg in content:
            chunks = [msg[i : i + MAX_MESSAGE_LENGTH] for i in range(0, len(msg), MAX_MESSAGE_LENGTH)]  # noqa: E203

            for chunk in chunks:
                await channel.send(chunk)  # send each chunk to the channel
    else:
        chunks = [content[i : i + MAX_MESSAGE_LENGTH] for i in range(0, len(content), MAX_MESSAGE_LENGTH)]  # noqa: E203

        for chunk in chunks:
            await channel.send(chunk)  # send each chunk to the channel


def company_size(revenue):
    """Determine company size by yearly revenue stream.

    https://www.iclub.com/faq/Home/Article?solution_id=1208
    Take company revenue numbers and return the company's size classification

    :param revenue: Company revenue for most recent 12 months.

    :return: <str> company size classification
    """
    # TODO check if revenue is numerical or str and work accordingly
    size = None
    if revenue < 100000000:  # $100 million
        size = "micro"
    elif revenue < 500000000:  # $500 million
        size = "small"
    elif revenue < 5000000000:  # $5 billion
        size = "mid"
    elif revenue < 15000000000:  # $15 billion
        size = "large"
    elif revenue >= 15000000000:
        size = "mega"
    return size


async def get_company_industry(cik):
    """Get Industry and Sector for a given company ticker.

    :param cik: <str> company SEC CIK number
    :return: (<industry>, <sector>)
    """
    url = f"https://data.sec.gov/submissions/CIK{fix_cik(cik)}.json"
    headers = {
        "user-agent": "Cypress Investment Club simmonsj@jasimmonsv.com",
    }
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != "200":
        await sleep(15)
        r = requests.get(url, headers=headers, timeout=30)
    r = r.json()
    return r["sicDescription"]


async def get_current_sec_10k_revenue(cik: str):
    """Get current 10-K from SEC Edgar API.

    :param cik:
    :return:
    """
    revenue = None
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{fix_cik(cik)}.json"
    headers = {
        "user-agent": "Cypress Investment Club simmonsj@jasimmonsv.com",
    }
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != "200":
        await sleep(15)
        r = requests.get(url, headers=headers, timeout=30)
    r = r.json()
    latest_year = 0
    for record in r["facts"]["us-gaap"]["Revenues"]["units"]["USD"]:
        if record["fy"] > latest_year and record["form"] == "10-K":
            revenue = record["val"]
            # fy = record["fy"]
    return revenue


def fix_cik(cik: str):
    """Check for proper CIK requirements.

    :param cik: <str> SEC CIK number
    :return: proper length CIK number
    """
    rtn_cik = None
    if len(cik) == 10:
        rtn_cik = cik
    else:
        rtn_cik = cik.rjust(10, "0")
    return rtn_cik


async def verify_club_data(data):
    """Lookup CIK info: https://www.sec.gov/edgar/searchedgar/cik.

    # https://data.sec.gov/submissions/CIK0000051143.json
    # https://data.sec.gov/api/xbrl/companyfacts/CIK0000051143.json
    # https://www.sec.gov/edgar/searchedgar/cik
    # https://www.sec.gov/edgar/sec-api-documentation

    :param data: <dict> club data json from local file
    :return data, changed: data is a dict with relevant club data, changed is a <bool> if anything was changed
    """
    changed = False
    assert "club" in data.keys()
    assert "name" in data["club"].keys()
    assert "valuation_dates" in data["club"].keys()
    # check valuation dates
    assert len(data["club"]["valuation_dates"]) > 0
    # check club stocks
    assert "club_stocks" in data["club"].keys()
    # check each club stock has verified info
    for stock in data["club"]["club_stocks"].keys():
        cik = fix_cik(data["club"]["club_stocks"][stock]["cik"])
        industry = data["club"]["club_stocks"][stock]["industry"]
        sector = data["club"]["club_stocks"][stock]["sector"]
        size = data["club"]["club_stocks"][stock]["company_size"]
        assert cik != ""
        if industry == "":
            data["club"]["club_stocks"][stock]["industry"] = await get_company_industry(cik)
            changed = True
        if sector != "":
            pass  # TODO get company sector information
        if size == "":
            revenue = await get_current_sec_10k_revenue(cik)
            size = company_size(revenue)
            changed = True
    return data, changed


def convert_html_to_pdf(source_html: str, output_filename: str):
    """Take HTML object and build a PDF document from it.

    :param source_html: (str) HTML string to write to PDF file
    :param output_filename: (str) path to pdf file
    :return: N/A
    """
    # open output file for writing (truncated binary)
    with open(output_filename, "w+b") as result_file:
        # convert HTML to PDF
        pisa.CreatePDF(source_html, dest=result_file)  # the HTML string to convert  # file handle to receive result


def draw_club_report(
    filename: str,
    stock_price_compare: pd.DataFrame,
    stock_charts: list,
    club_data: dict,
    reports_dir: str = "./reports/",
):
    # pylint: disable=consider-using-f-string, too-many-locals

    """Draw monthly club report.

    :param filename: <str> Filename to save report
    :param stock_price_compare: <pandas.DataFrame> Dataframe containing the ticker symbol,
                                Cost Basis, last month's stock price, this month's stock price,
                                and the % change between the two months.
    :param stock_charts: <list> of filenames of chart images
    :param club_data: <dict> json of club_data from club_info.json
    :param reports_dir: <str> optional directory to save reports to
    :return:
    """
    # Sanity checks for files and folders
    assert os.path.isdir(reports_dir)
    assert os.path.isdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources"))
    try:
        env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template("report_template.2.1.0.html")
        company_logo = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources", "logo.png")
        stock_info = []
        for index, row in stock_price_compare.iterrows():
            stock_info.append(
                {
                    "ticker": index,
                    "cost_basis": row["Cost Basis"].round(4),
                    "last_month_price": row["Last Month"].round(2),
                    "this_month_price": row["This Month"].round(2),
                    "percent_change": row["% change"].round(4),
                }
            )
        company_logo = ""  # TODO company logo file path
        portfolio_performance_chart = ""  # TODO portfolio performance chart file path
        # today = datetime.date.today()
        # first = today.replace(day=1)
        # last_month = first - datetime.timedelta(days=1)
        avail_capital = 0  # TODO available capital to invest minus 25% reserve
        min_investment = avail_capital * 0.03
        market_reaction_chart = ""  # TODO build market reaction chart
        last_month = datetime.datetime(1800, 1, 1).date()
        this_month = datetime.datetime(1800, 1, 1).date()
        for date in club_data["club"]["valuation_dates"]:
            date_t = datetime.datetime.strptime(date, "%m/%d/%Y").date()
            if date_t > this_month:
                last_month = this_month
                this_month = date_t
        # this_month = this_month.strftime("%m/%d/%Y")
        # last_month = last_month.strftime("%m/%d/%Y")
        last_unit_mkt = (
            club_data["club"]["valuation_dates"][last_month.strftime("%m/%d/%Y")]["total_market_value"]
            / club_data["club"]["valuation_dates"][last_month.strftime("%m/%d/%Y")]["total_units"]
        )
        this_unit_mkt = (
            club_data["club"]["valuation_dates"][this_month.strftime("%m/%d/%Y")]["total_market_value"]
            / club_data["club"]["valuation_dates"][this_month.strftime("%m/%d/%Y")]["total_units"]
        )
        this_earnings = (
            club_data["club"]["valuation_dates"][this_month.strftime("%m/%d/%Y")]["total_market_value"]
            - club_data["club"]["valuation_dates"][this_month.strftime("%m/%d/%Y")]["partner_equity"]
        ) / club_data["club"]["valuation_dates"][this_month.strftime("%m/%d/%Y")]["total_units"]
        last_earnings = (
            club_data["club"]["valuation_dates"][last_month.strftime("%m/%d/%Y")]["total_market_value"]
            - club_data["club"]["valuation_dates"][last_month.strftime("%m/%d/%Y")]["partner_equity"]
        ) / club_data["club"]["valuation_dates"][last_month.strftime("%m/%d/%Y")]["total_units"]
        club = {
            "last_month": {
                "unit_mkt": "{:,.3f}".format(last_unit_mkt),
                "tot_mkt_value": "{:,.2f}".format(
                    club_data["club"]["valuation_dates"][last_month.strftime("%m/%d/%Y")]["total_market_value"]
                ),
                "equity": "{:,.2f}".format(
                    club_data["club"]["valuation_dates"][last_month.strftime("%m/%d/%Y")]["partner_equity"]
                ),
                "units": "{:,.3f}".format(
                    club_data["club"]["valuation_dates"][last_month.strftime("%m/%d/%Y")]["total_units"]
                ),
                "earnings": "{:,.3f}".format(last_earnings),
            },
            "this_month": {
                "unit_mkt": "{:,.3f}".format(this_unit_mkt),
                "tot_mkt_value": "{:,.2f}".format(
                    club_data["club"]["valuation_dates"][this_month.strftime("%m/%d/%Y")]["total_market_value"]
                ),
                "equity": "{:,.2f}".format(
                    club_data["club"]["valuation_dates"][this_month.strftime("%m/%d/%Y")]["partner_equity"]
                ),
                "units": "{:,.3f}".format(
                    club_data["club"]["valuation_dates"][this_month.strftime("%m/%d/%Y")]["total_units"]
                ),
                "earnings": "{:,.3f}".format(this_earnings),
            },
            "unit_mkt_change": "{:,.3f}".format(this_unit_mkt - last_unit_mkt),
            "units_change": "{:,.3f}".format(
                club_data["club"]["valuation_dates"][this_month.strftime("%m/%d/%Y")]["total_units"]
                - club_data["club"]["valuation_dates"][last_month.strftime("%m/%d/%Y")]["total_units"]
            ),
            "tot_mkt_value_change": "{:.2f}".format(
                club_data["club"]["valuation_dates"][this_month.strftime("%m/%d/%Y")]["total_market_value"]
                - club_data["club"]["valuation_dates"][last_month.strftime("%m/%d/%Y")]["total_market_value"]
            ),
            "equity_change": "{:.2f}".format(
                club_data["club"]["valuation_dates"][this_month.strftime("%m/%d/%Y")]["partner_equity"]
                - club_data["club"]["valuation_dates"][last_month.strftime("%m/%d/%Y")]["partner_equity"]
            ),
            "earnings_change": f"{this_earnings - last_earnings:.3f}",
        }
        # Generate HTML page
        avail_capital = (
            club_data["club"]["valuation_dates"][this_month.strftime("%m/%d/%Y")]["available_capital"] * 0.75
        )
        min_investment = (
            club_data["club"]["valuation_dates"][this_month.strftime("%m/%d/%Y")]["total_market_value"] * 0.03
        )
        html_page = template.render(
            club_name="Cypress Investment Club",
            date=datetime.datetime.now().strftime("%B %Y"),
            logo=company_logo,
            last_month=last_month.strftime("%B"),
            this_month=datetime.datetime.now().strftime("%B"),
            stock_info=stock_info,
            stock_charts=stock_charts,
            portfolio_perfomrance_chart=portfolio_performance_chart,
            avail_capital=f"{avail_capital:,.2f}",
            min_investment=f"{min_investment:,.2f}",
            market_reaction=market_reaction_chart,
            club=club,
        )
        # save html page as PDF
        pdf_file_path = os.path.join(reports_dir, f"{filename}.pdf")
        convert_html_to_pdf(html_page, pdf_file_path)
    except AssertionError as err:
        raise FileNotFoundError(f"Company Logo not found! - {company_logo}") from err
    except Exception as err:
        print(err)
        raise err


# Configuration Management Functions
class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required values."""

    # pylint: disable=W0107
    pass


def load_env_config(existing_configuration_dictionary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # pylint: disable=too-many-branches
    """Load configuration from environment variables.

    Reads all required configuration values from environment variables
    and updates the provided configuration dictionary or creates a new one.

    {
        "logging_level": "INFO",
        "debug": False,
        "club_info_file": {},
        "club_stocks_file": {},
        "discord": {
            "token": "",
            "app_id": "",
            "public_key": "",
        },
        "alphavantage": {
            "key": "",
        },
        "slack": {
            "oauth_token": "",
            "signing_secret": "",
        },
        "fred": {
            "api_key": "",
        },
    }

    if os.getenv('CLUB_INFO_FILE'):
        configuration_dictionary["application"]["club_info_file_path"] = os.getenv('CLUB_INFO_FILE')

    if os.getenv('CLUB_STOCKS_FILE'):
        configuration_dictionary["application"]["club_stocks_file_path"] = os.getenv('CLUB_STOCKS_FILE')


    Args:
        existing_configuration_dictionary: Optional existing configuration dictionary to update

    Returns:
        Dict containing all configuration values (updated or newly created)

    Raises:
        ConfigurationError: If required environment variables are missing
    """
    required_environment_variables = {"DISCORD_TOKEN": "Discord bot token", "ALPHAVANTAGE_KEY": "Alpha Vantage API key"}

    # optional_environment_variables = {
    #     "DISCORD_APP_ID": "Discord application ID",
    #     "DISCORD_PUBLIC_KEY": "Discord public key",
    #     "SLACK_OAUTH": "Slack OAuth token",
    #     "SLACK_SIGNING_SECRET": "Slack signing secret",
    #     "FRED_KEY": "FRED API key",
    #     "LOGGING": "Logging level (INFO, DEBUG, WARNING, ERROR)",
    #     "DEBUG_MODE": "Debug mode flag (true/false)",
    #     "CONFIG_FILE": "Configuration file path",
    #     "CLUB_INFO_FILE": "Club information file path",
    #     "CLUB_STOCKS_FILE": "Club stocks CSV file path",
    # }

    # Start with existing configuration or create new one
    if existing_configuration_dictionary is None:
        configuration_dictionary = {
            "debug": False,
            "logging_level": "INFO",
            "club_info_file": {},
            "club_stocks_file": {},
            "discord": {},
            "alphavantage": {},
            "slack": {},
            "fred": {},
            "application": {},
        }
    else:
        configuration_dictionary = existing_configuration_dictionary.copy()
        # Ensure required sections exist
        configuration_dictionary.setdefault("discord", {})
        configuration_dictionary.setdefault("alphavantage", {})
        configuration_dictionary.setdefault("slack", {})
        configuration_dictionary.setdefault("fred", {})
        configuration_dictionary.setdefault("application", {})

    # Validate required environment variables exist
    missing_required_variables = []
    for environment_variable_name, description in required_environment_variables.items():
        if not os.getenv(environment_variable_name):
            missing_required_variables.append(f"{environment_variable_name} ({description})")

    if missing_required_variables:
        error_message = f"Missing required environment variables: {', '.join(missing_required_variables)}"
        LOGGER.error(error_message)
        raise ConfigurationError(error_message)

    # Update configuration dictionary with environment variables
    if os.getenv("DISCORD_TOKEN"):
        configuration_dictionary["discord"]["token"] = os.getenv("DISCORD_TOKEN")

    if os.getenv("DISCORD_APP_ID"):
        configuration_dictionary["discord"]["app_id"] = os.getenv("DISCORD_APP_ID")

    if os.getenv("DISCORD_PUBLIC_KEY"):
        configuration_dictionary["discord"]["public_key"] = os.getenv("DISCORD_PUBLIC_KEY")

    if os.getenv("ALPHAVANTAGE_KEY"):
        configuration_dictionary["alphavantage"]["key"] = os.getenv("ALPHAVANTAGE_KEY")

    if os.getenv("SLACK_OAUTH"):
        configuration_dictionary["slack"]["oauth_token"] = os.getenv("SLACK_OAUTH")

    if os.getenv("SLACK_SIGNING_SECRET"):
        configuration_dictionary["slack"]["signing_secret"] = os.getenv("SLACK_SIGNING_SECRET")

    if os.getenv("FRED_KEY"):
        configuration_dictionary["fred"]["api_key"] = os.getenv("FRED_KEY")

    if os.getenv("LOGGING"):
        configuration_dictionary["logging_level"] = os.getenv("LOGGING").upper()

    if os.getenv("DEBUG_MODE"):
        configuration_dictionary["debug_mode"] = os.getenv("DEBUG_MODE", "false").lower() == "true"

    if os.getenv("CLUB_INFO_FILE"):
        configuration_dictionary["club_info_file_path"] = os.getenv("CLUB_INFO_FILE")

    if os.getenv("CLUB_STOCKS_FILE"):
        configuration_dictionary["club_stocks_file_path"] = os.getenv("CLUB_STOCKS_FILE")

    # Validate logging level if it exists
    if "logging_level" in configuration_dictionary:
        valid_logging_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if configuration_dictionary["logging_level"] not in valid_logging_levels:
            LOGGER.warning(
                "Invalid logging level '%s', defaulting to INFO. Valid levels: %s",
                configuration_dictionary["logging_level"],
                ", ".join(valid_logging_levels),
            )
            configuration_dictionary["logging_level"] = "INFO"

    LOGGER.info("Configuration updated successfully from environment variables")
    LOGGER.debug("Updated configuration keys: %s", list(configuration_dictionary.keys()))

    return configuration_dictionary


def get_config_value(configuration_dictionary: Dict[str, Any], key_path: str, default_value: Any = None) -> Any:
    """Safely retrieve a nested configuration value.

    Args:
        configuration_dictionary: The configuration dictionary
        key_path: Dot-separated path to the value (e.g., 'discord.token')
        default_value: Value to return if key doesn't exist

    Returns:
        The configuration value or default_value if not found
    """
    keys = key_path.split(".")
    current_value = configuration_dictionary

    try:
        for key in keys:
            current_value = current_value[key]
        return current_value
    except (KeyError, TypeError):
        LOGGER.warning("Configuration key '%s' not found, using default: %s", key_path, default_value)
        return default_value


def validate_config(configuration_dictionary: Dict[str, Any]) -> bool:
    """Validate that all required configuration values are present and valid.

    Args:
        configuration_dictionary: Configuration dictionary to validate

    Returns:
        True if configuration is valid, False otherwise
    """
    validation_errors = []

    # Check Discord token
    discord_token = get_config_value(configuration_dictionary, "discord.token")
    if not discord_token or len(discord_token) < 50:  # Discord tokens are typically 59+ characters
        validation_errors.append("Discord token appears invalid (too short or missing)")

    # Check Alpha Vantage key
    alphavantage_key = get_config_value(configuration_dictionary, "alphavantage.key")
    if not alphavantage_key or len(alphavantage_key) < 10:  # Alpha Vantage keys are typically 16 characters
        validation_errors.append("Alpha Vantage API key appears invalid (too short or missing)")

    if validation_errors:
        for error in validation_errors:
            LOGGER.error("Configuration validation error: %s", error)
        return False

    LOGGER.info("Configuration validation passed")
    return True
