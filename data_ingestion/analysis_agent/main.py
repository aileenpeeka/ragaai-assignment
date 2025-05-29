from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn
import os
from dotenv import load_dotenv
import logging
import yfinance as yf
import pandas as pd
import numpy as np

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Analysis Agent API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/portfolio_exposure")
def calculate_portfolio_exposure(request: dict):
    holdings = request.get("holdings", {})
    if not holdings:
        raise HTTPException(status_code=400, detail="No holdings provided")
    
    total_value = sum(holdings.values())
    if total_value == 0:
        raise HTTPException(status_code=400, detail="Total value cannot be zero")
    
    exposures = {
        symbol: (amount / total_value) * 100
        for symbol, amount in holdings.items()
    }
    
    return {
        "exposures": exposures,
        "total_value": total_value
    }

@app.post("/portfolio_analysis")
def analyze_portfolio(request: dict):
    holdings = request.get("holdings", {})
    if not holdings:
        raise HTTPException(status_code=400, detail="No holdings provided")
    
    # Calculate basic metrics
    total_value = sum(holdings.values())
    exposures = {
        symbol: (amount / total_value) * 100
        for symbol, amount in holdings.items()
    }
    
    # For now, return basic analysis
    return {
        "exposures": exposures,
        "total_value": total_value,
        "message": "Full analysis coming soon"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003)
