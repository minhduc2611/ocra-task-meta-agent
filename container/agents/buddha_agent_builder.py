import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from langgraph.prebuilt import create_react_agent
from data_classes.common_classes import Message, Language, AppMessageResponse
from data_classes.common_classes import MessageType, AgentRole
from langchain_core.prompts import PromptTemplate
from agents.extract_message import extract_message_content, find_messages_in_chunk
from agents.tools.buddha_agent_builder_tools_manager import handle_approval_response, create_frontend_friendly_tools, buddha_agent_tools
from libs.langchain import get_langchain_model
from libs.file_utils import load_prompt_file

#  4 chức năng chính

# Giải đáp cuộc sống: agent trả lời câu hỏi của người dùng 

# Tìm kiếm & Ôn bài: dựa vào các cuốn kinh điển, agent đưa ra câu hỏi hoặc giải đáp, người dùng có thể ôn luyện và tự kiểm tra. Tìm hiểu các bài giảng, triết lý và kinh kệ của Sư Tam Vô. Ôn tập kiến thức Phật pháp một cách có hệ thống.

# Câu hỏi kiểm tra: agent đưa ra câu hỏi để người dùng trả lời. Kiểm tra hiểu biết về giáo pháp Phật giáo. Nhận đánh giá và gợi ý để cải thiện việc học tập.

# Tập làm Kệ: Sáng tác thơ kệ Phật giáo với sự hướng dẫn của BuddhaAI. Học cách diễn đạt tâm tư, cảm xúc qua ngôn ngữ thơ ca.

# Initialize OpenAI model
model = get_langchain_model(model="gpt-4o-mini", temperature=0.7)

# Buddha Agent Builder tools

buddha_agent_prompt = PromptTemplate.from_template("""
{system_prompt}

Current conversation:
{chat_history}

IMPORTANT: Always respond in {answer_language} regardless of input. Do NOT use any other language.

Human: {input}
{agent_scratchpad}
""")


ENGLISH_SYSTEM_PROMPT = """
You are the Buddha Agent Builder - a specialized AI that helps users create, manage, and interact with AI agents imbued with Buddhist wisdom, mindfulness, and compassion.

Your capabilities include:
- Creating Buddhist AI agents with specific focuses (mindfulness, meditation, compassion, wisdom, Zen, Theravada, Mahayana)
- Managing existing Buddhist agents
- Providing authentic Buddhist teachings and practices
- Testing and optimizing Buddhist agents
- Training and fine-tuning Buddhist agents
- Adding knowledge to Buddhist agents
- Searching for knowledge in Buddhist agents
- Adding teaching examples to Buddhist agents

AGENT IMPROVEMENT AND OPTIMIZATION:
- When user provides feedback or requests modifications, analyze and implement improvements to the agent's system prompt
- CRITICAL: check the current system prompt first by get_buddhist_agent_by_id tool and then add, modify, or remove rules based on user context and requirements
- Ensure all new rules follow consistent formatting structure
- Validate that new rules don't conflict with existing ones
- Prioritize clarity and specificity in rule descriptions

RULE FORMATTING STANDARD:
- Use clear, descriptive headers in ALL CAPS
- Follow with bullet points using specific, actionable language
- Include examples when rules might be ambiguous
- Structure format:
```
RULE CATEGORY HEADER:
- Specific instruction or requirement
- Additional clarification or constraint
- Example or exception if needed
```
RULE IMPLEMENTATION GUIDELINES:
- Use imperative language (MUST, ALWAYS, NEVER) for critical requirements
- Use descriptive language (SHOULD, PREFER) for recommendations  
- Include both positive examples (✅) and negative examples (❌) when helpful

EXAMPLES OF WELL-FORMATTED RULES:
```
RESPONSE FORMATTING REQUIREMENTS:
- ALWAYS format responses in markdown
- Use headers, bullet points, and code blocks appropriately
- Never use plain text for structured information

ERROR HANDLING PROTOCOL:
- When encountering errors, explain the issue clearly
- Provide alternative solutions when possible
- NEVER ignore user requests without explanation
```

RULE PRIORITY SYSTEM:
- CRITICAL: System functionality, safety, core behavior
- IMPORTANT: User experience, formatting, consistency  
- PREFERRED: Style guidelines, optimization suggestions

CRITICAL FORMATTING REQUIREMENT:
- Always response in markdown format
- CRITICAL: ALWAYS response with the agent ID in EXACTLY this format: [[<agent_id>]]
- ONLY include the agent ID when the following tool calls are triggered: create_buddhist_agent, update_buddhist_agent, delete_buddhist_agent
- The agent ID must be on a new line after your response
- Use ONLY square brackets, no other text or formatting.
- Never use id of any entity in the system except agent id, dont use approval request id.
- Example format:
  Your response here...
  
  [[57729587-0dbe-477a-ae52-e9fec26f10f3]]

FORMATTING RULES:
- NEVER use formats like:
  ❌ "Your current agent ID: <id>"
  ❌ "Agent ID: <id>"
  ❌ "<id>"
  ❌ "[<id>]"
- ONLY use: [[<agent_id>]]

AGENT SWITCHING REQUIREMENT: 
- When user asks for another agent (e.g., "agent B", "poem agent"), SEARCH for and return the actual agent information
- First search your knowledge base/database for the requested agent
- Return the found agent's details including: name, description, capabilities, etc.
- Also return/attach the actual agent ID at the end in the required format [[<agent_id>]]
- Example:
  User: "Give me information about the poem agent"
  Response: "Here is the information about the Poem Agent:
  
  Name: Creative Poetry Assistant
  Description: Specializes in writing, analyzing, and discussing poetry in various forms and styles
  Capabilities: Haiku creation, sonnet writing, free verse composition, poetry analysis
  
  [[a1b2c3d4-5e6f-7890-abcd-ef1234567890]]"

SEARCH BEHAVIOR:
- If agent is found: Return complete agent information with real agent ID
- If agent not found: Return "Agent '[name]' not found in system" and current agent ID
- Always provide actual data, not placeholder responses

REMINDER: Always end your response with the agent ID in this EXACT format:
[[<agent_id>]]
"""

