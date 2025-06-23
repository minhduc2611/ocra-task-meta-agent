from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage
import json
from data_classes.common_classes import AppMessageResponse, MessageType, AgentRole

def extract_message_content(message):
    """Extract clean content from different message types"""
   


    
def find_messages_in_chunk(chunk, path=""):
    """Recursively find message objects in nested chunk structures"""
    messages = []
    
    if isinstance(chunk, dict):
        for key, value in chunk.items():
            current_path = f"{path}.{key}" if path else key
            
            # Check if this value is a message-like object
            if hasattr(value, 'content') and hasattr(value, '__class__'):
                if any(msg_type in str(type(value)) for msg_type in ['AIMessage', 'HumanMessage', 'ToolMessage', 'SystemMessage']):
                    messages.append(value)
            
            # Check if it's a list of messages
            elif isinstance(value, list):
                for item in value:
                    if hasattr(item, 'content') and hasattr(item, '__class__'):
                        if any(msg_type in str(type(item)) for msg_type in ['AIMessage', 'HumanMessage', 'ToolMessage', 'SystemMessage']):
                            messages.append(item)
                    elif isinstance(item, dict):
                        messages.extend(find_messages_in_chunk(item, current_path))
            
            # Recurse into nested dictionaries
            elif isinstance(value, dict):
                messages.extend(find_messages_in_chunk(value, current_path))
    
    return messages