from typing import List, Dict, Any, Optional
from libs.weaviate_lib import client, insert_to_collection, update_collection_object, delete_collection_object, COLLECTION_AGENT_SETTINGS
from datetime import datetime
import uuid
import weaviate.classes as wvc

def create_agent_setting(key: str, label: str, short_label: str, agent_id: str) -> Dict[str, Any]:
    """
    Create a new agent setting.
    
    Args:
        key: Setting key/identifier
        label: Full label/description of the setting
        short_label: Short label for display
        agent_id: UUID of the agent this setting belongs to
    
    Returns:
        Dictionary containing the created setting's information
    """
    try:
        setting_id = str(uuid.uuid4())
        setting_config = {
            "key": key,
            "label": label,
            "short_label": short_label,
            "agent_id": agent_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Store in Weaviate
        insert_to_collection(COLLECTION_AGENT_SETTINGS, setting_config, setting_id)
        
        return {
            "setting_id": setting_id,
            "key": key,
            "label": label,
            "short_label": short_label,
            "agent_id": agent_id,
            "message": f"Agent setting '{key}' created successfully"
        }
    except Exception as e:
        return {"error": f"Failed to create agent setting: {str(e)}"}

def list_agent_settings(agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    List all agent settings, optionally filtered by agent_id.
    
    Args:
        agent_id: Optional agent ID to filter by
        limit: Maximum number of settings to return
    
    Returns:
        List of agent setting configurations
    """
    try:
        collection = client.collections.get(COLLECTION_AGENT_SETTINGS)
        
        if agent_id:
            filters = wvc.query.Filter.by_property("agent_id").equal(agent_id)
            response = collection.query.fetch_objects(
                limit=limit,
                filters=filters
            )
        else:
            response = collection.query.fetch_objects(
                limit=limit,
            )
        
        settings = []
        for obj in response.objects:
            setting_data = obj.properties
            setting_data["uuid"] = obj.uuid
            settings.append(setting_data)
        
        return settings
    except Exception as e:
        return [{"error": f"Failed to list agent settings: {str(e)}"}]

def get_agent_setting(setting_id: str) -> Dict[str, Any]:
    """
    Get a specific agent setting by ID.
    
    Args:
        setting_id: The UUID of the setting
    
    Returns:
        Setting configuration
    """
    try:
        collection = client.collections.get(COLLECTION_AGENT_SETTINGS)
        response = collection.query.fetch_object_by_id(setting_id)
        
        if response:
            setting_data = response.properties
            setting_data["uuid"] = response.uuid
            return setting_data
        else:
            return {"error": "Agent setting not found"}
    except Exception as e:
        return {"error": f"Failed to get agent setting: {str(e)}"}

def get_agent_setting_by_key(agent_id: str, key: str) -> Dict[str, Any]:
    """
    Get a specific agent setting by agent_id and key.
    
    Args:
        agent_id: The UUID of the agent
        key: The setting key
    
    Returns:
        Setting configuration
    """
    try:
        collection = client.collections.get(COLLECTION_AGENT_SETTINGS)
        
        filters = (
            wvc.query.Filter.by_property("agent_id").equal(agent_id) &
            wvc.query.Filter.by_property("key").equal(key)
        )
        
        response = collection.query.fetch_objects(
            limit=1,
            filters=filters
        )
        
        if response.objects:
            setting_data = response.objects[0].properties
            setting_data["uuid"] = response.objects[0].uuid
            return setting_data
        else:
            return {"error": "Agent setting not found"}
    except Exception as e:
        return {"error": f"Failed to get agent setting: {str(e)}"}

def update_agent_setting(setting_id: str, **kwargs) -> Dict[str, Any]:
    """
    Update an existing agent setting.
    
    Args:
        setting_id: The UUID of the setting
        **kwargs: Fields to update (key, label, short_label, agent_id)
    
    Returns:
        Updated setting configuration
    """
    try:
        # Get current setting
        current_setting = get_agent_setting(setting_id)
        if "error" in current_setting:
            return current_setting
        
        # Update fields
        update_data = {}
        for key, value in kwargs.items():
            if key in ["key", "label", "short_label", "agent_id"]:
                update_data[key] = value
        
        update_data["updated_at"] = datetime.now()
        
        # Update in Weaviate
        success = update_collection_object(COLLECTION_AGENT_SETTINGS, setting_id, update_data)
        
        if success:
            return {"message": f"Agent setting '{setting_id}' updated successfully", "updated_fields": list(update_data.keys())}
        else:
            return {"error": "Failed to update agent setting"}
    except Exception as e:
        return {"error": f"Failed to update agent setting: {str(e)}"}

def delete_agent_setting(setting_id: str) -> Dict[str, Any]:
    """
    Delete an agent setting by ID.
    
    Args:
        setting_id: The UUID of the setting to delete
    
    Returns:
        Success/error message
    """
    try:
        success = delete_collection_object(COLLECTION_AGENT_SETTINGS, setting_id)
        
        if success:
            return {"message": f"Agent setting '{setting_id}' deleted successfully"}
        else:
            return {"error": "Failed to delete agent setting"}
    except Exception as e:
        return {"error": f"Failed to delete agent setting: {str(e)}"}

def delete_agent_settings_by_agent(agent_id: str) -> Dict[str, Any]:
    """
    Delete all settings for a specific agent.
    
    Args:
        agent_id: The UUID of the agent
    
    Returns:
        Success/error message
    """
    try:
        collection = client.collections.get(COLLECTION_AGENT_SETTINGS)
        
        filters = wvc.query.Filter.by_property("agent_id").equal(agent_id)
        success = collection.data.delete_many(filters=filters)
        
        if success:
            return {"message": f"All settings for agent '{agent_id}' deleted successfully"}
        else:
            return {"error": "Failed to delete agent settings"}
    except Exception as e:
        return {"error": f"Failed to delete agent settings: {str(e)}"}

def search_agent_settings(query: str, agent_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for agent settings using text search.
    
    Args:
        query: Search query
        agent_id: Optional agent ID to filter by
        limit: Maximum number of results
    
    Returns:
        List of matching settings
    """
    try:
        collection = client.collections.get(COLLECTION_AGENT_SETTINGS)
        
        if agent_id:
            filters = wvc.query.Filter.by_property("agent_id").equal(agent_id)
            response = collection.query.fetch_objects(
                limit=limit,
                filters=filters
            )
        else:
            response = collection.query.fetch_objects(
                limit=limit,
            )
        
        # Filter results based on query
        settings = []
        query_lower = query.lower()
        for obj in response.objects:
            setting_data = obj.properties
            # Check if query matches key, label, or short_label
            if (query_lower in setting_data.get("key", "").lower() or
                query_lower in setting_data.get("label", "").lower() or
                query_lower in setting_data.get("short_label", "").lower()):
                setting_data["uuid"] = obj.uuid
                settings.append(setting_data)
        
        return settings[:limit]
    except Exception as e:
        return [{"error": f"Failed to search agent settings: {str(e)}"}] 