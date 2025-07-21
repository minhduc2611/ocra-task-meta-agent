import json
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from libs.weaviate_lib import client, insert_to_collection, COLLECTION_AGENTS, COLLECTION_DOCUMENTS, get_object_by_id
from datetime import datetime
import uuid
from weaviate.collections.classes.filters import Filter
from data_classes.common_classes import AgentStatus
from libs.open_ai import basic_openai_answer

# Buddhist wisdom and teachings database
BUDDHIST_TEACHINGS = {
    "four_noble_truths": {
        "en": [
            "The truth of suffering (Dukkha)",
            "The truth of the cause of suffering (Samudāya)",
            "The truth of the end of suffering (Nirodha)",
            "The truth of the path to the end of suffering (Magga)"
        ],
        "vi": [
            "Khổ đế (Dukkha): Sự thật về khổ",
            "Tập đế (Samudāya): Sự thật về nguyên nhân của khổ",
            "Diệt đế (Nirodha): Sự thật về sự chấm dứt khổ",
            "Đạo đế (Magga): Sự thật về con đường diệt khổ"
        ]
    },
    "eightfold_path": {
        "en": [
            "Right Understanding",
            "Right Thought",
            "Right Speech",
            "Right Action",
            "Right Livelihood",
            "Right Effort",
            "Right Mindfulness",
            "Right Concentration"
        ],
        "vi": [
            "Chánh Kiến",
            "Chánh Tư Duy",
            "Chánh Ngữ",
            "Chánh Nghiệp",
            "Chánh Mạng",
            "Chánh Tinh Tấn",
            "Chánh Niệm",
            "Chánh Định"
        ]
    },
    "five_precepts": {
        "en": [
            "Refrain from killing living beings",
            "Refrain from stealing",
            "Refrain from sexual misconduct",
            "Refrain from false speech",
            "Refrain from intoxicants"
        ],
        "vi": [
            "Không sát sinh",
            "Không trộm cắp",
            "Không tà dâm",
            "Không nói dối",
            "Không uống rượu bia"
        ]
    },
    "three_marks_of_existence": {
        "en": [
            "Impermanence (Anicca)",
            "Suffering (Dukkha)",
            "Non-self (Anatta)"
        ],
        "vi": [
            "Vô thường (Anicca)",
            "Khổ (Dukkha)",
            "Vô ngã (Anatta)"
        ]
    }
}

# Tools for the Buddha Agent Builder
@tool
def create_buddhist_agent(
    name: str, description: str, 
    language: str = "en", 
    system_prompt: str = None, 
    model: str = "gpt-4o-mini", 
    temperature: float = 0.7, 
    conversation_starters: List[str] = [],
    tags: List[str] = [],
    author: str = "system"
) -> Dict[str, Any]:
    """
    Create a new AI agent with Buddhist wisdom and teachings.
    
    Args:
        name: Name of the agent
        description: Description of what the agent does
        language: Language preference ("en" for English, "vi" for Vietnamese)
        system_prompt: Custom system prompt
        model: The LLM model to use (gpt-4o-mini, gpt-4o, gemini-2.0-flash-001)
        temperature: Temperature for response generation (default: 0.7)
        author: The user creating the agent
        conversation_starters: List of conversation starters
        tags: List of tags
    
    Returns:
        Dictionary containing the created agent's information
    """
    try:
        agent_id = str(uuid.uuid4())
        
        # Generate system prompt if not provided
        if not system_prompt:
            system_prompt = generate_buddhist_system_prompt(language)
        
        agent_config = {
            "name": name,
            "description": description,
            "language": language,
            "system_prompt": system_prompt,
            "tools": json.dumps([]),
            "model": model,
            "temperature": temperature,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "author": author,
            "status": AgentStatus.ACTIVE.value,
            "conversation_starters": json.dumps(conversation_starters),
            "tags": json.dumps(tags),
            "agent_type": "buddhist"
        }
        
        # Store in Weaviate
        insert_to_collection(COLLECTION_AGENTS, agent_config, agent_id)
        
        return {
            "agent_id": agent_id,
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "model": model,
            "temperature": temperature,
            "author": author,
            "language": language,
            "conversation_starters": json.dumps(conversation_starters),
            "tags": json.dumps(tags),
            "status": AgentStatus.ACTIVE.value,
            "message": f"Buddhist agent '{name}' created successfully in {language}"
        }
    except Exception as e:
        return {"error": f"Failed to create Buddhist agent: {str(e)}"}
      
