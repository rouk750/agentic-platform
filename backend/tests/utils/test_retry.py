"""
Tests for Retry Utilities
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch

from app.utils.retry import (
    with_retry,
    with_async_retry,
    llm_retry,
    retry_with_fallback,
    async_retry_with_fallback,
)


class TestSyncRetry:
    """Test synchronous retry decorator."""
    
    def test_success_no_retry(self):
        """Function succeeds on first attempt."""
        call_count = 0
        
        @with_retry(max_attempts=3)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = succeed()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_then_success(self):
        """Function fails twice then succeeds."""
        call_count = 0
        
        @with_retry(max_attempts=3, min_wait=0.01, max_wait=0.1)
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Failed")
            return "success"
        
        result = fail_twice()
        assert result == "success"
        assert call_count == 3
    
    def test_exhausted_retries(self):
        """All retries exhausted raises exception."""
        @with_retry(max_attempts=2, min_wait=0.01, max_wait=0.1)
        def always_fail():
            raise ConnectionError("Always fails")
        
        with pytest.raises(ConnectionError):
            always_fail()
    
    def test_non_retryable_exception(self):
        """Non-retryable exceptions propagate immediately."""
        call_count = 0
        
        @with_retry(max_attempts=3)
        def raise_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")
        
        with pytest.raises(ValueError):
            raise_value_error()
        
        assert call_count == 1  # No retries


class TestAsyncRetry:
    """Test async retry decorator."""
    
    @pytest.mark.asyncio
    async def test_async_success(self):
        call_count = 0
        
        @with_async_retry(max_attempts=3)
        async def async_succeed():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await async_succeed()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_retry_then_success(self):
        call_count = 0
        
        @with_async_retry(max_attempts=3, min_wait=0.01, max_wait=0.1)
        async def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise asyncio.TimeoutError("Timeout")
            return "success"
        
        result = await fail_once()
        assert result == "success"
        assert call_count == 2


class TestRetryWithFallback:
    """Test fallback behavior."""
    
    def test_fallback_on_exhausted_retries(self):
        @retry_with_fallback(fallback_value=[])
        def always_fail():
            raise ConnectionError("Failed")
        
        result = always_fail()
        assert result == []
    
    def test_success_no_fallback(self):
        @retry_with_fallback(fallback_value="fallback")
        def succeed():
            return "success"
        
        result = succeed()
        assert result == "success"
