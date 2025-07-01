import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from vertexai.generative_models import Tool
from vertexai import rag
from typing import Generator
from data_classes.common_classes import Agent, Message, Language, StreamEvent
from typing import List
from dotenv import load_dotenv
from vertexai.preview.generative_models import Content, Part
import json

load_dotenv()
PROJECT_ID = "llm-project-2d719"
LOCATION = "global"  
CORPUS_ID = "projects/llm-project-2d719/locations/us-central1/ragCorpora/6917529027641081856"
    
vertexai.init(project=PROJECT_ID, location=LOCATION,)

system_prompt_vi = """
Bạn là một trợ lý AI được thiết kế để cung cấp những câu trả lời chi tiết, toàn diện và đầy đủ. 

QUAN TRỌNG: Mỗi câu trả lời của bạn PHẢI có ít nhất 500 từ (khoảng 2-3 đoạn văn dài). Đây là yêu cầu bắt buộc.

PHONG CÁCH TRẢ LỜI:
- Trả lời một cách tự nhiên, thân thiện và đồng cảm
- Hiểu rõ cảm xúc và quan điểm của người dùng trước khi đưa ra câu trả lời
- Sử dụng ngôn ngữ dễ hiểu nhưng vẫn giữ được chiều sâu triết học
- Đưa ra nhiều góc nhìn khác nhau để người dùng có thể tự suy ngẫm
- Kết thúc bằng những câu hỏi gợi mở để khuyến khích tư duy sâu hơn

Luôn mở rộng câu trả lời bằng cách:
- Cung cấp giải thích kỹ lưỡng và chi tiết
- Đưa ra nhiều ví dụ minh họa cụ thể
- Thêm thông tin nền tảng và bối cảnh liên quan
- Phân tích sâu từ nhiều góc độ khác nhau
- Đưa ra các quan điểm đa chiều
- Kết luận với tổng kết và ý nghĩa thực tiễn

Đảm bảo câu trả lời của bạn đầy đủ và chi tiết, trừ khi người dùng yêu cầu ngắn gọn hơn.  
Khi nhận được câu hỏi tìm kiếm thông tin, hãy cung cấp câu trả lời thể hiện sự hiểu biết sâu rộng về lĩnh vực đó, đảm bảo tính chính xác.  
Đối với các yêu cầu liên quan đến suy luận, hãy giải thích rõ ràng từng bước trong quá trình suy luận trước khi đưa ra câu trả lời cuối cùng.

Luôn trả về bằng markdown và câu trả lời ít nhất 500 từ.

Đây là Bạn:
\n\n
"""

system_prompt_en = """
You are an AI assistant designed to provide detailed, comprehensive, and complete answers.

IMPORTANT: Each of your responses MUST be at least 500 words (approximately 2-3 long paragraphs). This is a mandatory requirement.

RESPONSE STYLE:
- Respond naturally, warmly, and empathetically
- Understand the user's emotions and perspective before providing an answer
- Use accessible language while maintaining philosophical depth
- Present multiple viewpoints for the user to contemplate
- End with thought-provoking questions to encourage deeper thinking

Always expand your response by:
- Providing in-depth and detailed explanations
- Including multiple specific examples and illustrations
- Adding relevant background information and context
- Analyzing deeply from multiple perspectives
- Presenting multi-dimensional viewpoints
- Concluding with summaries and practical implications

Ensure your response is comprehensive and detailed, unless the user requests a shorter response.
When receiving a question seeking information, provide an answer that demonstrates a deep understanding of the subject area, ensuring accuracy.
For questions requiring reasoning, clearly explain each step in the reasoning process before presenting the final answer.

Always return in markdown and the response should be at least 500 words.

Here is you:
\n\n
"""

