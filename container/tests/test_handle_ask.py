import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from flask import Response, Flask, stream_with_context
from services.handle_ask import validate_ask, handle_ask_streaming, handle_ask_non_streaming, AskError
from data_classes.common_classes import AskRequest, Message
from agents.buddha_agent import generate_answer
import json

# Test data
VALID_MESSAGES = [
    Message(role="user", content="What is the meaning of life?", session_id="test-session"),
    Message(role="assistant", content="Let me help you understand...", session_id="test-session"),
    Message(role="user", content="Thank you, but I have a question...", session_id="test-session"),
]

MOCK_DOCUMENTS = [
    {"title": "Document 1", "content": "Content about life"},
    {"title": "Document 2", "content": "More content about meaning"}
]

MOCK_ANSWER = "The meaning of life is to find inner peace and wisdom."

@pytest.fixture
def app():
    """Create a Flask app for testing"""
    app = Flask(__name__)
    return app

@pytest.fixture
def valid_ask_request():
    return AskRequest(
        messages=VALID_MESSAGES,
        session_id="test-session",
        options={}
    )

@pytest.fixture
def streaming_ask_request():
    return AskRequest(
        messages=VALID_MESSAGES,
        session_id="test-session",
        options={"stream": True}
    )

def test_validate_ask_valid_request(valid_ask_request):
    """Test validation of a valid request"""
    errors = validate_ask(valid_ask_request)
    assert len(errors) == 0

def test_validate_ask_missing_messages():
    """Test validation with missing messages"""
    request = AskRequest(messages=[], session_id="test-session")
    errors = validate_ask(request)
    assert "messages is required" in errors

def test_validate_ask_missing_session_id():
    """Test validation with missing session_id"""
    request = AskRequest(messages=VALID_MESSAGES, session_id="")
    errors = validate_ask(request)
    assert "session_id is required" in errors

@patch('services.handle_ask.search_documents')
@patch('services.handle_ask.generate_answer')
@patch('services.handle_ask.insert_to_collection_in_batch')
def test_handle_ask_non_streaming(
    mock_insert,
    mock_generate_answer,
    mock_search_documents,
    valid_ask_request
):
    """Test handle_ask with non-streaming response"""
    # Setup mocks
    mock_search_documents.return_value = MOCK_DOCUMENTS
    mock_generate_answer.return_value = MOCK_ANSWER
    mock_insert.return_value = ["msg-id-1", "msg-id-2"]

    # Call the function
    response = handle_ask_non_streaming(valid_ask_request)

    # Verify the response
    assert isinstance(response, str)
    assert response == MOCK_ANSWER

    # Verify mocks were called correctly
    mock_search_documents.assert_called_once_with(VALID_MESSAGES[-1].content)
    mock_generate_answer.assert_called_once()
    mock_insert.assert_called_once()

@patch('services.handle_ask.search_documents')
@patch('services.handle_ask.generate_answer')
@patch('services.handle_ask.insert_to_collection_in_batch')
def test_handle_ask_streaming(
    mock_insert,
    mock_generate_answer,
    mock_search_documents,
    streaming_ask_request,
    app
):
    """Test handle_ask with streaming response"""
    # Setup mocks
    mock_search_documents.return_value = MOCK_DOCUMENTS
    
    # Mock streaming response
    mock_chunk = MagicMock()
    mock_chunk.choices = [MagicMock(delta=MagicMock(content="streaming "))]
    
    # Create a mock stream that is iterable
    mock_stream = MagicMock()
    mock_stream.__iter__ = MagicMock(return_value=iter([mock_chunk]))
    
    mock_generate_answer.return_value = mock_stream
    mock_insert.return_value = ["msg-id-1", "msg-id-2"]

    # Create a test endpoint that uses handle_ask
    @app.route('/test-stream', methods=['POST'])
    def test_stream():
        return handle_ask_streaming(streaming_ask_request)

    # Test the endpoint using Flask's test client
    with app.test_client() as client:
        response = client.post('/test-stream')
        
        # Verify the response
        assert response.status_code == 200
        assert response.content_type == 'text/event-stream'
        assert b'streaming' in response.data

    # Verify mocks were called correctly
    mock_search_documents.assert_called_once_with(VALID_MESSAGES[-1].content)
    mock_generate_answer.assert_called_once()

@patch('services.handle_ask.search_documents')
def test_handle_ask_no_user_message(mock_search_documents):
    """Test handle_ask with no user message"""
    request = AskRequest(
        messages=[Message(role="assistant", content="Some content", session_id="test-session")],
        session_id="test-session"
    )
    try:
        handle_ask_non_streaming(request)
    except AskError as e:
        assert e.status_code == 400
        assert e.message == "No user message found"


@patch('services.handle_ask.search_documents')
def test_handle_ask_validation_error(mock_search_documents):
    """Test handle_ask with validation error"""
    request = AskRequest(messages=[], session_id="")
    
    try:
        handle_ask_non_streaming(request)
    except AskError as e:
        assert e.status_code == 400
        assert e.message == "messages is required, session_id is required"


@patch('services.handle_ask.search_documents')
@patch('services.handle_ask.generate_answer')
def test_handle_ask_search_error(mock_generate_answer, mock_search_documents):
    """Test handle_ask when search fails"""
    mock_search_documents.side_effect = Exception("Search failed")
    
    try:
        handle_ask_non_streaming(valid_ask_request)
    except AskError as e:
        assert e.status_code == 500
    
    

@patch('services.handle_ask.search_documents')
@patch('services.handle_ask.generate_answer')
@patch('services.handle_ask.insert_to_collection_in_batch')
def test_handle_ask_insert_error(
    mock_insert,
    mock_generate_answer,
    mock_search_documents,
    valid_ask_request
):
    """Test handle_ask when message insertion fails"""
    mock_search_documents.return_value = MOCK_DOCUMENTS
    mock_generate_answer.return_value = MOCK_ANSWER
    mock_insert.side_effect = Exception("Insert failed")
    
    try:
        handle_ask_non_streaming(valid_ask_request)
    except AskError as e:
        assert e.status_code == 500

@patch('services.handle_ask.search_documents')
def test_handle_ask_streaming_no_user_message(mock_search_documents, app):
    """Test handle_ask streaming with no user message"""
    request = AskRequest(
        messages=[Message(role="assistant", content="Some content", session_id="test-session")],
        session_id="test-session",
        options={"stream": True}
    )
    
    response = handle_ask_streaming(request)
    
    assert isinstance(response, Response)
    assert response.status_code == 400
    response_data = json.loads(response.get_data())
    assert response_data["error"] == "No user message found" 