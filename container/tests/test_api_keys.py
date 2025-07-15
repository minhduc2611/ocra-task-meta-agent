import pytest
from datetime import datetime, UTC, timedelta
from services.handle_api_keys import (
    generate_api_key, hash_api_key, verify_api_key, create_api_key,
    get_api_keys_by_user, validate_api_key, ApiKeyError
)
from data_classes.common_classes import CreateApiKeyRequest, ApiKeyStatus

class TestApiKeyGeneration:
    def test_generate_api_key(self):
        """Test API key generation"""
        key1 = generate_api_key()
        key2 = generate_api_key()
        
        # Keys should be different
        assert key1 != key2
        
        # Keys should start with 'pk_'
        assert key1.startswith('pk_')
        assert key2.startswith('pk_')
        
        # Keys should be reasonably long
        assert len(key1) > 40
        assert len(key2) > 40

    def test_hash_api_key(self):
        """Test API key hashing"""
        key = "pk_test_key_123"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        
        # Same key should produce same hash
        assert hash1 == hash2
        
        # Hash should be different from original key
        assert hash1 != key
        
        # Hash should be a hex string
        assert len(hash1) == 64  # SHA-256 hex length

    def test_verify_api_key(self):
        """Test API key verification"""
        key = "pk_test_key_123"
        stored_hash = hash_api_key(key)
        
        # Correct key should verify
        assert verify_api_key(key, stored_hash) is True
        
        # Wrong key should not verify
        assert verify_api_key("pk_wrong_key", stored_hash) is False
        
        # Empty key should not verify
        assert verify_api_key("", stored_hash) is False

class TestApiKeyCreation:
    def test_create_api_key_request(self):
        """Test CreateApiKeyRequest dataclass"""
        request = CreateApiKeyRequest(
            name="Test Key",
            description="Test description",
            permissions=["read", "write"],
            expires_at=datetime.now(UTC) + timedelta(days=30)
        )
        
        assert request.name == "Test Key"
        assert request.description == "Test description"
        assert request.permissions == ["read", "write"]
        assert request.expires_at is not None

    def test_create_api_key_minimal(self):
        """Test creating API key with minimal data"""
        request = CreateApiKeyRequest(name="Test Key")
        
        assert request.name == "Test Key"
        assert request.description is None
        assert request.permissions is None
        assert request.expires_at is None

class TestApiKeyStatus:
    def test_api_key_status_enum(self):
        """Test ApiKeyStatus enum values"""
        assert ApiKeyStatus.ACTIVE.value == "active"
        assert ApiKeyStatus.INACTIVE.value == "inactive"
        assert ApiKeyStatus.EXPIRED.value == "expired"
        assert ApiKeyStatus.REVOKED.value == "revoked"

# Note: The following tests would require a database connection
# and would be integration tests rather than unit tests

class TestApiKeyIntegration:
    @pytest.mark.skip(reason="Requires database connection")
    def test_create_api_key_integration(self):
        """Test creating an API key (integration test)"""
        # This would require a test database setup
        pass

    @pytest.mark.skip(reason="Requires database connection")
    def test_validate_api_key_integration(self):
        """Test API key validation (integration test)"""
        # This would require a test database setup
        pass

    @pytest.mark.skip(reason="Requires database connection")
    def test_api_key_expiration_integration(self):
        """Test API key expiration (integration test)"""
        # This would require a test database setup
        pass 