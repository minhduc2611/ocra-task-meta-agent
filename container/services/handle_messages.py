from data_classes.common_classes import Message
from typing import List
from libs.weaviate_lib import search_vector_collection, search_non_vector_collection
from typing import Dict, Any
from weaviate.collections.classes.filters import Filter
from weaviate.collections.classes.grpc import Sort

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


