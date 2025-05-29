from typing import List, Dict, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import logging
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseLoader(ABC):
    """Base class for document loaders"""
    
    @abstractmethod
    def load(self, symbol: str, **kwargs) -> List[Dict]:
        """Load documents for a given symbol"""
        pass

class SECFilingLoader(BaseLoader):
    """Loader for SEC filings"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self, symbol: str, filing_type: str = "10-K", limit: int = 5) -> List[Dict]:
        """
        Load SEC filings for a symbol
        
        Args:
            symbol: Stock symbol
            filing_type: Type of filing
            limit: Number of filings to load
        
        Returns:
            List of filing documents
        """
        try:
            filings = []
            filing_dir = self.data_dir / "sec_filings" / filing_type / symbol
            
            if not filing_dir.exists():
                return []
            
            for filing in filing_dir.glob("*.txt"):
                with open(filing, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Extract filing date from filename
                date_str = filing.stem.split("_")[-1]
                filing_date = datetime.strptime(date_str, "%Y%m%d")
                
                filings.append({
                    "symbol": symbol.upper(),
                    "filing_type": filing_type,
                    "date": filing_date,
                    "content": content,
                    "source": "SEC",
                    "url": f"https://www.sec.gov/Archives/edgar/data/{symbol}/{filing.name}"
                })
            
            return sorted(filings, key=lambda x: x["date"], reverse=True)[:limit]
        
        except Exception as e:
            logger.error(f"Error loading SEC filings: {str(e)}")
            return []

class EarningsTranscriptLoader(BaseLoader):
    """Loader for earnings call transcripts"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def load(self, symbol: str, limit: int = 5) -> List[Dict]:
        """
        Load earnings call transcripts for a symbol
        
        Args:
            symbol: Stock symbol
            limit: Number of transcripts to load
        
        Returns:
            List of transcript documents
        """
        try:
            url = f"https://seekingalpha.com/symbol/{symbol.upper()}/earnings/transcripts"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            transcripts = []
            
            # Find transcript links
            transcript_links = soup.find_all("a", href=lambda x: x and "/earnings/transcript/" in x)
            
            for link in transcript_links[:limit]:
                transcript_url = f"https://seekingalpha.com{link['href']}"
                transcript_response = requests.get(transcript_url, headers=self.headers)
                transcript_response.raise_for_status()
                
                transcript_soup = BeautifulSoup(transcript_response.text, "html.parser")
                content_div = transcript_soup.find("div", {"id": "transcript-content"})
                
                if content_div:
                    title = link.text.strip()
                    date_str = title.split("(")[-1].split(")")[0]
                    date = datetime.strptime(date_str, "%b. %d, %Y")
                    
                    transcripts.append({
                        "symbol": symbol.upper(),
                        "date": date,
                        "title": title,
                        "content": content_div.text.strip(),
                        "source": "Seeking Alpha",
                        "url": transcript_url
                    })
            
            return sorted(transcripts, key=lambda x: x["date"], reverse=True)
        
        except Exception as e:
            logger.error(f"Error loading earnings transcripts: {str(e)}")
            return []

class NewsLoader(BaseLoader):
    """Loader for news articles"""
    
    def load(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Load news articles for a symbol"""
        try:
            # Mock data for testing
            return [{
                "symbol": symbol,
                "date": datetime.now(),
                "title": "Test News Title",
                "content": "Test news content",
                "source": "Yahoo Finance",
                "url": "https://example.com/news"
            }]
        except Exception as e:
            logger.error(f"Error loading news for {symbol}: {str(e)}")
            return []

def get_loader(loader_type: str, **kwargs) -> BaseLoader:
    """
    Factory function to get the appropriate loader
    
    Args:
        loader_type: Type of loader ("sec", "transcript", "news")
        **kwargs: Additional arguments for loader initialization
    
    Returns:
        Loader instance
    """
    loaders = {
        "sec": SECFilingLoader,
        "transcript": EarningsTranscriptLoader,
        "news": NewsLoader
    }
    
    if loader_type not in loaders:
        raise ValueError(f"Unknown loader type: {loader_type}")
    
    return loaders[loader_type](**kwargs) 