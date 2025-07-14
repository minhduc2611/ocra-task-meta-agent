from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from data_classes.common_classes import User, AuthRequest
from libs.weaviate_lib import search_non_vector_collection, insert_to_collection, COLLECTION_TOKEN_BLACKLIST
from weaviate.collections.classes.filters import Filter
import os
import uuid
from data_classes.common_classes import UserRole    

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')  # In production, use a secure secret
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = timedelta(days=1)  # Token expires in 1 day

class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def create_jwt_token(user_id: str) -> str:
    """Create a JWT token for a user"""
    print('user_id:')
    print(user_id)
    payload = {
        'user_id': user_id,
        'exp': datetime.now(UTC) + JWT_EXPIRATION,
        'iat': datetime.now(UTC)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify a JWT token and return the payload"""
    try:
        # First check if token is blacklisted
        if is_token_blacklisted(token):
            raise AuthError("Token has been revoked", 401)
            
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired", 401)
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token", 401)

def blacklist_token(token: str, user_id: str) -> bool:
    """Add a token to the blacklist"""
    try:
        # Decode token to get expiration time
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        exp_timestamp = payload.get('exp')
        
        # Convert timestamp to datetime
        exp_datetime = datetime.fromtimestamp(exp_timestamp, UTC)
        
        token_data = {
            "token": token,
            "user_id": user_id,
            "blacklisted_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "expires_at": exp_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        # Insert into blacklist collection
        blacklist_id = insert_to_collection(
            collection_name=COLLECTION_TOKEN_BLACKLIST,
            properties=token_data
        )
        
        return blacklist_id is not None
    except Exception as e:
        print(f"Error blacklisting token: {str(e)}")
        return False

def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted"""
    try:
        filters = Filter.by_property("token").equal(token)
        blacklisted_tokens = search_non_vector_collection(
            collection_name=COLLECTION_TOKEN_BLACKLIST,
            filters=filters,
            limit=1,
            properties=["token", "blacklisted_at", "expires_at"]
        )
        
        return len(blacklisted_tokens) > 0
    except Exception as e:
        print(f"Error checking token blacklist: {str(e)}")
        return False

def cleanup_expired_blacklisted_tokens():
    """Clean up expired tokens from blacklist"""
    try:
        # This would require a more sophisticated cleanup mechanism
        # For now, we'll rely on the token expiration check in verify_jwt_token
        pass
    except Exception as e:
        print(f"Error cleaning up expired tokens: {str(e)}")

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a user by email"""
    filters = Filter.by_property("email").equal(email)
    users = search_non_vector_collection(
        collection_name="Users",
        filters=filters,
        limit=1,
        properties=["email", "password", "name", "role", "created_at", "updated_at"]
    )

    if users:
        user = users[0]
        return user
    return None

def sign_up(auth_request: AuthRequest) -> Dict[str, Any]:
    """Register a new user"""
    # Check if user already exists
    existing_user = get_user_by_email(auth_request.email)
    if existing_user:
        raise AuthError("Email already registered", 400)

    # Create new user
    user = User(
        email=auth_request.email,
        password=generate_password_hash(auth_request.password),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        name=auth_request.name,
        role=auth_request.role if auth_request.role else UserRole.STUDENT.value
    )

    # Insert user into database
    user_data = {
        "email": user.email,
        "password": user.password,
        "name": user.name,
        "role": user.role,
        "created_at": user.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": user.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    # Insert and get the UUID
    user_id = insert_to_collection(
        collection_name="Users",
        properties=user_data
    )
    if isinstance(user_id, uuid.UUID):
        user_id = str(user_id)
    
    if not user_id:
        raise AuthError("Failed to create user", 500)
        

    # Generate token
    token = create_jwt_token(user_id)
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    }

def sign_in(auth_request: AuthRequest) -> Dict[str, Any]:
    """Authenticate a user and return a token"""
    # Get user from database
    user = get_user_by_email(auth_request.email)
    if not user:
        raise AuthError("Invalid email or password", 401)

    # Verify password
    if not check_password_hash(user["password"], auth_request.password):
        raise AuthError("Invalid email or password", 401)

    # Generate token using user ID
    user_id = user.get("uuid")
    if not user_id:
        raise AuthError("Invalid user data", 500)
        
    token = create_jwt_token(user_id)
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": user["email"],
            "name": user["name"],
            "role": user.get("role")
        }
    } 