"""
Buddha-py: A Python application for Buddhist teachings and conversations
""" 

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from functools import wraps
from services.handle_auth import verify_jwt_token, AuthError

app = Flask(__name__)
CORS(app, expose_headers=["X-Total-Count", "X-Page-Size", "X-Page-Number", "X-Total-Pages"])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "No authorization header"}), 401

        try:
            # Extract token from "Bearer <token>"
            token = auth_header.split(" ")[1]
            payload = verify_jwt_token(token)
            g.user_id = payload['user_id']
            return f(*args, **kwargs)
        except AuthError as e:
            return jsonify({"error": e.message}), e.status_code
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 401

    return decorated_function

from controllers.auth_controller import *
from controllers.document_controller import *
from controllers.section_controller import *
from controllers.file_controller import *
from controllers.rag_file_controller import *
from controllers.rag_corpus_controller import *
from controllers.chat_controller import *
from controllers.agent_controller import *
from controllers.buddha_agent_controller import *
from controllers.user_controller import *
from controllers.agent_settings_controller import *
from controllers.message_controller import *
from controllers.fine_tuning_model_controller import *