@tool
def generate_buddhist_system_prompt(language: str = "en") -> str:
    """
    Generate a system prompt for a Buddhist agent based on language.
    
    Args:
        language: Language preference ("en" for English, "vi" for Vietnamese)
    
    Returns:
        Generated system prompt
    """
    return basic_openai_answer(query=f"Generate a system prompt for a Buddhist agent based on language. Language: {language}")
   

@tool
def list_buddhist_agents(author: str = "system", limit: int = 10) -> List[Dict[str, Any]]:
    """
    List all Buddhist agents created by a specific author.
    
    Args:
        author: The author to filter by
        limit: Maximum number of agents to return
    
    Returns:
        List of Buddhist agent configurations
    """
    try:
        filters = (Filter.by_property("agent_type").equal("buddhist"))
        collection = client.collections.get(COLLECTION_AGENTS)
        response = collection.query.fetch_objects(
            limit=limit,
            filters=filters
        )
        
        agents = []
        for obj in response.objects:
            agent_data = obj.properties
            agent_data["uuid"] = obj.uuid
            agents.append(agent_data)
        
        return agents
    except Exception as e:
        return [{"error": f"Failed to list Buddhist agents: {str(e)}"}]

@tool
def get_buddhist_agent_by_id(agent_id: str) -> Dict[str, Any]:
    """
    Get a Buddhist agent by ID.
    
    Args:
        agent_id: The ID of the agent to get

    Returns:
        Dictionary containing the agent's information
    """
    try:
        response = get_object_by_id(COLLECTION_AGENTS, agent_id)
        return response
    except Exception as e:
        return {"error": f"Failed to get Buddhist agent: {str(e)}"}




@tool
def get_buddhist_teachings(category: str = "all", language: str = "en") -> Dict[str, Any]:
    """
    Get Buddhist teachings by category and language.
    
    Args:
        category: Category of teachings (four_noble_truths, eightfold_path, five_precepts, three_marks_of_existence, all)
        language: Language preference ("en" for English, "vi" for Vietnamese)
    
    Returns:
        Buddhist teachings in the specified language
    """
    if category == "all":
        teachings = {}
        for key, value in BUDDHIST_TEACHINGS.items():
            teachings[key] = value.get(language, value["en"])
        return teachings
    else:
        teachings = BUDDHIST_TEACHINGS.get(category, {})
        return {category: teachings.get(language, teachings.get("en", []))}

