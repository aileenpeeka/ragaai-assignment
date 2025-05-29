import pytest
import pytest_asyncio
from unittest.mock import patch
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
import pandas as pd

from data_ingestion.api_agent import api_service

@pytest.fixture(autouse=True)
def clear_cache():
    api_service.CACHE.clear()

# Mock yfinance Ticker
class MockTicker:
    def __init__(self, symbol):
        self.symbol = symbol
    @property
    def info(self):
        if self.symbol == "INVALID":
            return {}
        return {
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "prev_close": 98.0
        }
    def history(self, period="1d", interval="1d"):
        if self.symbol == "INVALID":
            return pd.DataFrame()
        data = {
            "Open": [100.0],
            "High": [105.0],
            "Low": [95.0],
            "Close": [102.0],
            "Volume": [1000000]
        }
        return pd.DataFrame(data)

@pytest_asyncio.fixture()
async def test_app():
    async with LifespanManager(api_service.app):
        yield api_service.app

@pytest_asyncio.fixture()
async def async_client(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_health_check(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_get_market_data(async_client):
    with patch("yfinance.Ticker", MockTicker):
        response = await async_client.get("/market-data/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert "price" in data
        assert "change" in data
        assert "change_percent" in data
        assert "volume" in data
        assert "timestamp" in data
        assert "source" in data

@pytest.mark.asyncio
async def test_get_market_data_invalid_symbol(async_client):
    with patch("yfinance.Ticker", MockTicker):
        response = await async_client.get("/market-data/INVALID")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data or "detail" in data

@pytest.mark.asyncio
async def test_get_batch_market_data(async_client):
    with patch("data_ingestion.api_agent.api_service.yf.Ticker", MockTicker):
        response = await async_client.get("/market-data/batch?symbols=AAPL,GOOGL")
        assert response.status_code == 200
        data = response.json()
        print('BATCH RESPONSE:', data)
        assert len(data) == 2
        assert data[0]["symbol"] == "AAPL"
        assert data[1]["symbol"] == "GOOGL"

@pytest.mark.asyncio
async def test_get_historical_data(async_client):
    with patch("yfinance.Ticker", MockTicker):
        response = await async_client.get("/market-data/historical/AAPL?period=1mo&interval=1d")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["period"] == "1mo"
        assert data["interval"] == "1d"
        assert "data" in data

@pytest.mark.asyncio
async def test_cache_behavior(async_client):
    from unittest.mock import MagicMock
    mock_instance = MagicMock()
    mock_instance.info = {
        "open": 100.0,
        "high": 105.0,
        "low": 95.0,
        "prev_close": 98.0
    }
    mock_instance.history.return_value = pd.DataFrame({
        "Open": [100.0],
        "High": [105.0],
        "Low": [95.0],
        "Close": [102.0],
        "Volume": [1000000]
    })
    with patch("data_ingestion.api_agent.api_service.yf.Ticker", return_value=mock_instance):
        # First request
        response1 = await async_client.get("/market-data/AAPL")
        assert response1.status_code == 200
        # Second request should use cache
        response2 = await async_client.get("/market-data/AAPL")
        assert response2.status_code == 200
        # Verify the mock was only called once
        assert mock_instance.history.call_count == 1 