"""
Tests for LLM Caching with TTL
"""

import pytest
from unittest.mock import MagicMock, patch
from app.services.llm_factory import get_model, invalidate_model_cache, _model_cache, _cache_lock
from app.models.settings import LLMProfile, ProviderType

@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before and after each test."""
    invalidate_model_cache()
    yield
    invalidate_model_cache()

def test_get_model_caches_result():
    """Test that get_model caches the LLM instance."""
    mock_profile = LLMProfile(id=1, name="test", provider=ProviderType.OPENAI, model_id="gpt-4", temperature=0.7)
    
    with patch("app.services.llm_factory.get_llm_profile") as mock_get_profile, \
         patch("app.services.llm_factory.create_llm_instance") as mock_create:
        
        mock_get_profile.return_value = mock_profile
        mock_llm = MagicMock()
        mock_create.return_value = mock_llm
        
        # First call - should hit DB and create instance
        result1 = get_model(1)
        assert result1 == mock_llm
        assert mock_get_profile.call_count == 1
        assert mock_create.call_count == 1
        
        # Second call - should use cache
        result2 = get_model(1)
        assert result2 == mock_llm
        assert mock_get_profile.call_count == 1  # Still 1, not called again
        assert mock_create.call_count == 1  # Still 1, not called again

def test_invalidate_model_cache_clears_all():
    """Test that invalidate_model_cache() clears entire cache."""
    with patch("app.services.llm_factory.get_llm_profile") as mock_get_profile, \
         patch("app.services.llm_factory.create_llm_instance") as mock_create:
        
        mock_profile = LLMProfile(id=1, name="test", provider=ProviderType.OPENAI, model_id="gpt-4", temperature=0.7)
        mock_get_profile.return_value = mock_profile
        mock_create.return_value = MagicMock()
        
        # Populate cache
        get_model(1)
        assert 1 in _model_cache
        
        # Clear cache
        invalidate_model_cache()
        
        # Verify cache is empty
        with _cache_lock:
            assert len(_model_cache) == 0

def test_invalidate_model_cache_selective():
    """Test that invalidate_model_cache(profile_id) only clears specific entry."""
    with patch("app.services.llm_factory.get_llm_profile") as mock_get_profile, \
         patch("app.services.llm_factory.create_llm_instance") as mock_create:
        
        mock_profile_1 = LLMProfile(id=1, name="test1", provider=ProviderType.OPENAI, model_id="gpt-4", temperature=0.7)
        mock_profile_2 = LLMProfile(id=2, name="test2", provider=ProviderType.OPENAI, model_id="gpt-3.5-turbo", temperature=0.7)
        
        def get_profile_side_effect(profile_id, session=None):
            return mock_profile_1 if profile_id == 1 else mock_profile_2
        
        mock_get_profile.side_effect = get_profile_side_effect
        mock_create.return_value = MagicMock()
        
        # Populate cache with two models
        get_model(1)
        get_model(2)
        
        with _cache_lock:
            assert 1 in _model_cache
            assert 2 in _model_cache
        
        # Selectively invalidate model 1
        invalidate_model_cache(1)
        
        # Verify only model 1 is removed
        with _cache_lock:
            assert 1 not in _model_cache
            assert 2 in _model_cache

def test_different_profiles_cached_separately():
    """Test that different profile IDs are cached separately."""
    with patch("app.services.llm_factory.get_llm_profile") as mock_get_profile, \
         patch("app.services.llm_factory.create_llm_instance") as mock_create:
        
        def get_profile_side_effect(profile_id, session=None):
            return LLMProfile(id=profile_id, name=f"test{profile_id}", provider=ProviderType.OPENAI, model_id="gpt-4", temperature=0.7)
        
        mock_get_profile.side_effect = get_profile_side_effect
        mock_create.return_value = MagicMock()
        
        # Get two different models
        get_model(1)
        get_model(2)
        
        # Should have called get_llm_profile twice (once for each)
        assert mock_get_profile.call_count == 2
        assert mock_get_profile.call_args_list[0][0][0] == 1
        assert mock_get_profile.call_args_list[1][0][0] == 2
