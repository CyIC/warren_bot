# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Unit testing module for the utilities module."""
import asyncio
import os
import shutil
import tempfile
import unittest
from unittest import mock

from warren_bot import utilities as util


class FixCikTestCase(unittest.TestCase):
    """Unittest fix_cik."""

    def test_fix_cik_equal_str(self):
        """Test fix_cik to ensure proper size."""
        # Given
        cik = "0000001234"

        # When
        resp = util.fix_cik(cik)

        # Then
        self.assertTrue(len(resp) == 10)
        self.assertEqual(cik, resp)

    def test_fix_cik_smaller_str(self):
        """Test fix_cik to ensure proper size."""
        # Given
        cik = "1234"

        # When
        resp = util.fix_cik(cik)

        # Then
        self.assertTrue(len(resp) == 10)
        self.assertEqual(resp, "0000001234")

    def test_fix_cik_larger_str(self):
        """Test fix_cik to ensure proper size."""
        # Given
        cik = "00000001234"

        # When
        resp = util.fix_cik(cik)

        # Then
        self.assertEqual(resp, cik)


class CompanySizeTestCase(unittest.TestCase):
    """Unittest company_size classification boundaries."""

    def test_micro(self):
        self.assertEqual(util.company_size(50_000_000), "micro")

    def test_small(self):
        self.assertEqual(util.company_size(250_000_000), "small")

    def test_mid(self):
        self.assertEqual(util.company_size(1_000_000_000), "mid")

    def test_large(self):
        self.assertEqual(util.company_size(10_000_000_000), "large")

    def test_mega(self):
        self.assertEqual(util.company_size(20_000_000_000), "mega")

    def test_boundary_100m_is_small(self):
        # exactly $100M is not < 100M, so classified up
        self.assertEqual(util.company_size(100_000_000), "small")


class SendMessageInChunksTestCase(unittest.TestCase):
    """Unittest send_message_in_chunks."""

    def test_single_string_split_into_chunks(self):
        # Given - content longer than one Discord message
        channel = mock.AsyncMock()
        content = "a" * (util.MAX_MESSAGE_LENGTH + 10)

        # When
        asyncio.run(util.send_message_in_chunks(channel, content))

        # Then - two chunks sent
        self.assertEqual(channel.send.await_count, 2)
        first_chunk = channel.send.await_args_list[0].args[0]
        self.assertEqual(len(first_chunk), util.MAX_MESSAGE_LENGTH)

    def test_list_of_messages_each_sent(self):
        # Given - a list of short messages
        channel = mock.AsyncMock()
        content = ["one", "two", "three"]

        # When
        asyncio.run(util.send_message_in_chunks(channel, content))

        # Then - one send per list item
        self.assertEqual(channel.send.await_count, 3)


class PrepPipelineTestCase(unittest.TestCase):
    """Unittest prep_pipeline CSV loading."""

    def test_reads_csv_with_date_index(self):
        # Given
        csv_reader = mock.MagicMock(return_value="dataframe-sentinel")

        # When
        with mock.patch("warren_bot.utilities.pd.read_csv", csv_reader):
            result = util.prep_pipeline("club_stocks.csv")

        # Then - delegates to pandas with the date column parsed/indexed
        self.assertEqual(result, "dataframe-sentinel")
        _, kwargs = csv_reader.call_args
        self.assertEqual(kwargs["parse_dates"], ["date"])
        self.assertEqual(kwargs["index_col"], "date")


class SecApiTestCase(unittest.TestCase):
    """Unittest the async SEC EDGAR helpers with mocked requests."""

    def test_get_company_industry_returns_sic_description(self):
        # Given
        response = mock.MagicMock()
        response.status_code = "200"
        response.json.return_value = {"sicDescription": "Computer Services"}

        # When
        with mock.patch("warren_bot.utilities.requests.get", return_value=response) as get:
            result = asyncio.run(util.get_company_industry("1234"))

        # Then - CIK is zero-padded into the SEC URL and description returned
        self.assertEqual(result, "Computer Services")
        called_url = get.call_args.args[0]
        self.assertIn("CIK0000001234", called_url)

    def test_get_current_sec_10k_revenue_picks_latest_10k(self):
        # Given - two 10-K records; the later fiscal year wins
        response = mock.MagicMock()
        response.status_code = "200"
        response.json.return_value = {
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {"fy": 2020, "form": "10-K", "val": 100},
                                {"fy": 2022, "form": "10-K", "val": 300},
                                {"fy": 2023, "form": "10-Q", "val": 999},
                            ]
                        }
                    }
                }
            }
        }

        # When
        with mock.patch("warren_bot.utilities.requests.get", return_value=response):
            revenue = asyncio.run(util.get_current_sec_10k_revenue("1234"))

        # Then - latest 10-K value (fy 2022), ignoring the 10-Q
        self.assertEqual(revenue, 300)


