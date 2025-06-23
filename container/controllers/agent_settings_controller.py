from flask import request, jsonify, g
from services.handle_agent_settings import (
    create_agent_setting,
    list_agent_settings,
    get_agent_setting,
    get_agent_setting_by_key,
    update_agent_setting,
    delete_agent_setting,
    delete_agent_settings_by_agent,
    search_agent_settings
)
import logging

from __init__ import app, login_required

logger = logging.getLogger(__name__)

@app.route('/api/v1/agent-settings', methods=['POST'])
@login_required
def create_agent_setting_endpoint():
    """Create a new agent setting"""
    try:
        body = request.json
        key = body.get('key')
        label = body.get('label')
        short_label = body.get('short_label')
        agent_id = body.get('agent_id')
        
        # Validate required fields
        if not all([key, label, short_label, agent_id]):
            return jsonify({"error": "Missing required fields: key, label, short_label, agent_id"}), 400
        
        result = create_agent_setting(
            key=key,
            label=label,
            short_label=short_label,
            agent_id=agent_id
        )
        
        if "error" in result:
            return jsonify(result), 500
        
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Error creating agent setting: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agent-settings', methods=['GET'])
@login_required
def list_agent_settings_endpoint():
    """List all agent settings, optionally filtered by agent_id"""
    try:
        agent_id = request.args.get('agent_id')
        limit = int(request.args.get('limit', 100))
        
        settings = list_agent_settings(agent_id=agent_id, limit=limit)
        
        if settings and "error" in settings[0]:
            return jsonify(settings[0]), 500
        
        return jsonify(settings), 200
    except Exception as e:
        logger.error(f"Error listing agent settings: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agent-settings/<setting_id>', methods=['GET'])
@login_required
def get_agent_setting_endpoint(setting_id):
    """Get a specific agent setting by ID"""
    try:
        setting = get_agent_setting(setting_id)
        
        if "error" in setting:
            return jsonify(setting), 404
        
        return jsonify(setting), 200
    except Exception as e:
        logger.error(f"Error getting agent setting: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/<agent_id>/settings/<key>', methods=['GET'])
@login_required
def get_agent_setting_by_key_endpoint(agent_id, key):
    """Get a specific agent setting by agent_id and key"""
    try:
        setting = get_agent_setting_by_key(agent_id, key)
        
        if "error" in setting:
            return jsonify(setting), 404
        
        return jsonify(setting), 200
    except Exception as e:
        logger.error(f"Error getting agent setting by key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agent-settings/<setting_id>', methods=['PUT'])
@login_required
def update_agent_setting_endpoint(setting_id):
    """Update an agent setting"""
    try:
        body = request.json
        
        # Only allow updating specific fields
        allowed_fields = ['key', 'label', 'short_label', 'agent_id']
        update_data = {k: v for k, v in body.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400
        
        result = update_agent_setting(setting_id, **update_data)
        
        if "error" in result:
            return jsonify(result), 500
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error updating agent setting: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agent-settings/<setting_id>', methods=['DELETE'])
@login_required
def delete_agent_setting_endpoint(setting_id):
    """Delete an agent setting"""
    try:
        result = delete_agent_setting(setting_id)
        
        if "error" in result:
            return jsonify(result), 500
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error deleting agent setting: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/<agent_id>/settings', methods=['DELETE'])
@login_required
def delete_agent_settings_by_agent_endpoint(agent_id):
    """Delete all settings for a specific agent"""
    try:
        result = delete_agent_settings_by_agent(agent_id)
        
        if "error" in result:
            return jsonify(result), 500
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error deleting agent settings: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agent-settings/search', methods=['GET'])
@login_required
def search_agent_settings_endpoint():
    """Search for agent settings"""
    try:
        query = request.args.get('query', '')
        agent_id = request.args.get('agent_id')
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
        
        settings = search_agent_settings(query=query, agent_id=agent_id, limit=limit)
        
        if settings and "error" in settings[0]:
            return jsonify(settings[0]), 500
        
        return jsonify(settings), 200
    except Exception as e:
        logger.error(f"Error searching agent settings: {str(e)}")
        return jsonify({"error": str(e)}), 500 