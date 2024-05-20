# -*- coding: utf-8 -*-
"""Top-level package for warrenbot.

warren_bot
Copyright (c) 2024 Cypress Investment Club
Full license in LICENSE.md
"""
import logging
import os
import sys

from . import logging_config  # noqa: F401

from . import utilities as utils

__author__ = "J.A. Simmons V"
__maintainer__ = "J.A. Simmons V"
__email__ = "simmonsj@jasimmonsv.com"
__version__ = "0.1.0"

# Default
CLI_ARGS = None
CONFIG = {
    "config_file": "bot_config.ini",
    "logging_level": "INFO",
    "discord": {
        "token": "",
        "discord_app_id": "",
        "discord_public_key": "",
    },
    "alphavantage": {"key": ""},
}


def process_config():
    """Process configuration variations.

    This method will build the final CONFIG object based on suer supplied input through config files, CLI arguments,
    and environmental variables according to the order of precedence and write directly to the global CONFIG object.

    Order of precendence: (top overwrites lower)
    1. CLI Argument
    2. ENV variables
    3. config_file
    4. then default
    """
    global CONFIG, CLI_ARGS  # pylint: disable=global-variable-undefined,global-statement
    CLI_ARGS, unknown = utils.parse_args(sys.argv[1:])  # TODO pylint: disable=assignment-from-no-return,unused-variable
    # CONFIG FILE :: overwriting defaults
    # Check if config file was passed in CLI arguments
    LOGGER.debug("cli_args %s", CLI_ARGS)
    if "--config" in CLI_ARGS:
        if CLI_ARGS.config is not None:
            CONFIG["config_file"] = CLI_ARGS.config
    elif "WARREN_CONFIG" in os.environ:
        CONFIG["config_file"] = os.environ["WARREN_CONFIG"]
    else:  # Default to bot_config.ini
        CONFIG["config_file"] = "./bot_config.ini"

    # First, read from config file
    try:
        assert os.path.exists(CONFIG["config_file"])
        CONFIG = utils.process_config_file(CONFIG)
    except (AssertionError, TypeError):
        LOGGER.critical("Config file does not exist.")

    # Overwrite with ENV variables
    CONFIG = utils.process_env_variables(CONFIG)

    # Finally, overwrite with CLI arguments
    CONFIG = utils.process_cli(CONFIG, CLI_ARGS)  # pylint: disable=assignment-from-no-return
    LOGGER.info("Logging level: %s", LOGGER.getEffectiveLevel())


LOGGER = logging.getLogger(__name__)
LOGGER.info("Init warren_bot...")
