import configparser
import discord
import re

import stock_report
import utilities

config = configparser.ConfigParser()
config.read('.\bot_config.ini')
token = config['discord']['token']
KEY = config['alphavantage']['key']

DEBUT = False

commands_help = {
    "!stock_report": "!stock_report <ticker> will return club worksheet calculations of the "
                     "provided stock ticker.",
    "!club_status": "!club_status will deliver the current status of the investment club."
}

helpinfo = "Hi! I'm Warren, a bot here to help with your investment club. Press `!help` for " \
           "instructions. I won't know your name, so your information is secure. I'm constantly " \
           "being improved and you can trust that I'm always up to date with the latest technologies."

MAX_MESSAGE_LENGTH = 2000  # Maximum message length allowed by Discord


def divide_prompt_and_content(content):
    # Split the content into the prompt and the content
    split_content = re.split('''\n|\\.|\\?|\'\'\'|\\`\\`\\`|\\!''', content)
    if len(split_content) > 1:
        prompt, content = split_content[0], split_content[1:]
        return prompt, '\n'.join(content)
    else:
        return content, ''


async def help_command(message):
    command_strings = [f"{command}: {description}" for command, description in
                       commands_help.items()]
    # Join the command strings with a newline character
    command_list = "\n\n".join(command_strings)
    # Send the message
    help_message = helpinfo + "\n" + '''```''' + command_list + '''```'''
    await message.reply(help_message)
    return


async def send_message_in_chunks(channel, content):
    # split the message into chunks
    chunks = [content[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(content), MAX_MESSAGE_LENGTH)]

    for chunk in chunks:
        await channel.send(chunk)  # send each chunk to the channel

intents = discord.Intents.default()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(name='the markets.',
                                                           type=discord.ActivityType.watching))
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:  # if message is from the bot itself
        return

    if message.content.startswith('!hello'):
        await message.channel.send('Hello')

    if message.channel.type == discord.ChannelType.private:  # If the message is in a DM
        user = str(message.author.id)  # get user ID

        if message.content.startswith("!help"):  # if the message starts with !help
            await help_command(message)

        if message.content.startswith("!stock_report") or message.content.startswith("!sr"):  # run club report
            try:
                STOCK_TICKER = message.content.split(" ", 1)[1]  # Get the stock ticker
                STOCK_TICKER = str.upper(STOCK_TICKER)
            except IndexError:
                await message.reply("!stock_report requires a ticker symbol.")
                return

            # Get Company Data
            income_statement_json = utilities.get_alphavantage_data('INCOME_STATEMENT',
                                                                    STOCK_TICKER, KEY)
            balance_sheet_json = utilities.get_alphavantage_data('BALANCE_SHEET', STOCK_TICKER, KEY)
            monthly_company_price_json = utilities.get_alphavantage_data('TIME_SERIES_MONTHLY_ADJUSTED',
                                                                         STOCK_TICKER,
                                                                         KEY)
            company_data = utilities.process_alphavantage_annual_company_info(income_statement_json,
                                                                              balance_sheet_json)
            cash_flow_json = utilities.get_alphavantage_data('CASH_FLOW', STOCK_TICKER, KEY)
            # Get company stock prices
            stock_price_json = utilities.get_alphavantage_data('TIME_SERIES_DAILY_ADJUSTED',
                                                               STOCK_TICKER, KEY)
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



client.run(token)
