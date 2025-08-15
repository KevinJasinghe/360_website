# Simplified Railway-optimized build
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies with memory optimization
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

# Copy and install Python requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --no-deps -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Create necessary directories
RUN mkdir -p uploads logs static

# Copy a simple static index.html (skip React build for now)
RUN echo '<!DOCTYPE html><html><head><title>Piano Transcription API</title></head><body><h1>Piano Transcription API</h1><p>Backend is running. API endpoints available at /api/</p><p>Health check: <a href="/health">/health</a></p></body></html>' > static/index.html

# Set Railway environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PORT=3001
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE $PORT

# Start production app
CMD ["python", "app_production.py"]