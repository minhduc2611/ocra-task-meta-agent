import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from data_classes.common_classes import Section, Message
from libs.weaviate_lib import (
    COLLECTION_CHATS,
    insert_to_collection,
    search_non_vector_collection,
    search_vector_collection,
    update_collection_object,
    delete_collection_object,
    get_collection_count
)
from weaviate.collections.classes.filters import Filter
from weaviate.collections.classes.grpc import Sort
from agents.sumary_agent import generate_summary

def create_section(section: Section) -> Optional[Dict[str, Any]]:
    """Create a new section
    order: The order of the section
    title: The title of the section
    created_at: The date and time the section was created
    updated_at: The date and time the section was last updated
    Args:
        section: Section object
    Returns:
        Dict[str, Any]: The created section data or None if failed
    """
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    if not section.title and section.messages:
        messages = [Message(**msg) if isinstance(msg, dict) else msg for msg in section.messages]
        section.title = generate_summary(messages, section.language)
    if not section.order:
        section.order = 0
    if not section.uuid:
        section.uuid = str(uuid.uuid4())
    properties = {
        "title": section.title,
        "order": section.order,
        "created_at": now,
        "updated_at": now,
        "author": section.author,
        "language": section.language,
        "context": section.context,
        "agent_id": section.agent_id,
    }
    section_uuid = insert_to_collection(COLLECTION_CHATS, properties, section.uuid)
    return get_section_by_id(section_uuid)

def get_sections(email: str, limit: int = 10, offset: int = 0) -> tuple[List[Dict[str, Any]], int]:
    """Get all sections with pagination and total count"""
    filters = Filter.by_property("author").equal(email)
    
    # Get sections data
    sections = search_non_vector_collection(
        collection_name=COLLECTION_CHATS,
        limit=limit,
        offset=offset,
        properties=["title", "order", "created_at", "updated_at", "context", "language", "agent_id"],
        sort=Sort.by_property("created_at", ascending=False),
        filters=filters
    )
    
    # Get total count
    total_count = get_collection_count(
        collection_name=COLLECTION_CHATS,
        filters=filters
    )
    
    return sections, total_count

def get_section_by_id(section_id: str) -> Optional[Dict[str, Any]]:
    """Get a section by its ID"""
    filters = Filter.by_id().equal(section_id)
    sections = search_non_vector_collection(
        collection_name=COLLECTION_CHATS,
        limit=1,
        properties=["title", "order", "created_at", "updated_at", "context", "language", "agent_id"],
        filters=filters
    )

    if not sections:
        return None
    
    return sections[0]

def update_section(section_id: str, **kwargs) -> bool:
    """
    Update a section with partial properties.
    
    Args:
        section_id: The UUID of the section to update
        **kwargs: Fields to update (title, order, etc.)
    
    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        # Get current section to verify it exists
        current_section = get_section_by_id(section_id)
        if not current_section:
            print(f"Section with ID {section_id} not found")
            return False
        
        # Define allowed fields that can be updated
        allowed_fields = ["title", "order", "agent_id", "context"]
        
        # Build update properties
        update_data = {}
        for key, value in kwargs.items():
            if key in allowed_fields:
                update_data[key] = value
        
        if not update_data:
            print("No valid fields to update")
            return False
        
        # Always update the updated_at timestamp
        update_data["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Update in Weaviate
        update_collection_object(COLLECTION_CHATS, section_id, update_data)
        return True
        
    except Exception as e:
        print(f"Error updating section: {str(e)}")
        return False

def delete_section(section_id: str) -> bool:
    """Delete a section"""
    try:
        delete_collection_object(COLLECTION_CHATS, section_id)
        return True
    except Exception as e:
        print(f"Error deleting section: {str(e)}")
        return False

def search_sections(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search sections by content"""
    return search_vector_collection(
        collection_name=COLLECTION_CHATS,
        query=query,
        limit=limit,
        properties=["title", "order", "created_at", "updated_at", "context"]
    ) 