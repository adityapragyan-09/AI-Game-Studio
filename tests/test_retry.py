"""
Tests for retry utilities.
"""

import pytest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.retry import (
    RetryConfig,
    calculate_delay,
    retry_with_backoff,
    CircuitBreaker,
    CircuitBreakerOpenError
)


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_config(self):
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0
        assert config.jitter is True


class TestCalculateDelay:
    """Tests for delay calculation."""

    def test_exponential_backoff(self):
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        assert calculate_delay(0, config) == 1.0
        assert calculate_delay(1, config) == 2.0
        assert calculate_delay(2, config) == 4.0
        assert calculate_delay(3, config) == 8.0

    def test_max_delay_cap(self):
        config = RetryConfig(base_delay=10.0, exponential_base=2.0, max_delay=15.0, jitter=False)
        assert calculate_delay(0, config) == 10.0
        assert calculate_delay(1, config) == 15.0  # Capped
        assert calculate_delay(2, config) == 15.0  # Capped

    def test_jitter_adds_variance(self):
        config = RetryConfig(base_delay=10.0, jitter=True)
        delays = [calculate_delay(0, config) for _ in range(100)]
        # With jitter, delays should be between 5 and 15 (50-150%)
        assert all(5 <= d <= 15 for d in delays)
        # Should have some variance
        assert len(set(round(d, 1) for d in delays)) > 1


class TestRetryDecorator:
    """Tests for retry_with_backoff decorator."""

    def test_success_on_first_attempt(self):
        call_count = 0

        @retry_with_backoff(RetryConfig(max_attempts=3, base_delay=0.01, jitter=False))
        def succeed():
            nonlocal call_count
            call_count += 1
            return "success"

        result = succeed()
        assert result == "success"
        assert call_count == 1

    def test_retry_then_succeed(self):
        call_count = 0

        @retry_with_backoff(RetryConfig(max_attempts=3, base_delay=0.01, jitter=False))
        def succeed_on_third():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("fail")
            return "success"

        result = succeed_on_third()
        assert result == "success"
        assert call_count == 3

    def test_all_attempts_fail(self):
        call_count = 0

        @retry_with_backoff(RetryConfig(max_attempts=3, base_delay=0.01, jitter=False))
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("fail")

        with pytest.raises(ConnectionError):
            always_fail()
        assert call_count == 3

    def test_non_retryable_exception_not_retried(self):
        call_count = 0

        @retry_with_backoff(RetryConfig(max_attempts=3, base_delay=0.01, jitter=False,
                                        retryable_exceptions=(ConnectionError,)))
        def fail_with_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            fail_with_value_error()
        assert call_count == 1  # Should not retry


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_closed_by_default(self):
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == "CLOSED"

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        def fail():
            raise ConnectionError("fail")

        for _ in range(3):
            try:
                cb.call(fail)
            except ConnectionError:
                pass

        assert cb.state == "OPEN"

    def test_open_rejects_calls(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

        def fail():
            raise ConnectionError("fail")

        for _ in range(2):
            try:
                cb.call(fail)
            except ConnectionError:
                pass

        assert cb.state == "OPEN"

        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "success")

    def test_success_resets_failures(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        def fail():
            raise ConnectionError("fail")

        def succeed():
            return "ok"

        # Two failures
        for _ in range(2):
            try:
                cb.call(fail)
            except ConnectionError:
                pass

        assert cb._failure_count == 2

        # Success resets
        result = cb.call(succeed)
        assert result == "ok"
        assert cb._failure_count == 0
        assert cb.state == "CLOSED"

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        def fail():
            raise ConnectionError("fail")

        for _ in range(2):
            try:
                cb.call(fail)
            except ConnectionError:
                pass

        assert cb.state == "OPEN"

        # Wait for recovery timeout
        time.sleep(0.2)

        # Should be half-open now
        assert cb.state == "HALF_OPEN"

        # Successful call in half-open should close
        result = cb.call(lambda: "ok")
        assert result == "ok"
        assert cb.state == "CLOSED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])