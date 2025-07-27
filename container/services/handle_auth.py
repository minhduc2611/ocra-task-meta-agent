from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from data_classes.common_classes import User, AuthRequest, PasswordResetRequest, ResetPasswordRequest, PasswordResetToken
from libs.weaviate_lib import search_non_vector_collection, insert_to_collection, COLLECTION_TOKEN_BLACKLIST, update_collection_object
from weaviate.collections.classes.filters import Filter
from services.handle_email import send_password_reset_email, send_password_reset_confirmation_email, EmailError
import os
import uuid
import secrets
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

def request_password_reset(email: str) -> Dict[str, Any]:
    """Request password reset - generate token and send email"""
    try:
        # Check if user exists
        user = get_user_by_email(email)
        if not user:
            # For security, don't reveal if email exists or not
            return {"status": "success", "message": "If this email is registered, you will receive a reset link"}
        
        # Generate secure reset token
        reset_token = secrets.token_urlsafe(32)
        
        # Token expires in 1 hour
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        
        # Create password reset token record
        reset_token_data = {
            "email": email,
            "token": reset_token,
            "expires_at": expires_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "used": False
        }
        
        # Store the reset token
        token_id = insert_to_collection(
            collection_name="PasswordResetTokens",
            properties=reset_token_data
        )
        
        if not token_id:
            raise AuthError("Failed to create reset token", 500)
        
        # Send the reset email
        email_sent = send_password_reset_email(email, reset_token)
        
        if not email_sent:
            raise AuthError("Failed to send reset email", 500)
        
        return {
            "status": "success", 
            "message": "If this email is registered, you will receive a reset link"
        }
        
    except EmailError as e:
        raise AuthError(e.message, e.status_code)
    except Exception as e:
        print(f"Error requesting password reset: {str(e)}")
        raise AuthError("Failed to process password reset request", 500)

def reset_password(token: str, new_password: str) -> Dict[str, Any]:
    """Reset password using token"""
    try:
        # Find the reset token
        filters = Filter.by_property("token").equal(token) & Filter.by_property("used").equal(False)
        reset_tokens = search_non_vector_collection(
            collection_name="PasswordResetTokens",
            filters=filters,
            limit=1,
            properties=["email", "token", "expires_at", "used", "created_at"]
        )
        
        if not reset_tokens:
            raise AuthError("Invalid or expired reset token", 400)
        
        reset_token_data = reset_tokens[0]
        
        # Check if token has expired
        expires_at = reset_token_data["expires_at"]
        if isinstance(expires_at, str):
            # If it's a string, parse it
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        elif expires_at.tzinfo is None:
            # If it's a datetime without timezone, assume UTC
            expires_at = expires_at.replace(tzinfo=UTC)
        
        if datetime.now(UTC) > expires_at:
            raise AuthError("Reset token has expired", 400)
        
        # Get user by email
        email = reset_token_data["email"]
        user = get_user_by_email(email)
        
        if not user:
            raise AuthError("User not found", 404)
        
        # Update user password
        new_password_hash = generate_password_hash(new_password)
        
        # Update user in database
        user_filters = Filter.by_property("email").equal(email)
        users = search_non_vector_collection(
            collection_name="Users",
            filters=user_filters,
            limit=1
        )
        
        if not users:
            raise AuthError("User not found", 404)
        
        user_id = users[0]["uuid"]
        
        # Update password
        update_success = update_collection_object(
            collection_name="Users",
            uuid=user_id,
            properties={
                "password": new_password_hash,
                "updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )
        
        if not update_success:
            raise AuthError("Failed to update password", 500)
        
        # Mark token as used
        reset_token_filters = Filter.by_property("token").equal(token)
        reset_token_objects = search_non_vector_collection(
            collection_name="PasswordResetTokens",
            filters=reset_token_filters,
            limit=1        
        )
        
        if reset_token_objects:
            reset_token_id = reset_token_objects[0]["uuid"]
            update_collection_object(
                collection_name="PasswordResetTokens",
                uuid=reset_token_id,
                properties={"used": True}
            )
        
        # Send confirmation email (optional, don't fail if it doesn't work)
        try:
            send_password_reset_confirmation_email(email)
        except Exception as e:
            print(f"Failed to send confirmation email: {str(e)}")
        
        return {
            "status": "success", 
            "message": "Password has been successfully reset"
        }
        
    except AuthError:
        raise
    except Exception as e:
        print(f"Error resetting password: {str(e)}")
        raise AuthError("Failed to reset password", 500)

def cleanup_expired_reset_tokens():
    """Clean up expired reset tokens"""
    try:
        current_time = datetime.now(UTC)
        # This would require a more sophisticated cleanup mechanism
        # For now, we'll rely on the expiration check in reset_password
        pass
    except Exception as e:
        print(f"Error cleaning up expired reset tokens: {str(e)}")

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