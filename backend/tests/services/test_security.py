
import pytest
from unittest.mock import patch
from app.services.security import save_api_key, get_api_key, delete_api_key

def test_save_and_retrieve_key():
    """Verify flow of saving and retrieving key using mocked keyring."""
    
    mock_key = "sk-12345"
    
    with patch("keyring.set_password") as mock_set, \
         patch("keyring.get_password") as mock_get:
         
        # Test Save
        ref_id = save_api_key(mock_key)
        assert len(ref_id) > 0
        mock_set.assert_called_once()
        
        # Test Retrieve
        mock_get.return_value = mock_key
        retrieved = get_api_key(ref_id)
        assert retrieved == mock_key

def test_delete_key():
    with patch("keyring.delete_password") as mock_del:
        delete_api_key("some-ref")
        mock_del.assert_called_once()
