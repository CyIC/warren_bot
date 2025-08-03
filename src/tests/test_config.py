# -*- coding: utf-8 -*-
"""Unit tests for warren_bot.utilities module configuration functions."""
import os
import unittest
from unittest.mock import patch

from warren_bot.utilities import load_env_config, get_config_value, validate_config, ConfigurationError


class TestLoadEnvironmentConfiguration(unittest.TestCase):
    """Test load_environment_configuration function."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_environment_variables = {
            "DISCORD_TOKEN": "fantasy-entities-felipe",
            "ALPHAVANTAGE_KEY": "phantom-toes-striker",
            "DISCORD_APP_ID": "tok-madge-outfit",
            "DISCORD_PUBLIC_KEY": "asher-othello-pistol",
            "SLACK_OAUTH": "cork-allied-taylor",
            "SLACK_SIGNING_SECRET": "cesare-decipher-tougher",
            "FRED_KEY": "foggy-thump-grr",
            "LOGGING": "DEBUG",
            "DEBUG_MODE": "true",
        }

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_required_environment_variables_raises_error(self):
        """Test that missing required environment variables raise ConfigurationError."""
        with self.assertRaises(ConfigurationError) as context:
            load_env_config()

        error_message = str(context.exception)
        self.assertIn("DISCORD_TOKEN", error_message)
        self.assertIn("ALPHAVANTAGE_KEY", error_message)

    @patch.dict(os.environ, {"DISCORD_TOKEN": "test_token"}, clear=True)
    def test_missing_alphavantage_key_raises_error(self):
        """Test that missing ALPHAVANTAGE_KEY raises ConfigurationError."""
        with self.assertRaises(ConfigurationError) as context:
            load_env_config()

        error_message = str(context.exception)
        self.assertIn("ALPHAVANTAGE_KEY", error_message)
        self.assertNotIn("DISCORD_TOKEN", error_message)

    @patch.dict(os.environ, {"ALPHAVANTAGE_KEY": "test_key"}, clear=True)
    def test_missing_discord_token_raises_error(self):
        """Test that missing DISCORD_TOKEN raises ConfigurationError."""
        with self.assertRaises(ConfigurationError) as context:
            load_env_config()

        error_message = str(context.exception)
        self.assertIn("DISCORD_TOKEN", error_message)

    @patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "test_token_123456789012345678901234567890123456789012345678901234567890",
            "ALPHAVANTAGE_KEY": "test_key_16chars",
        },
        clear=True,
    )
    def test_loads_required_environment_variables_only(self):
        """Test loading with only required environment variables."""
        configuration_result = load_env_config()

        self.assertEqual(
            configuration_result["discord"]["token"],
            "test_token_123456789012345678901234567890123456789012345678901234567890",
        )
        self.assertEqual(configuration_result["alphavantage"]["key"], "test_key_16chars")

        # Optional variables should not be present
        self.assertNotIn("app_id", configuration_result["discord"])
        self.assertNotIn("oauth_token", configuration_result["slack"])

    @patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "test_discord_token_long_enough_for_validation_requirements",
            "ALPHAVANTAGE_KEY": "test_alphavantage_key",
            "DISCORD_APP_ID": "123456789",
            "DISCORD_PUBLIC_KEY": "test_public_key",
            "SLACK_OAUTH": "xoxb-test-slack-token",
            "SLACK_SIGNING_SECRET": "test_signing_secret",
            "FRED_KEY": "test_fred_key",
            "LOGGING": "WARNING",
            "DEBUG_MODE": "false",
        },
        clear=True,
    )
    def test_loads_all_environment_variables(self):
        """Test loading all environment variables."""
        configuration_result = load_env_config()

        # Check required variables
        self.assertEqual(
            configuration_result["discord"]["token"], "test_discord_token_long_enough_for_validation_requirements"
        )
        self.assertEqual(configuration_result["alphavantage"]["key"], "test_alphavantage_key")

        # Check optional Discord variables
        self.assertEqual(configuration_result["discord"]["app_id"], "123456789")
        self.assertEqual(configuration_result["discord"]["public_key"], "test_public_key")

        # Check Slack variables
        self.assertEqual(configuration_result["slack"]["oauth_token"], "xoxb-test-slack-token")
        self.assertEqual(configuration_result["slack"]["signing_secret"], "test_signing_secret")

        # Check FRED variable
        self.assertEqual(configuration_result["fred"]["api_key"], "test_fred_key")

        # Check application variables
        self.assertEqual(configuration_result["logging_level"], "WARNING")
        self.assertEqual(configuration_result["debug_mode"], False)

    @patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "test_token_123456789012345678901234567890123456789012345678901234567890",
            "ALPHAVANTAGE_KEY": "test_key_16chars",
            "DEBUG_MODE": "true",
        },
        clear=True,
    )
    def test_boolean_environment_variable_parsing(self):
        """Test parsing of boolean environment variables."""
        configuration_result = load_env_config()
        self.assertEqual(configuration_result["debug_mode"], True)

    @patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "test_token_123456789012345678901234567890123456789012345678901234567890",
            "ALPHAVANTAGE_KEY": "test_key_16chars",
            "LOGGING": "invalid_level",
        },
        clear=True,
    )
    def test_invalid_logging_level_defaults_to_info(self):
        """Test that invalid logging level defaults to INFO."""
        with patch("warren_bot.utilities.LOGGER") as mock_logger:
            configuration_result = load_env_config()
            self.assertEqual(configuration_result["logging_level"], "INFO")
            mock_logger.warning.assert_called_once()

    def test_updates_existing_configuration_dictionary(self):
        """Test updating an existing configuration dictionary."""
        existing_configuration = {"discord": {"token": "old_token"}, "application": {"existing_key": "existing_value"}}

        with patch.dict(
            os.environ,
            {
                "DISCORD_TOKEN": "new_token_123456789012345678901234567890123456789012345678901234567890",
                "ALPHAVANTAGE_KEY": "new_key_16chars",
            },
            clear=True,
        ):
            updated_configuration = load_env_config(existing_configuration)

            # Should update existing values
            self.assertEqual(
                updated_configuration["discord"]["token"],
                "new_token_123456789012345678901234567890123456789012345678901234567890",
            )
            self.assertEqual(updated_configuration["alphavantage"]["key"], "new_key_16chars")

            # Should preserve existing values not overwritten
            self.assertEqual(updated_configuration["application"]["existing_key"], "existing_value")


class TestGetConfigurationValue(unittest.TestCase):
    """Test get_configuration_value function."""

    def setUp(self):
        """Set up test configuration dictionary."""
        self.test_configuration_dictionary = {
            "discord": {"token": "test_token", "app_id": "123456"},
            "alphavantage": {"key": "test_key"},
            "nested": {"deep": {"value": "deep_value"}},
        }

    def test_gets_existing_single_level_value(self):
        """Test getting an existing single-level value."""
        result = get_config_value(self.test_configuration_dictionary, "discord.token")
        self.assertEqual(result, "test_token")

    def test_gets_existing_nested_value(self):
        """Test getting an existing nested value."""
        result = get_config_value(self.test_configuration_dictionary, "nested.deep.value")
        self.assertEqual(result, "deep_value")

    def test_returns_default_for_missing_key(self):
        """Test returning default value for missing key."""
        result = get_config_value(self.test_configuration_dictionary, "missing.key", "default")
        self.assertEqual(result, "default")

    def test_returns_none_for_missing_key_without_default(self):
        """Test returning None for missing key without default."""
        result = get_config_value(self.test_configuration_dictionary, "missing.key")
        self.assertIsNone(result)

    def test_handles_invalid_key_path(self):
        """Test handling invalid key path."""
        result = get_config_value(self.test_configuration_dictionary, "discord.invalid.path", "default")
        self.assertEqual(result, "default")

    @patch("warren_bot.utilities.LOGGER")
    def test_logs_warning_for_missing_key(self, mock_logger):
        """Test that warning is logged for missing key."""
        get_config_value(self.test_configuration_dictionary, "missing.key", "default")
        mock_logger.warning.assert_called_once()


class TestValidateConfiguration(unittest.TestCase):
    """Test validate_configuration function."""

    def test_validates_valid_configuration(self):
        """Test validation of valid configuration."""
        valid_configuration = {
            "discord": {"token": "fantasy-entities-felipe"},
            "alphavantage": {"key": "phantom-toes-striker"},
        }

        result = validate_config(valid_configuration)
        self.assertTrue(result)

    def test_fails_validation_for_short_discord_token(self):
        """Test validation failure for short Discord token."""
        invalid_configuration = {"discord": {"token": "short"}, "alphavantage": {"key": "phantom-toes-striker"}}

        with patch("warren_bot.utilities.LOGGER") as mock_logger:
            result = validate_config(invalid_configuration)
            self.assertFalse(result)
            mock_logger.error.assert_called()

    def test_fails_validation_for_missing_discord_token(self):
        """Test validation failure for missing Discord token."""
        invalid_configuration = {"discord": {}, "alphavantage": {"key": "phantom-toes-striker"}}

        with patch("warren_bot.utilities.LOGGER") as mock_logger:
            result = validate_config(invalid_configuration)
            self.assertFalse(result)
            mock_logger.error.assert_called()

    def test_fails_validation_for_short_alphavantage_key(self):
        """Test validation failure for short Alpha Vantage key."""
        invalid_configuration = {
            "discord": {"token": "fantasy-entities-felipe"},
            "alphavantage": {"key": "short"},
        }

        with patch("warren_bot.utilities.LOGGER") as mock_logger:
            result = validate_config(invalid_configuration)
            self.assertFalse(result)
            mock_logger.error.assert_called()

    def test_fails_validation_for_missing_alphavantage_key(self):
        """Test validation failure for missing Alpha Vantage key."""
        invalid_configuration = {
            "discord": {"token": "fantasy-entities-felipe"},
            "alphavantage": {},
        }

        with patch("warren_bot.utilities.LOGGER") as mock_logger:
            result = validate_config(invalid_configuration)
            self.assertFalse(result)
            mock_logger.error.assert_called()


class TestConfigurationError(unittest.TestCase):
    """Test ConfigurationError exception."""

    def test_configuration_error_is_exception(self):
        """Test that ConfigurationError is an Exception."""
        error = ConfigurationError("test message")
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "test message")


if __name__ == "__main__":
    unittest.main()
