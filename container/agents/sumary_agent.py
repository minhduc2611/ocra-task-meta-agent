import os
from openai import OpenAI
from typing import List, Dict, Any, Optional
from data_classes.common_classes import Message, Language

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# System prompts for different languages
SYSTEM_PROMPT_VI = """Bạn là một trợ lý AI chuyên nghiệp trong việc tóm tắt nội dung cuộc trò chuyện.
Nhiệm vụ của bạn là tạo ra một tiêu đề ngắn gọn và súc tích (không quá 10 từ) dựa trên tin nhắn đầu tiên của cuộc trò chuyện.
Tiêu đề nên:
1. Phản ánh chính xác nội dung chính của cuộc trò chuyện
2. Ngắn gọn và dễ hiểu
3. Sử dụng ngôn ngữ tự nhiên
4. Không chứa dấu câu ở cuối câu
5. Không chứa các từ thừa như "Cuộc trò chuyện về..." hoặc "Hỏi về..."

Chỉ trả về tiêu đề, không cần giải thích thêm."""

SYSTEM_PROMPT_EN = """You are a professional AI assistant specialized in summarizing conversations.
Your task is to create a concise title (no more than 10 words) based on the first message of the conversation.
The title should:
1. Accurately reflect the main content of the conversation
2. Be concise and clear
3. Use natural language
4. Not end with punctuation
5. Not include filler words like "Conversation about..." or "Question about..."

Return only the title, no additional explanation."""

def generate_summary(messages: List[Message], language: Language = Language.VI) -> str:
    """
    Generate a summary title from the first message of a conversation
    
    Args:
        messages (List[Message]): List of messages in the conversation
        language (Language): The language for the summary (VI or EN)
        
    Returns:
        str: A concise title summarizing the conversation
        
    Raises:
        Exception: If there's an error generating the summary
    """
    try:
        # Prepare the conversation context
        conversation = "Here is the conversation:\n" + "\n".join([f"{msg.role}: {msg.content}" for msg in messages])
        
        # Prepare the system prompt
        if language == Language.VI.value:
            system_prompt = SYSTEM_PROMPT_VI
        else:
            system_prompt = SYSTEM_PROMPT_EN
        
        # Generate summary using OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": conversation}
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        # Extract and clean the summary
        summary = response.choices[0].message.content.strip()
        
        # Remove any trailing punctuation
        summary = summary.rstrip('.,!?')
        
        return summary
        
    except Exception as e:
        raise Exception(f"Error generating summary: {str(e)}")

def generate_detailed_summary(messages: List[Message], language: Language = Language.VI) -> str:
    """
    Generate a detailed summary of a conversation
    
    Args:
        messages (List[Message]): List of messages in the conversation
        language (Language): The language for the summary (VI or EN)
        
    Returns:
        str: A detailed summary of the conversation
        
    Raises:
        Exception: If there's an error generating the summary
    """
    try:
        # Prepare the conversation context
        conversation = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])
        
        # System prompt for detailed summary
        if language == Language.VI:
            system_prompt = """Bạn là một trợ lý AI chuyên nghiệp trong việc tóm tắt cuộc trò chuyện.
            Hãy tạo một bản tóm tắt chi tiết về cuộc trò chuyện, bao gồm:
            1. Các điểm chính được thảo luận
            2. Kết luận hoặc giải pháp (nếu có)
            3. Các câu hỏi quan trọng và câu trả lời
            
            Tóm tắt nên ngắn gọn nhưng đầy đủ thông tin."""
        else:
            system_prompt = """You are a professional AI assistant specialized in summarizing conversations.
            Create a detailed summary of the conversation, including:
            1. Main points discussed
            2. Conclusions or solutions (if any)
            3. Important questions and answers
            
            The summary should be concise but informative."""
        
        # Generate detailed summary using OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": conversation}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        raise Exception(f"Error generating detailed summary: {str(e)}")
