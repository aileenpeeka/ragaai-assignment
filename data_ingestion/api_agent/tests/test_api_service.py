import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime
from data_ingestion.api_agent.api_service import app, MarketData

client = TestClient(app)

@pytest.fixture
def mock_yfinance():
    # Shared mock instance for valid symbols
    mock_data = pd.DataFrame({
        'Open': [100.0, 101.0],
        'High': [102.0, 103.0],
        'Low': [99.0, 100.0],
        'Close': [101.0, 102.0],
        'Volume': [1000000, 1100000]
    })
    shared_mock_instance = MagicMock()
    shared_mock_instance.history.return_value = mock_data
    def ticker_side_effect(symbol):
        if symbol == 'INVALID':
            raise Exception('Invalid symbol')
        return shared_mock_instance
    with patch('data_ingestion.api_agent.api_service.yf.Ticker', side_effect=ticker_side_effect) as mock:
        yield mock

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_get_market_data(mock_yfinance):
    """Test getting market data for a single symbol"""
    response = client.get("/market-data/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert "price" in data
    assert "change" in data
    assert "change_percent" in data
    assert "volume" in data
    assert "timestamp" in data
    assert "source" in data
    assert "additional_data" in data

def test_get_market_data_invalid_symbol():
    """Test getting market data for an invalid symbol"""
    response = client.get("/market-data/INVALID")
    assert response.status_code == 404

def test_get_batch_market_data(mock_yfinance):
    """Test getting market data for multiple symbols"""
    response = client.get("/market-data/batch?symbols=AAPL,GOOGL,MSFT")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(isinstance(item, dict) for item in data)
    assert all("symbol" in item for item in data)

def test_get_historical_data(mock_yfinance):
    """Test getting historical market data"""
    response = client.get("/market-data/historical/AAPL?period=1mo&interval=1d")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["period"] == "1mo"
    assert data["interval"] == "1d"
    assert "data" in data

def test_market_data_model():
    """Test MarketData Pydantic model"""
    data = {
        "symbol": "AAPL",
        "price": 150.0,
        "change": 2.0,
        "change_percent": 1.5,
        "percent_change": 1.5,
        "volume": 1000000,
        "timestamp": datetime.now(),
        "source": "Yahoo Finance",
        "additional_data": {
            "open": 148.0,
            "high": 151.0,
            "low": 147.0,
            "prev_close": 148.0
        }
    }
    market_data = MarketData(**data)
    assert market_data.symbol == "AAPL"
    assert market_data.price == 150.0
    assert market_data.change == 2.0
    assert market_data.change_percent == 1.5
    assert market_data.volume == 1000000
    assert market_data.source == "Yahoo Finance"
    assert market_data.additional_data is not None

@pytest.mark.asyncio
async def test_cache_behavior(mock_yfinance):
    """Test that the cache is working correctly"""
    from data_ingestion.api_agent import api_service
    api_service.CACHE.clear()

    # First request
    response1 = client.get("/market-data/AAPL")
    assert response1.status_code == 200
    cache_key = "market_data:AAPL"
    assert cache_key in api_service.CACHE
    first_cached = api_service.CACHE[cache_key]["data"]

    # Second request should use cache
    response2 = client.get("/market-data/AAPL")
    assert response2.status_code == 200
    # Cache should not change
    assert api_service.CACHE[cache_key]["data"] == first_cached

def test_cache_clear_endpoint():
    """Test clearing the cache via the /cache/clear endpoint"""
    # Fill the cache
    from data_ingestion.api_agent import api_service
    api_service.CACHE['test'] = {'data': 'dummy', 'timestamp': 0}
    assert api_service.CACHE
    response = client.post("/cache/clear")
    assert response.status_code == 200
    assert response.json()["status"] == "cache cleared"
    assert not api_service.CACHE

def test_refresh_market_data(mock_yfinance):
    """Test force-refreshing market data bypassing the cache"""
    # Fill the cache with dummy data
    from data_ingestion.api_agent import api_service
    api_service.CACHE['market_data:AAPL'] = {'data': 'dummy', 'timestamp': 0}
    response = client.get("/market-data/AAPL/refresh")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    # The cache should now be updated with real data
    assert isinstance(api_service.CACHE['market_data:AAPL']['data'], dict) or hasattr(api_service.CACHE['market_data:AAPL']['data'], 'symbol')

def test_cache_expiry(mock_yfinance):
    """Test that cache expires after TTL and new data is fetched"""
    from data_ingestion.api_agent import api_service, api_service as svc
    import time
    svc.CACHE_TTL = 1
    svc.CACHE.clear()
    cache_key = "market_data:AAPL"
    response1 = client.get("/market-data/AAPL")
    assert response1.status_code == 200
    first_cached = svc.CACHE[cache_key]["data"]
    # Wait for TTL to expire
    time.sleep(1.1)
    response2 = client.get("/market-data/AAPL")
    assert response2.status_code == 200
    second_cached = svc.CACHE[cache_key]["data"]
    # Should have updated the cache
    assert second_cached != first_cached
    svc.CACHE_TTL = 300

def test_batch_with_partial_invalid_symbols(mock_yfinance):
    """Test batch endpoint with some valid and some invalid symbols"""
    response = client.get("/market-data/batch?symbols=AAPL,INVALID,MSFT")
    assert response.status_code == 200
    data = response.json()
    # Should only return valid symbols
    assert any(item["symbol"] == "AAPL" for item in data)
    assert any(item["symbol"] == "MSFT" for item in data)
    assert all(item["symbol"] != "INVALID" for item in data) 