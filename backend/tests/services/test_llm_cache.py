"""
Tests for LLM Caching
"""

import pytest
from unittest.mock import MagicMock, patch
from app.services.llm_factory import get_model, invalidate_model_cache
from app.models.settings import LLMProfile, ProviderType

# Mock LLMProviderFactory to avoid actual calls
@pytest.fixture
def mock_factory():
    with patch("app.services.llm_factory.LLMProviderFactory") as mock:
        mock.create.return_value = MagicMock(name="LangChainModel")
        yield mock

# Mock get_llm_profile to avoid DB hits
@pytest.fixture
def mock_get_profile():
    with patch("app.services.llm_factory.get_llm_profile") as mock:
        mock.return_value = LLMProfile(
            id=1,
            name="Test",
            provider=ProviderType.OPENAI,
            model_id="gpt-4",
            api_key_ref="ref"
        )
        yield mock

# Mock get_api_key
@pytest.fixture
def mock_get_key():
    with patch("app.services.llm_factory.get_api_key") as mock:
        mock.return_value = "sk-test"
        yield mock

def test_cache_hit(mock_factory, mock_get_profile, mock_get_key):
    """Test that repeated calls use the cache."""
    invalidate_model_cache()
    
    # First call
    model1 = get_model(1)
    
    # Second call
    model2 = get_model(1)
    
    # Should be the same object
    assert model1 is model2
    
    # DB fetch should be called only once
    assert mock_get_profile.call_count == 1
    
    # Factory create should be called only once
    assert mock_factory.create.call_count == 1

def test_cache_invalidation(mock_factory, mock_get_profile, mock_get_key):
    """Test that cache invalidation forces refresh."""
    invalidate_model_cache()
    
    # First call
    get_model(1)
    assert mock_get_profile.call_count == 1
    
    # Invalidate
    invalidate_model_cache()
    
    # Second call
    get_model(1)
    assert mock_get_profile.call_count == 2

def test_different_profiles(mock_factory, mock_get_profile, mock_get_key):
    """Test that different IDs are cached separately."""
    invalidate_model_cache()
    
    # Setup profile return to vary (though mock returns same obj for now, calls count)
    get_model(1)
    get_model(2)
    
    assert mock_get_profile.call_count == 2
    assert mock_get_profile.call_args_list[0][0][0] == 1
    assert mock_get_profile.call_args_list[1][0][0] == 2
