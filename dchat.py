# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Discord chatbot entrypoint."""
import configparser
import discord
import re
import logging

from warrenBot import stock_analysis
from warrenBot import portfolio_analysis

config = configparser.ConfigParser()
config.read('bot_config.ini')
token = config['discord']['token']
KEY = config['alphavantage']['key']
logger = logging.getLogger('discord')

DEBUG = False

commands_help = {
    "!stock_report": "!stock_report <ticker> will return club worksheet calculations of the "
                     "provided stock ticker. (also !sr)",
    "!club_report": "!club_report will deliver the current status of the investment club. (also !cr)"
}

helpinfo = "Hi! I'm Warren, a bot here to help with your investment club. Press `!help` for " \
           "instructions. I won't know your name, so your information is secure. I'm constantly " \
           "being improved and you can trust that I'm always up to date with the latest " \
           "technologies."

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
    split_content = re.split('\s+', content, maxsplit=1)
    logger.info("split_content: {}".format(split_content))
    if len(split_content) > 1:
        prompt, content = split_content[0], split_content[1:]
        return prompt, '\n'.join(content)
    else:
        return content, ''


async def help_command(message):
    """Build and deliver help command response.

    Build and deliver all the options that this bot provides.

    :param message: Discord Message
    :return:
    """
    command_strings = [f"{command}: {description}" for command, description in
                       commands_help.items()]
    # Join the command strings with a newline character
    command_list = "\n\n".join(command_strings)
    # Send the message
    help_message = helpinfo + "\n" + '''```''' + command_list + '''```'''
    await message.reply(help_message)
    return

async def run_stock_report(message):
    try:
        ticker = message.content.split(" ", 1)[1]  # Get the stock ticker
        ticker = str.upper(ticker)
    except IndexError:
        await message.reply("!stock_report requires a ticker symbol.")
        return
    await message.add_reaction("⏳")
    await stock_analysis.run(message, ticker)
    await message.channel.send('\n✅__**Stock Report Finished!**__')


async def run_club_report(message):
    """Build and deliver club report.

    :return:
    """
    await message.add_reaction("⏳")
    await portfolio_analysis.run('./cyic_stocks.csv', './club_info.json', KEY)
    try:
        await message.clear_reaction("⏳")
    except discord.errors.Forbidden:
        pass
    await message.add_reaction("✅")


@CLIENT.event
async def on_ready():
    """React when bot is logged in.

    This method controls how the bot immediately reacts when initially connected and authenticated
    to the Discord system.

    :return:
    """
    await CLIENT.change_presence(activity=discord.Activity(name='the markets.',
                                                           type=discord.ActivityType.watching))
    logger.info(f'We have logged in as {CLIENT.user} :: {CLIENT.application_id}')


@CLIENT.event
async def on_message(message):
    if message.author == CLIENT.user:  # if message is from the bot itself
        return
    elif message.author.bot:  # ignore if author is another bot
        return

    if message.content.startswith("<@{}>".format(CLIENT.application_id)):
        id_length = len(str(CLIENT.application_id))
        message.content = message.content[id_length+3:].strip()

    prompt, query = divide_prompt_and_content(message.content)

    # skip if no one is talking to Warren
    if prompt is None or prompt == '':
        return

    match str.lower(prompt):
        case "!help":
            await help_command(message)
        case "!stock_report" | '!sr':
            await run_stock_report(message)
        case "!club_report" | '!cr':
            await run_club_report(message)
        case _:
            await message.reply("Command not recognized")


async def main():
    await portfolio_analysis.run('./cyic_stocks.csv', './club_info.json', KEY)

if __name__ == '__main__':
    CLIENT.run(token)
    # asyncio.run(main())
