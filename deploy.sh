#!/bin/bash

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi

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

# Generate SSL certificates if they don't exist
if [ ! -f "ssl/certs/ragai.crt" ] || [ ! -f "ssl/private/ragai.key" ]; then
    echo "Generating SSL certificates..."
    ./generate_ssl.sh
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs backups/redis backups/elasticsearch

# Pull latest images
echo "Pulling latest Docker images..."
docker-compose pull

# Build images
echo "Building Docker images..."
docker-compose build

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
check_service_health "http://localhost:8000" || exit 1  # API Agent
check_service_health "http://localhost:8001" || exit 1  # Scraping Agent
check_service_health "http://localhost:8002" || exit 1  # Retriever Agent
check_service_health "http://localhost:8003" || exit 1  # Analysis Agent
check_service_health "http://localhost:8004" || exit 1  # Language Agent
check_service_health "http://localhost:8005" || exit 1  # Voice Agent
check_service_health "http://localhost:8006" || exit 1  # Orchestrator

# Set up backup cron job
echo "Setting up backup cron job..."
(crontab -l 2>/dev/null; echo "0 0 * * * $(pwd)/backup.sh") | crontab -

echo "Deployment completed successfully!"
echo "Services are running at:"
echo "- API Documentation: http://localhost:8000/docs"
echo "- Scraper API: http://localhost:8001/docs"
echo "- Retriever API: http://localhost:8002/docs"
echo "- Analysis API: http://localhost:8003/docs"
echo "- Language API: http://localhost:8004/docs"
echo "- Voice API: http://localhost:8005/docs"
echo "- Orchestrator API: http://localhost:8006/docs"
echo "- Streamlit UI: http://localhost:8501"

echo 'Step 1: Creating minimal Dockerfile.test...'
cat <<EOF > Dockerfile.test
FROM python:3.11-slim
CMD ["python", "--version"]
EOF

echo 'Step 1: Building minimal Docker image...'
time docker build -f Dockerfile.test -t test-python .

echo 'Step 2: Checking system resources...'
echo '--- CPU and Memory ---'
if command -v top &> /dev/null; then
  top -l 1 | head -n 10
else
  echo 'top not available.'
fi

echo '--- Disk Usage ---'
df -h

echo '--- Docker Containers ---'
docker ps -a

echo '--- Docker Images ---'
docker images

echo 'Step 3: Review the output above.'
echo 'If the minimal build is fast, the issue is likely with your project dependencies or Dockerfile.'
echo 'If the minimal build is slow, the problem is with Docker or your system setup.' 