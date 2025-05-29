# Use our base image
FROM ragaai_base:latest

# Set working directory
WORKDIR /app

# Copy requirements file first for better caching
COPY requirements.txt .

# Install service-specific dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Expose service port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Command to run the service
CMD ["uvicorn", "retriever_service:app", "--host", "0.0.0.0", "--port", "8002"] 