from flask import request, jsonify, g
from services.handle_api_keys import (
    create_api_key, get_api_keys_by_user, get_api_key_by_id, 
    update_api_key, delete_api_key, revoke_api_key, ApiKeyError
)
from data_classes.common_classes import CreateApiKeyRequest, UpdateApiKeyRequest
import logging
from __init__ import app, login_required
import json
logger = logging.getLogger(__name__)

@app.route('/api/v1/api-keys', methods=['POST'])
@login_required
def create_api_key_endpoint():
    """Create a new API key"""
    try:
        body = request.json or {}
        name = body.get('name')
        if not name:
            return jsonify({"error": "Name is required"}), 400
            
        create_request = CreateApiKeyRequest(
            name=name,
            description=body.get('description'),
            permissions=body.get('permissions'),
            expires_at=body.get('expires_at')
        )
        result = create_api_key(g.user_id, create_request)
        return jsonify(result), 201
    except ApiKeyError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/api-keys', methods=['GET'])
@login_required
def list_api_keys_endpoint():
    """List all API keys for the current user"""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        api_keys = get_api_keys_by_user(g.user_id, limit=limit, offset=offset)
        results = []
        for api_key in api_keys:
            results.append({
                "uuid": api_key.get("uuid"),
                "name": api_key.get("name"),
                "description": api_key.get("description"),
                "status": api_key.get("status"),
                "permissions": json.loads(api_key.get("permissions") or "[]"),
                "created_at": api_key.get("created_at"),
                "updated_at": api_key.get("updated_at"),
                "expires_at": api_key.get("expires_at"),
                "last_used_at": api_key.get("last_used_at"),
            })
        return jsonify({"api_keys": results}), 200
    except ApiKeyError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/api-keys/<api_key_id>', methods=['GET'])
@login_required
def get_api_key_endpoint(api_key_id):
    """Get a specific API key by ID"""
    try:
        api_key = get_api_key_by_id(api_key_id)
        if not api_key:
            return jsonify({"error": "API key not found"}), 404
        
        # Check if user owns this API key
        if api_key.get("user_id") != g.user_id:
            return jsonify({"error": "Unauthorized"}), 403
        
        return jsonify(api_key), 200
    except ApiKeyError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error getting API key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/api-keys/<api_key_id>', methods=['PUT'])
@login_required
def update_api_key_endpoint(api_key_id):
    """Update an API key"""
    try:
        body = request.json or {}
        update_request = UpdateApiKeyRequest(
            name=body.get('name'),
            description=body.get('description'),
            permissions=body.get('permissions'),
            status=body.get('status'),
            expires_at=body.get('expires_at')
        )
        result = update_api_key(api_key_id, g.user_id, update_request)
        return jsonify(result), 200
    except ApiKeyError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error updating API key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/api-keys/<api_key_id>', methods=['DELETE'])
@login_required
def delete_api_key_endpoint(api_key_id):
    """Delete an API key"""
    try:
        success = delete_api_key(api_key_id, g.user_id)
        if success:
            return jsonify({"message": "API key deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete API key"}), 500
    except ApiKeyError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error deleting API key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/api-keys/<api_key_id>/revoke', methods=['POST'])
@login_required
def revoke_api_key_endpoint(api_key_id):
    """Revoke an API key"""
    try:
        result = revoke_api_key(api_key_id, g.user_id)
        return jsonify(result), 200
    except ApiKeyError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error revoking API key: {str(e)}")
        return jsonify({"error": str(e)}), 500
