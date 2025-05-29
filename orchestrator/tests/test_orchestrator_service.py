import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json
from ..orchestrator_service import app

client = TestClient(app)

# Mock responses
MOCK_MARKET_DATA = {
    "symbol": "AAPL",
    "price": 150.0,
    "change": 2.5,
    "percent_change": 1.67,
    "volume": 1000000,
    "timestamp": "2024-02-20T12:00:00Z"
}

MOCK_SCRAPING_DATA = {
    "symbol": "AAPL",
    "document_type": "sec_filing",
    "documents": [
        {
            "title": "10-K Report",
            "url": "https://example.com/10k",
            "date": "2024-02-20"
        }
    ]
}

MOCK_SEARCH_RESULTS = {
    "query": "earnings growth",
    "results": [
        {
            "title": "Q4 Earnings Report",
            "content": "Strong earnings growth...",
            "source": "10-K",
            "date": "2024-02-20"
        }
    ]
}

@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock:
        mock_client = AsyncMock()
        mock.return_value.__aenter__.return_value = mock_client
        yield mock_client

def test_health_check(mock_httpx_client):
    # Mock Redis ping
    with patch("redis.Redis.ping") as mock_ping:
        mock_ping.return_value = True
        
        # Mock service health checks
        mock_httpx_client.get.side_effect = [
            AsyncMock(status_code=200),  # API agent
            AsyncMock(status_code=200),  # Scraping agent
            AsyncMock(status_code=200)   # Retriever agent
        ]
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert all(data["services"].values())

def test_get_market_data(mock_httpx_client):
    mock_httpx_client.get.return_value = AsyncMock(
        status_code=200,
        json=lambda: MOCK_MARKET_DATA
    )
    
    response = client.get("/market-data/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert "price" in data

def test_scrape_data(mock_httpx_client):
    mock_httpx_client.post.return_value = AsyncMock(
        status_code=200,
        json=lambda: MOCK_SCRAPING_DATA
    )
    
    request_data = {
        "symbol": "AAPL",
        "document_type": "sec_filing",
        "start_date": "2024-01-01",
        "end_date": "2024-02-20"
    }
    
    response = client.post("/scrape", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert "documents" in data

def test_search_documents(mock_httpx_client):
    mock_httpx_client.post.return_value = AsyncMock(
        status_code=200,
        json=lambda: MOCK_SEARCH_RESULTS
    )
    
    request_data = {
        "query": "earnings growth",
        "document_type": "sec_filing",
        "limit": 10
    }
    
    response = client.post("/search", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0

def test_analyze_data(mock_httpx_client):
    # Mock responses for different data types
    mock_httpx_client.get.return_value = AsyncMock(
        status_code=200,
        json=lambda: MOCK_MARKET_DATA
    )
    
    mock_httpx_client.post.side_effect = [
        AsyncMock(status_code=200, json=lambda: MOCK_SCRAPING_DATA),  # SEC filings
        AsyncMock(status_code=200, json=lambda: MOCK_SCRAPING_DATA),  # Earnings calls
        AsyncMock(status_code=200, json=lambda: MOCK_SCRAPING_DATA)   # News
    ]
    
    request_data = {
        "symbol": "AAPL",
        "analysis_type": "all",
        "start_date": "2024-01-01",
        "end_date": "2024-02-20"
    }
    
    response = client.post("/analyze", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert "market_data" in data
    assert "sec_filings" in data
    assert "earnings_calls" in data
    assert "news" in data

def test_error_handling(mock_httpx_client):
    # Test market data error
    mock_httpx_client.get.return_value = AsyncMock(
        status_code=500,
        json=lambda: {"detail": "Internal server error"}
    )
    
    response = client.get("/market-data/AAPL")
    assert response.status_code == 500
    
    # Test scraping error
    mock_httpx_client.post.return_value = AsyncMock(
        status_code=500,
        json=lambda: {"detail": "Internal server error"}
    )
    
    request_data = {
        "symbol": "AAPL",
        "document_type": "sec_filing"
    }
    
    response = client.post("/scrape", json=request_data)
    assert response.status_code == 500 