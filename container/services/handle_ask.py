from typing import List, Dict, Any, Generator
import json
from libs.weaviate_lib import search_documents, insert_to_collection_in_batch, insert_to_collection, COLLECTION_MESSAGES
from data_classes.common_classes import AskRequest, Message, ApprovalStatus, Agent, Language, AgentProvider, StreamEvent
from agents.buddha_agent import generate_answer
from datetime import datetime, timedelta
from flask import Response, stream_with_context
from services.handle_agent import get_agent_by_id
from agents.buddha_agent import get_default_buddha_agent
from libs.open_ai import generate_openai_answer
from libs.google_vertex import generate_gemini_response
from libs.langchain import check_model
class AskError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def validate_ask(body: AskRequest) -> List[str]:
    errors: List[str] = []
    if not body.messages or not isinstance(body.messages, list):
        errors.append("messages is required")
    if not body.session_id:
        errors.append("session_id is required")
    return errors

def prepare_ask(body: AskRequest) -> tuple[Message, Message]:
    errors = validate_ask(body)
    if errors:
        raise AskError(", ".join(errors), 400)
    user_messages = [msg for msg in body.messages if msg.role == "user"]
    last_user_message = user_messages[-1] if user_messages else None
    previous_assistant_message = body.messages[-2] if len(body.messages) > 1 else None
    if not last_user_message:
        raise AskError("No user message found", 400)

    return last_user_message, previous_assistant_message

def get_agent(agent_id: str, language: Language) -> Agent:
    agent = get_agent_by_id(agent_id)
    if not agent or "error" in agent:
        return get_default_buddha_agent(language)
    return agent

def handle_insert_messages(body: AskRequest, last_user_message: Message, answer: str):
    user_time = datetime.now()
    # Insert messages to the database
    insert_to_collection_in_batch(
        collection_name="Messages",
        properties=[{
            "session_id": body.session_id,
            "content": last_user_message.content,
            "role": last_user_message.role,
            "created_at": user_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        {
            "session_id": body.session_id,
            "content": answer,
            "role": "assistant",
            "created_at": (user_time + timedelta(milliseconds=100)).strftime("%Y-%m-%dT%H:%M:%SZ")
        }]
    )
    
def handle_ask_non_streaming(body: AskRequest) -> str:
    try:
        # 1. prepare
        last_user_message, previous_assistant_message = prepare_ask(body)
        contexts = get_contexts(last_user_message)
        agent = get_agent(body.agent_id, body.language)
        provider = check_model(agent["model"])
        # 2. generate answer
        match provider.value:
            case AgentProvider.OPENAI.value:
                contexts = get_contexts(last_user_message)
                
                response: str = generate_openai_answer(
                    agent = agent,
                    messages = body.messages, 
                    contexts = contexts, 
                    stream = False
                )
            case AgentProvider.GOOGLE_VERTEX.value:
                response: str = generate_gemini_response(
                    agent = agent,
                    messages = body.messages, 
                    stream = False
                )
        # answer = generate_answer(body.messages, contexts, body.options, body.language, body.model)
        # 3. save messages
        # handle_insert_messages(body, last_user_message, answer)
        return response
    except AskError:
        raise
    except Exception as e:
        raise AskError(str(e), 500)

def get_contexts(last_user_message: Message) -> List[Dict[str, str]]:
    relevant_docs = search_documents(last_user_message.content)
                        
    contexts = [
        {
            "title": doc["title"],
            "content": doc["content"],
            "description": doc["description"]
        }
        for doc in relevant_docs
    ]
    return contexts

def handle_ask_streaming(body: AskRequest, is_test: bool = False) -> Response:
    try:
        # 1. prepare
        last_user_message, previous_assistant_message = prepare_ask(body)
        # 2. generate answer
        def generate():
            try:
                agent = get_agent(body.agent_id, body.language)
                provider = check_model(agent["model"])
                match provider.value:
                    case AgentProvider.OPENAI.value:
                        contexts = get_contexts(last_user_message)
                        
                        stream: Generator[StreamEvent, None, None] = generate_openai_answer(
                            agent = agent,
                            messages = body.messages, 
                            contexts = contexts, 
                            stream = True
                        )
                    case AgentProvider.GOOGLE_VERTEX.value:
                        stream: Generator[StreamEvent, None, None] = generate_gemini_response(
                            agent = agent,
                            messages = body.messages, 
                            stream = True
                        )
                full_response = ""
                for chunk in stream: 
                    if chunk.type == "text":
                        content = chunk.data
                        full_response += content
                        yield chunk.to_dict_json()
                    elif chunk.type == "end_of_stream":
                        yield chunk.to_dict_json()
                
                # After streaming is complete, save the messages
                user_time = datetime.now()
                # test agent dont save messages:
                if not is_test:
                    if body.mode == "quiz":
                        response_answer_id = insert_to_collection(
                            collection_name=COLLECTION_MESSAGES,
                            properties={
                                "session_id": body.session_id,
                                "content": last_user_message.content,
                                "role": last_user_message.role,
                                "created_at": (user_time + timedelta(milliseconds=2000)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "mode": body.mode,
                            }
                        )
                        
                        if previous_assistant_message:
                            insert_to_collection(
                                collection_name=COLLECTION_MESSAGES,
                                properties={
                                    "session_id": body.session_id,
                                    "content": previous_assistant_message.content,
                                    "role": "assistant",
                                    "mode": body.mode,
                                    "created_at": user_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    "approval_status": ApprovalStatus.PENDING.value,
                                    "response_answer_id": str(response_answer_id)
                                }
                            )
                            
                    else:
                        response_answer_id = insert_to_collection(
                            collection_name=COLLECTION_MESSAGES,
                            properties={
                                "session_id": body.session_id,
                                "content": full_response,
                                "role": "assistant",
                                "created_at": (user_time + timedelta(milliseconds=2000)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "mode": body.mode
                            }
                        )
                        insert_to_collection(
                            collection_name=COLLECTION_MESSAGES,
                            properties={
                                "session_id": body.session_id,
                                "content": last_user_message.content,
                                "role": last_user_message.role,
                                "created_at": user_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "mode": body.mode,
                                "response_answer_id": str(response_answer_id),
                                "approval_status": ApprovalStatus.PENDING.value
                            }
                        )
                    
            except Exception as e:
                raise AskError(str(e), 500)

        return Response(
            stream_with_context(generate()),
            content_type='application/json'
        )
    except AskError as e:
        return Response(
            response=json.dumps({"error": e.message}),
            status=e.status_code,
            mimetype="application/json"
        )
    except Exception as e:
        return Response(
            response=json.dumps({"error": str(e)}),
            status=500,
            mimetype="application/json"
        )
