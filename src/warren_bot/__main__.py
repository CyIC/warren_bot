# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Discord chatbot entrypoint."""
import configparser
import logging
import re

import discord

from warren_bot import portfolio_analysis
from warren_bot import stock_analysis


config = configparser.ConfigParser()
config.read("./bot_config.ini")
TOKEN = config["discord"]["token"]
KEY = config["alphavantage"]["key"]
LOGGER = logging.getLogger("discord")

DEBUG = False

COMMANDS_HELP = {
    "!stock_report": "!stock_report <ticker> will return club worksheet calculations of the "
    "provided stock ticker. (also !sr)",
    "!club_report": "!club_report will deliver the current status of the investment club. (also !cr)",
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


async def run_stock_report(message):
    try:
        ticker = message.content.split(" ", 1)[1]  # Get the stock ticker
        ticker = str.upper(ticker)
    except IndexError:
        await message.reply("!stock_report requires a ticker symbol.")
        return
    await message.add_reaction("⏳")
    try:
        await stock_analysis.run(message, ticker, KEY)
        await message.channel.send("\n✅ __**Stock Report Finished!**__")
    except Exception as e:
        try:
            await message.clear_reaction("⏳")
        except discord.errors.Forbidden:
            pass
        await message.add_reaction("🛑")
        await message.reply("\n❌ __**Stock Report Failed!**__")
        raise e


async def run_club_report(message):
    """Build and deliver club report.

    :return:
    """
    await message.add_reaction("⏳")
    try:
        await portfolio_analysis.run("./cyic_stocks.csv", "./club_info.json", key=KEY)
        try:
            await message.clear_reaction("⏳")
        except discord.errors.Forbidden:
            pass
        await message.add_reaction("✅")
    except Exception as e:
        # await message.clear_reaction("⏳")
        await message.add_reaction("🛑")
        await message.reply("\n❌ __**Portfolio Report Failed!**__")
        raise e


async def run_report_bug(message):
    """A method to log and track bug reports from users.

    This method will be used to provide feedback from users for warren_bot. Interactions will include modifying message
    reactions and adding new messages to the channel.

    :param message:  Discord Message
    """
    await message.add_reaction("⏳")
    try:
        # Display bug report
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
        case "!bug":
            await run_report_bug(message)
        case _:
            await message.reply("Command not recognized")


async def main():
    await portfolio_analysis.run("./cyic_stocks.csv", "./club_info.json", KEY)


async def run():
    CLIENT.run(TOKEN)


if __name__ == "__main__":
    CLIENT.run(TOKEN)
    # asyncio.run(main())
