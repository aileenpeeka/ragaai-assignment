import pytest
import requests
import json
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from pathlib import Path
from data_ingestion.scraping_agent.scraper_service import app, FilingData

client = TestClient(app)

BASE_URL = "http://localhost:8000"

@pytest.fixture
def mock_yfinance():
    with patch('data_ingestion.scraping_agent.scraper_service.yf.Ticker') as mock:
        mock_instance = MagicMock()
        mock_instance.info = {
            "longName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "currency": "USD"
        }
        mock_instance.financials = MagicMock()
        mock_instance.financials.to_dict.return_value = {"revenue": 1000000}
        mock_instance.quarterly_financials = MagicMock()
        mock_instance.quarterly_financials.to_dict.return_value = {"revenue": 250000}
        mock.return_value = mock_instance
        yield mock

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Financial Data Scraper Service Running"}

def test_get_filings(mock_yfinance):
    """Test getting SEC filings"""
    response = client.post("/filings?symbols=AAPL&filing_type=10-K&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"
    assert data[0]["filing_type"] == "10-K"
    assert "filing_date" in data[0]
    assert "content" in data[0]

def test_get_filings_not_found(mock_yfinance):
    """Test getting SEC filings when none exist"""
    mock_yfinance.return_value.financials.empty = True
    response = client.post("/filings?symbols=AAPL&filing_type=10-K&limit=5")
    assert response.status_code == 404

def test_get_historical_prices(mock_yfinance):
    """Test getting historical price data"""
    mock_yfinance.return_value.history.return_value = MagicMock()
    mock_yfinance.return_value.history.return_value.to_dict.return_value = [{"date": "2024-01-01", "close": 150.0}]
    
    response = client.get("/historical-prices/AAPL?period=1mo&interval=1d")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "date" in data[0]
    assert "close" in data[0]

def test_get_analyst_recommendations(mock_yfinance):
    """Test getting analyst recommendations"""
    mock_yfinance.return_value.recommendations = MagicMock()
    mock_yfinance.return_value.recommendations.to_dict.return_value = [{"date": "2024-01-01", "recommendation": "Buy"}]
    
    response = client.get("/analyst-recommendations/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "date" in data[0]
    assert "recommendation" in data[0]

def test_filing_data_model():
    """Test FilingData Pydantic model"""
    data = {
        "symbol": "AAPL",
        "filing_type": "10-K",
        "filing_date": datetime.now(),
        "url": "https://example.com/filing",
        "content": "Test content"
    }
    filing_data = FilingData(**data)
    assert filing_data.symbol == "AAPL"
    assert filing_data.filing_type == "10-K"
    assert filing_data.url == "https://example.com/filing"
    assert filing_data.content == "Test content" 