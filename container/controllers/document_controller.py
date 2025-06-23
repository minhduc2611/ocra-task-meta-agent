from flask import request, jsonify, g
from services.upload_file import upload_file, get_documents, create_document, update_document, delete_document, get_document_by_id
from data_classes.common_classes import Document
import logging
from __init__ import app, login_required
logger = logging.getLogger(__name__)


@app.route('/api/v1/upload-documents', methods=['POST'])
@login_required
def process_pdf_endpoint():
    """Endpoint to process a PDF file and return semantic chunks"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        # 1. prepare payload
        files = request.files.getlist('files')
        description = request.form.get('description')
        author = g.user_id
        # 2. handle request
        results, failed_objects = upload_file(files, description, author)

        # 3. return results
        return jsonify({
            "status": "success" if failed_objects == 0 else "failed",
            "description": description,
            "results": results,
            "failed_objects": failed_objects
        }), 200

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/documents', methods=['GET'])
@login_required
def get_documents_endpoint():
    """Get all documents"""
    try:
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        documents, total_count = get_documents(limit, offset)
        
        # Calculate pagination info
        page_number = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
        
        response = jsonify(documents)
        response.headers['X-Total-Count'] = str(total_count)
        response.headers['X-Page-Size'] = str(limit)
        response.headers['X-Page-Number'] = str(page_number)
        response.headers['X-Total-Pages'] = str(total_pages)
        return response, 200
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/documents/<document_id>', methods=['GET'])
@login_required
def get_document_endpoint(document_id):
    """Get a document by ID"""
    try:
        document = get_document_by_id(document_id) 
        return jsonify(document), 200
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/documents', methods=['POST'])
@login_required
def create_document_endpoint():
    """Create a new document"""
    try:
        body = request.json
        document = Document(**body) 
        document.author = g.user_id
        document = create_document(document)
        return jsonify(document), 201
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/v1/documents/<document_id>', methods=['PUT'])
@login_required
def update_document_endpoint(document_id):
    """Update a document"""
    try:
        body = request.json
        document = Document(**body)
        document.author = g.user_id
        document = update_document(document_id, document)
        return jsonify(document), 200
    except Exception as e:
        logger.error(f"Error updating document: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/v1/documents/<document_id>', methods=['DELETE'])
@login_required
def delete_document_endpoint(document_id):
    """Delete a document"""
    try:
        success = delete_document(document_id)
        if not success:
            return jsonify({"error": "Document not found"}), 404
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        return jsonify({"error": str(e)}), 500 