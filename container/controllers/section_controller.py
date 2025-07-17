from flask import request, jsonify, g
from services.handle_sections import (
    create_section,
    get_sections,
    get_section_by_id,
    update_section,
    delete_section,
    search_sections
)
from data_classes.common_classes import Section
import logging
from __init__ import app, login_required
logger = logging.getLogger(__name__)


@app.route('/api/v1/sections', methods=['POST'])
@login_required
def create_section_endpoint():
    """Create a new section"""
    try:
        body = request.json
        if not body:
            return jsonify({"error": "No data provided"}), 400
        section = Section(**body)
        section.author = g.user_id
        section = create_section(section)
        return jsonify(section), 201
    except Exception as e:
        logger.error(f"Error creating section: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sections', methods=['GET'])
@login_required
def get_sections_endpoint():
    """Get all sections with pagination"""
    try:
        # get email from jwt token
        email = g.user_id
        print(email)
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        sections, total_count = get_sections(email, limit, offset)
        
        # Calculate pagination info
        page_number = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
        
        response = jsonify(sections)
        response.headers['X-Total-Count'] = str(total_count)
        response.headers['X-Page-Size'] = str(limit)
        response.headers['X-Page-Number'] = str(page_number)
        response.headers['X-Total-Pages'] = str(total_pages)
        return response, 200
    except Exception as e:
        logger.error(f"Error getting sections: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sections/<section_id>', methods=['GET'])
@login_required
def get_section_endpoint(section_id):
    """Get a section by ID"""
    try:
        section = get_section_by_id(section_id)
        if not section:
            return jsonify({"error": "Section not found"}), 404
        return jsonify(section), 200
    except Exception as e:
        logger.error(f"Error getting section: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sections/<section_id>', methods=['PUT'])
@login_required
def update_section_endpoint(section_id):
    """Update a section"""
    try:
        body = request.json
        if not body:
            return jsonify({"error": "No data provided"}), 400
        # Extract only the fields that can be updated
        allowed_fields = ["title", "order", "agent_id"]
        update_data = {key: value for key, value in body.items() if key in allowed_fields}
        
        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400
        
        success = update_section(section_id, **update_data)
        if not success:
            return jsonify({"error": "Section not found"}), 404
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error updating section: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sections/<section_id>', methods=['DELETE'])
@login_required
def delete_section_endpoint(section_id):
    """Delete a section"""
    try:
        success = delete_section(section_id)
        if not success:
            return jsonify({"error": "Section not found"}), 404
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error deleting section: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sections/search', methods=['GET'])
@login_required
def search_sections_endpoint():
    """Search sections by content"""
    try:
        query = request.args.get('query', '')
        limit = int(request.args.get('limit', 10))
        sections = search_sections(query, limit)
        return jsonify(sections), 200
    except Exception as e:
        logger.error(f"Error searching sections: {str(e)}")
        return jsonify({"error": str(e)}), 500 