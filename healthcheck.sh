#!/bin/bash
# Simple script to check if the FastAPI service is healthy
# Intended for use in Docker healthchecks or CI pipelines

curl -f http://localhost:8000/health || exit 1
echo "Service is healthy!"
