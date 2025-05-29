#!/bin/bash

# Create SSL directories if they don't exist
mkdir -p ssl/private ssl/certs

# Generate SSL certificate and key
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/private/ragai.key \
  -out ssl/certs/ragai.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=ragai.example.com"

# Set proper permissions
chmod 600 ssl/private/ragai.key
chmod 644 ssl/certs/ragai.crt

echo "SSL certificates generated successfully in ssl directory" 