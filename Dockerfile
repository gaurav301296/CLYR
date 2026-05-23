# Dockerfile for CLYR - AI Credit Report Analysis
# Multi-stage build for production deployment

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
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Create non-root user
RUN useradd --create-home appuser
USER appuser

# Environment
ENV CLYR_DB_PATH=/app/data/clyr.db
ENV PYTHONPATH=/app/backend

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/api/health')" || exit 1

EXPOSE 8005

# Run
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8005"]
