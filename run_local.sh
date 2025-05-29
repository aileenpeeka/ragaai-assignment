#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Start Redis (if you have Redis installed locally)
echo "Starting Redis..."
redis-server &

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
sleep 2

# Start API Agent
echo "Starting API Agent..."
cd data_ingestion/api_agent
python -m uvicorn api_service:app --host 0.0.0.0 --port 8000 --reload &
cd ../..

# Start Scraper Agent
echo "Starting Scraper Agent..."
cd data_ingestion/scraping_agent
python -m uvicorn scraper_service:app --host 0.0.0.0 --port 8001 --reload &
cd ../..

# Start Retriever Agent
echo "Starting Retriever Agent..."
cd data_ingestion/retriever_agent
python -m uvicorn retriever_service:app --host 0.0.0.0 --port 8002 --reload &
cd ../..

echo "All services are running!"
echo "API Documentation:"
echo "- Market Data API: http://localhost:8000/docs"
echo "- Scraper API: http://localhost:8001/docs"
echo "- Retriever API: http://localhost:8002/docs"

# Keep the script running
wait 