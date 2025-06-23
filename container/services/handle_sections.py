import uuid
from typing import List, Dict, Any
from datetime import datetime
from data_classes.common_classes import Section, Message
from libs.weaviate_lib import (
    COLLECTION_SECTIONS,
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

def create_section(section: Section) -> Section:
    """Create a new section
    order: The order of the section
    title: The title of the section
    created_at: The date and time the section was created
    updated_at: The date and time the section was last updated
    Args:
        section: Section object
    Returns:
        Section: The created section
    """
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    if not section.title:
        messages = [Message(**msg) for msg in section.messages]
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
        "author": section.author
    }
    uuid =  insert_to_collection(COLLECTION_SECTIONS, properties, section.uuid)
    return get_section_by_id(uuid)

def get_sections(email: str, limit: int = 10, offset: int = 0) -> tuple[List[Dict[str, Any]], int]:
    """Get all sections with pagination and total count"""
    filters = Filter.by_property("author").equal(email)
    
    # Get sections data
    sections = search_non_vector_collection(
        collection_name=COLLECTION_SECTIONS,
        limit=limit,
        offset=offset,
        properties=["title", "order", "created_at", "updated_at"],
        sort=Sort.by_property("created_at", ascending=False),
        filters=filters
    )
    
    # Get total count
    total_count = get_collection_count(
        collection_name=COLLECTION_SECTIONS,
        filters=filters
    )
    
    return sections, total_count

def get_section_by_id(section_id: str) -> Section:
    """Get a section by its ID"""
    filters = Filter.by_id().equal(section_id)
    sections = search_non_vector_collection(
        collection_name=COLLECTION_SECTIONS,
        limit=1,
        properties=["title", "order", "created_at", "updated_at"],
        filters=filters
    )

    section = Section(**sections[0]) if sections else None
    return {
        "uuid": section.uuid,
        "title": section.title,
        "order": section.order,
        "created_at": section.created_at,
        "updated_at": section.updated_at
    }

def update_section(section_id: str, section: Section) -> bool:
    """Update a section"""
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    properties = {
        "title": section.title,
        "order": section.order or 0,
        "updated_at": now
    }
    try:
        update_collection_object(COLLECTION_SECTIONS, section_id, properties)
        return True
    except Exception as e:
        print(f"Error updating section: {str(e)}")
        return False

def delete_section(section_id: str) -> bool:
    """Delete a section"""
    try:
        delete_collection_object(COLLECTION_SECTIONS, section_id)
        return True
    except Exception as e:
        print(f"Error deleting section: {str(e)}")
        return False

def search_sections(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search sections by content"""
    return search_vector_collection(
        collection_name=COLLECTION_SECTIONS,
        query=query,
        limit=limit,
        properties=["title", "order", "created_at", "updated_at"]
    ) 