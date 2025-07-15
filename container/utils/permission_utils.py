from functools import wraps
from flask import g, jsonify
from typing import List, Optional

def require_permission(permission: str):
    """Decorator to require a specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'permissions'):
                return jsonify({"error": "No permissions available"}), 403
            
            if permission not in g.permissions:
                return jsonify({"error": f"Permission '{permission}' required"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_any_permission(permissions: List[str]):
    """Decorator to require any of the specified permissions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'permissions'):
                return jsonify({"error": "No permissions available"}), 403
            
            if not any(perm in g.permissions for perm in permissions):
                return jsonify({"error": f"One of permissions {permissions} required"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_all_permissions(permissions: List[str]):
    """Decorator to require all of the specified permissions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'permissions'):
                return jsonify({"error": "No permissions available"}), 403
            
            if not all(perm in g.permissions for perm in permissions):
                return jsonify({"error": f"All permissions {permissions} required"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def has_permission(permission: str) -> bool:
    """Check if the current user has a specific permission"""
    if not hasattr(g, 'permissions'):
        return False
    return permission in g.permissions

def has_any_permission(permissions: List[str]) -> bool:
    """Check if the current user has any of the specified permissions"""
    if not hasattr(g, 'permissions'):
        return False
    return any(perm in g.permissions for perm in permissions)

def has_all_permissions(permissions: List[str]) -> bool:
    """Check if the current user has all of the specified permissions"""
    if not hasattr(g, 'permissions'):
        return False
    return all(perm in g.permissions for perm in permissions) 