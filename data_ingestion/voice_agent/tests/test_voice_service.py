import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
from datetime import datetime
from ..main import app
from ..voice_service import VoiceService, VoiceResponse

client = TestClient(app)

@pytest.fixture
def mock_voice_service():
    with patch('voice_agent.voice_service.VoiceService') as mock:
        service = mock.return_value
        service.text_to_speech.return_value = VoiceResponse(
            text="Test response",
            timestamp=datetime.now()
        )
        service.speech_to_text.return_value = "Test transcription"
        service.process_market_query.return_value = VoiceResponse(
            text="Market data response",
            timestamp=datetime.now()
        )
        yield service

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_text_to_speech(mock_voice_service):
    """Test text to speech conversion"""
    response = client.post(
        "/text-to-speech",
        json={"text": "Test message", "language": "en-US"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "timestamp" in data

def test_speech_to_text(mock_voice_service):
    """Test speech to text conversion"""
    # Create a dummy audio file
    audio_content = b"dummy audio content"
    files = {"audio_file": ("test.wav", audio_content, "audio/wav")}
    
    response = client.post("/speech-to-text", files=files)
    assert response.status_code == 200
    assert "text" in response.json()

def test_market_query(mock_voice_service):
    """Test market data query processing"""
    response = client.post(
        "/market-query",
        json={"text": "AAPL", "language": "en-US"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "timestamp" in data

def test_invalid_audio_file():
    """Test speech to text with invalid audio file"""
    # Send empty file
    files = {"audio_file": ("test.wav", b"", "audio/wav")}
    response = client.post("/speech-to-text", files=files)
    assert response.status_code == 500

def test_invalid_market_query(mock_voice_service):
    """Test market query with invalid input"""
    mock_voice_service.process_market_query.side_effect = Exception("Invalid query")
    
    response = client.post(
        "/market-query",
        json={"text": "INVALID", "language": "en-US"}
    )
    assert response.status_code == 500 