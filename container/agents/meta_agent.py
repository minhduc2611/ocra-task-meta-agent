import os
import json
from typing import List, Dict, Any, Optional
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from libs.weaviate_lib import client, search_documents, insert_to_collection, update_collection_object, delete_collection_object, COLLECTION_AGENTS
from data_classes.common_classes import Message, Language, AgentStatus
from datetime import datetime
import uuid
import weaviate.classes as wvc
from libs.langchain import get_langchain_model
model = get_langchain_model(model="gemini-2.5-flash", temperature=0.7)
# Tools for the meta agent
@tool
def create_agent(name: str, description: str, system_prompt: str, tools: List[str], model: str = "gpt-4o-mini", temperature: float = 0, author: str = "system") -> Dict[str, Any]:
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

@tool
def list_agents(author: str = "system", limit: int = 10) -> List[Dict[str, Any]]:
    """
    List all agents created by a specific author.
    
    Args:
        author: The author to filter by
        limit: Maximum number of agents to return
    
    Returns:
        List of agent configurations
    """
    try:
        collection = client.collections.get(COLLECTION_AGENTS)
        response = collection.query.fetch_objects(
            limit=limit,
            filters=wvc.query.Filter.by_property("author").equal(author)
        )
        
        agents = []
        for obj in response.objects:
            agent_data = obj.properties
            agent_data["uuid"] = obj.uuid
            agents.append(agent_data)
        
        return agents
    except Exception as e:
        return [{"error": f"Failed to list agents: {str(e)}"}]

@tool
def get_agent(agent_id: str) -> Dict[str, Any]:
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

@tool
def update_agent(agent_id: str, **kwargs) -> Dict[str, Any]:
    """
    Update an existing agent's configuration.
    
    Args:
        agent_id: The UUID of the agent
        **kwargs: Fields to update (name, description, system_prompt, tools, model, temperature)
    
    Returns:
        Updated agent configuration
    """
    try:
        # Get current agent
        current_agent = get_agent(agent_id)
        if "error" in current_agent:
            return current_agent
        
        # Update fields
        update_data = {}
        for key, value in kwargs.items():
            if key in ["name", "description", "system_prompt", "model", "temperature"]:
                update_data[key] = value
            elif key == "tools":
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

@tool
def delete_agent(agent_id: str) -> Dict[str, Any]:
    """
    Delete an agent by ID.
    
    Args:
        agent_id: The UUID of the agent to delete
    
    Returns:
        Success/error message
    """
    try:
        success = delete_collection_object(COLLECTION_AGENTS, agent_id)
        
        if success:
            return {"message": f"Agent '{agent_id}' deleted successfully"}
        else:
            return {"error": "Failed to delete agent"}
    except Exception as e:
        return {"error": f"Failed to delete agent: {str(e)}"}

@tool
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

@tool
def generate_agent_code(agent_config: Dict[str, Any]) -> str:
    """
    Generate Python code for an agent based on its configuration.
    
    Args:
        agent_config: The agent configuration dictionary
    
    Returns:
        Generated Python code for the agent
    """
    try:
        name = agent_config.get("name", "MyAgent")
        system_prompt = agent_config.get("system_prompt", "")
        model = agent_config.get("model", "gpt-4o-mini")
        temperature = agent_config.get("temperature", 0)
        tools_json = agent_config.get("tools", "[]")
        tools = json.loads(tools_json) if isinstance(tools_json, str) else tools_json
        
        # Generate the code
        code = f'''import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict, Any

class {name.replace(" ", "").replace("-", "_")}:
    def __init__(self):
        self.model = ChatOpenAI(
            model="{model}",
            temperature={temperature}
        )
        self.system_prompt = """{system_prompt}"""
        
        # Initialize tools here
        self.tools = []
        # TODO: Add your tools implementation
        # Example: self.tools = [your_tool_function]
        
    def generate_response(self, user_input: str, context: List[Dict[str, Any]] = None) -> str:
        """
        Generate a response using the agent.
        
        Args:
            user_input: The user's input
            context: Optional context information
            
        Returns:
            The agent's response
        """
        messages = [
            ("system", self.system_prompt),
            ("human", user_input)
        ]
        
        if context:
            context_text = "\\n\\n".join([f"Context: {ctx.get('content', '')}" for ctx in context])
            messages.append(("human", f"Additional context:\\n{context_text}"))
        
        prompt = ChatPromptTemplate.from_messages(messages)
        chain = prompt | self.model
        
        response = chain.invoke({{}})
        return response.content
    
    def run(self, user_input: str) -> str:
        """
        Main method to run the agent.
        """
        return self.generate_response(user_input)

# Usage example
if __name__ == "__main__":
    agent = {name.replace(" ", "").replace("-", "_")}()
    response = agent.run("Hello, how can you help me?")
    print(response)
'''
        
        return code
    except Exception as e:
        return f"Error generating code: {str(e)}"

