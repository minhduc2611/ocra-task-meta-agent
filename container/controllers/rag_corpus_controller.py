from flask import request, jsonify, g
from libs.google_vertex import add_corpus, get_corpus, delete_corpus, list_corpora
from __init__ import app, login_required
import logging

logger = logging.getLogger(__name__)

@app.route('/api/v1/rag/corpus', methods=['GET'])
@login_required
def list_corpora_endpoint():
    """List all RAG corpora"""
    try:
        corpora = list_corpora()
        
        # Convert RagCorpus objects to dictionaries for JSON serialization
        corpus_list = []
        for corpus in corpora:
            corpus_dict = {
                "name": corpus.name,
                "display_name": corpus.display_name,
                "create_time": corpus.create_time.isoformat() if corpus.create_time else None,
                "id": corpus.name.split("/")[-1]
            }
            corpus_list.append(corpus_dict)
        
        return jsonify({"corpora": corpus_list}), 200
        
    except Exception as e:
        logger.error(f"Error listing RAG corpora: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/rag/corpus', methods=['POST'])
@login_required
def create_corpus():
    """Create a new RAG corpus"""
    try:
        body = request.json
        if not body.get('display_name'):
            return jsonify({"error": "display_name is required"}), 400
        corpus = add_corpus(
            display_name=body.get('display_name')
        )
        return jsonify({
            "message": f"Corpus '{corpus.display_name}' created successfully",
            "corpus": {
                "name": corpus.name,
                "display_name": corpus.display_name,
                "id": corpus.name.split("/")[-1],
                "backend_config": corpus.backend_config,
                "vertex_ai_search_config": corpus.vertex_ai_search_config,
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating RAG corpus: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/rag/corpus/<corpus_id>', methods=['GET'])
@login_required
def get_corpus_info(corpus_id):
    """Get information about a specific RAG corpus"""
    try:
        corpus = get_corpus(corpus_id)
        
        return jsonify({
            "corpus": {
                "name": corpus.name,
                "display_name": corpus.display_name,
                "create_time": corpus.create_time.isoformat() if corpus.create_time else None,
                "id": corpus.name.split("/")[-1]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting RAG corpus {corpus_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/rag/corpus/<corpus_id>', methods=['DELETE'])
@login_required
def delete_corpus_endpoint(corpus_id):
    """Delete a RAG corpus"""
    try:
        result = delete_corpus(corpus_id)
        
        return jsonify({"message": result}), 200
        
    except Exception as e:
        logger.error(f"Error deleting RAG corpus {corpus_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500 