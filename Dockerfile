# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install only the minimum system deps crewai needs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip first
RUN pip install --upgrade pip

# Install Python deps (cached layer — only rebuilds if requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY agents.py tasks.py crew.py api.py ./

# Copy frontend static files
COPY frontend/ ./frontend/

# Runtime environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

EXPOSE 8080

# Use shell form so $PORT is expanded at runtime
CMD uvicorn api:app --host 0.0.0.0 --port $PORT
