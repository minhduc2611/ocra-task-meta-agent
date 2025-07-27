import os
from typing import List, Dict, Any, Optional, TypeVar
import weaviate
from weaviate.auth import Auth
import weaviate.classes as wvc
from weaviate.collections.classes.grpc import Sorting
from weaviate.collections.classes.filters import _Filters, Filter
from datetime import datetime
# Environment variables
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
headers = {
    "X-OpenAI-Api-Key": OPENAI_API_KEY,
}

error_message = ""
if not WEAVIATE_URL:
    error_message += "Missing required environment variables: WEAVIATE_URL\n"
if not WEAVIATE_API_KEY:
    error_message += "Missing required environment variables: WEAVIATE_API_KEY\n"
if not EMBEDDING_MODEL:
    error_message += "Missing required environment variables: EMBEDDING_MODEL\n"
if not OPENAI_API_KEY:
    error_message += "Missing required environment variables: OPENAI_API_KEY\n"

if error_message:
    print('❌ Error initializing Weaviate client, missing required environment variables: ' + error_message)
    exit(1)

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,                     # Weaviate URL: "REST Endpoint" in Weaviate Cloud console
    auth_credentials=Auth.api_key(WEAVIATE_API_KEY),  # Weaviate API key: "ADMIN" API key in Weaviate Cloud console
    headers=headers,
    skip_init_checks=True
)
def close_client():
    client.close()
COLLECTION_DOCUMENTS = "Documents"
COLLECTION_MESSAGES = "Messages"
COLLECTION_CHATS = "Sections"
COLLECTION_USERS = "Users"
COLLECTION_FILES = "Files"
COLLECTION_TOKEN_BLACKLIST = "TokenBlacklist"
COLLECTION_AGENTS = "Agents"
COLLECTION_AGENT_SETTINGS = "AgentSettings"
COLLECTION_FINE_TUNING_MODELS = "FineTuningModels"
COLLECTION_API_KEYS = "ApiKeys"
COLLECTION_PASSWORD_RESET_TOKENS = "PasswordResetTokens"

