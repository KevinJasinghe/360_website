# Multi-stage build optimized for Railway
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
# Use npm ci for faster, reliable builds
RUN npm ci --only=production
COPY frontend/ .
RUN npm run build

# Python backend stage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (minimal set)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code (excluding large model file)
COPY backend/ .

# Copy built frontend from previous stage
COPY --from=frontend-builder /frontend/build ./static

# Create directories
RUN mkdir -p uploads logs

# Set environment variables for Railway
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PORT=3001

# Expose Railway port
EXPOSE $PORT

# Health check (simplified for Railway)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get(f'http://localhost:{os.environ.get(\"PORT\", 3001)}/health')" || exit 1

# Start with production app
CMD ["python", "app_production.py"]