# deprecated
@tool
def create_meditation_guide(duration: int = 10, type: str = "mindfulness") -> str:
    """
    Create a guided meditation session.
    
    Args:
        duration: Duration in minutes (default: 10)
        type: Type of meditation (mindfulness, loving_kindness, breathing, body_scan)
    
    Returns:
        Guided meditation script
    """
    meditation_guides = {
        "mindfulness": f"""
Mindfulness Meditation ({duration} minutes)

Find a comfortable seated position. Close your eyes or soften your gaze.

1. Take three deep breaths, inhaling through your nose and exhaling through your mouth.

2. Bring your attention to your natural breath. Notice the sensation of breathing - the rise and fall of your chest, the air moving through your nostrils.

3. When your mind wanders (and it will), gently bring your attention back to your breath. Don't judge yourself - this is normal.

4. Continue this practice for {duration} minutes, returning to your breath each time you notice your mind has wandered.

5. When the time is up, take a moment to notice how you feel, then slowly open your eyes.
""",
        "loving_kindness": f"""
Loving-Kindness Meditation ({duration} minutes)

Sit comfortably and close your eyes. Take a few deep breaths.

1. Begin by directing loving-kindness to yourself: "May I be happy. May I be healthy. May I be peaceful. May I be free from suffering."

2. Think of someone you love dearly: "May you be happy. May you be healthy. May you be peaceful. May you be free from suffering."

3. Think of a neutral person: "May you be happy. May you be healthy. May you be peaceful. May you be free from suffering."

4. Think of someone you have difficulty with: "May you be happy. May you be healthy. May you be peaceful. May you be free from suffering."

5. Extend to all beings: "May all beings be happy. May all beings be healthy. May all beings be peaceful. May all beings be free from suffering."

Continue this practice for {duration} minutes.
""",
        "breathing": f"""
Breathing Meditation ({duration} minutes)

Sit comfortably with your back straight but relaxed.

1. Place your hands on your belly and feel it rise and fall with each breath.

2. Count your breaths: Inhale (1), Exhale (2), Inhale (3), Exhale (4)... up to 10, then start over.

3. If you lose count, simply start over at 1. Don't worry about getting it perfect.

4. Continue this practice for {duration} minutes, maintaining gentle focus on your breath and counting.

5. When finished, take a moment to notice the calm that has developed.
""",
        "body_scan": f"""
Body Scan Meditation ({duration} minutes)

Lie down comfortably or sit with your back supported.

1. Take three deep breaths to settle in.

2. Bring your attention to the top of your head. Notice any sensations there.

3. Slowly move your attention down through your body: forehead, eyes, cheeks, jaw, neck, shoulders, arms, hands, chest, back, belly, hips, legs, feet.

4. At each area, pause briefly and notice any sensations - tension, warmth, tingling, or nothing at all.

5. Continue scanning your entire body for {duration} minutes, moving slowly and mindfully.

6. When finished, take a moment to feel your body as a whole.
"""
    }
    
    return meditation_guides.get(type, meditation_guides["mindfulness"])

# deprecated
@tool
def generate_mindfulness_exercise(context: str = "daily_life") -> str:
    """
    Generate a mindfulness exercise for specific contexts.
    
    Args:
        context: Context for the exercise (daily_life, work, eating, walking, stress)
    
    Returns:
        Mindfulness exercise
    """
    exercises = {
        "daily_life": """
Mindful Daily Activities

Choose one daily activity to do mindfully today:

1. Mindful Brushing: Pay full attention to brushing your teeth - the taste of toothpaste, the sensation of the brush, the sound.

2. Mindful Showering: Notice the temperature of the water, the sensation on your skin, the sound of water.

3. Mindful Walking: Feel each step, notice your surroundings, be present with each movement.

4. Mindful Listening: When someone speaks, give them your full attention without planning your response.

5. Mindful Waiting: Instead of checking your phone, simply wait and observe your surroundings and thoughts.
""",
        "work": """
Mindful Work Practice

1. Before starting work, take three deep breaths and set an intention for your work.

2. When switching tasks, pause briefly and take a breath.

3. During meetings, practice mindful listening - focus on what's being said without planning your response.

4. Take mindful breaks - step away from your desk and notice your surroundings.

5. End your workday with a brief reflection on what you accomplished and what you're grateful for.
""",
        "eating": """
Mindful Eating Exercise

1. Before eating, take a moment to appreciate your food and those who made it possible.

2. Notice the colors, smells, and textures of your food.

3. Take small bites and chew slowly, noticing the taste and texture.

4. Put your utensil down between bites.

5. Notice when you're getting full and stop eating when satisfied, not stuffed.

6. Express gratitude for the nourishment.
""",
        "walking": """
Mindful Walking Meditation

1. Walk slowly and deliberately, feeling each step.

2. Notice the sensation of your feet touching the ground.

3. Be aware of your surroundings - sights, sounds, smells.

4. If your mind wanders, bring it back to the sensation of walking.

5. Walk as if you're walking on sacred ground.

6. Practice for 10-15 minutes in a safe, quiet place.
""",
        "stress": """
Mindful Stress Relief

1. STOP: Stop what you're doing, Take a breath, Observe your thoughts and feelings, Proceed mindfully.

2. Take three deep breaths, counting to 4 on inhale, 6 on exhale.

3. Notice where you feel stress in your body - tension in shoulders, jaw, etc.

4. Breathe into those areas, imagining the breath softening the tension.

5. Remind yourself that this moment will pass.

6. Choose one small action to take that would be helpful right now.
"""
    }
    
    return exercises.get(context, exercises["daily_life"])

