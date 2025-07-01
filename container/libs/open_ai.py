import os
from openai import OpenAI
from typing import List, Dict, Any, Optional, Generator
from data_classes.common_classes import Message, Language, Agent
from services.handle_agent import get_agent_by_id
from data_classes.common_classes import StreamEvent
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_openai_answer(
    agent: Agent,
    messages: List[Message], 
    contexts: List[Dict[str, str]], 
    stream: bool = False,
) -> str | Generator[StreamEvent, None, None]:
    try:
        base_language = agent["language"] if agent else Language.VI
        base_model = agent["model"] if agent else "gpt-4o"
        base_temperature = agent["temperature"] if agent else 0
        base_system_prompt = agent["system_prompt"] if agent else ""
        
        # Prepare the context from relevant documents
        context_text = "\n\n".join([
            f"Source: {ctx['title']}\nContent: {ctx['content']}"
            for ctx in contexts
        ])
        
        # if not system_prompt:
        #     if language == Language.VI.value:
        #         system_prompt = SYSTEM_PROMPT_VI
        #     else:
        #         system_prompt = SYSTEM_PROMPT_EN
        
        if base_language == Language.VI.value:
            instruction = "Đây là nội dung liên quan đến câu hỏi của bạn"
        else:
            instruction = "Here is the relevant context from our knowledge base"
        # Prepare the messages for the chat
        chat_messages = [
            {"role": "system", "content": base_system_prompt},
            {"role": "system", "content": f"{instruction}:\n\n{context_text}"}
        ]
            
        # Add the conversation history
        for msg in messages:
            chat_messages.append({"role": msg.role, "content": msg.content})

        if stream:
            generator = client.chat.completions.create(
                model=base_model, 
                messages=chat_messages,
                temperature=base_temperature,
                max_completion_tokens=1500,
                stream=True
            )
            def generate():
                for chunk in generator:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        yield StreamEvent(type="text", data=content)
                
                yield StreamEvent(type="end_of_stream", data="", metadata=contexts)
            return generate()
        else:
            response = client.chat.completions.create(
                model=base_model, 
                messages=chat_messages,
                temperature=base_temperature,
                max_completion_tokens=1500,
                stream=False
            )
            return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error generating answer: {e}")


def basic_openai_answer(query: str, model: str = "gpt-4o", temperature: float = 0) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": query}],
            temperature=temperature,
            max_completion_tokens=1500,
            stream=False
        )
        result = response.choices[0].message.content
        print("***", result)
        return result
    except Exception as e:
        raise Exception(f"Error generating answer: {e}")