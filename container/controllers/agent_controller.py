from flask import request, jsonify, g, Response, stream_with_context
from services.handle_agent import (
    create_agent,
    list_agents,
    get_agent_by_id,
    update_agent,
    delete_agent,
    search_agents,
    test_agent
)
from services.handle_ask import handle_ask_streaming, handle_ask_non_streaming, AskError
from services.handle_rag import handle_upload_file
import json
import logging
import uuid
import asyncio
from data_classes.common_classes import AskRequest, Message, Language

from __init__ import app, login_required

logger = logging.getLogger(__name__)

@app.route('/api/v1/agents', methods=['POST'])
@login_required
def create_agent_endpoint():
    """Create a new agent"""
    try:
        body = request.json
        name = body.get('name')
        description = body.get('description')
        system_prompt = body.get('system_prompt')
        tools = body.get('tools', [])
        model = body.get('model', 'gpt-4o-mini')
        temperature = body.get('temperature', 0)
        language = body.get('language', Language.VI.value)
        result = create_agent(
            name=name,
            description=description,
            system_prompt=system_prompt,
            tools=tools,
            model=model,
            temperature=temperature,
            author=g.user_id,
            language=language
        )
        
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents', methods=['GET'])
@login_required
def list_agents_endpoint():
    """List all agents for the current user"""
    try:
        limit = int(request.args.get('limit', 10))
        language = request.args.get('language')
        if not language:
            agents = list_agents(limit=limit)
        else:
            agents = list_agents(limit=limit, language=language)
        # agents = list_assistants()
        return jsonify(agents), 200
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/<agent_id>', methods=['GET'])
@login_required
def get_agent_endpoint(agent_id):
    """Get a specific agent"""
    try:
        agent = get_agent_by_id(agent_id)
        if "error" in agent:
            return jsonify(agent), 404
        return jsonify(agent), 200
    except Exception as e:
        logger.error(f"Error getting agent: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/<agent_id>', methods=['PUT'])
@login_required
def update_agent_endpoint(agent_id):
    """Update an agent"""
    try:
        body = request.json
        result = update_agent(agent_id, **body)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error updating agent: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/<agent_id>', methods=['DELETE'])
@login_required
def delete_agent_endpoint(agent_id):
    """Delete an agent"""
    try:
        result = delete_agent(agent_id)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error deleting agent: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/search', methods=['GET'])
@login_required
def search_agents_endpoint():
    """Search for agents"""
    try:
        query = request.args.get('query', '')
        limit = int(request.args.get('limit', 5))
        agents = search_agents(query=query, limit=limit)
        return jsonify(agents), 200
    except Exception as e:
        logger.error(f"Error searching agents: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/agents/<agent_id>/test', methods=['POST'])
@login_required
def test_agent_endpoint(agent_id):
    """Test an agent with sample input"""
    try:
        body = request.json
        test_input = body.get('test_input', 'Hello, how can you help me?')
        
        result = test_agent(agent_id=agent_id, test_input=test_input)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error testing agent: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/<agent_id>/chat', methods=['POST'])
@login_required
def chat_with_agent_endpoint(agent_id):
    """Chat with an agent, optionally with streaming"""
    try:
        body = request.json
        if not body:
            return jsonify({"error": "Request body is required"}), 400
        session_id = str(uuid.uuid4())
        messages = [Message(**msg) for msg in body.get('messages', [])]
        ask_request = AskRequest(
            messages=messages,
            session_id=session_id,
            language=body.get('language', Language.VI),
            options=body.get('options'),
            model=body.get('model', 'gpt-4o'),
            agent_id=agent_id
        )
        
        if not agent_id:
            return {"error": "Agent ID is required"}
        
        is_streaming = ask_request.options and ask_request.options.get("stream", False)
        
        try:
            if is_streaming:
                return handle_ask_streaming(ask_request, True)
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
        logger.error(f"Error chatting with agent: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/chat', methods=['POST'])
@login_required
def chat_with_agent_endpoint_with_api_key():
    """Chat with an agent, optionally with streaming"""
    try:
        body = request.json
        if not body:
            return jsonify({"error": "Request body is required"}), 400
        session_id = str(uuid.uuid4())
        messages = [Message(**msg) for msg in body.get('messages', [])]
        ask_request = AskRequest(
            messages=messages,
            session_id=session_id,
            language=body.get('language', Language.VI),
            options=body.get('options'),
            model=body.get('model', 'gpt-4o'),
            agent_id=body.get('agent_id'),
        )
        
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
        logger.error(f"Error chatting with agent: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/agents/<agent_id>/upload', methods=['POST'])
@login_required
def upload_file_endpoint(agent_id):
    """Upload a file to an agent with streaming progress updates"""
    try:
        files = request.files.getlist('files')
        
        if not files:
            return jsonify({
                "error": "No files provided",
                "status": "error"
            }), 400
        
        def generate():
            try:
                # Create new event loop for this thread if needed
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Run the async generator
                async def async_generate():
                    async for update in handle_upload_file(files, agent_id):
                        yield f"{json.dumps(update)}\n\n"
                
                # Convert async generator to sync generator
                async_gen = async_generate()
                while True:
                    try:
                        result = loop.run_until_complete(async_gen.__anext__())
                        yield result
                    except StopAsyncIteration:
                        break
                        
            except Exception as e:
                error_response = {
                    "error": str(e),
                    "status": "error",
                    "message": f"Upload failed: {str(e)}"
                }
                yield f"{json.dumps(error_response)}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
            
    except Exception as e:      
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({
            "error": str(e),
            "status": "error",
            "message": f"Upload failed: {str(e)}"
        }), 500