# deprecated
@tool
def create_compassion_practice(target: str = "self") -> str:
    """
    Create a compassion practice exercise.
    
    Args:
        target: Target of compassion (self, others, difficult_person, all_beings)
    
    Returns:
        Compassion practice exercise
    """
    practices = {
        "self": """
Self-Compassion Practice

1. Place your hands over your heart and take a few deep breaths.

2. Acknowledge your suffering: "This is a moment of suffering" or "I'm having a hard time right now."

3. Remember common humanity: "Suffering is part of being human. I'm not alone in this."

4. Offer yourself kindness: "May I be kind to myself" or "May I give myself the compassion I need."

5. Repeat these phrases silently to yourself for 5-10 minutes.

6. Notice how it feels to be kind to yourself.
""",
        "others": """
Compassion for Others Practice

1. Sit comfortably and close your eyes.

2. Think of someone you care about who is suffering.

3. Imagine their suffering as a dark cloud around them.

4. With each breath, imagine sending them light, warmth, and love.

5. Silently repeat: "May you be free from suffering. May you have peace and happiness."

6. Continue for 5-10 minutes, feeling genuine care for their well-being.
""",
        "difficult_person": """
Compassion for Difficult People

1. Think of someone you have difficulty with (start with someone mildly difficult).

2. Remember that they, like you, want to be happy and avoid suffering.

3. Consider that their harmful actions come from their own suffering and confusion.

4. Silently wish: "May you be free from the suffering that causes you to act this way."

5. Remember that you don't need to approve of their actions to have compassion for their suffering.

6. Practice for 5 minutes, gradually working with more difficult people over time.
""",
        "all_beings": """
Compassion for All Beings

1. Sit comfortably and take a few deep breaths.

2. Imagine all beings in the world - humans, animals, all living things.

3. Recognize that all beings want to be happy and avoid suffering.

4. With each breath, imagine sending compassion to all beings everywhere.

5. Silently repeat: "May all beings be free from suffering. May all beings have peace and happiness."

6. Continue for 10-15 minutes, feeling connected to all life.
"""
    }
    
    return practices.get(target, practices["self"])

