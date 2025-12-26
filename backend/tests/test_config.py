"""
Tests for the config module.
"""

import pytest
import os
from unittest.mock import patch


def test_settings_default_values():
    """Test that default values are correctly set."""
    # Import fresh to get defaults
    from app.config import Settings
    
    settings = Settings()
    
    assert settings.database_url == "sqlite:///./database.db"
    assert settings.langgraph_recursion_limit == 50
    assert settings.max_subgraph_depth == 5
    assert settings.log_level == "INFO"
    assert settings.log_format == "json"
    assert settings.enable_json_api == False
    assert settings.api_prefix == "/api"


def test_settings_from_env():
    """Test that settings can be loaded from environment variables."""
    from app.config import Settings
    
    with patch.dict(os.environ, {
        "LOG_LEVEL": "DEBUG",
        "LANGGRAPH_RECURSION_LIMIT": "100",
        "ENABLE_JSON_API": "true"
    }):
        settings = Settings()
        
        assert settings.log_level == "DEBUG"
        assert settings.langgraph_recursion_limit == 100
        assert settings.enable_json_api == True


def test_settings_validation():
    """Test that invalid values raise validation errors."""
    from app.config import Settings
    from pydantic import ValidationError
    
    # Test invalid log level
    with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
        with pytest.raises(ValidationError):
            Settings()
    
    # Test invalid recursion limit (too high)
    with patch.dict(os.environ, {"LANGGRAPH_RECURSION_LIMIT": "1000"}):
        with pytest.raises(ValidationError):
            Settings()


def test_get_settings_caching():
    """Test that get_settings returns cached instance."""
    from app.config import get_settings
    
    # Clear cache first
    get_settings.cache_clear()
    
    settings1 = get_settings()
    settings2 = get_settings()
    
    assert settings1 is settings2