def initialize_schema() -> None:
    """Initialize the Weaviate schema if it doesn't exist."""
    print("Initializing schema...")
    exists = client.collections.exists(COLLECTION_DOCUMENTS)
    if not exists:
        client.collections.create(
            name=COLLECTION_DOCUMENTS,
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(
                model=EMBEDDING_MODEL
            ),
            properties=[
                wvc.config.Property(name="title", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="description", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="category", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="language", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="source", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="author", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="knowledge_type", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="updated_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="file_id", data_type=wvc.config.DataType.UUID), # optional    
            ]
        )
        print("🙌🏼 Collection Documents created successfully")
    exists = client.collections.exists(COLLECTION_MESSAGES)
    if not exists:
        client.collections.create(
            name=COLLECTION_MESSAGES,
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(
                model=EMBEDDING_MODEL
            ),
            inverted_index_config=wvc.config.Configure.inverted_index(
                index_null_state=True,
            ),
            properties=[
                wvc.config.Property(name="session_id", data_type=wvc.config.DataType.UUID),
                wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="role", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="mode", data_type=wvc.config.DataType.TEXT),
                # for prompt question
                wvc.config.Property(name="response_answer_id", data_type=wvc.config.DataType.UUID),
                # for response answer
                wvc.config.Property(name="feedback", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="edited_content", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="approval_status", data_type=wvc.config.DataType.TEXT),
            ]
        )
        print("🙌🏼 Collection Messages created successfully")
    # add thought property to Messages collection
    try:
        messages_collection = client.collections.get(COLLECTION_MESSAGES)
        messages_collection.config.add_property(
            wvc.config.Property(name="like_user_ids", data_type=wvc.config.DataType.TEXT),
        )
        messages_collection.config.add_property(
            wvc.config.Property(name="dislike_user_ids", data_type=wvc.config.DataType.TEXT),
        )
        messages_collection.config.add_property(
            wvc.config.Property(name="agent_id", data_type=wvc.config.DataType.UUID)
        )
        messages_collection.config.add_property(
                wvc.config.Property(name="thought", data_type=wvc.config.DataType.TEXT),
        )
    except Exception as e:
        print(f"Error adding thought property to Messages collection: {e}")
    
    exists = client.collections.exists(COLLECTION_FINE_TUNING_MODELS)
    if not exists:
        client.collections.create(
            name=COLLECTION_FINE_TUNING_MODELS,
            properties=[
                wvc.config.Property(name="name", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="description", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="base_model", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="status", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="language", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="updated_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="author", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="training_data_path", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="validation_data_path", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="hyperparameters", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="training_metrics", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="model_path", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="version", data_type=wvc.config.DataType.TEXT),
            ]
        )
        print("🙌🏼 Collection FineTuningModels created successfully")
    exists = client.collections.exists(COLLECTION_API_KEYS)
    if not exists:
        client.collections.create(
            name=COLLECTION_API_KEYS,
            properties=[
                wvc.config.Property(name="name", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="description", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="key_hash", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="user_id", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="status", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="permissions", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="updated_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="expires_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="last_used_at", data_type=wvc.config.DataType.DATE),
            ]
        )
        print("🙌🏼 Collection ApiKeys created successfully")
    exists = client.collections.exists(COLLECTION_CHATS)
    if not exists:
        client.collections.create(
            name=COLLECTION_CHATS,
            properties=[
                wvc.config.Property(name="title", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="order", data_type=wvc.config.DataType.INT),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="updated_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="author", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="language", data_type=wvc.config.DataType.TEXT),
            ]
        )
        print("🙌🏼 Collection Sections created successfully")
    # add thought property to Chats collection
    try:
        chats_collection = client.collections.get(COLLECTION_CHATS)
        chats_collection.config.add_property(
            wvc.config.Property(name="agent_id", data_type=wvc.config.DataType.UUID),
        )
        chats_collection.config.add_property(
            wvc.config.Property(name="context", data_type=wvc.config.DataType.TEXT),
        )
        print("🙌🏼 Collection Sections updated successfully")
    except Exception as e:
        print(f"Error adding context and thought property to Chats collection: {e}")
    
    exists = client.collections.exists(COLLECTION_USERS)
    if not exists:
        client.collections.create(
            name=COLLECTION_USERS,
            properties=[
                wvc.config.Property(name="email", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="password", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="name", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="role", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="updated_at", data_type=wvc.config.DataType.DATE), 
            ]
        )
        print("🙌🏼 Collection Users created successfully")
    exists = client.collections.exists(COLLECTION_FILES)
    if not exists:
        client.collections.create(
            name=COLLECTION_FILES,
            properties=[
                wvc.config.Property(name="name", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="path", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="updated_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="author", data_type=wvc.config.DataType.TEXT),
            ]
        )
        print("🙌🏼 Collection Files created successfully")
    exists = client.collections.exists(COLLECTION_TOKEN_BLACKLIST)
    if not exists:
        client.collections.create(
            name=COLLECTION_TOKEN_BLACKLIST,
            properties=[
                wvc.config.Property(name="token", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="user_id", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="blacklisted_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="expires_at", data_type=wvc.config.DataType.DATE),
            ]
        )
        print("🙌🏼 Collection TokenBlacklist created successfully")
    exists = client.collections.exists(COLLECTION_AGENTS)
    if not exists:
        client.collections.create(
            name=COLLECTION_AGENTS,
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(
                model=EMBEDDING_MODEL
            ),
            properties=[
                wvc.config.Property(name="name", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="description", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="system_prompt", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="tools", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="model", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="temperature", data_type=wvc.config.DataType.NUMBER),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="updated_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="author", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="status", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="agent_type", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="language", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="corpus_id", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="conversation_starters", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="tags", data_type=wvc.config.DataType.TEXT),
            ]
        )
        print("🙌🏼 Collection Agents created successfully")
    exists = client.collections.exists(COLLECTION_AGENT_SETTINGS)
    if not exists:
        client.collections.create(
            name=COLLECTION_AGENT_SETTINGS,
            properties=[
                wvc.config.Property(name="key", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="label", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="short_label", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="agent_id", data_type=wvc.config.DataType.UUID),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="updated_at", data_type=wvc.config.DataType.DATE),
            ]
        )
        print("🙌🏼 Collection AgentSettings created successfully")
    exists = client.collections.exists(COLLECTION_PASSWORD_RESET_TOKENS)
    if not exists:
        client.collections.create(
            name=COLLECTION_PASSWORD_RESET_TOKENS,
            properties=[
                wvc.config.Property(name="email", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="token", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="expires_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="used", data_type=wvc.config.DataType.BOOL),
            ]
        )
        print("🙌🏼 Collection PasswordResetTokens created successfully")
    print("🙌🏼 Schema initialized successfully")

def upload_documents(documents: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Upload documents to Weaviate.
    
    Args:
        documents: List of dictionaries containing document data
    
    Returns:
        Response from Weaviate
    """
    data_objects = []
    
    for doc in documents:
        data_object = {
            "title": doc.get("title", ""),
            "content": doc.get("content", ""),
            "description": doc.get("description", ""),
            "author": doc.get("author", "system"),
            "file_id": doc.get("file_id", ""),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        # Add optional fields if they exist
        if "category" in doc:
            data_object["category"] = doc["category"]
        if "language" in doc:
            data_object["language"] = doc["language"]
        if "source" in doc:
            data_object["source"] = doc["source"]
        if "knowledge_type" in doc:
            data_object["knowledge_type"] = doc["knowledge_type"]
        
        data_objects.append(data_object)
    
    # response = 
    collection = client.collections.get(COLLECTION_DOCUMENTS)

    with collection.batch.fixed_size(batch_size=200) as batch:
        for data_object in data_objects:
            batch.add_object(
                properties=data_object,
            )
            if batch.number_errors > 10:
                print("Batch import stopped due to excessive errors.")
                break
    failed_objects = collection.batch.failed_objects
    if failed_objects:
        print(f"Number of failed imports: {len(failed_objects)}")
        print(f"First failed object: {failed_objects[0]}")

    
    return failed_objects

def search_documents(query: str, limit: int = 3) -> list[dict]:
    """
    Search for relevant documents using vector similarity.

    Args:
        query: Search query string
        limit: Maximum number of results to return

    Returns:
        List of matching documents
    """
    collection = client.collections.get(COLLECTION_DOCUMENTS)
    response = collection.query.near_text(
        query=query,
        limit=limit,
        certainty=0.7,
        
    )
    # Each object in response.objects contains .properties with your fields
    return [obj.properties for obj in response.objects]

def search_non_vector_collection(
    collection_name: str,
    limit: int = 100,
    properties: List[str] = [],
    filters: Optional[_Filters] = None,
    offset: Optional[int] = None,
    sort: Optional[Sorting] = None,
) -> list[dict]:
    """
    For non vector search, use this function.
    Search for relevant collection.

    Args:
        collection_name: Name of the collection to search
        limit: Maximum number of results to return
        properties: List of properties to return
        filters: Filters to apply to the search
        offset: Offset to start from
        sort: Sorting to apply to the search

    Returns:
        List of matching collection
    """
    collection = client.collections.get(collection_name)
    response = collection.query.fetch_objects(
        limit=limit,
        return_properties=properties,
        filters=filters,
        offset=offset,
        sort=sort,
    )
    # Each object in response.objects contains .properties with your fields, and uuid
    return [{"uuid": str(obj.uuid), **obj.properties} for obj in response.objects]

def get_object_by_id(collection_name: str, uuid: str) -> dict:
    collection = client.collections.get(collection_name)
    response = collection.query.fetch_objects(
        filters=Filter.by_id().equal(uuid)
    )
    return response.objects[0].properties

def search_vector_collection(
    collection_name: str,
    query: str,
    limit: int = 3,
    properties: List[str] = [],
    filters: Optional[_Filters] = None,
    offset: Optional[int] = None,
    sort: Optional[Sorting] = None,
) -> list[dict]:
    """
    Search for relevant collection using vector similarity.

    Args:
        collection_name: Name of the collection to search
        query: Search query string
        limit: Maximum number of results to return
        properties: List of properties to return
        filters: Filters to apply to the search 
        offset: Offset to start from
        sort: Sorting to apply to the search

    Returns:
        List of matching collection
    """
    collection = client.collections.get(collection_name)
    response = collection.query.near_text(
        query=query,
        limit=limit,
        return_properties=properties,
        filters=filters,
        offset=offset,
        sort=sort,
    )
    # Each object in response.objects contains .properties with your fields
    return [obj.properties for obj in response.objects]

T = TypeVar('T', bound=Dict[str, Any])

def insert_to_collection(
    collection_name: str,
    properties: T,
    uuid: Optional[str] = None
) -> str:
    # Get the collection
    collection = client.collections.get(collection_name)

    # Insert a single object
    if uuid:
        uuid = collection.data.insert(properties=properties, uuid=uuid)
    else:
        uuid = collection.data.insert(properties=properties)

    return uuid

def insert_to_collection_in_batch(
    collection_name: str,
    properties: List[T]
) -> List[str]:
    # Get the collection
    collection = client.collections.get(collection_name)
    # Insert a single object
    uuids = collection.data.insert_many(properties)
    return uuids

def update_collection_object(
    collection_name: str,
    uuid: str,
    properties: T
) -> bool:
    # Get the collection
    collection = client.collections.get(collection_name)
    # Update a single object
    collection.data.update(properties=properties, uuid=uuid)
    return True

def delete_collection_object(
    collection_name: str,
    uuid: str
) -> str:
    # Get the collection
    collection = client.collections.get(collection_name)
    # Delete a single object
    collection.data.delete_by_id(uuid)
    return uuid

def delete_collection_objects_many(
    collection_name: str,
    filters: Optional[_Filters] = None
) -> bool:
    # Get the collection
    collection = client.collections.get(collection_name)
    # Delete a single object
    collection.data.delete_many(where=filters)
    return True

def get_collection_count(
    collection_name: str,
    filters: Optional[_Filters] = None,
) -> int:
    """
    Get the total count of objects in a collection with optional filters.
    
    Args:
        collection_name: Name of the collection to count
        filters: Optional filters to apply to the count
        
    Returns:
        Total count of objects matching the filters
    """
    collection = client.collections.get(collection_name)
    
    # Use aggregate to get count
    response = collection.aggregate.over_all(
        filters=filters
    )
    
    return response.total_count


def get_aggregate(
    collection_name: str,
    filters: Filter
):
    users = client.collections.get(collection_name)
    response = users.aggregate.over_all(
        filters=filters,
        total_count=True
    )
    return response