@tool
def search_buddhist_agents(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for Buddhist agents using semantic search.
    
    Args:
        query: Search query
        limit: Maximum number of results
    
    Returns:
        List of matching Buddhist agents
    """
    try:
        collection = client.collections.get(COLLECTION_AGENTS)
        response = collection.query.near_text(
            query=query,
            limit=limit,
            certainty=0.7,
            filters=Filter.by_property("agent_type").equal("buddhist")
        )
        
        agents = []
        for obj in response.objects:
            agent_data = obj.properties
            agent_data["uuid"] = obj.uuid
            agents.append(agent_data)
        
        return agents
    except Exception as e:
        return [{"error": f"Failed to search Buddhist agents: {str(e)}"}]

# deprecated
@tool
def test_buddhist_agent(agent_id: str, test_input: str) -> Dict[str, Any]:
    """
    Test a Buddhist agent with a sample input.
    
    Args:
        agent_id: The UUID of the agent to test
        test_input: The test input to send to the agent
    
    Returns:kjhg
        Test results with agent_id
    """
    try:
        # Get agent configuration
        collection = client.collections.get(COLLECTION_AGENTS)
        response = collection.query.fetch_object_by_id(agent_id)
        
        if not response:
            return {"error": "Buddhist agent not found"}
        
        agent_config = response.properties
        
        # Create a simple test instance
        system_prompt = agent_config.get("system_prompt", "")
        model_name = agent_config.get("model", "gpt-4o-mini")
        temperature = agent_config.get("temperature", 0.7)
        
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
            "agent_id": agent_id,
            "agent_name": agent_config.get("name", "Unknown"),
            "test_input": test_input,
            "response": response.content,
            "model_used": model_name,
            "temperature": temperature
        }
    except Exception as e:
        return {"error": f"Failed to test Buddhist agent: {str(e)}"}


# deprecated
@tool
def create_life_guidance_response(question: str, language: str = "en") -> str:
    """
    Provide life guidance based on Buddhist wisdom.
    
    Args:
        question: User's life question or concern
        language: Language preference ("en" for English, "vi" for Vietnamese)
    
    Returns:
        Buddhist wisdom-based guidance
    """
    if language == "vi":
        return f"""Dựa trên câu hỏi của bạn: "{question}"

Tôi sẽ cung cấp hướng dẫn dựa trên giáo pháp Phật giáo. Hãy để tôi suy ngẫm về tình huống này và đưa ra lời khuyên từ góc nhìn của Đức Phật.

Bạn có thể chia sẻ thêm về hoàn cảnh cụ thể để tôi có thể đưa ra hướng dẫn phù hợp hơn không?"""
    else:
        return f"""Based on your question: "{question}"

I will provide guidance based on Buddhist teachings. Let me reflect on this situation and offer advice from the Buddha's perspective.

Could you share more about the specific circumstances so I can provide more appropriate guidance?"""

# deprecated
@tool
def create_study_review_material(topic: str, language: str = "en") -> str:
    """
    Create study and review materials for Buddhist learning.
    
    Args:
        topic: Buddhist topic to study
        language: Language preference ("en" for English, "vi" for Vietnamese)
    
    Returns:
        Study and review material
    """
    if language == "vi":
        return f"""Tài liệu ôn tập về: {topic}

Dựa trên kinh điển và giáo pháp, đây là những điểm chính để ôn tập:

1. Khái niệm cơ bản
2. Ý nghĩa và ứng dụng
3. Cách thực hành
4. Lợi ích và kết quả

Bạn muốn tôi tạo câu hỏi kiểm tra về chủ đề này không?"""
    else:
        return f"""Study and review material for: {topic}

Based on Buddhist scriptures and teachings, here are the key points to review:

1. Basic concepts
2. Meaning and application
3. How to practice
4. Benefits and results

Would you like me to create test questions about this topic?"""

# deprecated
@tool
def create_knowledge_test(topic: str, difficulty: str = "medium", language: str = "en") -> str:
    """
    Create a knowledge test for Buddhist learning.
    
    Args:
        topic: Topic to test
        difficulty: Test difficulty (easy, medium, hard)
        language: Language preference ("en" for English, "vi" for Vietnamese)
    
    Returns:
        Knowledge test with questions
    """
    if language == "vi":
        return f"""Bài kiểm tra kiến thức về: {topic}
Mức độ: {difficulty}

Câu hỏi 1: [Câu hỏi về chủ đề]
A) [Lựa chọn A]
B) [Lựa chọn B]
C) [Lựa chọn C]
D) [Lựa chọn D]

Câu hỏi 2: [Câu hỏi về chủ đề]
A) [Lựa chọn A]
B) [Lựa chọn B]
C) [Lựa chọn C]
D) [Lựa chọn D]

Hãy trả lời các câu hỏi và tôi sẽ đánh giá kiến thức của bạn."""
    else:
        return f"""Knowledge test for: {topic}
Difficulty: {difficulty}

Question 1: [Question about topic]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]

Question 2: [Question about topic]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]

Please answer the questions and I will evaluate your knowledge."""

# deprecated
@tool
def create_buddhist_poetry(theme: str, style: str = "traditional", language: str = "en") -> str:
    """
    Create Buddhist poetry (kệ) based on theme and style.
    
    Args:
        theme: Theme for the poetry
        style: Style of poetry (traditional, modern, zen)
        language: Language preference ("en" for English, "vi" for Vietnamese)
    
    Returns:
        Buddhist poetry
    """
    if language == "vi":
        return f"""Thơ Kệ Phật Giáo
Chủ đề: {theme}
Phong cách: {style}

[Thơ kệ sẽ được tạo dựa trên chủ đề và phong cách]

Hướng dẫn sáng tác:
1. Bắt đầu với cảm xúc chân thành
2. Sử dụng ngôn ngữ đơn giản nhưng sâu sắc
3. Thể hiện giáo pháp một cách tự nhiên
4. Tập trung vào thông điệp tích cực"""
    else:
        return f"""Buddhist Poetry (Gatha)
