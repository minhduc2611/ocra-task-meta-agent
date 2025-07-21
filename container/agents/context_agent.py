import os
from openai import OpenAI
from typing import List, Dict, Any, Optional
from data_classes.common_classes import Message, Language

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """You are a context generation engine that updates a list of concise behavior rules for an AI assistant.

Input:
persisted previous context:
{previous_context}

user prompt:
{user_prompt}

Instructions:
1. If the user prompt modifies or adds behavioral instructions, extract and summarize them into clear, concise rules.
2. Keep all valid previous rules unless explicitly overridden.
3. If the user prompt does not include any behavioral or stylistic instruction, output just 1 word: "None"
4. Output the final list as bullet points.
5. Output must be in English.

Output:

"""


def generate_context(user_prompt: str, previous_context: Optional[str]) -> Optional[str]:
    try:
        
        system_prompt = SYSTEM_PROMPT
        system_prompt = system_prompt.replace("{previous_context}", previous_context or "")
        system_prompt = system_prompt.replace("{user_prompt}", user_prompt)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        result = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
        if result == "None":
            return None
        return result
        
    except Exception as e:
        raise Exception(f"Error generating context: {str(e)}")
