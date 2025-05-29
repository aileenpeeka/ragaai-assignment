import pytest
from fastapi.testclient import TestClient
import httpx
import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import requests

# Import FastAPI apps
from data_ingestion.api_agent.api_service import app as api_app
from data_ingestion.scraping_agent.scraper_service import app as scraper_app
from data_ingestion.retriever_agent.retriever_service import app as retriever_app
from orchestrator.orchestrator_service import app as orchestrator_app

# Create test clients
api_client = TestClient(api_app)
scraper_client = TestClient(scraper_app)
retriever_client = TestClient(retriever_app)

BASE_URL = "http://localhost:8000"

@pytest.fixture
def test_symbol():
    return "AAPL"

@pytest.fixture
def test_document():
    return {
        "id": "test_doc_1",
        "content": "This is a test document about Apple's latest earnings",
        "metadata": {
            "source": "test",
            "date": datetime.now().isoformat(),
            "symbol": "AAPL"
        }
    }

@pytest.mark.asyncio
async def test_market_data_to_retriever_flow(test_symbol, test_document):
    """Test the flow from market data to document retrieval"""
    # 1. Get market data
    market_response = api_client.get(f"/market-data/{test_symbol}")
    assert market_response.status_code == 200
    market_data = market_response.json()
    
    # 2. Add market data to retriever
    document = {
        "id": f"market_{test_symbol}_{datetime.now().isoformat()}",
        "content": json.dumps(market_data),
        "metadata": {
            "source": "market_data",
            "symbol": test_symbol,
            "timestamp": datetime.now().isoformat()
        }
    }
    retriever_response = retriever_client.post("/documents", json=document)
    assert retriever_response.status_code == 200
    
    # 3. Search for the document
    search_query = {
        "query": f"market data for {test_symbol}",
        "limit": 5,
        "min_score": 0.5
    }
    search_response = retriever_client.post("/search", json=search_query)
    assert search_response.status_code == 200
    search_results = search_response.json()
    assert len(search_results) > 0
    assert any(test_symbol in result["document"]["metadata"]["symbol"] for result in search_results)

@pytest.mark.asyncio
async def test_sec_filing_to_retriever_flow(test_symbol):
    """Test the flow from SEC filing to document retrieval"""
    # 1. Get SEC filings
    filing_response = scraper_client.get(f"/sec-filings/{test_symbol}?filing_type=10-K&limit=1")
    assert filing_response.status_code == 200
    filings = filing_response.json()
    
    if filings:
        filing = filings[0]
        # 2. Add filing to retriever
        document = {
            "id": f"filing_{test_symbol}_{filing['filing_date']}",
            "content": filing["content"],
            "metadata": {
                "source": "sec_filing",
                "symbol": test_symbol,
                "filing_type": filing["filing_type"],
                "filing_date": filing["filing_date"]
            }
        }
        retriever_response = retriever_client.post("/documents", json=document)
        assert retriever_response.status_code == 200
        
        # 3. Search for the document
        search_query = {
            "query": f"SEC filing for {test_symbol}",
            "limit": 5,
            "min_score": 0.5
        }
        search_response = retriever_client.post("/search", json=search_query)
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert len(search_results) > 0
        assert any(test_symbol in result["document"]["metadata"]["symbol"] for result in search_results)

@pytest.mark.asyncio
async def test_earnings_transcript_to_retriever_flow(test_symbol):
    """Test the flow from earnings transcript to document retrieval"""
    # 1. Get earnings transcripts
    transcript_response = scraper_client.get(f"/earnings-transcripts/{test_symbol}?limit=1")
    assert transcript_response.status_code == 200
    transcripts = transcript_response.json()
    
    if transcripts:
        transcript = transcripts[0]
        # 2. Add transcript to retriever
        document = {
            "id": f"transcript_{test_symbol}_{transcript['date']}",
            "content": transcript["content"],
            "metadata": {
                "source": "earnings_transcript",
                "symbol": test_symbol,
                "date": transcript["date"],
                "title": transcript["title"]
            }
        }
        retriever_response = retriever_client.post("/documents", json=document)
        assert retriever_response.status_code == 200
        
        # 3. Search for the document
        search_query = {
            "query": f"earnings call transcript for {test_symbol}",
            "limit": 5,
            "min_score": 0.5
        }
        search_response = retriever_client.post("/search", json=search_query)
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert len(search_results) > 0
        assert any(test_symbol in result["document"]["metadata"]["symbol"] for result in search_results)

@pytest.mark.asyncio
async def test_health_check_integration():
    """Test health check endpoints across all services"""
    # Check API service health
    api_health = api_client.get("/health")
    assert api_health.status_code == 200
    assert api_health.json()["status"] == "healthy"
    
    # Check scraper service health
    scraper_health = scraper_client.get("/health")
    assert scraper_health.status_code == 200
    assert scraper_health.json()["status"] == "healthy"
    
    # Check retriever service health
    retriever_health = retriever_client.get("/health")
    assert retriever_health.status_code == 200
    assert retriever_health.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_error_handling_integration(test_symbol):
    """Test error handling across services"""
    # Test invalid symbol in API service
    api_response = api_client.get("/market-data/INVALID_SYMBOL")
    assert api_response.status_code == 404
    
    # Test invalid filing type in scraper service
    scraper_response = scraper_client.get(f"/sec-filings/{test_symbol}?filing_type=INVALID")
    assert scraper_response.status_code == 500
    
    # Test invalid document ID in retriever service
    retriever_response = retriever_client.get("/documents/invalid_id")
    assert retriever_response.status_code == 404

@pytest.mark.asyncio
async def test_rate_limiting_integration(test_symbol):
    """Test rate limiting across services"""
    # Test API service rate limiting
    for _ in range(101):  # Exceed rate limit
        api_client.get(f"/market-data/{test_symbol}")
    rate_limit_response = api_client.get(f"/market-data/{test_symbol}")
    assert rate_limit_response.status_code == 429
    
    # Test scraper service rate limiting
    for _ in range(101):  # Exceed rate limit
        scraper_client.get(f"/sec-filings/{test_symbol}")
    rate_limit_response = scraper_client.get(f"/sec-filings/{test_symbol}")
    assert rate_limit_response.status_code == 429
    
    # Test retriever service rate limiting
    for _ in range(101):  # Exceed rate limit
        retriever_client.post("/search", json={"query": "test", "limit": 5})
    rate_limit_response = retriever_client.post("/search", json={"query": "test", "limit": 5})
    assert rate_limit_response.status_code == 429 