Theme: {theme}
Style: {style}

[Poetry will be generated based on theme and style]

Creation guidance:
1. Start with sincere emotion
2. Use simple but profound language
3. Express teachings naturally
4. Focus on positive messages"""

@tool
def update_buddhist_agent(agent_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing Buddhist agent's configuration.
    When updating system_prompt, try to keep, combine or modify the original system_prompt and suggest the changes to the user.
    Args:
        agent_id: The UUID of the agent to update
        updates: Dictionary containing the fields to update (name, description, language, system_prompt, model, temperature, status)
    
    Returns:
        Dictionary containing the update result
    """
    try:
        collection = client.collections.get(COLLECTION_AGENTS)
        
        # Check if agent exists
        existing_agent = collection.query.fetch_object_by_id(agent_id)
        if not existing_agent:
            return {"error": "Buddhist agent not found"}
        
        # Validate that this is a Buddhist agent
        if existing_agent.properties.get("agent_type") != "buddhist":
            return {"error": "Agent is not a Buddhist agent"}
        
        # Prepare update data
        update_data = {}
        allowed_fields = ["name", "description", "language", "system_prompt", "model", "temperature", "status"]
        
        for field, value in updates.items():
            if field in allowed_fields:
                update_data[field] = value
        
        # Add updated timestamp
        update_data["updated_at"] = datetime.now()
        
        # Update the agent
        collection.data.update(
            uuid=agent_id,
            properties=update_data
        )
        
        return {
            "agent_id": agent_id,
            "message": f"Buddhist agent '{existing_agent.properties.get('name', 'Unknown')}' updated successfully",
            "updated_fields": list(update_data.keys())
        }
    except Exception as e:
        return {"error": f"Failed to update Buddhist agent: {str(e)}"}

@tool
def delete_buddhist_agent(agent_id: str) -> Dict[str, Any]:
    """
    Delete a Buddhist agent.
    
    Args:
        agent_id: The UUID of the agent to delete
    
    Returns:
        Dictionary containing the deletion result
    """
    try:
        collection = client.collections.get(COLLECTION_AGENTS)
        
        # Check if agent exists
        existing_agent = collection.query.fetch_object_by_id(agent_id)
        if not existing_agent:
            return {"error": "Buddhist agent not found"}
        
        # Validate that this is a Buddhist agent
        if existing_agent.properties.get("agent_type") != "buddhist":
            return {"error": "Agent is not a Buddhist agent"}
        
        agent_name = existing_agent.properties.get("name", "Unknown")
        
        # Delete the agent
        collection.data.delete_by_id(agent_id)
        
        return {
            "agent_id": agent_id,
            "status": AgentStatus.DELETED.value,
            "message": f"Buddhist agent '{agent_name}' deleted successfully"
        }
    except Exception as e:
        return {"error": f"Failed to delete Buddhist agent: {str(e)}"}

