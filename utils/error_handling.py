"""
Error handling utilities for AI Game Studio.

Maps technical exceptions to user-friendly messages.
"""

import logging
from typing import Optional
from dataclasses import dataclass

from llm import LLMError, RateLimitError, AuthenticationError, ProviderError, TimeoutError, NetworkError, map_llm_error

logger = logging.getLogger(__name__)


@dataclass
class UserError:
    """User-friendly error information."""
    title: str
    message: str
    recoverable: bool = True
    technical_details: Optional[str] = None


# Mapping of error types to user-friendly messages
ERROR_MESSAGES = {
    RateLimitError: UserError(
        title="Service Busy",
        message="The AI service is temporarily busy. Please wait a moment and try again.",
        recoverable=True,
    ),
    AuthenticationError: UserError(
        title="Configuration Error",
        message="The AI service is not properly configured. Please contact the administrator.",
        recoverable=False,
    ),
    ProviderError: UserError(
        title="Service Unavailable",
        message="The AI service is temporarily unavailable. Please try again later.",
        recoverable=True,
    ),
    TimeoutError: UserError(
        title="Request Timeout",
        message="The request took too long. Please try again.",
        recoverable=True,
    ),
    NetworkError: UserError(
        title="Connection Error",
        message="Unable to connect to the AI service. Please check your internet connection.",
        recoverable=True,
    ),
}


def get_user_error(error: Exception) -> UserError:
    """Convert any exception to a user-friendly error."""
    # First, try to map LLM-specific errors
    if isinstance(error, LLMError):
        for error_type, user_error in ERROR_MESSAGES.items():
            if isinstance(error, error_type):
                return UserError(
                    title=user_error.title,
                    message=user_error.message,
                    recoverable=user_error.recoverable,
                    technical_details=str(error.original_error) if error.original_error else str(error),
                )

    # Generic error mapping
    error_str = str(error).lower()

    if any(x in error_str for x in ["429", "rate limit", "quota"]):
        return ERROR_MESSAGES[RateLimitError]

    if any(x in error_str for x in ["401", "403", "unauthorized", "forbidden", "api key"]):
        return ERROR_MESSAGES[AuthenticationError]

    if any(x in error_str for x in ["500", "502", "503", "504"]):
        return ERROR_MESSAGES[ProviderError]

    if "timeout" in error_str:
        return ERROR_MESSAGES[TimeoutError]

    if any(x in error_str for x in ["connection", "network", "dns"]):
        return ERROR_MESSAGES[NetworkError]

    # Default fallback
    logger.error(f"Unhandled error: {type(error).__name__}: {error}")
    return UserError(
        title="Generation Failed",
        message="An unexpected error occurred during game generation. Please try again.",
        recoverable=True,
        technical_details=str(error),
    )


def format_error_for_ui(error: Exception) -> str:
    """Format error for display in Streamlit UI."""
    user_error = get_user_error(error)
    return f"**{user_error.title}**: {user_error.message}"


def log_generation_error(stage: str, error: Exception, context: dict = None):
    """Log generation error with context."""
    context_str = f" | Context: {context}" if context else ""
    logger.error(f"Generation failed at stage '{stage}': {type(error).__name__}: {error}{context_str}")