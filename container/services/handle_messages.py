from data_classes.common_classes import Message
from typing import List, Optional
from libs.weaviate_lib import search_vector_collection, search_non_vector_collection, update_collection_object, delete_collection_object, get_object_by_id, COLLECTION_MESSAGES, insert_to_collection_in_batch, COLLECTION_DOCUMENTS
from typing import Dict, Any
from weaviate.collections.classes.filters import Filter
from weaviate.collections.classes.grpc import Sort
from datetime import datetime
import logging
from data_classes.common_classes import ApprovalStatus
from libs.weaviate_lib import insert_to_collection
from libs.jsonl_converter import convert_json_to_jsonl, save_jsonl_to_file, convert_messages_to_fine_tune_format, validate_fine_tune_data
from google.cloud import aiplatform
from google.cloud.aiplatform_v1.types import training_pipeline
from google.cloud.aiplatform_v1.services.pipeline_service import PipelineServiceClient
from google.cloud.aiplatform_v1.types import pipeline_service
import uuid
from libs.google_vertex import upload_to_gcs, create_fine_tuning_job

logger = logging.getLogger(__name__)

class MessageError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def handle_chat(session_id: str) -> Dict[str, Any]:
    # Get messages from the database
    messages = get_messages(session_id, 30)
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
        properties=["content", "role", "created_at", "thought", "like_user_ids", "dislike_user_ids", "feedback", "agent_id"],
        sort=Sort.by_property("created_at", ascending=True).by_property("role", ascending=False)
    )
    # turn joined likes into array dict
    for message in messages:
        if message.get("like_user_ids"):
            message["like_user_ids"] = message["like_user_ids"].split(",")
        if message.get("dislike_user_ids"):
            message["dislike_user_ids"] = message["dislike_user_ids"].split(",")
        
    return messages

