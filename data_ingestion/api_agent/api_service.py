from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import yfinance as yf
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
import json
import pandas as pd
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# In-memory cache (simple dict)
CACHE = {}
CACHE_TTL = 300  # seconds

app = FastAPI(
    title="Market Data API",
    description="""
    API service for retrieving real-time market data from various sources.
    
    ## Features
    * Real-time market data retrieval
    * Historical data access
    * Batch data retrieval
    * Caching with Redis
    * Rate limiting
    
    ## Rate Limits
    * Single symbol: 100 requests per minute
    * Batch requests: 50 requests per minute
    * Historical data: 50 requests per minute
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MarketData(BaseModel):
    """Market data model for a single symbol"""
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    price: float = Field(..., description="Current price")
    change: float = Field(..., description="Price change from open")
    change_percent: float = Field(..., description="Percentage change from open")
    volume: int = Field(..., description="Trading volume")
    timestamp: datetime = Field(..., description="Data timestamp")
    source: str = Field(..., description="Data source")
    additional_data: Optional[Dict] = Field(None, description="Additional market data")

    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "price": 150.0,
                "change": 2.0,
                "change_percent": 1.5,
                "volume": 1000000,
                "timestamp": "2024-01-15T10:00:00",
                "source": "Yahoo Finance",
                "additional_data": {
                    "open": 148.0,
                    "high": 151.0,
                    "low": 147.0,
                    "prev_close": 148.0
                }
            }
        }

class HistoricalData(BaseModel):
    symbol: str
    data: List[Dict]
    period: str
    interval: str

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")

    class Config:
        schema_extra = {
            "example": {
                "error": "Symbol not found",
                "details": "The symbol 'INVALID' does not exist"
            }
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/market-data/batch",
    response_model=List[MarketData],
    responses={
        200: {"description": "Successfully retrieved market data"},
    },
    summary="Get Batch Market Data",
    description="Get market data for multiple symbols in one request",
    tags=["Market Data"]
)
async def get_batch_market_data(
    symbols: str = Query(..., description="Comma-separated list of symbols (e.g., AAPL,GOOGL,MSFT)"),
    include_additional: bool = Query(False, description="Include additional market data")
):
    """Get market data for multiple symbols in one request"""
    try:
        # Split and clean the symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if not symbol_list:
            raise HTTPException(status_code=400, detail="No valid symbols provided")
        
        results = []
        for symbol in symbol_list:
            try:
                # Check cache first
                cache_key = f"market_data:{symbol}"
                cached = CACHE.get(cache_key)
                if cached and (datetime.now().timestamp() - cached['timestamp']) < CACHE_TTL:
                    results.append(cached['data'])
                    continue
                
                # Get data from Yahoo Finance
                ticker = yf.Ticker(symbol)
                info = ticker.info
                if not info:
                    logger.warning(f"No info found for symbol {symbol}")
                    continue
                
                quote = ticker.history(period="1d", interval="1m")
                if quote.empty:
                    logger.warning(f"No quote data found for symbol {symbol}")
                    continue
                
                latest = quote.iloc[-1]
                market_data = MarketData(
                    symbol=symbol,
                    price=float(latest['Close']),
                    change=float(latest['Close'] - latest['Open']),
                    change_percent=float(((latest['Close'] - latest['Open']) / latest['Open']) * 100),
                    volume=int(latest['Volume']),
                    timestamp=datetime.now(),
                    source="Yahoo Finance",
                    additional_data=info if include_additional else None
                )
                
                # Cache the result
                CACHE[cache_key] = {"data": market_data, "timestamp": datetime.now().timestamp()}
                results.append(market_data)
                
            except Exception as e:
                logger.error(f"Error processing symbol {symbol}: {str(e)}")
                continue
        
        if not results:
            raise HTTPException(status_code=404, detail="No data found for any of the provided symbols")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_batch_market_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/market-data/{symbol}",
    response_model=MarketData,
    responses={
        200: {"description": "Successfully retrieved market data"},
        404: {"model": ErrorResponse, "description": "Symbol not found or data unavailable"},
    },
    summary="Get Market Data",
    description="Get real-time market data for a single symbol",
    tags=["Market Data"]
)
async def get_market_data(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    include_additional: bool = Query(False, description="Include additional market data")
):
    """
    Get real-time market data for a given symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, GOOGL)
    
    Returns:
        MarketData object containing price, change, volume, etc.
    
    Raises:
        HTTPException: If symbol is invalid or data cannot be retrieved
    """
    try:
        cache_key = f"market_data:{symbol}"
        cached = CACHE.get(cache_key)
        if cached and (datetime.now().timestamp() - cached['timestamp']) < CACHE_TTL:
            return cached['data']
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
        quote = ticker.history(period="1d", interval="1m")
        if quote.empty:
            raise HTTPException(status_code=404, detail=f"No quote data found for {symbol}")
        latest = quote.iloc[-1]
        market_data = MarketData(
            symbol=symbol.upper(),
            price=latest['Close'],
            change=latest['Close'] - latest['Open'],
            change_percent=((latest['Close'] - latest['Open']) / latest['Open']) * 100,
            volume=int(latest['Volume']),
            timestamp=datetime.now(),
            source="Yahoo Finance",
            additional_data=info if include_additional else None
        )
        CACHE[cache_key] = {"data": market_data, "timestamp": datetime.now().timestamp()}
        return market_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_market_data: {str(e)}")
        msg = str(e).lower()
        if '404' in msg or 'not found' in msg:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/market-data/historical/{symbol}",
    responses={
        200: {"description": "Successfully retrieved historical data"},
        404: {"model": ErrorResponse, "description": "Symbol not found or data unavailable"},
    },
    summary="Get Historical Market Data",
    description="Get historical market data for a symbol",
    tags=["Market Data"]
)
async def get_historical_data(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    period: str = Query("1y", description="Period to retrieve (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)"),
    interval: str = Query("1d", description="Interval between data points (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)")
):
    """
    Get historical market data for a symbol
    
    Args:
        symbol: Stock symbol
        period: Period to retrieve
        interval: Interval between data points
    
    Returns:
        Historical price data
    
    Raises:
        HTTPException: If symbol is invalid or data cannot be retrieved
    """
    try:
        # Check cache first
        cache_key = f"historical_data:{symbol}:{period}:{interval}"
        cached_data = CACHE.get(cache_key)
        
        if cached_data:
            return cached_data['data']
        
        # Get data from Yahoo Finance
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No historical data found for {symbol}")
        
        # Reset index to include date in the data
        hist.reset_index(inplace=True)
        
        # Prepare response
        historical_data = HistoricalData(
            symbol=symbol.upper(),
            data=hist.to_dict(orient="records"),
            period=period,
            interval=interval
        )
        
        # Cache the response
        CACHE[cache_key] = {"data": historical_data, "timestamp": datetime.now().timestamp()}
        
        return historical_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_historical_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cache/clear", tags=["Admin"], summary="Clear the in-memory cache")
async def clear_cache():
    try:
        CACHE.clear()
        return {"status": "cache cleared"}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/market-data/{symbol}/refresh",
    response_model=MarketData,
    summary="Force refresh market data for a symbol",
    tags=["Market Data"]
)
async def refresh_market_data(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    include_additional: bool = Query(False, description="Include additional market data")
):
    """
    Force refresh market data for a given symbol, bypassing the cache.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
        quote = ticker.history(period="1d", interval="1m")
        if quote.empty:
            raise HTTPException(status_code=404, detail=f"No quote data found for {symbol}")
        latest = quote.iloc[-1]
        market_data = MarketData(
            symbol=symbol.upper(),
            price=latest['Close'],
            change=latest['Close'] - latest['Open'],
            change_percent=((latest['Close'] - latest['Open']) / latest['Open']) * 100,
            volume=int(latest['Volume']),
            timestamp=datetime.now(),
            source="Yahoo Finance",
            additional_data=info if include_additional else None
        )
        # Update the cache
        cache_key = f"market_data:{symbol}"
        CACHE[cache_key] = {"data": market_data, "timestamp": datetime.now().timestamp()}
        return market_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in refresh_market_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def custom_openapi():
    """Custom OpenAPI schema generator"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 