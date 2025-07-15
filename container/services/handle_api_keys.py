from datetime import datetime, UTC
from typing import Optional, Dict, Any, List
import secrets
import hashlib
import hmac
import json
from werkzeug.security import generate_password_hash
from data_classes.common_classes import ApiKey, CreateApiKeyRequest, UpdateApiKeyRequest, ApiKeyStatus
from libs.weaviate_lib import search_non_vector_collection, insert_to_collection, update_collection_object, delete_collection_object, COLLECTION_API_KEYS
from weaviate.collections.classes.filters import Filter
import logging

logger = logging.getLogger(__name__)

class ApiKeyError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"pk_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Verify an API key against its stored hash"""
    return hmac.compare_digest(hash_api_key(api_key), stored_hash)

def create_api_key(user_id: str, request: CreateApiKeyRequest) -> Dict[str, Any]:
    """Create a new API key for a user"""
    try:
        # Generate the API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        
        # Prepare API key data
        api_key_data = {
            "name": request.name,
            "description": request.description or "",
            "key_hash": key_hash,
            "user_id": user_id,
            "status": ApiKeyStatus.ACTIVE.value,
            "permissions": json.dumps(request.permissions or []),
            "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "expires_at": request.expires_at.strftime("%Y-%m-%dT%H:%M:%SZ") if request.expires_at else None,
            "last_used_at": None
        }
        
        # Insert into database
        api_key_id = insert_to_collection(
            collection_name=COLLECTION_API_KEYS,
            properties=api_key_data
        )
        
        if not api_key_id:
            raise ApiKeyError("Failed to create API key", 500)
        
        return {
            "id": str(api_key_id),
            "name": request.name,
            "api_key": api_key,  # Only returned once
            "description": request.description,
            "permissions": request.permissions or [],
            "status": ApiKeyStatus.ACTIVE.value,
            "created_at": api_key_data["created_at"],
            "expires_at": api_key_data["expires_at"]
        }
        
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        raise ApiKeyError(f"Failed to create API key: {str(e)}", 500)

