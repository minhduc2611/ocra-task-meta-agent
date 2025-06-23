from typing import List, Dict, Any, Generator
import json
from libs.weaviate_lib import search_documents, insert_to_collection_in_batch, search_non_vector_collection
from data_classes.common_classes import AskRequest, Message
from agents.buddha_agent import generate_answer
from datetime import datetime, timedelta
from flask import Response, stream_with_context

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

def prepare_ask(body: AskRequest) -> tuple[Message, List[Dict[str, str]]]:
    errors = validate_ask(body)
    if errors:
        raise AskError(", ".join(errors), 400)
    user_messages = [msg for msg in body.messages if msg.role == "user"]
    last_user_message = user_messages[-1] if user_messages else None

    if not last_user_message:
        raise AskError("No user message found", 400)

    # Search for relevant documents
    relevant_docs = search_documents(last_user_message.content)
    print("relevant_docs")
    print(relevant_docs)
    print("--------------------------------")
    
    contexts = [
        {
            "title": doc["title"],
            "content": doc["content"],
            "description": doc["description"]
        }
        for doc in relevant_docs
    ]
    return last_user_message, contexts

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
        last_user_message, contexts = prepare_ask(body)
        # 2. generate answer
        answer = generate_answer(body.messages, contexts, body.options, body.language, body.model)
        # 3. save messages
        handle_insert_messages(body, last_user_message, answer)
        return answer
    except AskError:
        raise
    except Exception as e:
        raise AskError(str(e), 500)

def handle_ask_streaming(body: AskRequest, is_test: bool = False) -> Response:
    try:
        # 1. prepare
        last_user_message, contexts = prepare_ask(body)
        # 2. generate answer
        def generate():
            try:
                stream = generate_answer(
                    messages = body.messages, 
                    contexts = contexts, 
                    options = body.options, 
                    language = body.language, 
                    model = body.model, 
                    agent_id = body.agent_id
                )
                full_response = ""
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield content
                
                # After streaming is complete, save the messages
                user_time = datetime.now()
                
                # test agent dont save messages:
                if not is_test:
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
                            "content": full_response,
                            "role": "assistant",
                            "created_at": (user_time + timedelta(milliseconds=100)).strftime("%Y-%m-%dT%H:%M:%SZ")
                        }]
                    )
                yield ""
            except Exception as e:
                raise AskError(str(e), 500)

        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream'
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
