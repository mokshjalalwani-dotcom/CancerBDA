# Stage 1: Builder
FROM python:3.10-slim AS builder

WORKDIR /app

# Install system dependencies if required (e.g., for building some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Gunicorn is needed for production server
RUN pip install --no-cache-dir gunicorn==21.2.0

# Stage 2: Runner
FROM python:3.10-slim AS runner

WORKDIR /app

# Copy installed python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code and models
COPY . .

# Expose port
EXPOSE 8000

# Start Gunicorn with Uvicorn workers
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--workers", "1", "--bind", "0.0.0.0:8000", "--timeout", "120", "--keep-alive", "5", "api.main:app"]