VIETNAMESE_SYSTEM_PROMPT = """
"""

async def generate_buddha_agent_response(
    messages: List[Message], 
    contexts: List[Dict[str, str]] = None, 
    options: Optional[Dict[str, Any]] = None, 
    language: Language = Language.EN,
    approval_response: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[AppMessageResponse, None]:
    """
    Generate a response using the Buddha Agent Builder and yield messages to client.
    
    Args:
        messages: List of conversation messages
        contexts: Optional context from relevant documents
        options: Optional configuration options
        language: Language preference
        approval_response: Response to pending approval {"approval_id": "...", "approved": True/False}
    Yields:
        Individual messages as they are generated
    """
    try:
        # Handle approval response first
        if approval_response:
            for response in handle_approval_response(approval_response, language):
                yield response
            return
        
        # Prepare the input
        if not messages:
            if language == Language.VI.value:
                yield "Namaste! Tôi là Buddha Agent Builder. Tôi giúp tạo ra các AI agent mang trí tuệ, chánh niệm và từ bi của Phật giáo. Làm thế nào tôi có thể hỗ trợ bạn trên hành trình tâm linh hôm nay?"
            else:
                yield "Namaste! I am the Buddha Agent Builder. I help create AI agents imbued with Buddhist wisdom, mindfulness, and compassion. How may I assist you on your spiritual journey today?"
            return
        
        # Get the latest user message
        latest_message = messages[-1].content
        
        # Add context if available
        if contexts:
            context_text = "\n\n".join([
                f"Context: {ctx['content']}"
                for ctx in contexts
            ])
            latest_message = f"{latest_message}\n\nRelevant context:\n{context_text}"
        
        # Prepare chat history as string
        chat_history = []
        for msg in messages[:-1]:  # Exclude the latest message
            if msg.role == "user":
                chat_history.append(f"Human: {msg.content}")
            elif msg.role == "assistant":
                chat_history.append(f"Assistant: {msg.content}")
        
        chat_history_str = "\n".join(chat_history)
        # system_prompt = ENGLISH_SYSTEM_PROMPT if language == Language.EN.value else VIETNAMESE_SYSTEM_PROMPT
        
        vi_system_prompt = load_prompt_file(filepath="agents/prompts/buddha_agent_builder_vi.txt")
        en_system_prompt = load_prompt_file(filepath="agents/prompts/buddha_agent_builder_en.txt")
        system_prompt = vi_system_prompt if language == Language.VI.value else en_system_prompt
        input_buddha_agent_prompt = buddha_agent_prompt.format(
            system_prompt=system_prompt,
            chat_history=chat_history_str,
            answer_language="Tiếng Việt" if language == Language.VI.value else "English",
            input=latest_message,
            agent_scratchpad=""
        )
    
        # Create the Buddha Agent Builder
        buddha_agent_builder = create_react_agent(
            model=model,
            tools=create_frontend_friendly_tools(buddha_agent_tools),
            prompt=input_buddha_agent_prompt,
            debug=True
        )
  
        async for event in buddha_agent_builder.astream_events(input={"input": latest_message}, version="v2"):
            event_type = event.get("event")
            
            # Stream tool messages (including approval requests)
            if event_type == "on_tool_end":
                tool_data = event.get("data", {})
                tool_output = tool_data.get("output")
                
                # Convert ToolMessage to dict if needed
                if tool_output:
                    if hasattr(tool_output, 'to_dict'):
                        tool_output = tool_output.to_dict()
                    elif hasattr(tool_output, '__dict__'):
                        tool_output = tool_output.__dict__
                    elif not isinstance(tool_output, (dict, str, int, float, bool, type(None))):
                        tool_output = str(tool_output)
                    else:
                        tool_output = str(tool_output)
                print(f"tool_output: {tool_output}")
                yield AppMessageResponse(
                    type=MessageType.TOOL_MESSAGE,
                    content=tool_output if tool_output else "",
                    role=AgentRole.TOOL,
                    tool_name=event.get("name"),
                    tool_call_id=tool_data.get("tool_call_id")
                )
            
            # Stream AI message chunks
            elif event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, 'content'):
                    yield AppMessageResponse(
                        type=MessageType.AI_MESSAGE_CHUNK,
                        content=chunk.content,
                        role=AgentRole.ASSISTANT
                    )
            
            # Stream final AI messages
            elif event_type == "on_chat_model_end":
                message = event.get("data", {}).get("output")
                if message:
                    # Convert message to dict if needed
                    if hasattr(message, 'to_dict'):
                        message_dict = message.to_dict()
                    elif hasattr(message, '__dict__'):
                        message_dict = message.__dict__
                    else:
                        message_dict = {"content": str(message)}
                    
                    yield AppMessageResponse(
                        type=MessageType.AI_MESSAGE_FINAL,
                        content=message_dict.get("content", str(message)),
                        role=AgentRole.ASSISTANT,
                        metadata=message_dict.get("additional_kwargs", {})
                    )
        
    except Exception as e:
        if language == Language.VI.value:
            yield AppMessageResponse(
                type=MessageType.ERROR,
                content=f"Lỗi tạo phản hồi: {str(e)}",
                role=AgentRole.SYSTEM
            )
        else:
            yield AppMessageResponse(
                type=MessageType.ERROR,
                content=f"Error generating response: {str(e)}",
                role=AgentRole.SYSTEM
            )

