# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Discord chatbot entrypoint."""
import logging
import re
import sys

import discord

from . import portfolio_analysis
from . import stock_analysis
from . import utilities
from .utilities import ConfigurationError

LOGGER = logging.getLogger("discord")
# Global configuration instance - load on module import
# pylint: disable=broad-exception-caught

try:
    CONFIG = utilities.load_env_config()
    if not utilities.validate_config(CONFIG):
        LOGGER.warning("Configuration validation failed - some features may not work correctly")
except ConfigurationError as configuration_error:
    LOGGER.critical("Failed to load configuration: %s", configuration_error)
    sys.exit(1)

COMMANDS_HELP = {
    "!stock_report": "!stock_report <ticker> will return club worksheet calculations of the "
    "provided stock ticker. (also !sr)",
    "!graham_value": "!graham_value <ticker> will return the Graham Revised Valuation Formula",
    "!club_report": "!club_report will deliver the current status of the investment club. (also !cr)",
    "!terms_of_use": "!terms_of_use will display the current terms of use you (as the user) agree to abid by.",
    "!bug_report": "!bug_report will ",
}

HELP_INFO = (
    "Hi! I'm Warren, a bot here to help with your investment club. Press `!help` for "
    "instructions. I don't know, nor save your name, so your information is secure. I'm constantly "
    "being improved and you can trust that I'm always up to date with the latest "
    "technologies."
)

# Build and initialize discord Client
intents = discord.Intents.default()
intents.guild_messages = True
intents.messages = True
CLIENT = discord.Client(intents=intents)


def divide_prompt_and_content(content: str):
    """Process a prompt and return the query of a command.

    :param content: <str> Complete message from Discord
    :return: the query minus the bot prompt
    """
    # Split the content into the prompt and the content
    split_content = re.split("\\s+", content, maxsplit=1)
    LOGGER.debug("split_content: %s", split_content)
    rtn_content = None
    if len(split_content) > 1:
        prompt, content = split_content[0], split_content[1:]
        rtn_content = (prompt, "\n".join(content))
    else:
        rtn_content = (content, "")
    return rtn_content


async def help_command(message):
    """Build and deliver help command response.

    Build and deliver all the options that this bot provides.

    :param message: Discord Message
    """
    command_strings = [f"{command}: {description}" for command, description in COMMANDS_HELP.items()]
    # Join the command strings with a newline character
    command_list = "\n\n".join(command_strings)
    # Send the message
    help_message = HELP_INFO + "\n" + """```""" + command_list + """```"""
    await message.reply(help_message)


async def display_terms_of_use(message):
    """Display terms of use.

    :param message:
    :return:
    """
    msg = """By using this application, you agree to be bound by the Terms of Use. https://github.com/CyIC/warren_bot/blob/main/terms_of_use.md"""  # pylint: disable=line-too-long
    await message.reply(f"\n{msg}")


async def run_stock_report(message):
    """

    :param message:
    :return:
    """
    try:
        ticker = message.content.split(" ", 1)[1]  # Get the stock ticker
        ticker = ticker.strip().upper()
        if not re.match(r"^[A-Z]{1,5}$", ticker):
            await message.reply("Invalid ticker symbol. Please use 1-5 letters.")
            return
    except IndexError:
        await message.reply("!stock_report requires a ticker symbol.")
        return
    await message.add_reaction("⏳")
    try:
        await stock_analysis.club_analysis(message, ticker)
        await message.channel.send("\n✅ __**Stock Report Finished!**__")
    except Exception as e:
        try:
            await message.clear_reaction("⏳")
        except discord.errors.Forbidden:
            pass
        await message.add_reaction("🛑")
        LOGGER.error("Stock report failed for ticker %s: %s", ticker, str(e))
        await message.reply("❌ Stock report failed. Please try again later.")
        # Don't re-raise - let bot continue running


async def run_club_report(message):
    """Build and deliver club report.

    :return:
    """
    await message.add_reaction("⏳")
    try:
        await portfolio_analysis.run("./cyic_stocks.csv", "./club_info.json")
        try:
            await message.clear_reaction("⏳")
        except discord.errors.Forbidden:
            pass
        await message.add_reaction("✅")
    except Exception as e:
        # await message.clear_reaction("⏳")
        await message.add_reaction("🛑")
        LOGGER.error("Club report failed: %s", str(e))
        await message.reply("\n❌ __**Club Report Failed!**__")


async def run_graham_value(message):
    """Use a given stock ticker to calculate the graham value

    :param message: Discord Message
    """
    try:
        ticker = message.content.split(" ", 1)[1]  # Get the stock ticker
        ticker = str.upper(ticker)
    except IndexError:
        await message.reply("!graham_value requires a ticker symbol.")
        return
    await message.add_reaction("⏳")
    try:
        await stock_analysis.graham_value(message, ticker)
        await message.channel.send("\n✅ __**Stock Report Finished!**__")
    except Exception as e:
        try:
            await message.clear_reaction("⏳")
        except discord.errors.Forbidden:
            pass
        await message.add_reaction("🛑")
        LOGGER.error("Graham report failed for ticker %s: %s", ticker, str(e))
        await message.reply("\n❌ __**Graham Report Failed!**__")


async def run_report_bug(message):
    """A method to log and track bug reports from users.

    This method will be used to provide feedback from users for warren_bot. Interactions will include modifying message
    reactions and adding new messages to the channel.

    :param message:  Discord Message
    """
    await message.add_reaction("⏳")
    try:
        # TODO Display bug report
        try:
            await message.clear_reaction("⏳")
        except discord.errors.Forbidden:
            pass
        await message.add_reaction("✅")
    except Exception as e:
        await message.add_reaction("🛑")
        await message.reply("\n❌ __**Portfolio Report Failed!**__")
        raise e


@CLIENT.event
async def on_ready():
    """React when bot is logged in.

    This method controls how the bot immediately reacts when initially connected and authenticated
    to the Discord system.
    """
    await CLIENT.change_presence(activity=discord.Activity(name="the markets.", type=discord.ActivityType.watching))
    LOGGER.info("We have logged in as %s :: %s", CLIENT.user, CLIENT.application_id)


@CLIENT.event
async def on_message(message):
    """Retrieve messages and act on them.

    :param message: a typed message to, or in the presence of the bot
    """
    if message.author == CLIENT.user:  # if message is from the bot itself
        return
    if message.author.bot:  # if author is another bot
        return

    if message.content.startswith(f"<@{CLIENT.application_id}>"):
        id_length = len(str(CLIENT.application_id))
        LOGGER.debug(message.content)
        message.content = message.content[id_length + 3 :].strip()  # noqa: E203

    prompt, query = divide_prompt_and_content(message.content)  # pylint: disable=unused-variable

    # skip if no one is talking to Warren
    if prompt is None or prompt == "":
        return

    # List of commands warren_bot will respond to
    match str.lower(prompt):
        case "!help":
            await help_command(message)
        case "!stock_report" | "!sr":
            await run_stock_report(message)
        case "!club_report" | "!cr":
            await run_club_report(message)
        # case "!bug":
        #     await run_report_bug(message)
        case "!graham_value":
            await run_graham_value(message)
        case "!terms_of_use":
            await display_terms_of_use(message)
        case _:
            await message.reply("Command not recognized")


async def main():
    await portfolio_analysis.run("./cyic_stocks.csv", "./club_info.json")


def run():
    CLIENT.run(CONFIG["discord"]["token"])


if __name__ == "__main__":
    CLIENT.run(CONFIG["discord"]["token"])
    # asyncio.run(main())
