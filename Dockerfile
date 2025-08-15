# Multi-stage build to minimize final image size

# Stage 1: Build React frontend
FROM node:18-alpine as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
# Use npm install instead of npm ci to handle lock file mismatches
RUN npm install --omit=dev
COPY frontend/ ./
RUN npm run build

# Stage 2: Python dependencies
FROM python:3.11-slim as python-builder

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libsndfile1-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 3: Production
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder stage
COPY --from=python-builder /root/.local /root/.local

# Set working directory
WORKDIR /app

# Copy backend application code
COPY backend/ backend/

# Copy the trained model file
COPY *.pth ./

# Create the static directory first
RUN mkdir -p backend/static

# Copy built frontend from frontend-builder stage
# Copy all React build files to backend/static/
COPY --from=frontend-builder /app/frontend/build/ backend/static/

# Debug: List what was copied to static directory
RUN echo "=== Contents of backend/static ===" && ls -la backend/static/
RUN echo "=== Contents of backend/static/static ===" && ls -la backend/static/static/ || echo "nested static directory doesn't exist"

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Create necessary directories
RUN mkdir -p backend/uploads backend/logs

# Expose port
EXPOSE $PORT

# Start command
CMD ["python", "backend/app_production.py"]