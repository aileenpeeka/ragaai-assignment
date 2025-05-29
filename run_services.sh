#!/bin/bash

# Exit on error
set -e

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to check if a service is healthy
check_service_health() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    echo "Checking health of $url..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url/health" > /dev/null; then
            echo "Service at $url is healthy!"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts: Service not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "Service at $url failed to become healthy after $max_attempts attempts"
    return 1
}

# Start Redis
echo "Starting Redis..."
docker-compose up -d redis

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
sleep 5

# Start API Agent
echo "Starting API Agent..."
cd data_ingestion/api_agent
uvicorn api_service:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info &
cd ../..

# Start Scraper Agent
echo "Starting Scraper Agent..."
cd data_ingestion/scraping_agent
uvicorn scraper_service:app --host 0.0.0.0 --port 8001 --workers 4 --log-level info &
cd ../..

# Start Retriever Agent
echo "Starting Retriever Agent..."
cd data_ingestion/retriever_agent
uvicorn retriever_service:app --host 0.0.0.0 --port 8002 --workers 4 --log-level info &
cd ../..

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
check_service_health "http://localhost:8000" || exit 1
check_service_health "http://localhost:8001" || exit 1
check_service_health "http://localhost:8002" || exit 1

echo "All services are running!"
echo "API Documentation:"
echo "- Market Data API: http://localhost:8000/docs"
echo "- Scraper API: http://localhost:8001/docs"
echo "- Retriever API: http://localhost:8002/docs"

# Keep script running and handle cleanup on exit
trap 'echo "Shutting down services..."; pkill -P $$' EXIT
wait 