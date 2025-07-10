"""
JSON to JSONL converter utility for fine-tuning data preparation.
"""

import json
import os
import uuid
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def convert_json_to_jsonl(json_data: List[Dict[str, Any]]) -> str:
    """
    Convert JSON data to JSONL format for fine-tuning.
    
    Args:
        json_data: List of dictionaries with the structure:
                  {
                    "contents": [
                      {"role": "user", "parts": [{"text": "..."}]},
                      {"role": "model", "parts": [{"text": "..."}]}
                    ]
                  }
    
    Returns:
        JSONL string with each line being a valid JSON object
    """
    try:
        jsonl_lines = []
        for item in json_data:
            # Validate the structure
            if not isinstance(item, dict) or "contents" not in item:
                raise ValueError("Each item must be a dictionary with 'contents' key")
            
            if not isinstance(item["contents"], list):
                raise ValueError("'contents' must be a list")
            
            # Validate each content item
            for content in item["contents"]:
                if not isinstance(content, dict) or "role" not in content or "parts" not in content:
                    raise ValueError("Each content item must have 'role' and 'parts' keys")
                
                if not isinstance(content["parts"], list):
                    raise ValueError("'parts' must be a list")
                
                for part in content["parts"]:
                    if not isinstance(part, dict) or "text" not in part:
                        raise ValueError("Each part must have a 'text' key")
            
            # Convert to JSONL line
            jsonl_lines.append(json.dumps(item, ensure_ascii=False))
        
        return "\n".join(jsonl_lines)
    
    except Exception as e:
        logger.error(f"Error converting JSON to JSONL: {str(e)}")
        raise ValueError(f"Failed to convert JSON to JSONL: {str(e)}")

def save_jsonl_to_file(jsonl_content: str, filename: str = None, directory: str = None) -> str:
    """
    Save JSONL content to a file.
    
    Args:
        jsonl_content: The JSONL string content
        filename: Optional filename (if not provided, a temporary name will be generated)
        directory: Optional directory path (if not provided, uses 'temp' directory)
    
    Returns:
        Path to the saved file
    """
    try:
        if not filename:
            filename = f"fine_tune_data_{uuid.uuid4().hex[:8]}.jsonl"
        
        # Create directory if it doesn't exist
        if not directory:
            directory = os.path.join(os.getcwd(), "temp")
        
        os.makedirs(directory, exist_ok=True)
        
        file_path = os.path.join(directory, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(jsonl_content)
        
        logger.info(f"JSONL file saved to: {file_path}")
        return file_path
    
    except Exception as e:
        logger.error(f"Error saving JSONL file: {str(e)}")
        raise ValueError(f"Failed to save JSONL file: {str(e)}")

def convert_messages_to_fine_tune_format(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert messages to the format required for Vertex AI fine-tuning.
    
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
        List of dictionaries in the fine-tuning format
    """
    fine_tune_data = []
    
    for message in messages:
        # Skip messages without related messages (we need conversation pairs)
        if not message.get("related_message"):
            continue
        
        # Determine the conversation flow
        if message["role"] == "user" and message["related_message"]["role"] == "assistant":
            # User message followed by assistant response
            conversation = [
                {
                    "role": "user",
                    "parts": [{"text": message["content"]}]
                },
                {
                    "role": "model",
                    "parts": [{"text": message["related_message"]["content"]}]
                }
            ]
        elif message["role"] == "assistant" and message["related_message"]["role"] == "user":
            # Assistant message preceded by user message
            conversation = [
                {
                    "role": "user",
                    "parts": [{"text": message["related_message"]["content"]}]
                },
                {
                    "role": "model",
                    "parts": [{"text": message["content"]}]
                }
            ]
        else:
            # Skip invalid conversation pairs
            continue
        
        fine_tune_data.append({
            "contents": conversation
        })
    
    return fine_tune_data

def validate_fine_tune_data(data: List[Dict[str, Any]]) -> bool:
    """
    Validate that the data is in the correct format for fine-tuning.
    
    Args:
        data: List of dictionaries to validate
    
    Returns:
        True if valid, raises ValueError if invalid
    """
    if not isinstance(data, list):
        raise ValueError("Data must be a list")
    
    if not data:
        raise ValueError("Data list cannot be empty")
    
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Item {i} must be a dictionary")
        
        if "contents" not in item:
            raise ValueError(f"Item {i} must have 'contents' key")
        
        if not isinstance(item["contents"], list):
            raise ValueError(f"Item {i} 'contents' must be a list")
        
        if len(item["contents"]) < 2:
            raise ValueError(f"Item {i} must have at least 2 content items (user and model)")
        
        for j, content in enumerate(item["contents"]):
            if not isinstance(content, dict):
                raise ValueError(f"Item {i}, content {j} must be a dictionary")
            
            if "role" not in content:
                raise ValueError(f"Item {i}, content {j} must have 'role' key")
            
            if "parts" not in content:
                raise ValueError(f"Item {i}, content {j} must have 'parts' key")
            
            if not isinstance(content["parts"], list):
                raise ValueError(f"Item {i}, content {j} 'parts' must be a list")
            
            for k, part in enumerate(content["parts"]):
                if not isinstance(part, dict):
                    raise ValueError(f"Item {i}, content {j}, part {k} must be a dictionary")
                
                if "text" not in part:
                    raise ValueError(f"Item {i}, content {j}, part {k} must have 'text' key")
                
                if not isinstance(part["text"], str):
                    raise ValueError(f"Item {i}, content {j}, part {k} 'text' must be a string")
    
    return True 