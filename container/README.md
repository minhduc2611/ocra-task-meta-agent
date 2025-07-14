# Buddha-Py - AI Agent Platform

A comprehensive AI platform that includes multiple specialized agents and a powerful meta agent for building AI agents.

## 🚀 Features

### Core Platform
- **Buddha Agent**: AI monk that provides guidance on Buddhist teachings
- **Summary Agent**: Intelligent document summarization and analysis
- **Meta Agent**: AI agent builder that helps create and manage other AI agents
- **Document Management**: Upload, process, and search documents
- **User Authentication**: Secure user management with JWT tokens
- **Vector Database**: Weaviate integration for semantic search

### Meta Agent Capabilities
- **Agent Creation**: Create new AI agents with custom system prompts and tools
- **Agent Management**: List, update, delete, and search existing agents
- **Code Generation**: Automatically generate Python code for your agents
- **Agent Testing**: Test agents with sample inputs to verify functionality
- **Semantic Search**: Find agents using natural language queries
- **Best Practices**: Get guidance on agent design and optimization

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- OpenAI API key
- Weaviate instance (cloud or local)

### Setup

1. **Create a virtual environment**:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables** in your `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
WEAVIATE_URL=your_weaviate_url
WEAVIATE_API_KEY=your_weaviate_api_key
EMBEDDING_MODEL=text-embedding-3-small
```

4. **Test the installation**:
```bash
python test_meta_agent.py
```

## 🧪 Testing

### Test Meta Agent
```bash
python test_meta_agent.py
```

### Test Example Usage
```bash
python example_meta_agent.py
```

### Run the Platform
```bash
python main.py
```

## 📖 Usage

### Meta Agent - Building AI Agents

The meta agent is the star feature that helps you create and manage AI agents:

```python
from agents.meta_agent import generate_meta_agent_response
from data_classes.common_classes import Message, Language

# Chat with the meta agent
messages = [
    Message(role="user", content="I want to create an AI agent for customer service. Can you help me?")
]

response = generate_meta_agent_response(
    messages=messages,
    language=Language.EN
)

print(response)
```

### Creating Agents

```python
from agents.meta_agent import create_simple_agent

# Create a customer service agent
agent = create_simple_agent(
    name="Customer Service Agent",
    description="A helpful customer service agent",
    system_prompt="""You are a helpful customer service agent. Your role is to:
- Answer customer questions about products and services
- Help with order status and tracking
- Be polite, professional, and helpful""",
    author="your_email@example.com"
)
```

### API Endpoints

The platform provides RESTful APIs for all functionality:

#### Meta Agent Chat
```bash
POST /api/v1/meta-agent/chat
```

#### Agent Management
```bash
POST /api/v1/agents          # Create agent
GET /api/v1/agents           # List agents
GET /api/v1/agents/{id}      # Get agent
PUT /api/v1/agents/{id}      # Update agent
DELETE /api/v1/agents/{id}   # Delete agent
GET /api/v1/agents/search    # Search agents
GET /api/v1/agents/{id}/code # Generate code
POST /api/v1/agents/{id}/test # Test agent
```

## 🏗️ Architecture

### Components
- **Flask Backend**: RESTful API server
- **Weaviate Database**: Vector database for semantic search
- **OpenAI Integration**: Language models for AI agents
- **LangChain**: Framework for building AI applications
- **JWT Authentication**: Secure user management

### Agents
1. **Buddha Agent**: Specialized in Buddhist teachings
2. **Summary Agent**: Document analysis and summarization
3. **Meta Agent**: AI agent builder and manager

## 📚 Documentation

- [Meta Agent Guide](META_AGENT_README.md) - Comprehensive guide for the meta agent
- [API Documentation](docs/api.md) - API reference (coming soon)
- [Agent Development Guide](docs/agent-development.md) - How to create custom agents (coming soon)

## 🔧 Development

### Adding Dependencies
```bash
pip install <package-name>
pip freeze > requirements.txt
```

### Project Structure
```
├── agents/                 # AI agents
│   ├── meta_agent.py      # Meta agent for building agents
│   ├── buddha_agent.py    # Buddhist teachings agent
│   └── sumary_agent.py    # Document summarization agent
├── data_classes/          # Data models
├── libs/                  # Utility libraries
├── services/              # Business logic
├── tests/                 # Test files
├── main.py               # Flask application
├── example_meta_agent.py # Example usage
└── test_meta_agent.py    # Test suite
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

If you encounter any issues:
1. Check that all environment variables are set correctly
2. Verify your Weaviate instance is running and accessible
3. Ensure your OpenAI API key is valid
4. Run the test suite: `python test_meta_agent.py`

For additional help, please open an issue in the repository.
