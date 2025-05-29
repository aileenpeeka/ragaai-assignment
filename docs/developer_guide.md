# Developer Guide

## Getting Started

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Redis
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ragaai_assignment.git
cd ragaai_assignment
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running the Services

1. Start Redis:
```bash
docker-compose up -d redis
```

2. Start the services:
```bash
# Start all services
docker-compose up -d

# Or start individual services
docker-compose up -d api_agent
docker-compose up -d scraping_agent
docker-compose up -d retriever_agent
```

3. Check service status:
```bash
docker-compose ps
```

## Project Structure

```
ragaai_assignment/
├── data_ingestion/
│   ├── api_agent/
│   │   ├── api_service.py
│   │   ├── requirements.txt
│   │   └── tests/
│   ├── scraping_agent/
│   │   ├── scraper_service.py
│   │   ├── loaders.py
│   │   ├── requirements.txt
│   │   └── tests/
│   └── retriever_agent/
│       ├── retriever_service.py
│       ├── requirements.txt
│       └── tests/
├── docs/
│   ├── api_reference.md
│   └── developer_guide.md
├── tests/
│   └── integration/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Development Workflow

### Running Tests

1. Unit Tests:
```bash
# Run all unit tests
pytest

# Run tests for a specific service
pytest data_ingestion/api_agent/tests/
pytest data_ingestion/scraping_agent/tests/
pytest data_ingestion/retriever_agent/tests/
```

2. Integration Tests:
```bash
pytest tests/integration/
```

3. Test Coverage:
```bash
pytest --cov=data_ingestion tests/
```

### Code Style

We use:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

Run code quality checks:
```bash
# Format code
black .

# Sort imports
isort .

# Run linter
flake8

# Type checking
mypy .
```

### Git Workflow

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and commit:
```bash
git add .
git commit -m "feat: your feature description"
```

3. Push changes:
```bash
git push origin feature/your-feature-name
```

4. Create a pull request

## Adding New Features

### Adding a New API Endpoint

1. Create a new route in the appropriate service file:
```python
@app.get("/your-endpoint")
async def your_endpoint():
    # Your implementation
    pass
```

2. Add tests:
```python
def test_your_endpoint():
    # Your test implementation
    pass
```

3. Update API documentation in `docs/api_reference.md`

### Adding a New Loader

1. Create a new loader class in `loaders.py`:
```python
class YourLoader(BaseLoader):
    def load(self, *args, **kwargs):
        # Your implementation
        pass
```

2. Add tests:
```python
def test_your_loader():
    # Your test implementation
    pass
```

## Debugging

### Logging

- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log format: `[timestamp] [level] [service] message`
- Log location: `logs/`

Example:
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Your message")
```

### Debugging Services

1. View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api_agent
```

2. Access service shell:
```bash
docker-compose exec api_agent bash
```

3. Debug with VS Code:
- Install Remote Development extension
- Attach to running container
- Set breakpoints in code

## Performance Optimization

### Caching

- Use Redis for caching
- Set appropriate TTL
- Implement cache invalidation

Example:
```python
# Cache data
redis_client.setex(
    "key",
    timedelta(minutes=5),
    json.dumps(data)
)

# Get cached data
cached_data = redis_client.get("key")
if cached_data:
    return json.loads(cached_data)
```

### Rate Limiting

- Configure rate limits in `docker-compose.yml`
- Monitor rate limit usage
- Implement backoff strategy

Example:
```python
@app.get("/endpoint")
@rate_limit(times=100, seconds=60)
async def endpoint():
    pass
```

## Security

### API Authentication

1. Generate API key:
```python
api_key = secrets.token_urlsafe(32)
```

2. Validate API key:
```python
async def validate_api_key(api_key: str = Header(...)):
    if not is_valid_api_key(api_key):
        raise HTTPException(status_code=401)
```

### Data Validation

1. Use Pydantic models:
```python
class YourModel(BaseModel):
    field: str = Field(..., min_length=1, max_length=100)
```

2. Validate input:
```python
@app.post("/endpoint")
async def endpoint(data: YourModel):
    # Data is already validated
    pass
```

## Monitoring

### Health Checks

- Endpoint: `/health`
- Checks: Service status, Redis connection, Model loading
- Response: `{"status": "healthy", "timestamp": "..."}`

### Metrics

- Endpoint: `/metrics`
- Metrics: Request count, latency, error rate
- Format: Prometheus

## Deployment

### Production Setup

1. Update environment variables:
```bash
cp .env.example .env.prod
# Edit .env.prod
```

2. Build and deploy:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Scaling

1. Horizontal scaling:
```yaml
services:
  api_agent:
    deploy:
      replicas: 3
```

2. Load balancing:
```yaml
services:
  nginx:
    # Configure load balancer
```

## Troubleshooting

### Common Issues

1. Redis Connection Error:
- Check Redis service is running
- Verify connection settings in `.env`
- Check network connectivity

2. Rate Limit Exceeded:
- Implement exponential backoff
- Increase rate limits if needed
- Cache responses

3. Model Loading Error:
- Check model files exist
- Verify model version compatibility
- Check memory usage

### Getting Help

- Check documentation
- Search issues
- Create new issue
- Contact maintainers

## Contributing

1. Fork repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit pull request

## License

This project is licensed under the MIT License - see LICENSE file for details. 