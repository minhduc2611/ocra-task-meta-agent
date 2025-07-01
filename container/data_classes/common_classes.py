from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum
import json
@dataclass
class StreamEvent:
    type: Literal["text", "end_of_stream"]
    data: str
    metadata: Optional[Dict[str, Any]] = None
    def to_dict_json(self):
        return f"{json.dumps({
            "type": self.type,
            "data": self.data,
            "metadata": self.metadata
        })}\n"

@dataclass
class Assistant:
    id: str
    name: str
    instructions: str
    model: str
    description: Optional[str] = None
    tools: Optional[List[dict]] = None
    
class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    
@dataclass
class Message:
    role: str
    content: str
    session_id: Optional[str] = None
    created_at: Optional[str] = None
    mode: Optional[str] = None
    feedback: Optional[str] = None
    edited_content: Optional[str] = None
    approval_status: Optional[ApprovalStatus] = None
    response_answer_id: Optional[str] = None

# enum for language
class Language(Enum):
    VI = "vi"
    EN = "en"

@dataclass
class AskRequest:
    messages: List[Message]
    session_id: Optional[str] = None
    model: Optional[str] = None
    language: Language = Language.VI
    options: Optional[Dict[str, Any]] = None
    agent_id: Optional[str] = None
    mode: Optional[str] = None

class AgentStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    
class AgentProvider(Enum):
    OPENAI = "openai"
    GOOGLE_VERTEX = "google_vertex"
    
@dataclass
class Agent:
    name: str
    description: str
    system_prompt: str
    tools: List[str]
    model: str
    temperature: float
    language: Language
    created_at: datetime
    updated_at: datetime
    author: str
    status: AgentStatus
    agent_type: str
    uuid: str

@dataclass
class Pagination:
    limit: int = 3
    offset: Optional[int] = None
    page: Optional[int] = None

@dataclass
class Section:
    uuid: Optional[str] = None
    language: Language = Language.VI
    messages: Optional[List[Message]] = None
    title: Optional[str] = None
    order: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    author: Optional[str] = None
    mode: Optional[str] = None

@dataclass
class SignInRequest:
    email: str
    password: str

@dataclass
class SignUpRequest:
    email: str
    password: str
    name: Optional[str] = None

@dataclass
class User:
    email: str
    password: str  # This will be hashed
    name: Optional[str] = None
    role: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class AuthRequest:
    email: str
    password: str
    name: Optional[str] = None
    role: Optional[str] = None
    
@dataclass
class Document:
    uuid: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: Optional[str] = None
    
@dataclass
class File:
    uuid: Optional[str] = None
    name: Optional[str] = None
    path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: Optional[str] = None
    
class UserRole(Enum):
    ADMIN = "admin"
    STUDENT = "student"
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    
class MessageType(Enum):
    AI_MESSAGE_CHUNK = "ai_message_chunk"
    AI_MESSAGE_FINAL = "ai_message_final"
    TOOL_MESSAGE = "tool_message"
    AGENT_MESSAGE = "agent_message"
    APPROVAL_REQUEST = "approval_request"
    TOOL_EXECUTION = "tool_execution"
    ERROR = "error"
    SYSTEM = "system"

@dataclass
class ApprovalRequest:
    """Structured approval request for frontend"""
    id: str
    tool_name: str
    tool_description: str
    arguments: Dict[str, Any]
    reasoning: str = ""
    timestamp: str = ""
    
    def to_dict(self):
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "tool_description": self.tool_description,
            "arguments": self.arguments,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp
        }


class AgentRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class FineTuningStatus(Enum):
    PENDING = "pending"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class FineTuningModel:
    uuid: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    base_model: Optional[str] = None
    status: Optional[FineTuningStatus] = None
    language: Optional[Language] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: Optional[str] = None
    training_data_path: Optional[str] = None
    validation_data_path: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    training_metrics: Optional[Dict[str, Any]] = None
    model_path: Optional[str] = None
    version: Optional[str] = None

@dataclass
class AppMessageResponse:
    type: MessageType
    content: str
    role: AgentRole
    approval_id: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_description: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
    requires_user_action: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self):
        return {
            "type": self.type.value,
            "content": self.content,
            "role": self.role.value,
            "approval_id": self.approval_id,
            "tool_name": self.tool_name,
            "tool_description": self.tool_description,
            "arguments": self.arguments,
            "reasoning": self.reasoning,
            "requires_user_action": self.requires_user_action,
            "metadata": self.metadata
        }