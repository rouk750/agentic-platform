"""
Retry Utilities

Tenacity-based retry decorators for resilient operations.
"""

import asyncio
from typing import Callable, TypeVar, Any
from functools import wraps

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)

from app.logging import get_logger
from app.config import settings

logger = get_logger(__name__)

T = TypeVar("T")


# Exception types that warrant retry
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    asyncio.TimeoutError,
)


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exceptions: tuple = RETRYABLE_EXCEPTIONS,
):
    """
    Decorator for synchronous functions with exponential backoff retry.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        exceptions: Tuple of exception types to retry on
    
    Example:
        @with_retry(max_attempts=3)
        def fetch_data():
            ...
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, log_level=20),  # INFO
        reraise=True,
    )


def with_async_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exceptions: tuple = RETRYABLE_EXCEPTIONS,
):
    """
    Decorator for async functions with exponential backoff retry.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        exceptions: Tuple of exception types to retry on
    
    Example:
        @with_async_retry(max_attempts=3)
        async def fetch_data():
            ...
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, log_level=20),
        reraise=True,
    )


def llm_retry(max_attempts: int = 3):
    """
    Retry decorator specifically for LLM API calls.
    
    Uses random exponential backoff to avoid thundering herd
    when multiple requests fail simultaneously.
    
    Retries on:
    - Connection errors
    - Timeout errors
    - Rate limit errors (common with LLM APIs)
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_random_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type((
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        )),
        before_sleep=before_sleep_log(logger, log_level=30),  # WARNING
        reraise=True,
    )


def retry_with_fallback(fallback_value: Any, exceptions: tuple = RETRYABLE_EXCEPTIONS):
    """
    Retry decorator that returns a fallback value on exhausted retries.
    
    Args:
        fallback_value: Value to return if all retries fail
        exceptions: Exception types to catch for fallback
    
    Example:
        @retry_with_fallback(fallback_value=[])
        def get_items():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Apply retry decorator
        retried_func = retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=0.01, max=0.1),
            retry=retry_if_exception_type(exceptions),
            reraise=True,
        )(func)
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return retried_func(*args, **kwargs)
            except exceptions:
                logger.warning(
                    "retry_exhausted_using_fallback",
                    function=func.__name__,
                    fallback=str(fallback_value)
                )
                return fallback_value
        return wrapper
    return decorator


def async_retry_with_fallback(fallback_value: Any):
    """
    Async version of retry_with_fallback.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await with_async_retry()(func)(*args, **kwargs)
            except RetryError:
                logger.warning(
                    "retry_exhausted_using_fallback",
                    function=func.__name__,
                    fallback=str(fallback_value)
                )
                return fallback_value
        return wrapper
    return decorator
