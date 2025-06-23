from flask import request, jsonify, g
from services.upload_file import get_files, get_file_by_id, create_file, update_file, delete_file
from data_classes.common_classes import File
import logging
from __init__ import app, login_required
logger = logging.getLogger(__name__)


@app.route('/api/v1/files', methods=['GET'])
@login_required
def get_files_endpoint():
    """Get all files"""
    try:
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        files, total_count = get_files(limit, offset)
        
        # Calculate pagination info
        page_number = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
        
        response = jsonify(files)
        response.headers['X-Total-Count'] = str(total_count)
        response.headers['X-Page-Size'] = str(limit)
        response.headers['X-Page-Number'] = str(page_number)
        response.headers['X-Total-Pages'] = str(total_pages)
        return response, 200
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/v1/files/<file_id>', methods=['GET'])
@login_required
def get_file_endpoint(file_id):
    """Get a file by ID"""
    try:
        file = get_file_by_id(file_id)
        return jsonify(file), 200
    except Exception as e:
        logger.error(f"Error getting file: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/v1/files/<file_id>', methods=['PUT'])
@login_required
def update_file_endpoint(file_id):
    """Update a file"""
    try:
        body = request.json
        file = File(**body)
        file.author = g.user_id
        file = update_file(file_id, file)
        return jsonify(file), 200
    except Exception as e:
        logger.error(f"Error updating file: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/v1/files/<file_id>', methods=['DELETE'])
@login_required
def delete_file_endpoint(file_id):
    """Delete a file"""
    try:
        success = delete_file(file_id)
        if not success:
            return jsonify({"error": "File not found"}), 404
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return jsonify({"error": str(e)}), 500 