def generate_buddha_agent_response_sync(messages: List[Message], contexts: List[Dict[str, str]] = None, options: Optional[Dict[str, Any]] = None, language: Language = Language.EN) -> str:
    """
    Generate a response using the Buddha Agent Builder (synchronous version).
    
    Args:
        messages: List of conversation messages
        contexts: Optional context from relevant documents
        options: Optional configuration options
        language: Language preference
    
    Returns:
        The complete response as a string
    """
    try:
        # Use asyncio to run the async generator
        async def collect_responses():
            response_parts = []
            async for message in generate_buddha_agent_response(messages, contexts, options, language):
                response_parts.append(str(message))
            return " ".join(response_parts)
        
        return asyncio.run(collect_responses())
        
    except Exception as e:
        if language == Language.VI.value:
            return f"Lỗi tạo phản hồi: {str(e)}"
        else:
            return f"Error generating response: {str(e)}"

# Convenience function for creating Buddhist agents
# def create_simple_buddhist_agent(name: str, description: str, language: str = "en", author: str = "system") -> Dict[str, Any]:
#     """
#     Create a simple Buddhist agent with basic configuration.
    
#     Args:
#         name: Name of the agent
#         description: Description of the agent
#         language: Language preference ("en" for English, "vi" for Vietnamese)
#         author: Author of the agent
    
#     Returns:
#         Created Buddhist agent information
#     """
#     return create_buddhist_agent(
#         name=name,
#         description=description,
#         language=language,
#         author=author
#     )
