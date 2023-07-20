# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Slack chatbot entrypoint."""
import configparser
import re
import logging

from warrenBot import stock_analysis
from warrenBot import portfolio_analysis

config = configparser.ConfigParser()
config.read('bot_config.ini')
SLACK_BOT_TOKEN = config['slack']['oauth']
SLACK_SIGNING_SECRET = config['slack']['signing_secret']
KEY = config['alphavantage']['key']
logger = logging.getLogger('slack')

import os
# Use the package we installed
from slack_bolt import App

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Add functionality here
# @app.event("app_home_opened") etc


# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))