@tool
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
        agent_config = get_agent(agent_id)
        if "error" in agent_config:
            return agent_config
        
        # Create a simple test instance
        system_prompt = agent_config.get("system_prompt", "")
        model_name = agent_config.get("model", "gpt-4o-mini")
        temperature = agent_config.get("temperature", 0)
        
        test_model = ChatOpenAI(model=model_name, temperature=temperature)
        
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

# Meta agent tools
meta_agent_tools = [
    create_agent,
    list_agents,
    get_agent,
    update_agent,
    delete_agent,
    search_agents,
    generate_agent_code,
    test_agent
]

# Meta agent prompt
meta_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an AI Agent Builder - a specialized AI that helps users create, manage, and optimize other AI agents.

Your capabilities include:
1. Creating new AI agents with custom system prompts, tools, and configurations
2. Managing existing agents (list, update, delete)
3. Searching for agents using semantic search
4. Generating Python code for agents
5. Testing agents with sample inputs
6. Providing guidance on agent design and best practices

When helping users:
- Ask clarifying questions to understand their requirements
- Suggest appropriate tools and configurations
- Provide examples and best practices
- Help debug and optimize agent performance
- Generate clean, well-documented code

Always be helpful, patient, and thorough in your explanations. Focus on creating agents that are useful, safe, and well-designed."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    # MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Create the meta agent
meta_agent = create_react_agent(
    model=model,
    tools=meta_agent_tools,
    prompt=meta_agent_prompt,
)

def generate_meta_agent_response(messages: List[Message], contexts: List[Dict[str, str]] = None, options: Optional[Dict[str, Any]] = None, language: Language = Language.EN) -> str:
    """
    Generate a response using the meta agent.
    
    Args:
        messages: List of conversation messages
        contexts: Optional context from relevant documents
        options: Optional configuration options
        language: Language preference
    
    Returns:
        The meta agent's response
    """
    try:
        # Prepare the input
        if not messages:
            return "Hello! I'm your AI Agent Builder. How can I help you create or manage AI agents today?"
        
        # Get the latest user message
        latest_message = messages[-1].content
        
        # Add context if available
        if contexts:
            context_text = "\n\n".join([
                f"Context: {ctx['content']}"
                for ctx in contexts
            ])
            latest_message = f"{latest_message}\n\nRelevant context:\n{context_text}"
        
        # Prepare chat history
        chat_history = []
        for msg in messages[:-1]:  # Exclude the latest message
            if msg.role == "user":
                chat_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                chat_history.append(AIMessage(content=msg.content))
        
        # Invoke the meta agent
        response = meta_agent.invoke({
            "input": latest_message,
            "chat_history": chat_history,
        })
        
        return response["output"]
        
    except Exception as e:
        return f"Error generating response: {str(e)}"

# Convenience function for direct agent creation
def create_simple_agent(name: str, description: str, system_prompt: str, author: str = "system") -> Dict[str, Any]:
    """
    Create a simple agent with basic configuration.
    
    Args:
        name: Name of the agent
        description: Description of the agent
        system_prompt: System prompt for the agent
        author: Author of the agent
    
    Returns:
        Created agent information
    """
    return create_agent(
        name=name,
        description=description,
        system_prompt=system_prompt,
        tools=[],
        author=author
    )