class ConvertHtmlToPdfTestCase(unittest.TestCase):
    """Unittest convert_html_to_pdf delegates to pisa."""

    def test_writes_pdf_via_pisa(self):
        # Given
        create_pdf = mock.MagicMock()

        # When
        with mock.patch("warren_bot.utilities.pisa.CreatePDF", create_pdf), mock.patch(
            "warren_bot.utilities.open", mock.mock_open(), create=True
        ) as opened:
            util.convert_html_to_pdf("<html></html>", "out.pdf")

        # Then - opened the target file for binary write and rendered the html
        opened.assert_called_once_with("out.pdf", "w+b")
        self.assertEqual(create_pdf.call_args.args[0], "<html></html>")


class VerifyClubDataTestCase(unittest.TestCase):
    """Unittest verify_club_data with fully/partially populated club data."""

    @staticmethod
    def _club(industry, sector, size):
        return {
            "club": {
                "name": "Test Club",
                "valuation_dates": {"01/01/2024": {}},
                "club_stocks": {
                    "IBM": {
                        "cik": "51143",
                        "industry": industry,
                        "sector": sector,
                        "company_size": size,
                    }
                },
            }
        }

    def test_complete_data_reports_no_change(self):
        # Given - every field already populated
        data = self._club("Computers", "Tech", "mega")

        # When
        _, changed = asyncio.run(util.verify_club_data(data))

        # Then - nothing looked up, nothing changed
        self.assertFalse(changed)

    def test_missing_industry_and_size_are_filled(self):
        # Given - industry and company_size blank => remote lookups needed
        data = self._club("", "Tech", "")

        # When
        with mock.patch(
            "warren_bot.utilities.get_company_industry",
            new=mock.AsyncMock(return_value="Computer Services"),
        ), mock.patch(
            "warren_bot.utilities.get_current_sec_10k_revenue",
            new=mock.AsyncMock(return_value=50_000_000),
        ):
            result, changed = asyncio.run(util.verify_club_data(data))

        # Then - industry backfilled and change flagged
        self.assertTrue(changed)
        self.assertEqual(
            result["club"]["club_stocks"]["IBM"]["industry"], "Computer Services"
        )

    def test_missing_required_key_raises(self):
        # Given - no "club" key
        data = {}

        # Then
        with self.assertRaises(AssertionError):
            asyncio.run(util.verify_club_data(data))


class DataPathTestCase(unittest.TestCase):
    """Test the data_path writable-output-dir resolver."""

    def test_default_uses_cwd(self):
        """With WARREN_DATA_DIR unset, paths resolve under the current directory."""
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("WARREN_DATA_DIR", None)
            result = util.data_path("eps_fig.jpg")
        self.assertEqual(result, os.path.join(".", "eps_fig.jpg"))

    def test_uses_env_var(self):
        """WARREN_DATA_DIR relocates output under the configured directory."""
        tmp = tempfile.mkdtemp()
        try:
            with mock.patch.dict(os.environ, {"WARREN_DATA_DIR": tmp}):
                result = util.data_path("stocks.pkl")
            self.assertEqual(result, os.path.join(tmp, "stocks.pkl"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_creates_parent_directory_for_subpath(self):
        """A nested part (e.g. charts/) has its parent directory created."""
        tmp = tempfile.mkdtemp()
        try:
            with mock.patch.dict(os.environ, {"WARREN_DATA_DIR": tmp}):
                result = util.data_path("charts", "AAPL_chart.png")
            self.assertEqual(result, os.path.join(tmp, "charts", "AAPL_chart.png"))
            self.assertTrue(os.path.isdir(os.path.join(tmp, "charts")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class LoadDiscordTokenTestCase(unittest.TestCase):
    """Test the Discord token resolver."""

    def test_from_env_var(self):
        """DISCORD_TOKEN environment variable takes precedence."""
        with mock.patch.dict(os.environ, {"DISCORD_TOKEN": "env-token"}, clear=False):
            self.assertEqual(util.load_discord_token(), "env-token")

    def test_from_token_file(self):
        """DISCORD_TOKEN_FILE (Docker secret) is read and stripped when no env var is set."""
        tmp = tempfile.mkdtemp()
        try:
            token_path = os.path.join(tmp, "discord_token")
            with open(token_path, "w", encoding="utf-8") as f:
                f.write("file-token\n")
            with mock.patch.dict(os.environ, {"DISCORD_TOKEN_FILE": token_path}, clear=False):
                os.environ.pop("DISCORD_TOKEN", None)
                self.assertEqual(util.load_discord_token(), "file-token")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_from_ini_fallback(self):
        """The legacy bot_config.ini in the working dir is used when no env config exists."""
        tmp = tempfile.mkdtemp()
        cwd = os.getcwd()
        try:
            with open(os.path.join(tmp, "bot_config.ini"), "w", encoding="utf-8") as f:
                f.write("[discord]\ntoken = ini-token\n")
            os.chdir(tmp)
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("DISCORD_TOKEN", None)
                os.environ.pop("DISCORD_TOKEN_FILE", None)
                self.assertEqual(util.load_discord_token(), "ini-token")
        finally:
            os.chdir(cwd)
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
