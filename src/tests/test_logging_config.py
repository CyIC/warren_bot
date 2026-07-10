# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Unit testing module for logging_config."""
import logging
import logging.config
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


class LoggingDictConfigTestCase(unittest.TestCase):
    """Ensure the dictConfig produces a working stdout stream."""

    def test_stdout_handler_resolves_to_writable_stream(self):
        """Regression: a malformed 'stream' URI left the handler with a str (no .write)."""
        logging.config.dictConfig(logging_config.LOGGING)
        stream_handlers = [
            handler for handler in logging.getLogger().handlers if isinstance(handler, logging.StreamHandler)
        ]
        self.assertTrue(stream_handlers, "expected a StreamHandler on the root logger")
        for handler in stream_handlers:
            self.assertTrue(hasattr(handler.stream, "write"), "handler stream must be a real file object")


if __name__ == "__main__":
    unittest.main()
