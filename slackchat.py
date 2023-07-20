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
from slack_bolt import App, Say

# Initializes your app with your bot token and signing secret
app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

# Add functionality here
@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    try:
        # views.publish is the method that your app uses to push a view to the Home tab
        client.views_publish(
            # the user that opened your app's app home
            user_id=event["user"],
            # the view object that appears in the app home
            view={
                "type": "home",
                "callback_id": "home_view",
                # body of the view
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Welcome to your _App's Home_* :tada:"
                        }
                    },
                    {
                        "type": "divider",
                    },
                    {   "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "This button won't do much for now but you can setup a listener for it using the `actions()` method and passing its unique `action_id`"
                        }
                    },
                    {   "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Click Me!"
                                }
                            }
                        ]
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")


@app.message("test")
def reply_to_test(say):
    say("Yes, tests are important!")

@message.im("test")
def reply_to_test(say):
    say("yes, test away")


# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
