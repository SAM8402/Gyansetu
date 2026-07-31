# Stage 1: Build Frontend Vue 3 Assets
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Production Python Backend Container
FROM python:3.13-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies: curl for healthcheck, libgomp1 for onnxruntime/chromadb
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy built frontend static files
COPY --from=frontend-builder /app/frontend/dist /app/static

# Install backend Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source code
COPY backend/ .

# Ensure storage directories exist
RUN mkdir -p /app/uploads /app/outputs /app/chroma_db /app/logs

EXPOSE 8000

# Container Healthcheck (${PORT} is injected by Render; 8000 is the local fallback)
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

