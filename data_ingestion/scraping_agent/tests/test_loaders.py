import pytest
import requests
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime
from data_ingestion.scraping_agent.loaders import (
    BaseLoader,
    SECFilingLoader,
    EarningsTranscriptLoader,
    NewsLoader,
    get_loader
)

BASE_URL = "http://localhost:8000"

@pytest.fixture
def mock_requests():
    with patch('data_ingestion.scraping_agent.loaders.requests') as mock:
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <body>
                <a href="/earnings/transcript/123">Q4 2023 Earnings Call (Jan. 15, 2024)</a>
                <div id="transcript-content">Test transcript content</div>
                <div class="js-content-viewer">
                    <h3>Test News Title</h3>
                    <a href="https://example.com/news">Link</a>
                    <time>Jan 15, 2024</time>
                </div>
            </body>
        </html>
        """
        mock_response.raise_for_status = MagicMock()
        mock.get.return_value = mock_response
        yield mock

def test_base_loader():
    """Test that BaseLoader is abstract"""
    with pytest.raises(TypeError):
        BaseLoader()

def test_sec_filing_loader(tmp_path):
    """Test SEC filing loader"""
    # Create mock filing
    filing_dir = tmp_path / "sec_filings" / "10-K" / "AAPL"
    filing_dir.mkdir(parents=True)
    filing_file = filing_dir / "AAPL_10-K_20240101.txt"
    filing_file.write_text("Test filing content")
    
    loader = SECFilingLoader(tmp_path)
    filings = loader.load("AAPL", filing_type="10-K", limit=5)
    
    assert len(filings) == 1
    assert filings[0]["symbol"] == "AAPL"
    assert filings[0]["filing_type"] == "10-K"
    assert "date" in filings[0]
    assert filings[0]["content"] == "Test filing content"
    assert filings[0]["source"] == "SEC"

def test_sec_filing_loader_no_filings(tmp_path):
    """Test SEC filing loader when no filings exist"""
    loader = SECFilingLoader(tmp_path)
    filings = loader.load("AAPL", filing_type="10-K", limit=5)
    assert len(filings) == 0

def test_earnings_transcript_loader(mock_requests):
    """Test earnings transcript loader"""
    loader = EarningsTranscriptLoader()
    transcripts = loader.load("AAPL", limit=5)
    
    assert len(transcripts) == 1
    assert transcripts[0]["symbol"] == "AAPL"
    assert "date" in transcripts[0]
    assert "title" in transcripts[0]
    assert transcripts[0]["content"] == "Test transcript content"
    assert transcripts[0]["source"] == "Seeking Alpha"

def test_news_loader(mock_requests):
    """Test news loader"""
    loader = NewsLoader()
    articles = loader.load("AAPL", limit=10)
    
    assert len(articles) == 1
    assert articles[0]["symbol"] == "AAPL"
    assert "date" in articles[0]
    assert articles[0]["title"] == "Test News Title"
    assert "content" in articles[0]
    assert articles[0]["source"] == "Yahoo Finance"
    assert "url" in articles[0]

def test_get_loader():
    """Test loader factory function"""
    # Test SEC loader
    sec_loader = get_loader("sec", data_dir=Path("data"))
    assert isinstance(sec_loader, SECFilingLoader)
    
    # Test transcript loader
    transcript_loader = get_loader("transcript")
    assert isinstance(transcript_loader, EarningsTranscriptLoader)
    
    # Test news loader
    news_loader = get_loader("news")
    assert isinstance(news_loader, NewsLoader)
    
    # Test invalid loader type
    with pytest.raises(ValueError):
        get_loader("invalid")

def test_loader_error_handling(mock_requests):
    """Test error handling in loaders"""
    # Mock request to raise an exception
    mock_requests.get.side_effect = Exception("Test error")
    
    # Test SEC loader error handling
    sec_loader = SECFilingLoader(Path("data"))
    filings = sec_loader.load("AAPL")
    assert len(filings) == 0
    
    # Test transcript loader error handling
    transcript_loader = EarningsTranscriptLoader()
    transcripts = transcript_loader.load("AAPL")
    assert len(transcripts) == 0
    
    # Test news loader error handling
    news_loader = NewsLoader()
    articles = news_loader.load("AAPL")
    assert len(articles) == 0 