def get_messages_list(
    limit: int = 100, 
    offset: int = 0, 
    session_id: Optional[str] = None,
    role: Optional[str] = None,
    agent_id: Optional[str] = None,
    search: Optional[str] = None,
    include_related: bool = True,
    approval_status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a list of messages with pagination and filtering.
    
    Args:
        limit: Maximum number of messages to return (default: 100, max: 1000)
        offset: Number of messages to skip (default: 0)
        session_id: Filter by session ID
        role: Filter by role (user, assistant, system)
        agent_id: Filter by agent ID
        search: Search in message content
        include_related: Whether to include related messages (default: False for performance)
        approval_status: Filter by approval status (APPROVED, PENDING, REJECTED)
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
        
        if agent_id:
            agent_filter = Filter.by_property("agent_id").equal(agent_id)
            if filters:
                filters = filters & agent_filter
            else:
                filters = agent_filter
                
        if include_related:
            if filters:
                filters = filters & Filter.by_property("response_answer_id").is_none(False)
            else:
                filters = Filter.by_property("response_answer_id").is_none(False)
        
        if approval_status: 
            approval_status_filter = Filter.by_property("approval_status").equal(approval_status)
            if filters:
                filters = filters & approval_status_filter
            else:
                filters = approval_status_filter
                
        # Get messages
        if search:
            # Use vector search for content search
            messages = search_vector_collection(
                collection_name=COLLECTION_MESSAGES,
                query=search,
                limit=limit,
                filters=filters,
                offset=offset,
                properties=["content", "role", "created_at", "session_id", "agent_id", "feedback", "response_answer_id", "approval_status", "edited_content", "thought", "like_user_ids", "dislike_user_ids"]
            )
        else:
            # Use non-vector search for regular queries
            messages = search_non_vector_collection(
                collection_name=COLLECTION_MESSAGES,
                limit=limit,
                filters=filters,
                offset=offset,
                properties=["content", "role", "created_at", "session_id", "agent_id", "feedback", "response_answer_id", "approval_status", "edited_content", "thought", "like_user_ids", "dislike_user_ids"],
                sort=Sort.by_property("created_at", ascending=False)
            )
        
        # Attach related messages only if requested
        if include_related:
            messages_with_related = attach_related_messages(messages)
        else:
            messages_with_related = messages

        # turn joined likes into array dict
        for message in messages_with_related:
            if message['related_message'] and message['related_message'].get("like_user_ids"):
                message["related_message"]["like_user_ids"] = message["related_message"]["like_user_ids"].split(",")
            if message['related_message'] and message['related_message'].get("dislike_user_ids"):
                message["related_message"]["dislike_user_ids"] = message["related_message"]["dislike_user_ids"].split(",")
        
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
                limit=len(response_ids) + 3,
                properties=["content", "role", "created_at", "session_id", "agent_id", "feedback", "response_answer_id", "approval_status", "edited_content", "thought", "like_user_ids", "dislike_user_ids"]
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
        allowed_fields = ["content", "role", "mode", "feedback", "approval_status", "edited_content", "thought", "response_answer_id", "like_user_ids", "dislike_user_ids"]
        
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

def save_q_and_a_pairs_to_system(q_and_a_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Save Q&A pairs to the system as documents.
    
    Args:
        q_and_a_pairs: List of dictionaries containing 'question' and 'answer' keys
    
    Returns:
        Dictionary containing success/error message and saved document IDs
    """
    try:
        if not q_and_a_pairs:
            return {"error": "No Q&A pairs provided"}
        
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        for i, pair in enumerate(q_and_a_pairs):
            if not isinstance(pair, dict) or 'question' not in pair or 'answer' not in pair:
                return {"error": f"Invalid Q&A pair format at index {i}"}
            
            question = pair['question']
            answer = pair['answer']
            response_answer_id = insert_to_collection(
                collection_name=COLLECTION_MESSAGES,
                properties={
                    "content": answer,
                    "role": "user",
                    "created_at": current_time,
                    "mode": "fine-tune"
                }
            )
            insert_to_collection(
                collection_name=COLLECTION_MESSAGES,
                properties={
                    "content": question,
                    "role": 'assistant',
                    "created_at": current_time,
                    "mode": "fine-tune",
                    "response_answer_id": str(response_answer_id),
                    "approval_status": ApprovalStatus.APPROVED.value
                }
            )
        
        return {
            "message": f"Successfully saved {len(q_and_a_pairs)} Q&A pairs to system",
            "saved_count": len(q_and_a_pairs),
        }
        
    except Exception as e:
        logger.error(f"Error saving Q&A pairs to system: {str(e)}")
        return {"error": f"Failed to save Q&A pairs: {str(e)}"}


def fine_tune_messages(messages: List[Dict[str, Any]], base_model: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """
    Fine tune messages using Google Vertex AI.
    
    Args:
        messages: List of message dictionaries with the structure:
                 {
                   "content": "message content",
                   "role": "user" or "assistant",
                   "session_id": "session identifier",
                   "related_message": {
                     "content": "related message content",
                     "role": "user" or "assistant"
                   }
                 }
    
    Returns:
        Dictionary containing fine-tuning job information
    """
    try:
        if not messages:
            return {"error": "No messages provided for fine-tuning"}
        
        # Convert messages to the required format for Vertex AI fine-tuning
        fine_tune_data = convert_messages_to_fine_tune_format(messages)
        
        if not fine_tune_data:
            return {"error": "No valid conversation pairs found for fine-tuning"}
        
        logger.info(f"Prepared {len(fine_tune_data)} conversation pairs for fine-tuning")
        
        # Validate the data format
        validate_fine_tune_data(fine_tune_data)
        
        # Convert to JSONL format
        jsonl_content = convert_json_to_jsonl(fine_tune_data)
        
        # Save JSONL content to a temporary file
        temp_file_path = save_jsonl_to_file(jsonl_content)
        
        # Upload JSONL file to GCS
        training_data_path = upload_to_gcs(temp_file_path, "buddha-ai-bucket")
        
        # Create fine-tuning job
        job_info = create_fine_tuning_job(
            training_data_path=training_data_path,
            base_model=base_model,
            model_display_name=f"fine_tuned_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            hyperparameters={
                "epoch_count": 3,
                "batch_size": 4,
                "learning_rate": 0.0001
            }
        )
        
        return {
            "message": "Fine-tuning job created successfully",
            "job_info": job_info,
            "training_pairs_count": len(fine_tune_data),
            "training_data_path": training_data_path
        }
        
    except Exception as e:
        logger.error(f"Error fine tuning messages: {str(e)}")
        return {"error": f"Failed to fine tune messages: {str(e)}"}


def like_message(message_id: str, user_id: str) -> Dict[str, Any]:
    """
    Like a message by adding user_id to like_user_ids and removing from dislike_user_ids.
    
    Args:
        message_id: The UUID of the message
        user_id: The UUID of the user liking the message
    
    Returns:
        Success/error message with updated message data
    """
    try:
        # Get current message to verify it exists
        current_message = get_message_by_id(message_id)
        if "error" in current_message:
            return current_message
        
        message_data = current_message.get("message", {})
        
        # Get current like and dislike lists
        like_user_ids = message_data.get("like_user_ids", "")
        dislike_user_ids = message_data.get("dislike_user_ids", "")
        
        # Convert comma-separated strings to lists
        like_list = like_user_ids.split(",") if like_user_ids else []
        dislike_list = dislike_user_ids.split(",") if dislike_user_ids else []
        
        # Remove empty strings
        like_list = [uid for uid in like_list if uid.strip()]
        dislike_list = [uid for uid in dislike_list if uid.strip()]
        
        # Check if user already liked
        if user_id in like_list:
            # remove user from like_list
            like_list.remove(user_id)
        
        # Add user to likes and remove from dislikes
        if user_id not in like_list:
            like_list.append(user_id)
            if user_id in dislike_list:
                dislike_list.remove(user_id)
        
        
        # Convert back to comma-separated strings
        update_data = {
            "like_user_ids": ",".join(like_list),
            "dislike_user_ids": ",".join(dislike_list)
        }
        
        # Update in Weaviate
        success = update_collection_object(COLLECTION_MESSAGES, message_id, update_data)
        
        if success:
            # Get updated message
            updated_message = get_message_by_id(message_id)
            return {
                "message": "Message liked successfully",
                "data": updated_message.get("message")
            }
        else:
            return {"error": "Failed to like message"}
    except Exception as e:
        logger.error(f"Error liking message: {str(e)}")
        return {"error": f"Failed to like message: {str(e)}"}


def dislike_message(message_id: str, user_id: str) -> Dict[str, Any]:
    """
    Dislike a message by adding user_id to dislike_user_ids and removing from like_user_ids.
    
    Args:
        message_id: The UUID of the message
        user_id: The UUID of the user disliking the message
    
    Returns:
        Success/error message with updated message data
    """
    try:
        # Get current message to verify it exists
        current_message = get_message_by_id(message_id)
        if "error" in current_message:
            return current_message
        
        message_data = current_message.get("message", {})
        
        # Get current like and dislike lists
        like_user_ids = message_data.get("like_user_ids", "")
        dislike_user_ids = message_data.get("dislike_user_ids", "")
        
        # Convert comma-separated strings to lists
        like_list = like_user_ids.split(",") if like_user_ids else []
        dislike_list = dislike_user_ids.split(",") if dislike_user_ids else []
        
        # Remove empty strings
        like_list = [uid for uid in like_list if uid.strip()]
        dislike_list = [uid for uid in dislike_list if uid.strip()]
        
        # Check if user already disliked
        if user_id in dislike_list:
            # remove user from dislike_list
            dislike_list.remove(user_id)
        
        # Add user to dislikes and remove from likes
        if user_id not in dislike_list:
            dislike_list.append(user_id)
            if user_id in like_list:
                like_list.remove(user_id)
        
        # Convert back to comma-separated strings
        update_data = {
            "like_user_ids": ",".join(like_list),
            "dislike_user_ids": ",".join(dislike_list)
        }
        
        # Update in Weaviate
        success = update_collection_object(COLLECTION_MESSAGES, message_id, update_data)
        
        if success:
            # Get updated message
            updated_message = get_message_by_id(message_id)
            if updated_message["message"].get("like_user_ids"):
                updated_message["message"]["like_user_ids"] = updated_message["message"]["like_user_ids"].split(",")
            if updated_message["message"].get("dislike_user_ids"):
                updated_message["message"]["dislike_user_ids"] = updated_message["message"]["dislike_user_ids"].split(",")
        
            return {
                "message": "Message disliked successfully",
                "data": updated_message.get("message")
            }
        else:
            return {"error": "Failed to dislike message"}
    except Exception as e:
        logger.error(f"Error disliking message: {str(e)}")
        return {"error": f"Failed to dislike message: {str(e)}"}