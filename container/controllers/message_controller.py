from flask import request, jsonify, g
from __init__ import app, login_required
from services.handle_messages import update_message, delete_message, get_message_by_id, get_messages_list, MessageError
import logging

logger = logging.getLogger(__name__)

@app.route('/api/v1/messages', methods=['GET'])
@login_required
def get_messages_endpoint():
    """Get list of messages with pagination and filtering"""
    try:
        # Get query parameters for pagination and filtering
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        session_id = request.args.get('session_id', type=str)
        role = request.args.get('role', type=str)
        mode = request.args.get('mode', type=str)
        search = request.args.get('search', type=str)
        include_related = request.args.get('include_related', 'false').lower() == 'true'
        
        # Get messages
        result = get_messages_list(
            limit=limit,
            offset=offset,
            session_id=session_id,
            role=role,
            mode=mode,
            search=search,
            include_related=include_related
        )
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 400
        
        return jsonify(result), 200

    except MessageError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error in get_messages_endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/messages/<message_id>', methods=['PUT'])
@login_required
def update_message_endpoint(message_id):
    """Update message by ID"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate required fields
        allowed_fields = ["content", "role", "mode", "feedback", "edited_content", "approval_status"]
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        # Update message
        result = update_message(message_id, **update_data)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 400
        
        return jsonify(result), 200

    except MessageError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error in update_message_endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/messages/<message_id>', methods=['DELETE'])
@login_required
def delete_message_endpoint(message_id):
    """Delete message by ID"""
    try:
        # Delete message
        result = delete_message(message_id)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 400
        
        return jsonify(result), 200

    except MessageError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error in delete_message_endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/messages/<message_id>', methods=['GET'])
@login_required
def get_message_endpoint(message_id):
    """Get single message by ID"""
    try:
        # Get message
        result = get_message_by_id(message_id)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 404
        
        return jsonify(result), 200

    except MessageError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error in get_message_endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500 
    
    