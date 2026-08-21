"""
Tests for error handling utilities.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.error_handling import (
    get_user_error,
    format_error_for_ui,
    UserError,
    ERROR_MESSAGES
)
from llm import (
    LLMError,
    RateLimitError,
    AuthenticationError,
    ProviderError,
    TimeoutError,
    NetworkError,
    map_llm_error
)


class TestErrorMapping:
    """Tests for LLM error mapping."""

    def test_rate_limit_error(self):
        original = Exception("429 Rate limit exceeded")
        mapped = map_llm_error(original)
        assert isinstance(mapped, RateLimitError)
        assert mapped.retryable is True

    def test_rate_limit_variations(self):
        for msg in ["rate limit", "RATE_LIMIT", "quota exceeded", "too many requests"]:
            original = Exception(msg)
            mapped = map_llm_error(original)
            assert isinstance(mapped, RateLimitError), f"Failed for: {msg}"

    def test_authentication_error(self):
        for msg in ["401 unauthorized", "403 forbidden", "invalid api key", "API key invalid"]:
            original = Exception(msg)
            mapped = map_llm_error(original)
            assert isinstance(mapped, AuthenticationError), f"Failed for: {msg}"

    def test_provider_error(self):
        for msg in ["500 internal server error", "502 bad gateway", "503 service unavailable", "504 gateway timeout"]:
            original = Exception(msg)
            mapped = map_llm_error(original)
            assert isinstance(mapped, ProviderError), f"Failed for: {msg}"

    def test_timeout_error(self):
        for msg in ["timeout", "timed out", "deadline exceeded"]:
            original = Exception(msg)
            mapped = map_llm_error(original)
            assert isinstance(mapped, TimeoutError), f"Failed for: {msg}"

    def test_network_error(self):
        for msg in ["connection error", "network unreachable", "dns resolution failed"]:
            original = Exception(msg)
            mapped = map_llm_error(original)
            assert isinstance(mapped, NetworkError), f"Failed for: {msg}"


class TestUserErrorFormatting:
    """Tests for user-friendly error formatting."""

    def test_rate_limit_user_error(self):
        error = RateLimitError()
        user_error = get_user_error(error)
        assert user_error.title == "Service Busy"
        assert "busy" in user_error.message.lower()
        assert user_error.recoverable is True

    def test_auth_error_user_error(self):
        error = AuthenticationError()
        user_error = get_user_error(error)
        assert user_error.title == "Configuration Error"
        assert user_error.recoverable is False

    def test_provider_error_user_error(self):
        error = ProviderError()
        user_error = get_user_error(error)
        assert user_error.title == "Service Unavailable"
        assert user_error.recoverable is True

    def test_timeout_user_error(self):
        error = TimeoutError()
        user_error = get_user_error(error)
        assert user_error.title == "Request Timeout"
        assert user_error.recoverable is True

    def test_network_user_error(self):
        error = NetworkError()
        user_error = get_user_error(error)
        assert user_error.title == "Connection Error"
        assert user_error.recoverable is True

    def test_generic_error_fallback(self):
        error = Exception("Some unknown error")
        user_error = get_user_error(error)
        assert user_error.title == "Generation Failed"
        assert user_error.recoverable is True

    def test_format_for_ui(self):
        error = RateLimitError()
        formatted = format_error_for_ui(error)
        assert "**Service Busy**" in formatted
        assert "busy" in formatted.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])