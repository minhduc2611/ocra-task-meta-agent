from flask import request, jsonify, Response, g
from services.handle_ask import handle_ask_streaming, handle_ask_non_streaming, AskError
from services.handle_messages import handle_chat
from data_classes.common_classes import AskRequest, Message, Language
import json
import logging
from __init__ import app, login_required
logger = logging.getLogger(__name__)

@app.route('/api/v1/chat/<session_id>/ask', methods=['POST'])
@login_required
def ask_endpoint(session_id):
    try:
        # 1. prepare payload
        body = request.json
        messages = [Message(**msg) for msg in body.get('messages', [])]
        ask_request = AskRequest(
            messages=messages,
            session_id=session_id,
            language=body.get('language', Language.VI),
            options=body.get('options'),
            model=body.get('model', 'gpt-4o'),
            agent_id=body.get('agent_id'),
            context=body.get('context'),
        )
        # session_id
        if not session_id:
            raise AskError("Session ID is required")
        # 2. handle request
        is_streaming = ask_request.options and ask_request.options.get("stream", False)
        try:
            if is_streaming:
                return handle_ask_streaming(ask_request, False)
            else:
                results = handle_ask_non_streaming(ask_request)
                return jsonify(results), 200
        except AskError as e:
            return Response(
                response=json.dumps({"error": e.message}),
                status=e.status_code,
                mimetype="application/json"
            )
    except Exception as e:
        logger.error(f"Error processing ask: {str(e)}")
        return Response(
            response=json.dumps({"error": str(e)}),
            status=500,
            mimetype="application/json"
        )

@app.route('/api/v1/sections/<section_id>/messages', methods=['GET'])
@login_required
def chat_endpoint(section_id):
    try:
        results = handle_chat(section_id)
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        return jsonify({"error": str(e)}), 500 