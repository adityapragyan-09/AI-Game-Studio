"""
Centralized LLM Configuration for AI Game Studio.

Provides resilient Gemini API integration with:
- Configurable timeouts
- Exponential backoff retries
- Rate-limit handling
- Structured error mapping
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    model: str = "gemini/gemini-3.5-flash"
    api_key: Optional[str] = None
    timeout: int = 120  # seconds
    max_retries: int = 3
    temperature: float = 0.3
    top_p: float = 0.95
    top_k: int = 40

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API configuration is missing. "
                "Please configure GEMINI_API_KEY in your environment."
            )


class LLMError(Exception):
    """Base exception for LLM errors."""
    def __init__(self, message: str, original_error: Optional[Exception] = None, retryable: bool = False):
        super().__init__(message)
        self.original_error = original_error
        self.retryable = retryable


class RateLimitError(LLMError):
    """Rate limit exceeded."""
    def __init__(self, message: str = "AI service is temporarily busy. Please wait a moment and try again.", original_error: Optional[Exception] = None):
        super().__init__(message, original_error, retryable=True)


class AuthenticationError(LLMError):
    """Invalid or missing API key."""
    def __init__(self, message: str = "Invalid API configuration. Please check your API key.", original_error: Optional[Exception] = None):
        super().__init__(message, original_error, retryable=False)


class ProviderError(LLMError):
    """Provider-side error (5xx)."""
    def __init__(self, message: str = "AI service is temporarily unavailable. Please try again later.", original_error: Optional[Exception] = None):
        super().__init__(message, original_error, retryable=True)


class TimeoutError(LLMError):
    """Request timeout."""
    def __init__(self, message: str = "Request timed out. Please try again.", original_error: Optional[Exception] = None):
        super().__init__(message, original_error, retryable=True)


class NetworkError(LLMError):
    """Network connectivity issue."""
    def __init__(self, message: str = "Network error. Please check your connection and try again.", original_error: Optional[Exception] = None):
        super().__init__(message, original_error, retryable=True)


def map_llm_error(error: Exception) -> LLMError:
    """Map provider exceptions to user-friendly errors."""
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()

    # Rate limiting
    if any(x in error_str for x in ["429", "rate limit", "rate_limit", "quota", "too many requests"]):
        return RateLimitError(original_error=error)

    # Authentication
    if any(x in error_str for x in ["401", "403", "unauthorized", "forbidden", "invalid api key", "api key"]):
        return AuthenticationError(original_error=error)

    # Provider errors (5xx)
    if any(x in error_str for x in ["500", "502", "503", "504", "internal server error", "bad gateway", "service unavailable", "gateway timeout"]):
        return ProviderError(original_error=error)

    # Timeout
    if any(x in error_str for x in ["timeout", "timed out", "deadline exceeded"]):
        return TimeoutError(original_error=error)

    # Network
    if any(x in error_str for x in ["connection", "connect", "network", "dns", "resolve", "unreachable"]):
        return NetworkError(original_error=error)

    # Default: treat as potentially retryable provider error
    logger.warning(f"Unmapped LLM error: {error_type}: {error}")
    return ProviderError(original_error=error)


def create_llm(config: Optional[LLMConfig] = None):
    """
    Create a CrewAI LLM instance with resilient configuration.

    Args:
        config: Optional LLMConfig. If None, uses defaults from environment.

    Returns:
        Configured CrewAI LLM instance.

    Raises:
        ValueError: If API key is missing.
    """
    if config is None:
        config = LLMConfig()

    # Import here to avoid circular imports
    from crewai import LLM

    logger.info(f"Initializing LLM: model={config.model}, timeout={config.timeout}s, retries={config.max_retries}")

    return LLM(
        model=config.model,
        api_key=config.api_key,
        timeout=config.timeout,
        max_retries=config.max_retries,
        temperature=config.temperature,
        top_p=config.top_p,
        top_k=config.top_k,
    )


# Default configuration instance
_default_config: Optional[LLMConfig] = None


def get_llm_config() -> LLMConfig:
    """Get or create the default LLM configuration."""
    global _default_config
    if _default_config is None:
        _default_config = LLMConfig()
    return _default_config


def get_llm() -> "LLM":
    """Get the default LLM instance (lazy initialization)."""
    return create_llm(get_llm_config())


# Backward compatibility: expose llm instance
try:
    llm = get_llm()
except ValueError as e:
    # Allow import-time failure to be handled gracefully
    logger.warning(f"LLM initialization deferred: {e}")
    llm = None