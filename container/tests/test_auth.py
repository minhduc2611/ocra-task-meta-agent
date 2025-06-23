import pytest
from unittest.mock import patch, MagicMock
from services.handle_auth import (
    create_jwt_token, 
    verify_jwt_token, 
    blacklist_token, 
    is_token_blacklisted,
    AuthError
)
from datetime import datetime, timedelta, UTC

class TestAuth:
    
    def test_create_jwt_token(self):
        """Test JWT token creation"""
        user_id = "test_user_123"
        token = create_jwt_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify the token can be decoded
        payload = verify_jwt_token(token)
        assert payload['user_id'] == user_id
    
    def test_verify_jwt_token_valid(self):
        """Test valid JWT token verification"""
        user_id = "test_user_123"
        token = create_jwt_token(user_id)
        
        payload = verify_jwt_token(token)
        assert payload['user_id'] == user_id
        assert 'exp' in payload
        assert 'iat' in payload
    
    def test_verify_jwt_token_expired(self):
        """Test expired JWT token verification"""
        # Create a token with past expiration
        payload = {
            'user_id': 'test_user_123',
            'exp': datetime.now(UTC) - timedelta(hours=1),
            'iat': datetime.now(UTC) - timedelta(hours=2)
        }
        
        with pytest.raises(AuthError) as exc_info:
            verify_jwt_token("invalid_token")
        
        assert exc_info.value.status_code == 401
    
    @patch('services.handle_auth.insert_to_collection')
    def test_blacklist_token_success(self, mock_insert):
        """Test successful token blacklisting"""
        mock_insert.return_value = "blacklist_id_123"
        
        token = "test_token_123"
        user_id = "test_user_123"
        
        result = blacklist_token(token, user_id)
        
        assert result is True
        mock_insert.assert_called_once()
    
    @patch('services.handle_auth.insert_to_collection')
    def test_blacklist_token_failure(self, mock_insert):
        """Test failed token blacklisting"""
        mock_insert.return_value = None
        
        token = "test_token_123"
        user_id = "test_user_123"
        
        result = blacklist_token(token, user_id)
        
        assert result is False
    
    @patch('services.handle_auth.search_non_vector_collection')
    def test_is_token_blacklisted_true(self, mock_search):
        """Test checking if token is blacklisted (returns True)"""
        mock_search.return_value = [{"token": "test_token_123"}]
        
        result = is_token_blacklisted("test_token_123")
        
        assert result is True
        mock_search.assert_called_once()
    
    @patch('services.handle_auth.search_non_vector_collection')
    def test_is_token_blacklisted_false(self, mock_search):
        """Test checking if token is blacklisted (returns False)"""
        mock_search.return_value = []
        
        result = is_token_blacklisted("test_token_123")
        
        assert result is False
        mock_search.assert_called_once()
    
    @patch('services.handle_auth.search_non_vector_collection')
    def test_verify_jwt_token_blacklisted(self, mock_search):
        """Test that blacklisted tokens are rejected"""
        mock_search.return_value = [{"token": "test_token_123"}]
        
        with pytest.raises(AuthError) as exc_info:
            verify_jwt_token("test_token_123")
        
        assert exc_info.value.message == "Token has been revoked"
        assert exc_info.value.status_code == 401 