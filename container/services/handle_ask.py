from typing import List, Dict, Any, Generator, Optional
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
from constants.separators import ENDING_SEPARATOR, STARTING_SEPARATOR
from utils.string_utils import get_text_after_separator
from services.handle_sections import get_section_by_id, update_section
from agents.context_agent import generate_context
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
    return Agent(
        name=agent["name"],
        description=agent["description"],
        system_prompt=agent["system_prompt"],
        tools=agent["tools"],
        model=agent["model"],
        temperature=agent["temperature"],
        language=agent["language"],
        created_at=agent["created_at"],
        updated_at=agent["updated_at"],
        author=agent["author"],
        status=agent["status"],
        agent_type=agent["agent_type"],
        uuid=agent["uuid"],
        corpus_id=agent["corpus_id"],
        tags=agent["tags"],
        conversation_starters=agent["conversation_starters"],
    )

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
        if not body.agent_id:
            raise AskError("Agent ID is required", 400)
        last_user_message, previous_assistant_message = prepare_ask(body)
        contexts = get_contexts(last_user_message)
        agent = get_agent(body.agent_id or "", body.language)
        provider = check_model(agent.model)
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
                    context = contexts,
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

def format_response(chunk: StreamEvent, text_only: bool) -> str:
    if text_only:
        if ENDING_SEPARATOR in chunk.data:
            return chunk.data.split(ENDING_SEPARATOR)[1]
        else:
            return chunk.data
    else:
        return f"data: {chunk.to_dict_json()}"

def handle_ask_streaming(body: AskRequest, is_test: bool = False) -> Response:
    try:
        headers = {}
        # 1. prepare
        last_user_message, previous_assistant_message = prepare_ask(body)
        # 2. generate answer
        def generate():
            try:
                if not body.agent_id:
                    raise AskError("Agent ID is required", 400)
                if not body.options:
                    raise AskError("Options are required", 400)
                text_only = body.options.get('text_only', False)
                if not text_only:
                    text_only = False
                agent = get_agent(body.agent_id, body.language)
                if not agent:
                    raise AskError("Agent not found", 404)
                context: Optional[str] = None
                if body.session_id:
                    chat_section = get_section_by_id(body.session_id)
                    if chat_section:
                        context = chat_section.get("context", None)
                    else:
                        context = None
                provider = check_model(agent.model)
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
                            context = context if context else "" + ( "\n" + body.context if body.context else "" ),
                            stream = True
                        )
                
                full_response = ""
                thought_response = ""
                for chunk in stream: 
                    if chunk.type == "text":
                        content = chunk.data
                        full_response += content
                        yield format_response(chunk, text_only)
                    elif chunk.type == "thought":
                        thought_response += chunk.data
                        yield format_response(chunk, text_only)
                    elif chunk.type == "end_of_stream":
                        # response_content, response_thought = get_text_after_separator(full_response, ENDING_SEPARATOR)
                        
                        # After streaming is complete, save the messages
                        user_time = datetime.now()
                        # test agent dont save messages:
                        if not is_test:
                            response_answer_id = None
                            
                            # if body.context:
                            #     response_answer_id = insert_to_collection(
                            #         collection_name=COLLECTION_MESSAGES,
                            #         properties={
                            #             "session_id": body.session_id,
                            #             "content": last_user_message.content,
                            #             "role": last_user_message.role,
                            #             "created_at": (user_time + timedelta(milliseconds=2000)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            #             "agent_id": body.agent_id,
                            #         }
                            #     )
                                
                            #     if previous_assistant_message:
                            #         insert_to_collection(
                            #             collection_name=COLLECTION_MESSAGES,
                            #             properties={
                            #                 "session_id": body.session_id,
                            #                 "content": previous_assistant_message.content,
                            #                 "role": "assistant",
                            #                 "created_at": user_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            #                 "approval_status": ApprovalStatus.PENDING.value,
                            #                 "response_answer_id": str(response_answer_id),
                            #                 "agent_id": body.agent_id,
                            #             }
                            #         )
                            # else:
                            response_answer_id = insert_to_collection(
                                collection_name=COLLECTION_MESSAGES,
                                properties={
                                    "session_id": body.session_id,
                                    "content": full_response,
                                    "thought": thought_response,
                                    "role": "assistant",
                                    "created_at": (user_time + timedelta(milliseconds=2000)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    "agent_id": body.agent_id,
                                }
                            )
                            question_id = insert_to_collection(
                                collection_name=COLLECTION_MESSAGES,
                                properties={
                                    "session_id": body.session_id,
                                    "content": last_user_message.content,
                                    "role": last_user_message.role,
                                    "created_at": user_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    "response_answer_id": str(response_answer_id),
                                    "approval_status": ApprovalStatus.PENDING.value,
                                    "agent_id": body.agent_id,
                                }
                            )
                        chunk.metadata = {
                            "question_id": str(question_id),
                            "response_answer_id": str(response_answer_id),
                        }
                        yield format_response(chunk, text_only)
                        if body.session_id:
                            new_context = generate_context(last_user_message.content, context)
                            if new_context:
                                if chat_section:
                                    update_section(
                                        section_id=body.session_id,
                                        context=new_context,
                                    )
                                # else:
                                #     insert_to_collection(
                                #         collection_name=COLLECTION_CHATS,
                                #         properties={"context": new_context},
                                #     )
                
            except Exception as e:
                raise AskError(str(e), 500)

        return Response(
            stream_with_context(generate()),
            content_type='application/json',
            headers=headers
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
