from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from werkzeug.security import generate_password_hash
from libs.weaviate_lib import get_aggregate, search_non_vector_collection, insert_to_collection, update_collection_object, delete_collection_object
from weaviate.classes.query import Filter
from weaviate.collections.classes.grpc import Sort
import uuid
from libs.weaviate_lib import COLLECTION_USERS
from data_classes.common_classes import UserRole
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

class UserError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get a user by ID"""
    try:
        users = search_non_vector_collection(
            collection_name="Users",
            filters=Filter.by_id().equal(user_id),
            limit=1,
            properties=["email", "name", "role", "created_at", "updated_at"]
        )
        if users:
            user = users[0]
            return user
        return None
    except Exception as e:
        print(f"Error getting user by ID: {str(e)}")
        return None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a user by email"""
    try:
        filters = Filter.by_property("email").equal(email)
        users = search_non_vector_collection(
            collection_name="Users",
            filters=filters,
            limit=1,
            properties=["email", "name", "role", "created_at", "updated_at"]
        )
        if users:
            user = users[0]
            return user
        return None
    except Exception as e:
        print(f"Error getting user by email: {str(e)}")
        return None

def get_all_users(limit: int = 100, offset: int = 0, search: str = "") -> List[Dict[str, Any]]:
    """Get all users with pagination"""
    sort = Sort.by_property("created_at", ascending=False)
    if search:
        filters = Filter.by_property("name").like(search) | Filter.by_property("email").like(search)
    else:
        filters = None
    try:
        users = search_non_vector_collection(
            collection_name="Users",
            limit=limit,
            offset=offset,
            properties=["email", "name", "role", "created_at", "updated_at"],
            sort=sort,
            filters=filters
        )
        
        return users
    except Exception as e:
        print(f"Error getting all users: {str(e)}")
        return []

def create_user(user_data: Dict[str, Any]) -> str:
    """Create a new user"""
    try:
        # Check if user already exists
        existing_user = get_user_by_email(user_data["email"])
        if existing_user:
            raise UserError("Email already registered", 400)

        # Hash password if provided
        if "password" in user_data:
            user_data["password"] = generate_password_hash(user_data["password"])

        # Set default values
        user_data["role"] = user_data.get("role", UserRole.VIEWER.value)
        user_data["created_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        user_data["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Insert user
        user_id = insert_to_collection(
            collection_name="Users",
            properties=user_data
        )
        
        if isinstance(user_id, uuid.UUID):
            user_id = str(user_id)
        
        if not user_id:
            raise UserError("Failed to create user", 500)
        
        return user_id
    except UserError:
        raise
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        raise UserError("Failed to create user", 500)

def update_user(user_id: str, user_data: Dict[str, Any]) -> bool:
    """Update an existing user"""
    try:
        # Check if user exists
        existing_user = get_user_by_id(user_id)
        if not existing_user:
            raise UserError("User not found", 404)

        # Hash password if provided
        if "password" in user_data and user_data["password"]:
            user_data["password"] = generate_password_hash(user_data["password"])

        # Update timestamp
        user_data["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Remove fields that shouldn't be updated
        user_data.pop("created_at", None)
        user_data.pop("email", None)  # Email should not be changed

        # Update user
        success = update_collection_object(
            collection_name="Users",
            uuid=user_id,
            properties=user_data
        )
        
        if not success:
            raise UserError("Failed to update user", 500)
        
        return True
    except UserError:
        raise
    except Exception as e:
        print(f"Error updating user: {str(e)}")
        raise UserError("Failed to update user", 500)

def delete_user(user_id: str) -> bool:
    """Delete a user"""
    try:
        # Check if user exists
        existing_user = get_user_by_id(user_id)
        if not existing_user:
            raise UserError("User not found", 404)

        # Delete user
        result = delete_collection_object(
            collection_name="Users",
            uuid=user_id
        )
        
        if not result:
            raise UserError("Failed to delete user", 500)
        
        return True
    except UserError:
        raise
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
        raise UserError("Failed to delete user", 500)

def check_user_permissions(current_user_id: str, target_user_id: str = None, action: str = "read") -> bool:
    """Check if current user has permissions for the action"""
    try:
        current_user = get_user_by_id(current_user_id)
        if not current_user:
            return False

        # Admin can do everything
        if current_user.get("role", UserRole.VIEWER.value) == UserRole.ADMIN.value:
            return True

        # For non-admin users
        if action == "list":
            # Non-admin users cannot list all users
            return False
        elif action == "stats":
            # Only admins can view stats
            return False
        elif action == "create":
            # Only admins can create users
            return False
        elif action in ["read", "update", "delete"]:
            # Non-admin users can only access their own data
            return current_user_id == target_user_id
        else:
            return False
    except Exception as e:
        print(f"Error checking user permissions: {str(e)}")
        return False

def create_admin_user(email: str, password: str, name: str = None) -> str:
    """Create an admin user (for testing/initial setup)"""
    try:
        user_data = {
            "email": email,
            "password": password,
            "name": name or email,
            "role": UserRole.ADMIN.value
        }
        return create_user(user_data)
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        raise UserError("Failed to create admin user", 500)

def get_user_stats():
    """Get user statistics - Admin only"""
    try:
        # Define the stats we want to collect
        stats_queries = [
            ("total", None),  # No filter for total count
            ("admin", Filter.by_property("role").equal(UserRole.ADMIN.value)),
            ("student", Filter.by_property("role").equal(UserRole.STUDENT.value)),
            ("viewer", Filter.by_property("role").equal(UserRole.VIEWER.value)),
            ("contributor", Filter.by_property("role").equal(UserRole.CONTRIBUTOR.value))
        ]
        
        # Function to execute a single aggregate query
        def execute_aggregate_query(query_name, filter_obj):
            try:
                response = get_aggregate(
                    collection_name=COLLECTION_USERS,
                    filters=filter_obj
                )
                return query_name, response.total_count
            except Exception as e:
                print(f"Error in {query_name} query: {str(e)}")
                return query_name, 0
        
        # Execute all queries in parallel using ThreadPoolExecutor
        results = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            future_to_query = {}
            for query_name, filter_obj in stats_queries:
                future = executor.submit(execute_aggregate_query, query_name, filter_obj)
                future_to_query[future] = query_name
            
            # Collect results as they complete
            for future in future_to_query:
                query_name, count = future.result()
                results[query_name] = count
        
        # Construct the final stats object
        stats = {
            "total": results.get("total", 0),
            "admin": results.get("admin", 0),
            "student": results.get("student", 0),
            "viewer": results.get("viewer", 0),
            "contributor": results.get("contributor", 0),
            "online": results.get("total", 0)  # For now, assume all users are online
        }
        
        return stats
        
    except Exception as e:
        print(f"Error getting user stats: {str(e)}")
        raise UserError("Failed to get user stats", 500)