@tool
def add_buddhist_knowledge_to_context(
    title: str, 
    content: str, 
    category: str = "general", 
    language: str = "en", 
    source: str = "buddha_agent",
    author: str = "system"
) -> Dict[str, Any]:
    """
    Add Buddhist knowledge and teachings to the vector store for future retrieval and learning.
    
    Args:
        title: Title of the knowledge piece
        content: The Buddhist teaching, wisdom, or knowledge content
        category: Category of knowledge (meditation, wisdom, compassion, mindfulness, sutras, koans, general)
        language: Language of the content ("en" for English, "vi" for Vietnamese)
        source: Source of the knowledge (buddha_agent, user_input, sutra, teacher)
        author: The author or creator of this knowledge
    
    Returns:
        Dictionary containing the result of adding knowledge to the vector store
    """
    try:
        # Create a unique ID for this knowledge piece
        knowledge_id = "rag_context_" + str(uuid.uuid4())
        
        # Create description based on category and content
        description = f"Buddhist knowledge about {category} in {language}"
        
        # Prepare the knowledge data for storage
        knowledge_data = {
            "title": title,
            "content": content,
            "description": description,
            "category": category,
            "language": language,
            "source": source,
            "author": author,
            "knowledge_type": "buddhist",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        # Store in Weaviate Documents collection
        stored_id = insert_to_collection(COLLECTION_DOCUMENTS, knowledge_data)
        
        return {
            "knowledge_id": stored_id,
            "title": title,
            "category": category,
            "language": language,
            "status": AgentStatus.ACTIVE.value,
            "message": f"Buddhist knowledge '{title}' added successfully to the knowledge base",
            "content_preview": content[:100] + "..." if len(content) > 100 else content
        }
    except Exception as e:
        return {"error": f"Failed to add Buddhist knowledge to context: {str(e)}"}

@tool
def search_buddhist_knowledge(
    query: str, 
    category: str = None, 
    language: str = "en", 
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search for Buddhist knowledge in the vector store.
    
    Args:
        query: Search query
        category: Filter by category (optional)
        language: Language preference ("en" for English, "vi" for Vietnamese)
        limit: Maximum number of results to return
    
    Returns:
        List of matching Buddhist knowledge pieces
    """
    try:
        from libs.weaviate_lib import search_vector_collection, COLLECTION_DOCUMENTS
        from weaviate.collections.classes.filters import Filter
        
        # Build filters
        filters = Filter.by_property("knowledge_type").equal("buddhist")
        
        if category:
            filters = filters & Filter.by_property("category").equal(category)
        
        if language:
            filters = filters & Filter.by_property("language").equal(language)
        
        # Search the documents collection
        results = search_vector_collection(
            collection_name=COLLECTION_DOCUMENTS,
            query=query,
            limit=limit,
            filters=filters
        )
        
        return results
    except Exception as e:
        return [{"error": f"Failed to search Buddhist knowledge: {str(e)}"}]

@tool
def add_buddhist_teaching_example(
    teaching_type: str,
    example_content: str,
    language: str = "en",
    difficulty: str = "beginner"
) -> Dict[str, Any]:
    """
    Add a specific Buddhist teaching example to the knowledge base.
    
    Args:
        teaching_type: Type of teaching (sutra, koan, meditation_instruction, wisdom_story, practice_guidance)
        example_content: The teaching content
        language: Language preference ("en" for English, "vi" for Vietnamese)
        difficulty: Difficulty level (beginner, intermediate, advanced)
    
    Returns:
        Dictionary containing the result of adding the teaching example
    """
    try:
        # Generate appropriate title based on teaching type
        titles = {
            "sutra": f"Buddhist Sutra Teaching - {language.upper()}",
            "koan": f"Zen Koan - {language.upper()}",
            "meditation_instruction": f"Meditation Instruction - {difficulty.title()}",
            "wisdom_story": f"Buddhist Wisdom Story - {language.upper()}",
            "practice_guidance": f"Practice Guidance - {difficulty.title()}"
        }
        
        title = titles.get(teaching_type, f"Buddhist Teaching - {teaching_type}")
        
        # Add to knowledge base
        return add_buddhist_knowledge_to_context(
            title=title,
            content=example_content,
            category=teaching_type,
            language=language,
            source="buddha_agent_teaching",
            author="buddha_agent"
        )
    except Exception as e:
        return {"error": f"Failed to add Buddhist teaching example: {str(e)}"}

@tool
def add_user_insight_to_knowledge_base(
    insight: str,
    context: str = "",
    language: str = "en"
) -> Dict[str, Any]:
    """
    Add a user's insight or realization to the Buddhist knowledge base for learning.
    
    Args:
        insight: The user's insight or realization
        context: Context about when/where this insight occurred (optional)
        language: Language of the insight ("en" for English, "vi" for Vietnamese)
    
    Returns:
        Dictionary containing the result of adding the insight
    """
    try:
        title = f"User Insight - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Combine insight with context if provided
        full_content = insight
        if context:
            full_content = f"Context: {context}\n\nInsight: {insight}"
        
        return add_buddhist_knowledge_to_context(
            title=title,
            content=full_content,
            category="user_insight",
            language=language,
            source="user_input",
            author="user"
        )
    except Exception as e:
        return {"error": f"Failed to add user insight: {str(e)}"}



