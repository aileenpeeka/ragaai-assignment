# Market Data API Service

This is a FastAPI-based service that provides market data using Yahoo Finance as the data source.

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Service

To run the service:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the service is running, you can access:
- Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## Available Endpoints

- `GET /health` - Health check endpoint
- `GET /market-data/{symbol}` - Get market data for a single symbol
- `GET /market-data/batch?symbols=AAPL,GOOGL` - Get market data for multiple symbols
- `GET /market-data/historical/{symbol}` - Get historical data for a symbol

## Testing

To run the tests:
```bash
pytest test_api_service.py -v
``` 