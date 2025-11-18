# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import unittest
from unittest.mock import MagicMock, patch

from lisa.util import LisaException, get_public_ip


class GetPublicIpTestCase(unittest.TestCase):
    @patch("lisa.util.requests.get")
    def test_get_public_ip_primary_success(self, mock_get: MagicMock) -> None:
        """Test that get_public_ip returns IP from primary service when available."""
        # Mock successful response from api.ipify.org
        mock_response = MagicMock()
        mock_response.text = "203.0.113.1"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_public_ip()
        
        self.assertEqual(result, "203.0.113.1")
        mock_get.assert_called_once_with("https://api.ipify.org/", timeout=5)

    @patch("lisa.util.requests.get")
    def test_get_public_ip_fallback_success(self, mock_get: MagicMock) -> None:
        """Test that get_public_ip falls back to ipinfo.io when primary fails."""
        # Mock failed response from api.ipify.org and successful from ipinfo.io
        def mock_get_side_effect(url: str, timeout: int) -> MagicMock:
            mock_response = MagicMock()
            if "api.ipify.org" in url:
                # Simulate failure for primary service
                raise Exception("Connection error")
            elif "ipinfo.io" in url:
                # Simulate success for fallback service
                mock_response.text = "198.51.100.1"
                mock_response.raise_for_status = MagicMock()
                return mock_response
            return mock_response

        mock_get.side_effect = mock_get_side_effect

        result = get_public_ip()
        
        self.assertEqual(result, "198.51.100.1")
        # Should have called both services
        self.assertEqual(mock_get.call_count, 2)

    @patch("lisa.util.requests.get")
    def test_get_public_ip_both_fail(self, mock_get: MagicMock) -> None:
        """Test that get_public_ip raises exception when both services fail."""
        # Mock failed responses from both services
        mock_get.side_effect = Exception("Network error")

        with self.assertRaises(LisaException) as context:
            get_public_ip()
        
        self.assertIn("Failed to get public IP", str(context.exception))
        # With retry decorator set to 10 tries, it should make multiple attempts
        # The last attempt will try the fallback
        self.assertGreater(mock_get.call_count, 1)

    @patch("lisa.util.requests.get")
    def test_get_public_ip_invalid_ip_fallback(self, mock_get: MagicMock) -> None:
        """Test that get_public_ip falls back when primary returns invalid IP."""
        # Mock primary service returning invalid IP, fallback returning valid IP
        def mock_get_side_effect(url: str, timeout: int) -> MagicMock:
            mock_response = MagicMock()
            if "api.ipify.org" in url:
                # Return invalid IP
                mock_response.text = "invalid-ip"
                mock_response.raise_for_status = MagicMock()
                return mock_response
            elif "ipinfo.io" in url:
                # Return valid IP
                mock_response.text = "192.0.2.1  "  # with whitespace to test strip()
                mock_response.raise_for_status = MagicMock()
                return mock_response
            return mock_response

        mock_get.side_effect = mock_get_side_effect

        result = get_public_ip()
        
        # Should successfully get IP from fallback and strip whitespace
        self.assertEqual(result, "192.0.2.1")
        self.assertEqual(mock_get.call_count, 2)

    @patch("lisa.util.requests.get")
    def test_get_public_ip_ipv6(self, mock_get: MagicMock) -> None:
        """Test that get_public_ip works with IPv6 addresses."""
        # Mock successful response with IPv6 address
        mock_response = MagicMock()
        mock_response.text = "2001:db8::1"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_public_ip()
        
        self.assertEqual(result, "2001:db8::1")
        mock_get.assert_called_once_with("https://api.ipify.org/", timeout=5)


if __name__ == "__main__":
    unittest.main()
