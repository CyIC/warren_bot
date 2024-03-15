# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0511
"""Unit testing module for the utilities module."""
import unittest
from warren_bot import utilities as util


class UtilitiesTestCase(unittest.TestCase):
    """Unittest utilities.py module."""

    def test_fix_cik_equal_str(self):
        """Test fix_cik to ensure proper size."""
        # Given
        cik = '0000001234'

        # When
        resp = util.fix_cik(cik)

        # Then
        self.assertTrue(len(resp) == 10)
        self.assertEqual(cik, resp)

    def test_fix_cik_smaller_str(self):
        """Test fix_cik to ensure proper size."""
        # Given
        cik = '1234'

        # When
        resp = util.fix_cik(cik)

        # Then
        self.assertTrue(len(resp) == 10)

    def test_fix_cik_larger_str(self):
        """Test fix_cik to ensure proper size."""
        # Given
        cik = '00000001234'

        # When
        resp = util.fix_cik(cik)

        # Then
        self.assertEqual(resp, cik)


if __name__ == '__main__':
    unittest.main()
