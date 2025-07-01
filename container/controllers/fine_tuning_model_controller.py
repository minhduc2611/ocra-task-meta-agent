from flask import request, jsonify, g
from __init__ import app, login_required
from services.handle_fine_tuning_models import (
    get_all_fine_tuning_models, get_fine_tuning_model_by_id, update_fine_tuning_model, 
    delete_fine_tuning_model, check_fine_tuning_model_permissions, FineTuningModelError, 
    create_fine_tuning_model, get_fine_tuning_model_stats
)
from services.handle_user import get_user_by_id
from data_classes.common_classes import FineTuningStatus, Language


@app.route('/api/v1/fine-tuning-models', methods=['POST'])
@login_required
def create_fine_tuning_model_endpoint():
    """Create a new fine-tuning model"""
    try:
        # Get current user to check permissions
        current_user = get_user_by_id(g.user_id)
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        # Check if user has permission to create models
        if not check_fine_tuning_model_permissions(current_user, action="create"):
            return jsonify({"error": "Insufficient permissions"}), 403

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate required fields
        required_fields = ["name", "base_model"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Field '{field}' is required"}), 400

        # Validate status if provided
        if "status" in data:
            valid_statuses = [status.value for status in FineTuningStatus]
            if data["status"] not in valid_statuses:
                return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

        # Validate language if provided
        if "language" in data:
            valid_languages = [lang.value for lang in Language]
            if data["language"] not in valid_languages:
                return jsonify({"error": f"Invalid language. Must be one of: {', '.join(valid_languages)}"}), 400

        # Create model
        model_id = create_fine_tuning_model(data, current_user["uuid"])
        
        # Get created model
        created_model = get_fine_tuning_model_by_id(model_id)
        
        return jsonify({
            "message": "Fine-tuning model created successfully",
            "model": created_model
        }), 201

    except FineTuningModelError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        print(f"Error in create_fine_tuning_model_endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/fine-tuning-models', methods=['GET'])
@login_required
def get_fine_tuning_models():
    """Get list of fine-tuning models"""
    try:
        # Get current user to check permissions
        current_user = get_user_by_id(g.user_id)
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        # Check if user has permission to list models
        if not check_fine_tuning_model_permissions(current_user, action="list"):
            return jsonify({"error": "Insufficient permissions"}), 403

        # Get query parameters for pagination and filtering
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search', '', type=str)
        status = request.args.get('status', '', type=str)
        language = request.args.get('language', '', type=str)
        
        # Ensure reasonable limits
        limit = min(limit, 1000)  # Max 1000 models per request
        offset = max(offset, 0)

        # Convert empty strings to None for filtering
        status = status if status else None
        language = language if language else None

        # Get models
        models = get_all_fine_tuning_models(
            limit=limit, 
            offset=offset, 
            search=search, 
            status=status, 
            language=language
        )
        
        return jsonify({
            "models": models,
            "limit": limit,
            "offset": offset,
            "count": len(models)
        }), 200

    except FineTuningModelError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        print(f"Error in get_fine_tuning_models: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/fine-tuning-models/<model_id>', methods=['GET'])
@login_required
def get_fine_tuning_model(model_id):
    """Get single fine-tuning model by ID"""
    try:
        # Get current user to check permissions
        current_user = get_user_by_id(g.user_id)
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        # Check if user has permission to read this model
        if not check_fine_tuning_model_permissions(current_user, model_id, "read"):
            return jsonify({"error": "Insufficient permissions"}), 403

        # Get model
        model = get_fine_tuning_model_by_id(model_id)
        if not model:
            return jsonify({"error": "Fine-tuning model not found"}), 404

        return jsonify({"model": model}), 200

    except FineTuningModelError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        print(f"Error in get_fine_tuning_model: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/fine-tuning-models/<model_id>', methods=['PUT'])
@login_required
def update_fine_tuning_model_endpoint(model_id):
    """Update fine-tuning model by ID"""
    try:
        # Get current user to check permissions
        current_user = get_user_by_id(g.user_id)
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        # Check if user has permission to update this model
        if not check_fine_tuning_model_permissions(current_user, model_id, "update"):
            return jsonify({"error": "Insufficient permissions"}), 403

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate allowed fields
        allowed_fields = ["name", "description", "base_model", "status", "language", 
                         "training_data_path", "validation_data_path", "hyperparameters", 
                         "training_metrics", "model_path", "version"]
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        # Validate status if provided
        if "status" in update_data:
            valid_statuses = [status.value for status in FineTuningStatus]
            if update_data["status"] not in valid_statuses:
                return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

        # Validate language if provided
        if "language" in update_data:
            valid_languages = [lang.value for lang in Language]
            if update_data["language"] not in valid_languages:
                return jsonify({"error": f"Invalid language. Must be one of: {', '.join(valid_languages)}"}), 400

        # Update model
        success = update_fine_tuning_model(model_id, update_data)
        if not success:
            return jsonify({"error": "Failed to update fine-tuning model"}), 500

        # Get updated model
        updated_model = get_fine_tuning_model_by_id(model_id)
        
        return jsonify({
            "message": "Fine-tuning model updated successfully",
            "model": updated_model
        }), 200

    except FineTuningModelError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        print(f"Error in update_fine_tuning_model_endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/fine-tuning-models/<model_id>', methods=['DELETE'])
@login_required
def delete_fine_tuning_model_endpoint(model_id):
    """Delete fine-tuning model by ID"""
    try:
        # Get current user to check permissions
        current_user = get_user_by_id(g.user_id)
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        # Check if user has permission to delete this model
        if not check_fine_tuning_model_permissions(current_user, model_id, "delete"):
            return jsonify({"error": "Insufficient permissions"}), 403

        # Delete model
        success = delete_fine_tuning_model(model_id)
        if not success:
            return jsonify({"error": "Failed to delete fine-tuning model"}), 500

        return jsonify({
            "message": "Fine-tuning model deleted successfully"
        }), 200

    except FineTuningModelError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        print(f"Error in delete_fine_tuning_model_endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/fine-tuning-models/stats', methods=['GET'])
@login_required
def get_fine_tuning_model_stats_endpoint():
    """Get statistics about fine-tuning models - Admin only"""
    try:
        # Get current user to check permissions
        current_user = get_user_by_id(g.user_id)
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        # Check if user has permission to view stats (admin only)
        if not check_fine_tuning_model_permissions(current_user, action="stats"):
            return jsonify({"error": "Insufficient permissions"}), 403

        # Get stats
        stats = get_fine_tuning_model_stats()
        
        return jsonify({
            "stats": stats
        }), 200

    except FineTuningModelError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        print(f"Error in get_fine_tuning_model_stats_endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/fine-tuning-models/statuses', methods=['GET'])
@login_required
def get_fine_tuning_statuses():
    """Get available fine-tuning statuses"""
    try:
        statuses = [status.value for status in FineTuningStatus]
        return jsonify({
            "statuses": statuses
        }), 200
    except Exception as e:
        print(f"Error in get_fine_tuning_statuses: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/fine-tuning-models/languages', methods=['GET'])
@login_required
def get_fine_tuning_languages():
    """Get available languages for fine-tuning models"""
    try:
        languages = [lang.value for lang in Language]
        return jsonify({
            "languages": languages
        }), 200
    except Exception as e:
        print(f"Error in get_fine_tuning_languages: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500 