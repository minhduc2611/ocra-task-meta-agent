import json
from typing import List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from libs.weaviate_lib import client, insert_to_collection, update_collection_object, delete_collection_object, COLLECTION_AGENTS
from datetime import datetime
import uuid
import weaviate.classes as wvc
from data_classes.common_classes import AgentStatus, AgentProvider
from libs.langchain import get_langchain_model
from libs.google_vertex import delete_corpus

def create_agent(
    name: str, 
    description: str, 
    system_prompt: str, 
    tools: List[str], 
    model: str = "gpt-4o-mini", 
    temperature: float = 0, 
    author: str = "system", 
    language: str = "en",
) -> Dict[str, Any]:
    """
    Create a new AI agent with the specified configuration.
    
    Args:
        name: Name of the agent
        description: Description of what the agent does
        system_prompt: The system prompt that defines the agent's behavior
        tools: List of tool names the agent should have access to
        model: The LLM model to use (default: gpt-4o-mini)
        temperature: Temperature for response generation (default: 0)
        author: The user creating the agent
        language: The language of the agent
    
    Returns:
        Dictionary containing the created agent's information
    """
    try:
        agent_id = str(uuid.uuid4())
        agent_config = {
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "tools": json.dumps(tools),
            "model": model,
            "temperature": temperature,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "author": author,
            "status": AgentStatus.ACTIVE.value,
            "language": language
        }
        
        # Store in Weaviate
        insert_to_collection(COLLECTION_AGENTS, agent_config, agent_id)
        
        return {
            "agent_id": agent_id,
            "name": name,
            "description": description,
            "status": AgentStatus.ACTIVE.value,
            "message": f"Agent '{name}' created successfully with {len(tools)} tools"
        }
    except Exception as e:
        return {"error": f"Failed to create agent: {str(e)}"}

def list_agents(author: str = "system", limit: int = 10, language: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all agents created by a specific author.
    
    Args:
        author: The author to filter by
        limit: Maximum number of agents to return
        language: Language of the agents
    Returns:
        List of agent configurations
    """
    try:
        collection = client.collections.get(COLLECTION_AGENTS)
        
        # filters = wvc.query.Filter.by_property("author").equal(author)
        if language:
            filters = wvc.query.Filter.by_property("language").equal(language)
            response = collection.query.fetch_objects(
                limit=limit,
                filters=filters
            )
        else:
            response = collection.query.fetch_objects(
                limit=limit,
            )
        
        agents = []
        for obj in response.objects:
            agent_data = obj.properties
            agent_data["uuid"] = obj.uuid
            agent_data["conversation_starters"] = json.loads(agent_data["conversation_starters"]) if agent_data["conversation_starters"] else []
            agent_data["tags"] = json.loads(agent_data["tags"]) if agent_data["tags"] else []
            agents.append(agent_data)
        
        return agents
    except Exception as e:
        return [{"error": f"Failed to list agents: {str(e)}"}]

def get_agent_by_id(agent_id: str) -> Dict[str, Any]:
    """
    Get a specific agent's configuration by ID.
    
    Args:
        agent_id: The UUID of the agent
    
    Returns:
        Agent configuration
    """
    try:
        collection = client.collections.get(COLLECTION_AGENTS)
        response = collection.query.fetch_object_by_id(agent_id)
        
        if response:
            agent_data = response.properties
            agent_data["uuid"] = response.uuid
            return agent_data
        else:
            return {"error": "Agent not found"}
    except Exception as e:
        return {"error": f"Failed to get agent: {str(e)}"}

def update_agent(agent_id: str, **kwargs) -> Dict[str, Any]:
    """
    Update an existing agent's configuration.
    
    Args:
        agent_id: The UUID of the agent
        **kwargs: Fields to update (name, description, system_prompt, tools, model, temperature, language, system_prompt, conversation_starters, tags)
    
    Returns:
        Updated agent configuration
    """
    try:
        # Get current agent
        current_agent = get_agent_by_id(agent_id)
        if "error" in current_agent:
            return current_agent
        
        # Update fields
        update_data = {}
        for key, value in kwargs.items():
            if key in ["name", "description", "system_prompt", "model", "temperature", "language", "system_prompt", "corpus_id"]:
                update_data[key] = value
            elif key in ["tools", "conversation_starters", "tags"]:
                update_data[key] = json.dumps(value) if isinstance(value, list) else value
        
        update_data["updated_at"] = datetime.now()
        
        # Update in Weaviate
        success = update_collection_object(COLLECTION_AGENTS, agent_id, update_data)
        
        if success:
            return {"message": f"Agent '{agent_id}' updated successfully", "updated_fields": list(update_data.keys())}
        else:
            return {"error": "Failed to update agent"}
    except Exception as e:
        return {"error": f"Failed to update agent: {str(e)}"}

def delete_agent(agent_id: str) -> Dict[str, Any]:
    """
    Delete an agent by ID.
    
    Args:
        agent_id: The UUID of the agent to delete
    
    Returns:
        Success/error message
    """
    try:
        # delete all files in the agent's corpus
        agent = get_agent_by_id(agent_id)
        if agent["corpus_id"]:
            delete_corpus(agent["corpus_id"])
        success = delete_collection_object(COLLECTION_AGENTS, agent_id)
        
        if success:
            return {"message": f"Agent '{agent_id}' deleted successfully"}
        else:
            return {"error": "Failed to delete agent"}
    except Exception as e:
        return {"error": f"Failed to delete agent: {str(e)}"}

def search_agents(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for agents using semantic search.
    
    Args:
        query: Search query
        limit: Maximum number of results
    
    Returns:
        List of matching agents
    """
    try:
        collection = client.collections.get(COLLECTION_AGENTS)
        response = collection.query.near_text(
            query=query,
            limit=limit,
            certainty=0.7
        )
        
        agents = []
        for obj in response.objects:
            agent_data = obj.properties
            agent_data["uuid"] = obj.uuid
            agents.append(agent_data)
        
        return agents
    except Exception as e:
        return [{"error": f"Failed to search agents: {str(e)}"}]


def test_agent(agent_id: str, test_input: str) -> Dict[str, Any]:
    """
    Test an agent with a sample input.
    
    Args:
        agent_id: The UUID of the agent to test
        test_input: The test input to send to the agent
    
    Returns:
        Test results
    """
    try:
        # Get agent configuration
        agent_config = get_agent_by_id(agent_id)
        if "error" in agent_config:
            return agent_config
        
        # Create a simple test instance
        system_prompt = agent_config.get("system_prompt", "")
        model_name = agent_config.get("model", "gpt-4o-mini")
        temperature = agent_config.get("temperature", 0)
        
        test_model = get_langchain_model(model=model_name, temperature=temperature)
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", test_input)
        ])
        
        # Generate response
        chain = prompt | test_model
        response = chain.invoke({})
        
        return {
            "agent_name": agent_config.get("name", "Unknown"),
            "test_input": test_input,
            "response": response.content,
            "model_used": model_name,
            "temperature": temperature
        }
    except Exception as e:
        return {"error": f"Failed to test agent: {str(e)}"}
