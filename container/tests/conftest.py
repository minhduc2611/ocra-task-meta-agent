import pytest
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    # Set test environment variables
    os.environ["WEAVIATE_URL"] = "http://test-weaviate:8080"
    os.environ["WEAVIATE_API_KEY"] = "test-key"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["EMBEDDING_MODEL"] = "text-embedding-3-small"
    
    yield
    
    # Cleanup after tests
    for key in ["WEAVIATE_URL", "WEAVIATE_API_KEY", "OPENAI_API_KEY", "EMBEDDING_MODEL"]:
        if key in os.environ:
            del os.environ[key] 