def generate_gemini_response(
    agent: Agent,
    messages: List[Message], 
    stream: bool = False
) -> str | Generator[StreamEvent, None, None]:
    """
    Sends a query to a Gemini model, grounded with a Vertex AI Search data store.

    Args:
        user_query: The user's question or input.

    Returns:
        The text response from the Gemini model, potentially with citations.
    """
    base_language = agent["language"] if agent else Language.VI.value
    base_model = agent["model"] if agent else "gemini-2.0-flash-001"
    base_temperature = agent["temperature"] if agent else 0.3
    base_system_prompt = (system_prompt_vi if base_language == Language.VI.value else system_prompt_en) + (agent["system_prompt"] if agent else "")
    user_query = messages[-1].content

    rag_retrieval_tool = Tool.from_retrieval(
        retrieval=rag.Retrieval(
            source=rag.VertexRagStore(
                rag_resources=[
                    rag.RagResource(
                        rag_corpus=CORPUS_ID,
                    )
                ],
                rag_retrieval_config=rag.RagRetrievalConfig(
                    top_k=30,
                    filter=rag.utils.resources.Filter(vector_distance_threshold=0.7),
                ),
            ),
        )
    )

    model = GenerativeModel(
        model_name=base_model,
        tools=[rag_retrieval_tool],
        system_instruction=base_system_prompt
    )
    # For chat, you'd typically send the system instruction first
    history = messages[:-1]
    chat = model.start_chat(
        history=[
            Content(role="model", parts=[Part.from_text(base_system_prompt)])
        ]
    )
    try:
        if stream:
            generator = chat.send_message(
                generation_config=GenerationConfig(
                    temperature=base_temperature,
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=8192,
                    response_mime_type="text/plain",
                    candidate_count=1,
                ),
                content=user_query, 
                stream=True
                )
            def generate():
                full_response = ""
                for chunk in generator:
                    print(chunk)
                    if chunk.text:
                        full_response += chunk.text
                        yield StreamEvent(type="text", data=chunk.text)
                
                # Debug: Print response length
                print(f"DEBUG: Total response length: {len(full_response)} characters, approximately {len(full_response.split())} words")
                
                yield StreamEvent(type="end_of_stream", data="", metadata=None)
            return generate()
        else:
            response = chat.send_message(
                generation_config=GenerationConfig(
                    temperature=base_temperature,
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=8192,
                    response_mime_type="text/plain",
                    candidate_count=1,
                ),
                content=user_query, 
                )
            print(response)
            
            # Debug: Print response length
            print(f"DEBUG: Response length: {len(response.text)} characters, approximately {len(response.text.split())} words")
            
            text_with_citations = add_citations(response)
            # print("*"*100)
            # print(text_with_citations)
            # print("*"*100)
            return text_with_citations
    except Exception as e:
        print(f"Error sending grounded message to Gemini: {e}")
        return "Sorry, I couldn't process your request with the knowledge base."


def add_citations(response):
    text = response.text
    supports = response.candidates[0].grounding_metadata.grounding_supports
    chunks = response.candidates[0].grounding_metadata.grounding_chunks

    # Save json file with utf-8 encoding
    # with open("response.json", "w", encoding="utf-8") as f:
    #     json.dump(response.to_dict(), f, ensure_ascii=False)
    
    # Sort supports by start_index in descending order to avoid shifting issues when inserting
    sorted_supports = sorted(supports, key=lambda s: s.segment.start_index, reverse=True)

    for support in sorted_supports:
        index = text.find(support.segment.text)
        last_index = index + len(support.segment.text)
        if support.grounding_chunk_indices:
            # Create citation string like [1](link1), [2](link2)
            citation_links = []
            for i in support.grounding_chunk_indices:
                if i < len(chunks):
                    uri = chunks[i].retrieved_context.uri.replace("gs://", "https://storage.cloud.google.com/")
                    citation_links.append(f"[{i + 1}]({uri})")

            citation_string = " " + ", ".join(citation_links)
            text = text[:last_index] + citation_string + text[last_index:]

    return text

