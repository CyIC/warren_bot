import asyncio
import configparser
import discord
import re

from warrenBot import utilities as utils
from warrenBot import stock_report
from warrenBot import club_analysis

config = configparser.ConfigParser()
config.read('bot_config.ini')
token = config['discord']['token']
KEY = config['alphavantage']['key']

DEBUT = False

commands_help = {
    "!stock_report": "!stock_report <ticker> will return club worksheet calculations of the "
                     "provided stock ticker. (also !sr)",
    "!club_report": "!club_report will deliver the current status of the investment club. (also !cr)"
}

helpinfo = "Hi! I'm Warren, a bot here to help with your investment club. Press `!help` for " \
           "instructions. I won't know your name, so your information is secure. I'm constantly " \
           "being improved and you can trust that I'm always up to date with the latest " \
           "technologies."

MAX_MESSAGE_LENGTH = 2000  # Maximum message length allowed by Discord

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
    print("split_content: {}".format(split_content))
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


async def send_message_in_chunks(channel, content):
    """Split a long message into Discord allowed chunks.

    :param channel: Discord message channel
    :param content: Message to break into chunks
    :return:
    """
    # split the message into chunks
    chunks = [content[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(content), MAX_MESSAGE_LENGTH)]

    for chunk in chunks:
        await channel.send(chunk)  # send each chunk to the channel


async def run_stock_report(message):
    try:
        ticker = message.content.split(" ", 1)[1]  # Get the stock ticker
        ticker = str.upper(ticker)
    except IndexError:
        await message.reply("!stock_report requires a ticker symbol.")
        return

    # Get Company Data
    income_statement_json = utils.get_alphavantage_data('INCOME_STATEMENT',
                                                        ticker, KEY)
    balance_sheet_json = utils.get_alphavantage_data('BALANCE_SHEET', ticker, KEY)
    monthly_company_price_json = utils.get_alphavantage_data('TIME_SERIES_MONTHLY_ADJUSTED',
                                                             ticker,
                                                             KEY)
    company_data = utils.process_alphavantage_annual_company_info(income_statement_json,
                                                                  balance_sheet_json)
    cash_flow_json = utils.get_alphavantage_data('CASH_FLOW', ticker, KEY)
    # Get company stock prices
    stock_price_json = utils.get_alphavantage_data('TIME_SERIES_DAILY_ADJUSTED',
                                                   ticker, KEY)
    # Build and send report components
    await stock_report.past_sales_records(message, company_data)
    await stock_report.past_eps(message, company_data)
    await stock_report.record_of_stock(message,
                                       company_data,
                                       stock_price_json,
                                       income_statement_json,
                                       monthly_company_price_json,
                                       )
    await stock_report.trend(message,
                             income_statement_json,
                             company_data,
                             monthly_company_price_json)
    await stock_report.cash_position(message, company_data)
    await stock_report.revenue_growth(message,
                                      company_data,
                                      stock_price_json,
                                      income_statement_json,
                                      cash_flow_json)
    await stock_report.earnings_growth(message, cash_flow_json)
    await message.channel.send('Stock Report Finished!')


async def run_club_report(message):
    """Build and deliver club report.

    :param message: discord.message.Message message passed from Discord
    :return:
    """
    await message.reply("Functionality has not been built yet.")
    club_analysis.load_club_stocks('./personal_stocks.csv', KEY)


@CLIENT.event
async def on_ready():
    """React when bot is logged in.

    This method controls how the bot immediately reacts when initially connected and authenticated
    to the Discord system.

    :return:
    """
    await CLIENT.change_presence(activity=discord.Activity(name='the markets.',
                                                           type=discord.ActivityType.watching))
    print(f'We have logged in as {CLIENT.user} :: {CLIENT.application_id}')


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
    # CLIENT.run(token)
    await club_analysis.load_club_stocks('./cyic_stocks.csv', './club_info.json', KEY)

if __name__ == '__main__':
    asyncio.run(main())
