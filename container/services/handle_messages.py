from data_classes.common_classes import Message
from typing import List
from libs.weaviate_lib import search_vector_collection, search_non_vector_collection, update_collection_object, delete_collection_object, get_object_by_id, COLLECTION_MESSAGES
from typing import Dict, Any
from weaviate.collections.classes.filters import Filter
from weaviate.collections.classes.grpc import Sort
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MessageError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def handle_chat(session_id: str) -> Dict[str, Any]:
    # Get messages from the database
    messages = get_messages(session_id, 10)
    # Return the relevant messages
    return messages

def get_relevant_messages(session_id: str, limit: int = 10) -> List[Message]:
    # Get messages from the database
    filters = Filter.by_property("session_id").equal(session_id)
    messages = search_vector_collection(
        collection_name="Messages",
        filters=filters,
        limit=limit
    )
    # Return the relevant messages
    return messages


def get_messages(session_id: str, limit: int = 10) -> List[Message]:
    # Get messages from the database
    filters = Filter.by_property("session_id").equal(session_id)
    messages = search_non_vector_collection(
        collection_name="Messages",
        filters=filters,
        limit=limit,
        properties=["content", "role", "created_at"],
        sort=Sort.by_property("created_at", ascending=True).by_property("role", ascending=False)
    )
    # Get relevant messages from the database
    # relevant_messages = get_relevant_messages(messages, limit)
    # Return the relevant messages
    return messages

def get_messages_list(
    limit: int = 100, 
    offset: int = 0, 
    session_id: str = None,
    role: str = None,
    mode: str = None,
    search: str = None,
    include_related: bool = True
) -> Dict[str, Any]:
    """
    Get a list of messages with pagination and filtering.
    
    Args:
        limit: Maximum number of messages to return (default: 100, max: 1000)
        offset: Number of messages to skip (default: 0)
        session_id: Filter by session ID
        role: Filter by role (user, assistant, system)
        mode: Filter by mode
        search: Search in message content
        include_related: Whether to include related messages (default: False for performance)
    
    Returns:
        Dictionary containing messages and pagination info
    """
    try:
        # Ensure reasonable limits
        limit = min(limit, 1000)  # Max 1000 messages per request
        offset = max(offset, 0)
        
        # Build filters
        filters = None
        
        if session_id:
            filters = Filter.by_property("session_id").equal(session_id)
        
        if role:
            role_filter = Filter.by_property("role").equal(role)
            if filters:
                filters = filters & role_filter
            else:
                filters = role_filter
        
        if mode:
            mode_filter = (Filter.by_property("mode").equal(mode) & Filter.by_property("response_answer_id").is_none(False))
            if filters:
                filters = filters & mode_filter
            else:
                filters = mode_filter
        
        # Get messages
        if search:
            # Use vector search for content search
            messages = search_vector_collection(
                collection_name=COLLECTION_MESSAGES,
                query=search,
                limit=limit,
                filters=filters,
                offset=offset,
                properties=["content", "role", "created_at", "session_id", "mode", "feedback", "response_answer_id", "approval_status", "edited_content"]
            )
        else:
            # Use non-vector search for regular queries
            messages = search_non_vector_collection(
                collection_name=COLLECTION_MESSAGES,
                limit=limit,
                filters=filters,
                offset=offset,
                properties=["content", "role", "created_at", "session_id", "mode", "feedback", "response_answer_id", "approval_status", "edited_content"],
                sort=Sort.by_property("created_at", ascending=False)
            )
        
        # Attach related messages only if requested
        if include_related:
            messages_with_related = attach_related_messages(messages)
        else:
            messages_with_related = messages

        return {
            "messages": messages_with_related,
            "limit": limit,
            "offset": offset,
            "count": len(messages)
        }
        
    except Exception as e:
        return {"error": f"Failed to get messages: {str(e)}"}


def attach_related_messages(messages):
    """
    Attach related messages using batch queries for better performance.
    """
    # Collect all unique response_answer_ids
    response_ids = set()
    for message in messages:
        if message.get("response_answer_id"):
            response_ids.add(str(message["response_answer_id"]))
    
    # Batch fetch all related messages
    related_messages = {}
    if response_ids:
        try:
            # Use batch query instead of individual queries
            filters = Filter.by_id().contains_any(list(response_ids))
            related_results = search_non_vector_collection(
                collection_name=COLLECTION_MESSAGES,
                filters=filters,
                limit=len(response_ids),
                properties=["content", "role", "created_at", "session_id", "mode", "feedback", "response_answer_id", "approval_status", "edited_content"]
            )
            for msg in related_results:
                related_messages[msg["uuid"]] = msg
        except Exception as e:
            # Log error but don't fail the entire request
            logger.error(f"Failed to fetch related messages: {str(e)}")
    
    # Attach related messages
    for message in messages:
        response_id = str(message.get("response_answer_id"))
        if response_id and response_id in related_messages:
            message["related_message"] = related_messages[response_id]
        else:
            message["related_message"] = None
    
    return messages

def get_message_by_id(message_id: str) -> Dict[str, Any]:
    """
    Get a single message by ID.
    
    Args:
        message_id: The UUID of the message
    
    Returns:
        Dictionary containing the message data or error
    """
    try:
        message = get_object_by_id(COLLECTION_MESSAGES, message_id)
        if not message:
            return {"error": "Message not found"}
        
        return {"message": message}
    except (IndexError, Exception) as e:
        if isinstance(e, IndexError):
            return {"error": "Message not found"}
        return {"error": f"Failed to get message: {str(e)}"}

def update_message(message_id: str, **kwargs) -> Dict[str, Any]:
    """
    Update an existing message.
    
    Args:
        message_id: The UUID of the message
        **kwargs: Fields to update (content, role, mode, feedback)
    
    Returns:
        Updated message data or error
    """
    try:
        # Get current message to verify it exists
        current_message = get_message_by_id(message_id)
        if "error" in current_message:
            return current_message
        
        # Update fields
        update_data = {}
        allowed_fields = ["content", "role", "mode", "feedback", "approval_status", "edited_content"]
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                update_data[key] = value
        
        if not update_data:
            return {"error": "No valid fields to update"}
        
        # Update in Weaviate
        success = update_collection_object(COLLECTION_MESSAGES, message_id, update_data)
        
        if success:
            # Get updated message
            updated_message = get_message_by_id(message_id)
            return {
                "message": "Message updated successfully",
                "updated_fields": list(update_data.keys()),
                "data": updated_message.get("message")
            }
        else:
            return {"error": "Failed to update message"}
    except Exception as e:
        return {"error": f"Failed to update message: {str(e)}"}

def delete_message(message_id: str) -> Dict[str, Any]:
    """
    Delete a message by ID.
    
    Args:
        message_id: The UUID of the message to delete
    
    Returns:
        Success/error message
    """
    try:
        # Get current message to verify it exists
        current_message = get_message_by_id(message_id)
        if "error" in current_message:
            return current_message
        
        # Delete from Weaviate
        success = delete_collection_object(COLLECTION_MESSAGES, message_id)
        
        if success:
            return {"message": f"Message '{message_id}' deleted successfully"}
        else:
            return {"error": "Failed to delete message"}
    except Exception as e:
        return {"error": f"Failed to delete message: {str(e)}"}


