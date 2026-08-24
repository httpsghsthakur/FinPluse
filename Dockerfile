
# ==============================================================================
# FinPaluse — Multi-Stage Unified Dockerfile (Frontend + Backend on One Port)
# ==============================================================================

# ── Stage 1: Build React Frontend ─────────────────────────────────────────────
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# ── Stage 2: Python Backend with Embedded Frontend ────────────────────────────
FROM python:3.12-slim AS runner

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend assets into dist/
COPY --from=frontend-builder /app/dist ./dist

# Create necessary ML and data directories
RUN mkdir -p backend/models backend/reports backend/data

ENV PORT=8000
ENV ENVIRONMENT=production
ENV DEBUG=false
ENV PYTHONPATH=/app/backend

EXPOSE 8000

WORKDIR /app/backend

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
