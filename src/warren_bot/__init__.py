# -*- coding: utf-8 -*-
"""Top-level package for warrenbot.

warren_bot
Copyright (c) 2024 Cypress Investment Club
Full license in LICENSE.md
"""
import logging

from . import logging_config  # noqa: F401

__author__ = "J.A. Simmons V"
__maintainer__ = "J.A. Simmons V"
__email__ = "simmonsj@jasimmonsv.com"
__version__ = "0.1.0"

# Default
CONFIG = {
    "logging_level": "INFO",
    "discord": {
        "token": "",
        "discord_app_id": "",
        "discord_public_key": "",
    },
}

LOGGER = logging.getLogger(__name__)
LOGGER.info("Init warren_bot...")
