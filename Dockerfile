# Production Dockerfile for Visitor Counter Backend Server & Dashboard UI
FROM python:3.10-slim

WORKDIR /app

# Install dependencies required by Python & system
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements & install lightweight backend requirements
COPY requirements.txt .
RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    sqlalchemy \
    pydantic \
    requests

# Copy project files
COPY src/ /app/src/
COPY reset_db.py /app/

# Environment Variables
ENV PORT=8000
ENV API_KEY=""
ENV DATABASE_URL="sqlite:///./data/visitor_counter.db"

# Expose API & Dashboard port
EXPOSE 8000

# Create volume directory for persistent SQLite storage
RUN mkdir -p /app/data

CMD ["sh", "-c", "uvicorn src.api.app:app --host 0.0.0.0 --port ${PORT}"]
