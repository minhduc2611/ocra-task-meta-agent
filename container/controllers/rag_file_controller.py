from flask import request, jsonify, g
from werkzeug.datastructures import FileStorage
from libs.google_vertex import add_file, remove_file, get_files, read_one_file
from services.handle_agent import get_agent_by_id
from __init__ import app, login_required
import logging

logger = logging.getLogger(__name__)

@app.route('/api/v1/rag/files', methods=['POST'])
@login_required
def upload_rag_file():
    """Upload a file to RAG corpus"""
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({"error": "No file provided"}), 400
        
        # Get corpus_id from request, use default if not provided
        corpus_id = request.form.get('corpus_id', None)
        agent_id = request.form.get('agent_id', None)
        if agent_id and not corpus_id:
            agent = get_agent_by_id(agent_id)
            corpus_id = agent["corpus_id"]
        if not corpus_id:
            return jsonify({"error": "No corpus_id provided"}), 400
        
        results = []
        for file in files:
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            result = add_file(file, corpus_id)
            results.append(result)
        
        # Check if any results contain errors
        for result in results:
            if isinstance(result, dict) and "Error" in result:
                return jsonify({"error": result}), 500
        
        return jsonify({"message": results}), 200
        
    except Exception as e:
        logger.error(f"Error uploading RAG file: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/rag/files', methods=['GET'])
@login_required
def list_rag_files():
    """List all files in RAG corpus"""
    try:
        # Get corpus_id from request, use default if not provided
        corpus_id = request.args.get('corpus_id', None)
        agent_id = request.args.get('agent_id', None)
        if agent_id and not corpus_id:
            agent = get_agent_by_id(agent_id)
            corpus_id = agent["corpus_id"]
        if not corpus_id:
            return jsonify({"files": [], "message": "No corpus_id provided"}), 200
        files = get_files(corpus_id)
        
        # Convert RagFile objects to dictionaries for JSON serialization
        file_list = []
        for file in files:
            file_dict = {
                "name": file.name,
                "display_name": file.display_name,
                "create_time": file.create_time.isoformat() if file.create_time else None,
                # "update_time": file.update_time.isoformat() if file.update_time else None,
                # STATE_UNSPECIFIED (0):
                #     RagFile state is unspecified.
                # ACTIVE (1):
                #     RagFile resource has been created and indexed
                #     successfully.
                # ERROR (2):
                #     RagFile resource is in a problematic state. See
                #     ``error_message`` field for details.
                "state": file.file_status.state.value if file.file_status.state else None,
                "id": file.name.split("/")[-1]
            }
            file_list.append(file_dict)
        
        return jsonify({"files": file_list}), 200
        
    except Exception as e:
        logger.error(f"Error listing RAG files: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/rag/files/<file_id>', methods=['GET'])
@login_required
def read_rag_file(file_id):
    """Read content of a specific file from RAG corpus"""
    try:
        # Get corpus_id from request, use default if not provided
        corpus_id = request.args.get('corpus_id', None)
        agent_id = request.args.get('agent_id', None)
        if agent_id and not corpus_id:
            agent = get_agent_by_id(agent_id)
            corpus_id = agent["corpus_id"]
        if not corpus_id:
            return jsonify({"error": "No corpus_id provided"}), 400
        
        file_content = read_one_file(file_id, corpus_id)
        
        return jsonify({
            "file_id": file_id,
            "content": file_content
        }), 200
        
    except Exception as e:
        logger.error(f"Error reading RAG file {file_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/rag/files/<file_name>', methods=['DELETE'])
@login_required
def delete_rag_file(file_name):
    """Delete a file from RAG corpus"""
    try:
        # Get corpus_id from request, use default if not provided
        corpus_id = request.args.get('corpus_id', None)
        agent_id = request.args.get('agent_id', None)
        if agent_id and not corpus_id:
            agent = get_agent_by_id(agent_id)
            corpus_id = agent["corpus_id"]
        if not corpus_id:
            return jsonify({"error": "No corpus_id provided"}), 400
        
        result = remove_file(file_name, corpus_id)
        
        return jsonify({"message": result}), 200
        
    except Exception as e:
        logger.error(f"Error deleting RAG file {file_name}: {str(e)}")
        return jsonify({"error": str(e)}), 500
