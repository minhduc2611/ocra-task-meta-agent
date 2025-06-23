from flask import request, jsonify, g
from services.handle_auth import sign_in, sign_up, verify_jwt_token, AuthError, blacklist_token
from data_classes.common_classes import AuthRequest
import logging
from __init__ import app, login_required

logger = logging.getLogger(__name__)

@app.route('/api/v1/sign-in', methods=['POST'])
def sign_in_endpoint():
    """Sign in endpoint"""
    try:
        body = request.json
        auth_request = AuthRequest(**body)
        result = sign_in(auth_request)
        return jsonify(result), 200
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error signing in: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sign-up', methods=['POST'])
def sign_up_endpoint():
    """Sign up endpoint"""
    try:
        body = request.json
        auth_request = AuthRequest(**body)
        result = sign_up(auth_request)
        return jsonify(result), 201
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error signing up: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/logout', methods=['POST'])
@login_required
def logout_endpoint():
    """Logout"""
    try:
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(" ")[1]
        
        # Blacklist the token
        success = blacklist_token(token, g.user_id)
        
        if not success:
            return jsonify({"error": "Failed to logout"}), 500
            
        return jsonify({"status": "success", "message": "Successfully logged out"}), 200
        
    except Exception as e:
        logger.error(f"Error logging out: {str(e)}")
        return jsonify({"error": str(e)}), 500 
