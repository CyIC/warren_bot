# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Unit testing module for logging_config."""
import logging
import unittest

from warren_bot import logging_config


class SetLoggingLevelTestCase(unittest.TestCase):
    """Cover every branch of set_logging_level."""

    def test_debug(self):
        self.assertEqual(logging_config.set_logging_level("debug"), logging.DEBUG)

    def test_info(self):
        self.assertEqual(logging_config.set_logging_level("info"), logging.INFO)

    def test_warn_alias(self):
        self.assertEqual(logging_config.set_logging_level("warn"), logging.WARNING)

    def test_warning(self):
        self.assertEqual(logging_config.set_logging_level("WARNING"), logging.WARNING)

    def test_error(self):
        self.assertEqual(logging_config.set_logging_level("error"), logging.ERROR)

    def test_critical(self):
        self.assertEqual(logging_config.set_logging_level("critical"), logging.CRITICAL)

    def test_unknown_defaults_to_info(self):
        self.assertEqual(logging_config.set_logging_level("bogus"), logging.INFO)


if __name__ == "__main__":
    unittest.main()
