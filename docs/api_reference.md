# API Reference Documentation

## Overview

This document provides detailed information about the available API endpoints, their request/response formats, and usage examples.

## Base URLs

- Market Data API: `http://localhost:8000`
- Scraper API: `http://localhost:8001`
- Retriever API: `http://localhost:8002`

## Authentication

All APIs require an API key for authentication. Include the API key in the request header:

```http
X-API-Key: your-api-key-here
```

## Rate Limits

- Market Data API:
  - Single symbol: 100 requests per minute
  - Batch requests: 50 requests per minute
  - Historical data: 50 requests per minute

- Scraper API:
  - SEC filings: 100 requests per minute
  - Earnings transcripts: 100 requests per minute

- Retriever API:
  - Document operations: 100 requests per minute
  - Search operations: 100 requests per minute

## Market Data API

### Get Market Data

```http
GET /market-data/{symbol}
```

Get real-time market data for a single symbol.

#### Parameters

- `symbol` (path): Stock symbol (e.g., AAPL)

#### Response

```json
{
  "symbol": "AAPL",
  "price": 150.0,
  "change": 2.0,
  "percent_change": 1.5,
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
```

### Get Batch Market Data

```http
GET /market-data/batch?symbols=AAPL,GOOGL,MSFT
```

Get market data for multiple symbols in one request.

#### Parameters

- `symbols` (query): Comma-separated list of symbols

#### Response

```json
[
  {
    "symbol": "AAPL",
    "price": 150.0,
    "change": 2.0,
    "percent_change": 1.5,
    "volume": 1000000,
    "timestamp": "2024-01-15T10:00:00",
    "source": "Yahoo Finance",
    "additional_data": {
      "open": 148.0,
      "high": 151.0,
      "low": 147.0,
      "prev_close": 148.0
    }
  },
  // ... more symbols
]
```

### Get Historical Market Data

```http
GET /market-data/historical/{symbol}?period=1mo&interval=1d
```

Get historical market data for a symbol.

#### Parameters

- `symbol` (path): Stock symbol
- `period` (query): Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
- `interval` (query): Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

#### Response

```json
{
  "symbol": "AAPL",
  "period": "1mo",
  "interval": "1d",
  "data": [
    {
      "Date": "2024-01-15",
      "Open": 148.0,
      "High": 151.0,
      "Low": 147.0,
      "Close": 150.0,
      "Volume": 1000000
    },
    // ... more data points
  ]
}
```

## Scraper API

### Get SEC Filings

```http
GET /sec-filings/{symbol}?filing_type=10-K&limit=5
```

Get SEC filings for a given symbol.

#### Parameters

- `symbol` (path): Stock symbol
- `filing_type` (query): Type of filing (10-K, 10-Q, 8-K)
- `limit` (query): Number of filings to retrieve

#### Response

```json
[
  {
    "symbol": "AAPL",
    "filing_type": "10-K",
    "filing_date": "2024-01-15T00:00:00",
    "url": "https://www.sec.gov/Archives/edgar/data/...",
    "content": "..."
  },
  // ... more filings
]
```

### Get Earnings Transcripts

```http
GET /earnings-transcripts/{symbol}?limit=5
```

Get earnings call transcripts for a given symbol.

#### Parameters

- `symbol` (path): Stock symbol
- `limit` (query): Number of transcripts to retrieve

#### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2024-01-15T00:00:00",
    "title": "Q4 2023 Earnings Call",
    "content": "...",
    "url": "https://seekingalpha.com/..."
  },
  // ... more transcripts
]
```

## Retriever API

### Add Document

```http
POST /documents
```

Add a document to the index.

#### Request Body

```json
{
  "id": "doc_1",
  "content": "Document content",
  "metadata": {
    "source": "market_data",
    "symbol": "AAPL",
    "timestamp": "2024-01-15T10:00:00"
  }
}
```

#### Response

```json
{
  "id": "doc_1",
  "content": "Document content",
  "metadata": {
    "source": "market_data",
    "symbol": "AAPL",
    "timestamp": "2024-01-15T10:00:00"
  },
  "embedding": [0.1, 0.2, 0.3, ...]
}
```

### Get Document

```http
GET /documents/{document_id}
```

Get a document by ID.

#### Parameters

- `document_id` (path): Document ID

#### Response

```json
{
  "id": "doc_1",
  "content": "Document content",
  "metadata": {
    "source": "market_data",
    "symbol": "AAPL",
    "timestamp": "2024-01-15T10:00:00"
  },
  "embedding": [0.1, 0.2, 0.3, ...]
}
```

### Search Documents

```http
POST /search
```

Search documents by query.

#### Request Body

```json
{
  "query": "market data for AAPL",
  "limit": 5,
  "min_score": 0.5
}
```

#### Response

```json
[
  {
    "document": {
      "id": "doc_1",
      "content": "Document content",
      "metadata": {
        "source": "market_data",
        "symbol": "AAPL",
        "timestamp": "2024-01-15T10:00:00"
      },
      "embedding": [0.1, 0.2, 0.3, ...]
    },
    "score": 0.85
  },
  // ... more results
]
```

### Delete Document

```http
DELETE /documents/{document_id}
```

Delete a document.

#### Parameters

- `document_id` (path): Document ID

#### Response

```json
{
  "message": "Document deleted successfully"
}
```

## Error Responses

All APIs return error responses in the following format:

```json
{
  "error": "Error message",
  "details": "Additional error details"
}
```

Common HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

## Examples

### Python

```python
import requests

# Market Data API
response = requests.get(
    "http://localhost:8000/market-data/AAPL",
    headers={"X-API-Key": "your-api-key"}
)
market_data = response.json()

# Scraper API
response = requests.get(
    "http://localhost:8001/sec-filings/AAPL",
    params={"filing_type": "10-K", "limit": 5},
    headers={"X-API-Key": "your-api-key"}
)
filings = response.json()

# Retriever API
response = requests.post(
    "http://localhost:8002/search",
    json={
        "query": "market data for AAPL",
        "limit": 5,
        "min_score": 0.5
    },
    headers={"X-API-Key": "your-api-key"}
)
search_results = response.json()
```

### cURL

```bash
# Market Data API
curl -X GET "http://localhost:8000/market-data/AAPL" \
     -H "X-API-Key: your-api-key"

# Scraper API
curl -X GET "http://localhost:8001/sec-filings/AAPL?filing_type=10-K&limit=5" \
     -H "X-API-Key: your-api-key"

# Retriever API
curl -X POST "http://localhost:8002/search" \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"query": "market data for AAPL", "limit": 5, "min_score": 0.5}'
``` 