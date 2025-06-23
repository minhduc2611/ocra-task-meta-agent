from data_classes.common_classes import AskRequest
from services.handle_ask import handle_ask_streaming

def handle_test_agent(body: AskRequest):
    """
    Chat with an agent.
    
    Args:
        agent_id: The agent ID to chat with
        user_message: The user's message
        stream: Whether to stream the response
    """
    try:

        
        return handle_ask_streaming(body, True)
    except Exception as e:
        return {"error": f"Failed to chat with agent: {str(e)}"}
    