def get_api_keys_by_user(user_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Get all API keys for a user"""
    try:
        filters = Filter.by_property("user_id").equal(user_id)
        api_keys = search_non_vector_collection(
            collection_name=COLLECTION_API_KEYS,
            filters=filters,
            limit=limit,
            offset=offset,
            properties=["name", "description", "status", "permissions", "created_at", "updated_at", "expires_at", "last_used_at"]
        )
        
        return api_keys
        
    except Exception as e:
        logger.error(f"Error getting API keys: {str(e)}")
        raise ApiKeyError(f"Failed to get API keys: {str(e)}", 500)

def get_api_key_by_id(api_key_id: str) -> Optional[Dict[str, Any]]:
    """Get an API key by ID"""
    try:
        from libs.weaviate_lib import get_object_by_id
        api_key = get_object_by_id(COLLECTION_API_KEYS, api_key_id)
        return api_key
    except Exception as e:
        logger.error(f"Error getting API key by ID: {str(e)}")
        return None

def update_api_key(api_key_id: str, user_id: str, request: UpdateApiKeyRequest) -> Dict[str, Any]:
    """Update an API key"""
    try:
        # Get the existing API key
        existing_key = get_api_key_by_id(api_key_id)
        if not existing_key:
            raise ApiKeyError("API key not found", 404)
        
        # Check if user owns this API key
        if existing_key.get("user_id") != user_id:
            raise ApiKeyError("Unauthorized", 403)
        
        # Prepare update data
        update_data = {
            "updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.permissions is not None:
            update_data["permissions"] = json.dumps(request.permissions)
        if request.status is not None:
            if type(request.status) == ApiKeyStatus:
                update_data["status"] = request.status.value
            elif type(request.status) == str:
                update_data["status"] = request.status
        if request.expires_at is not None:
            update_data["expires_at"] = request.expires_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Update in database
        success = update_collection_object(
            collection_name=COLLECTION_API_KEYS,
            uuid=api_key_id,
            properties=update_data
        )
        
        if not success:
            raise ApiKeyError("Failed to update API key", 500)
        
        # Return updated API key (without the actual key)
        updated_key = get_api_key_by_id(api_key_id)
        if not updated_key:
            raise ApiKeyError("Failed to retrieve updated API key", 500)
        return updated_key
        
    except ApiKeyError:
        raise
    except Exception as e:
        logger.error(f"Error updating API key: {str(e)}")
        raise ApiKeyError(f"Failed to update API key: {str(e)}", 500)

def delete_api_key(api_key_id: str, user_id: str) -> bool:
    """Delete an API key"""
    try:
        # Get the existing API key
        existing_key = get_api_key_by_id(api_key_id)
        if not existing_key:
            raise ApiKeyError("API key not found", 404)
        
        # Check if user owns this API key
        if existing_key.get("user_id") != user_id:
            raise ApiKeyError("Unauthorized", 403)
        
        # Delete from database
        success = delete_collection_object(COLLECTION_API_KEYS, api_key_id)
        
        if not success:
            raise ApiKeyError("Failed to delete API key", 500)
        
        return True
        
    except ApiKeyError:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {str(e)}")
        raise ApiKeyError(f"Failed to delete API key: {str(e)}", 500)

def revoke_api_key(api_key_id: str, user_id: str) -> Dict[str, Any]:
    """Revoke an API key (mark as revoked)"""
    try:
        update_request = UpdateApiKeyRequest(status=ApiKeyStatus.REVOKED)
        return update_api_key(api_key_id, user_id, update_request)
    except Exception as e:
        logger.error(f"Error revoking API key: {str(e)}")
        raise ApiKeyError(f"Failed to revoke API key: {str(e)}", 500)

def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """Validate an API key and return user info if valid"""
    try:
        key_hash = hash_api_key(api_key)
        
        # Search for the API key
        filters = Filter.by_property("key_hash").equal(key_hash)
        api_keys = search_non_vector_collection(
            collection_name=COLLECTION_API_KEYS,
            filters=filters,
            limit=1,
            properties=["user_id", "status", "permissions", "expires_at", "last_used_at"]
        )
        
        if not api_keys:
            return None
        
        api_key_data = api_keys[0]
        
        # Check if key is active
        if api_key_data.get("status") != ApiKeyStatus.ACTIVE.value:
            return None
        
        # Check if key is expired
        expires_at = api_key_data.get("expires_at")
        if expires_at:
            expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if datetime.now(UTC) > expires_datetime:
                # Mark as expired
                api_key_uuid = api_key_data.get("uuid")
                if api_key_uuid:
                    update_collection_object(
                        collection_name=COLLECTION_API_KEYS,
                        uuid=api_key_uuid,
                        properties={"status": ApiKeyStatus.EXPIRED.value}
                    )
                return None
        
        # Update last used timestamp
        api_key_uuid = api_key_data.get("uuid")
        if api_key_uuid:
            update_collection_object(
                collection_name=COLLECTION_API_KEYS,
                uuid=api_key_uuid,
                properties={"last_used_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
            )
        
        return {
            "user_id": api_key_data.get("user_id"),
            "permissions": api_key_data.get("permissions", []),
            "api_key_id": api_key_data.get("uuid")
        }
        
    except Exception as e:
        logger.error(f"Error validating API key: {str(e)}")
        return None

def get_user_by_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """Get user information by API key"""
    try:
        from services.handle_user import get_user_by_id
        
        validation_result = validate_api_key(api_key)
        if not validation_result:
            return None
        
        user_id = validation_result.get("user_id")
        if not user_id:
            return None
        
        # Get user details
        user = get_user_by_id(user_id)
        if not user:
            return None
        
        return {
            "user": user,
            "permissions": validation_result.get("permissions", []),
            "api_key_id": validation_result.get("api_key_id")
        }
        
    except Exception as e:
        logger.error(f"Error getting user by API key: {str(e)}")
        return None 