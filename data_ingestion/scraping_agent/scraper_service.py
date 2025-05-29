from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
import yfinance as yf
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
import time
from dotenv import load_dotenv
from pydantic import BaseModel
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Financial Data Scraper",
    description="API service for retrieving financial data using Yahoo Finance",
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

# Create data directory if it doesn't exist
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Initialize Redis client
redis_client = redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)

@app.on_event("startup")
async def startup():
    if "pytest" in sys.modules:
        return
    await FastAPILimiter.init(redis_client)

# Pydantic models
class FilingData(BaseModel):
    symbol: str
    filing_type: str
    filing_date: datetime
    url: str
    content: str

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/filings", response_model=List[FilingData])
async def get_filings(
    symbols: str = Query(..., description="Comma-separated list of stock symbols"),
    filing_type: str = Query("10-K", description="Type of filing (10-K, 10-Q)"),
    limit: int = Query(5, description="Number of filings to retrieve"),
    include_metrics: bool = Query(True, description="Include additional financial metrics")
):
    """
    Get financial filings for one or more symbols using Yahoo Finance
    """
    try:
        # Split and validate symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        if not symbol_list:
            raise HTTPException(status_code=400, detail="No symbols provided")
        # Validate filing type
        if filing_type not in ["10-K", "10-Q"]:
            raise HTTPException(status_code=400, detail="Invalid filing type. Must be 10-K or 10-Q")
        filings = []
        for symbol in symbol_list:
            try:
                logger.info(f"Fetching {filing_type} filings for {symbol}")
                # Get company info from Yahoo Finance
                ticker = yf.Ticker(symbol)
                company_info = ticker.info
                if not company_info:
                    logger.warning(f"No data found for symbol {symbol}")
                    continue
                # Get financial statements
                if filing_type == "10-K":
                    statements = ticker.financials
                else:  # 10-Q
                    statements = ticker.quarterly_financials
                if statements.empty:
                    logger.warning(f"No {filing_type} data found for {symbol}")
                    continue
                # Get additional metrics if requested
                metrics = {}
                if include_metrics:
                    try:
                        # Get key statistics
                        stats = ticker.info
                        metrics = {
                            "market_cap": stats.get("marketCap"),
                            "pe_ratio": stats.get("trailingPE"),
                            "eps": stats.get("trailingEps"),
                            "dividend_yield": stats.get("dividendYield"),
                            "beta": stats.get("beta"),
                            "52_week_high": stats.get("fiftyTwoWeekHigh"),
                            "52_week_low": stats.get("fiftyTwoWeekLow"),
                            "volume": stats.get("volume"),
                            "avg_volume": stats.get("averageVolume")
                        }
                    except Exception as e:
                        logger.warning(f"Failed to get additional metrics for {symbol}: {str(e)}")
                # Convert statements to dictionary format for better structure
                statements_dict = {str(k): v for k, v in statements.to_dict().items()}
                # Create filing data with improved structure
                filing = FilingData(
                    symbol=symbol,
                    filing_type=filing_type,
                    filing_date=datetime.now(),
                    url=f"https://finance.yahoo.com/quote/{symbol}/financials",
                    content=json.dumps({
                        "financial_statements": statements_dict,
                        "metrics": metrics,
                        "company_info": {
                            "name": company_info.get("longName"),
                            "sector": company_info.get("sector"),
                            "industry": company_info.get("industry"),
                            "currency": company_info.get("currency")
                        }
                    })
                )
                filings.append(filing)
            except Exception as e:
                logger.error(f"Error processing symbol {symbol}: {str(e)}")
                continue
        if not filings:
            raise HTTPException(status_code=404, detail="No filings found for any of the provided symbols")
        return filings[:limit]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_filings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/historical-prices/{symbol}")
async def get_historical_prices(
    symbol: str,
    period: str = Query("1y", description="Period to retrieve (e.g., 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)"),
    interval: str = Query("1d", description="Interval between data points (e.g., 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)")
):
    """
    Get historical price data for a given symbol using Yahoo Finance
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No historical data found for {symbol}")
        hist.reset_index(inplace=True)
        return hist.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error in get_historical_prices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyst-recommendations/{symbol}")
async def get_analyst_recommendations(symbol: str):
    """
    Get analyst recommendations for a given symbol using Yahoo Finance
    """
    try:
        ticker = yf.Ticker(symbol)
        recommendations = ticker.recommendations
        if recommendations is None or recommendations.empty:
            raise HTTPException(status_code=404, detail=f"No analyst recommendations found for {symbol}")
        recommendations.reset_index(inplace=True)
        return recommendations.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error in get_analyst_recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def _override():
    return mock_redis
app.dependency_overrides[get_redis_client] = _override 