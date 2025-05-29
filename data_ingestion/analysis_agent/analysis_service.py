from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import logging
import yfinance as yf
import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Analysis Agent",
    description="API service for portfolio analysis and risk metrics",
    version="1.0.0"
)

class PortfolioRequest(BaseModel):
    symbols: List[str]
    weights: Optional[List[float]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class PortfolioAnalysis(BaseModel):
    total_exposure: float
    sector_exposure: Dict[str, float]
    regional_exposure: Dict[str, float]
    risk_metrics: Dict[str, float]
    performance_metrics: Dict[str, float]
    timestamp: datetime = Field(default_factory=datetime.now)

class RiskMetrics(BaseModel):
    volatility: float
    sharpe_ratio: float
    var_95: float
    beta: float
    correlation_matrix: Dict[str, Dict[str, float]]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now()
    }

@app.post("/portfolio/analyze", response_model=PortfolioAnalysis)
async def analyze_portfolio(request: PortfolioRequest):
    """
    Analyze portfolio exposure and risk metrics
    
    Args:
        request: Portfolio request with symbols and optional weights
    
    Returns:
        Portfolio analysis with exposures and risk metrics
    """
    try:
        # Download historical data
        data = yf.download(
            request.symbols,
            start=request.start_date,
            end=request.end_date or datetime.now().strftime("%Y-%m-%d"),
            progress=False
        )
        logger.info(f"Downloaded data columns: {data.columns}")
        if data.empty:
            logger.error("No data returned from yfinance for the given symbols and date range.")
            raise HTTPException(status_code=400, detail="No data returned from yfinance for the given symbols and date range.")
        if 'Close' not in data:
            logger.error(f"'Close' not found in data columns: {data.columns}")
            raise HTTPException(status_code=400, detail="'Close' not found in yfinance data. Check ticker symbols and date range.")
        # If MultiIndex, select 'Close' level
        if isinstance(data.columns, pd.MultiIndex):
            data = data['Close']
        else:
            data = data['Close']
        
        # Calculate weights if not provided
        weights = request.weights or [1/len(request.symbols)] * len(request.symbols)
        weights = np.array(weights) / sum(weights)  # Normalize weights
        
        # Calculate returns
        returns = data.pct_change().dropna()
        
        # Calculate portfolio metrics
        portfolio_returns = (returns * weights).sum(axis=1)
        
        # Calculate exposures
        total_exposure = sum(weights)
        
        # Get sector and regional exposures (simplified example)
        sector_exposure = {
            "Technology": sum(w for s, w in zip(request.symbols, weights) if "AAPL" in s or "MSFT" in s),
            "Finance": sum(w for s, w in zip(request.symbols, weights) if "JPM" in s or "BAC" in s),
            "Other": 1 - sum(w for s, w in zip(request.symbols, weights) if "AAPL" in s or "MSFT" in s or "JPM" in s or "BAC" in s)
        }
        
        regional_exposure = {
            "US": sum(w for s, w in zip(request.symbols, weights) if not any(x in s for x in ["TSM", "005930.KS"])),
            "Asia": sum(w for s, w in zip(request.symbols, weights) if "TSM" in s or "005930.KS" in s),
            "Other": 0.0
        }
        
        # Calculate risk metrics
        volatility = portfolio_returns.std() * np.sqrt(252)  # Annualized
        sharpe_ratio = (portfolio_returns.mean() * 252) / volatility if volatility != 0 else 0
        var_95 = np.percentile(portfolio_returns, 5)
        beta = returns.cov()['SPY'].mean() / returns['SPY'].var() if 'SPY' in request.symbols else 1.0
        
        # Calculate correlation matrix
        correlation_matrix = returns.corr().to_dict()
        
        return PortfolioAnalysis(
            total_exposure=total_exposure,
            sector_exposure=sector_exposure,
            regional_exposure=regional_exposure,
            risk_metrics={
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "var_95": var_95,
                "beta": beta
            },
            performance_metrics={
                "total_return": (1 + portfolio_returns).prod() - 1,
                "annualized_return": (1 + portfolio_returns).prod() ** (252/len(portfolio_returns)) - 1,
                "max_drawdown": (portfolio_returns.cumsum() - portfolio_returns.cumsum().cummax()).min()
            }
        )
        
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/risk/metrics", response_model=RiskMetrics)
async def calculate_risk_metrics(request: PortfolioRequest):
    """
    Calculate detailed risk metrics for a portfolio
    
    Args:
        request: Portfolio request with symbols
    
    Returns:
        Risk metrics including volatility, Sharpe ratio, VaR, and correlations
    """
    try:
        # Download historical data
        data = yf.download(
            request.symbols,
            start=request.start_date,
            end=request.end_date or datetime.now().strftime("%Y-%m-%d"),
            progress=False
        )
        logger.info(f"Downloaded data columns: {data.columns}")
        if data.empty:
            logger.error("No data returned from yfinance for the given symbols and date range.")
            raise HTTPException(status_code=400, detail="No data returned from yfinance for the given symbols and date range.")
        if 'Close' not in data:
            logger.error(f"'Close' not found in data columns: {data.columns}")
            raise HTTPException(status_code=400, detail="'Close' not found in yfinance data. Check ticker symbols and date range.")
        # If MultiIndex, select 'Close' level
        if isinstance(data.columns, pd.MultiIndex):
            data = data['Close']
        else:
            data = data['Close']
        
        # Calculate returns
        returns = data.pct_change().dropna()
        
        # Calculate weights if not provided
        weights = request.weights or [1/len(request.symbols)] * len(request.symbols)
        weights = np.array(weights) / sum(weights)  # Normalize weights
        
        # Calculate portfolio returns
        portfolio_returns = (returns * weights).sum(axis=1)
        
        # Calculate risk metrics
        volatility = portfolio_returns.std() * np.sqrt(252)  # Annualized
        sharpe_ratio = (portfolio_returns.mean() * 252) / volatility if volatility != 0 else 0
        var_95 = np.percentile(portfolio_returns, 5)
        beta = returns.cov()['SPY'].mean() / returns['SPY'].var() if 'SPY' in request.symbols else 1.0
        
        # Calculate correlation matrix
        correlation_matrix = returns.corr().to_dict()
        
        return RiskMetrics(
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            var_95=var_95,
            beta=beta,
            correlation_matrix=correlation_matrix
        )
        
    except Exception as e:
        logger.error(f"Error calculating risk metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 