"""
Failure Classification, Bounded Retries, and Graceful Degradation Subsystem.

CAPABL Track 6 Requirement:
- Classify failures into Retryable (transient network, provider timeout, CUDA glitch)
  and Non-Retryable (validation error, unconfirmed booking, missing config, policy violation).
- Bounded retries with exponential backoff (no infinite loops).
- Clear error states preserving human-readable explanations.
- Never silently fall back between LLM providers.
- Maintain M7 transient GPU/CUDA recovery while rejecting unauthorized state mutations immediately.
"""

import time
import logging
from typing import Callable, TypeVar, Any, Optional

logger = logging.getLogger(__name__)

T = TypeVar("T")

RETRYABLE_KEYWORDS = {
    "cuda",
    "connection",
    "connection refused",
    "connection reset",
    "timeout",
    "timed out",
    "readtimeout",
    "ratelimit",
    "rate limit",
    "429",
    "503",
    "temporarily unavailable",
    "service unavailable",
    "server error",
}

NON_RETRYABLE_EXCEPTIONS = (
    ValueError,
    FileNotFoundError,
    KeyError,
    AssertionError,
    PermissionError,
)

NON_RETRYABLE_KEYWORDS = {
    "confirmation_required",
    "confirmation required",
    "unauthorized",
    "invalid_slot",
    "already_booked",
    "candidate_mismatch",
    "job_mismatch",
    "invalid pdf",
    "exceeds page limit",
    "exceeds maximum allowed",
    "missing required",
    "invalid document_type",
    "policy violation",
}


def is_retryable_error(exc: Exception) -> bool:
    """
    Evaluates whether an exception represents a transient, recoverable failure.
    Returns False immediately for domain violations and deterministic errors.
    """
    if isinstance(exc, NON_RETRYABLE_EXCEPTIONS):
        return False

    err_str = str(exc).lower()

    # Explicit non-retryable keywords take precedence
    for kw in NON_RETRYABLE_KEYWORDS:
        if kw in err_str:
            return False

    # Check for transient retryable conditions
    for kw in RETRYABLE_KEYWORDS:
        if kw in err_str:
            return True

    return False


def execute_with_retry(
    fn: Callable[[], T],
    max_retries: int = 2,
    initial_delay: float = 1.5,
    backoff_factor: float = 2.0,
    operation_name: str = "operation",
) -> T:
    """
    Executes a callable with bounded retries and exponential backoff for transient failures.
    Fails fast for non-retryable errors.
    
    Args:
        fn: Zero-argument callable to execute.
        max_retries: Maximum number of retry attempts after initial failure.
        initial_delay: Initial sleep duration in seconds.
        backoff_factor: Multiplier applied to delay after each retry.
        operation_name: Descriptive name for logging.
        
    Returns:
        T: The result of fn().
        
    Raises:
        Exception: The underlying exception if non-retryable or if retries are exhausted.
    """
    attempt = 0
    current_delay = initial_delay

    while True:
        try:
            return fn()
        except Exception as exc:
            if not is_retryable_error(exc):
                logger.debug(f"{operation_name}: Non-retryable error encountered: {exc}")
                raise exc

            attempt += 1
            if attempt > max_retries:
                logger.error(
                    f"{operation_name}: Exhausted all {max_retries} retries. Final error: {exc}"
                )
                raise exc

            logger.warning(
                f"{operation_name}: Transient error (attempt {attempt}/{max_retries}): {exc}. "
                f"Retrying in {current_delay:.1f}s..."
            )
            time.sleep(current_delay)
            current_delay *= backoff_factor
