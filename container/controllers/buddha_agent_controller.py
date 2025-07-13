from flask import request, jsonify, Response, g
import asyncio
from agents.buddha_agent_builder import (
    generate_buddha_agent_response,
    generate_buddha_agent_response_sync
)
from data_classes.common_classes import Message, Language, AppMessageResponse   
import json
from datetime import datetime
import logging
from __init__ import app, login_required

logger = logging.getLogger(__name__)


@app.route('/api/v1/buddha-agent-builder/chat', methods=['POST'])
@login_required
def meta_agent_chat_endpoint():
    """Chat with the buddha agent builder - streaming response"""
    try:
        body = request.json
        if not body:
            raise ValueError("Request body is required")
        messages = [Message(**msg) for msg in body.get('messages', [])]
            
        language = body.get('language', Language.EN)
        options = body.get('options', {})
        approval_response = body.get('approval_response', None)
        
        def generate():
            """Generate streaming response"""
            try:
                async def async_generate():
                    async for message in generate_buddha_agent_response(
                        messages=messages,
                        language=language,
                        options=options,
                        approval_response=approval_response
                    ):
                        try:
                            # Format as proper Server-Sent Events (SSE)
                            json_data = message.to_dict_json()
                            yield f"data: {json_data}"
                        except Exception as e:
                            # Fallback for any serialization issues
                            error_msg = {
                                "type": "error",
                                "content": f"Serialization error: {str(e)}",
                                "original_message": str(message),
                                "timestamp": datetime.now().isoformat()
                            }
                            yield f"data: {json.dumps(error_msg)}"
                    # Send end signal
                    yield f"data: {json.dumps({'type': 'end', 'timestamp': datetime.now().isoformat()})}"
                
                # Run the async generator in the current event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    async_gen = async_generate()
                    while True:
                        try:
                            message = loop.run_until_complete(async_gen.__anext__())
                            yield message
                        except StopAsyncIteration:
                            break
                finally:
                    loop.close()
                
            except Exception as e:
                error_data = {
                    "type": "error",
                    "content": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
        
    except Exception as e:
        logger.error(f"Error in buddha agent chat: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/buddha-agent-builder/chat/sync', methods=['POST'])
@login_required
def buddha_agent_builder_chat_sync_endpoint():
    """Chat with the buddha agent builder - synchronous response (backward compatibility)"""
    try:
        body = request.json
        if not body:
            raise ValueError("Request body is required")
        messages = [Message(**msg) for msg in body.get('messages', [])]
        language = body.get('language', Language.EN)
        options = body.get('options', {})
        
        response = generate_buddha_agent_response_sync(
            messages=messages,
            language=language,
            options=options
        )
        
        return jsonify({"response": response}), 200
    except Exception as e:
        logger.error(f"Error in buddha agent chat sync: {str(e)}")
        return jsonify({"error": str(e)}), 500 