from flask import request, jsonify, g
from __init__ import app, login_required
from services.handle_messages import update_message, delete_message, get_message_by_id, get_messages_list, MessageError, save_q_and_a_pairs_to_system, like_message, dislike_message
import logging
import json
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
        agent_id = request.args.get('agent_id', type=str)
        search = request.args.get('search', type=str)
        include_related = request.args.get('include_related', 'false').lower() == 'true'
        approval_status = request.args.get('approval_status', type=str)
        # Get messages
        result = get_messages_list(
            limit=limit,
            offset=offset,
            session_id=session_id,
            role=role,
            agent_id=agent_id,
            search=search,
            include_related=include_related,
            approval_status=approval_status
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
        
        # data is an json array, now join it with , 
        if "like_user_ids" in data:
            data["like_user_ids"] = ",".join(data["like_user_ids"])
        if "dislike_user_ids" in data:
            data["dislike_user_ids"] = ",".join(data["dislike_user_ids"])

        # Validate required fields
        allowed_fields = ["content", "role", "mode", "feedback", "edited_content", "approval_status", "like_user_ids", "dislike_user_ids"]
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

@app.route('/api/v1/messages/save-q-and-a-pairs-to-system', methods=['POST'])
@login_required
def save_q_and_a_pairs_to_system_endpoint():
    """Save Q&A pairs to the system as documents"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate required fields
        q_and_a_pairs = data.get('qAndAPairs')
        if not q_and_a_pairs:
            return jsonify({"error": "qAndAPairs field is required"}), 400

        if not isinstance(q_and_a_pairs, list):
            return jsonify({"error": "qAndAPairs must be a list"}), 400

        # Validate each Q&A pair
        for i, pair in enumerate(q_and_a_pairs):
            if not isinstance(pair, dict):
                return jsonify({"error": f"Q&A pair at index {i} must be an object"}), 400
            
            if 'question' not in pair or 'answer' not in pair:
                return jsonify({"error": f"Q&A pair at index {i} must have 'question' and 'answer' fields"}), 400
            
            if not isinstance(pair['question'], str) or not isinstance(pair['answer'], str):
                return jsonify({"error": f"Q&A pair at index {i} must have string values for 'question' and 'answer'"}), 400

        # Save Q&A pairs to system
        result = save_q_and_a_pairs_to_system(q_and_a_pairs)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 400
        
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error in save_q_and_a_pairs_to_system_endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/messages/<message_id>/like', methods=['POST'])
@login_required
def like_message_endpoint(message_id):
    """Like a message"""
    try:
        user_id = g.user_id
        
        # Like message
        result = like_message(message_id, user_id)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 400
        
        return jsonify(result), 200

    except MessageError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error in like_message_endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/messages/<message_id>/dislike', methods=['POST'])
@login_required
def dislike_message_endpoint(message_id):
    """Dislike a message"""
    try:
        user_id = g.user_id
        
        # Dislike message
        result = dislike_message(message_id, user_id)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 400
        
        return jsonify(result), 200

    except MessageError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error in dislike_message_endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500