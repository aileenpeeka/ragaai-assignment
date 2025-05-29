from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import os
from dotenv import load_dotenv
from loguru import logger
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import sys

# Load environment variables
load_dotenv()

# Configure logging
logger.add("logs/orchestrator.log", rotation="500 MB")

# Initialize FastAPI app
app = FastAPI(
    title="Financial Data Orchestrator",
    description="Orchestrates data flow between Market Data, Scraper, and Retriever services",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis client
redis_client = redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)

# Initialize rate limiter
@app.on_event("startup")
async def startup():
    if "pytest" in sys.modules:
        return
    await FastAPILimiter.init(redis_client)

# Service URLs
API_AGENT_URL = os.getenv("API_AGENT_URL", "http://api_agent:8000")
SCRAPING_AGENT_URL = os.getenv("SCRAPING_AGENT_URL", "http://scraping_agent:8000")
RETRIEVER_AGENT_URL = os.getenv("RETRIEVER_AGENT_URL", "http://retriever_agent:8002")

# Pydantic models
class MarketDataRequest(BaseModel):
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ScrapingRequest(BaseModel):
    symbol: str
    document_type: str  # "sec_filing", "earnings_call", "news"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    document_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: Optional[int] = 10

class AnalysisRequest(BaseModel):
    symbol: str
    analysis_type: str  # "market_data", "sec_filings", "earnings_calls", "news"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check the health of the orchestrator and its dependencies."""
    try:
        # Check Redis connection
        await redis_client.ping()
        
        # Check service dependencies
        async with httpx.AsyncClient() as client:
            api_health = await client.get(f"{API_AGENT_URL}/health")
            scraping_health = await client.get(f"{SCRAPING_AGENT_URL}/health")
            retriever_health = await client.get(f"{RETRIEVER_AGENT_URL}/health")
            
            services_health = {
                "api_agent": api_health.status_code == 200,
                "scraping_agent": scraping_health.status_code == 200,
                "retriever_agent": retriever_health.status_code == 200
            }
        
        return {
            "status": "healthy",
            "services": services_health
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Market data endpoint
@app.get("/market-data/{symbol}")
async def get_market_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    rate_limiter: RateLimiter = Depends(RateLimiter(times=100, minutes=1))
):
    """Get market data for a symbol."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_AGENT_URL}/market-data/{symbol}",
                params={"start_date": start_date, "end_date": end_date}
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Scraping endpoint
@app.post("/scrape")
async def scrape_data(
    request: ScrapingRequest,
    rate_limiter: RateLimiter = Depends(RateLimiter(times=50, minutes=1))
):
    """Scrape financial data for a symbol."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SCRAPING_AGENT_URL}/scrape",
                json=request.dict()
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error scraping data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Search endpoint
@app.post("/search")
async def search_documents(
    request: SearchRequest,
    rate_limiter: RateLimiter = Depends(RateLimiter(times=50, minutes=1))
):
    """Search for documents across all sources."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RETRIEVER_AGENT_URL}/search",
                json=request.dict()
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Analysis endpoint
@app.post("/analyze")
async def analyze_data(
    request: AnalysisRequest,
    rate_limiter: RateLimiter = Depends(RateLimiter(times=50, minutes=1))
):
    """Analyze data across all sources for a symbol."""
    try:
        # Get market data
        market_data = None
        if request.analysis_type in ["market_data", "all"]:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_AGENT_URL}/market-data/{request.symbol}",
                    params={"start_date": request.start_date, "end_date": request.end_date}
                )
                market_data = response.json()

        # Get SEC filings
        sec_filings = None
        if request.analysis_type in ["sec_filings", "all"]:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SCRAPING_AGENT_URL}/scrape",
                    json={
                        "symbol": request.symbol,
                        "document_type": "sec_filing",
                        "start_date": request.start_date,
                        "end_date": request.end_date
                    }
                )
                sec_filings = response.json()

        # Get earnings calls
        earnings_calls = None
        if request.analysis_type in ["earnings_calls", "all"]:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SCRAPING_AGENT_URL}/scrape",
                    json={
                        "symbol": request.symbol,
                        "document_type": "earnings_call",
                        "start_date": request.start_date,
                        "end_date": request.end_date
                    }
                )
                earnings_calls = response.json()

        # Get news
        news = None
        if request.analysis_type in ["news", "all"]:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SCRAPING_AGENT_URL}/scrape",
                    json={
                        "symbol": request.symbol,
                        "document_type": "news",
                        "start_date": request.start_date,
                        "end_date": request.end_date
                    }
                )
                news = response.json()

        return {
            "symbol": request.symbol,
            "market_data": market_data,
            "sec_filings": sec_filings,
            "earnings_calls": earnings_calls,
            "news": news
        }
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 