# CLYR v2 — Production Dockerfile
# Multi-stage build: frontend (Node) + backend (Python)

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim AS backend
WORKDIR /app

# Install system dependencies for reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements-v2.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Environment
ENV PYTHONPATH=/app/backend
ENV CLYR_DB_PATH=/app/data/clyr.db

# Create non-root user
RUN useradd --create-home appuser && mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/api/health')" || exit 1

EXPOSE 8005

# Run
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8005", "--workers", "2"]
