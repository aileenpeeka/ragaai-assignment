#!/bin/bash

# Load environment variables
source .env

# Set variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"
REDIS_BACKUP_DIR="$BACKUP_DIR/redis"
ES_BACKUP_DIR="$BACKUP_DIR/elasticsearch"

# Create backup directories
mkdir -p "$REDIS_BACKUP_DIR" "$ES_BACKUP_DIR"

# Backup Redis
echo "Backing up Redis..."
docker-compose exec redis redis-cli -a "$REDIS_PASSWORD" SAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb "$REDIS_BACKUP_DIR/redis_$TIMESTAMP.rdb"

# Backup Elasticsearch
echo "Backing up Elasticsearch..."
curl -X PUT "http://localhost:9200/_snapshot/backup_$TIMESTAMP" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"fs\",
    \"settings\": {
      \"location\": \"$ES_BACKUP_DIR/backup_$TIMESTAMP\"
    }
  }"

# Cleanup old backups (keep last 30 days)
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "Backup completed successfully!" 