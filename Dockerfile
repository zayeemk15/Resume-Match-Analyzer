# ── Dockerfile: Multi-Service AI Deployment ────────────────────
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifest
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# --- AI PRE-CACHE STEP (PRO MOVE) ---
# Pre-download models to avoid timeouts during live server startup
RUN python -m spacy download en_core_web_sm && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" && \
    python -c "from transformers import AutoTokenizer, AutoModel; AutoTokenizer.from_pretrained('bert-base-uncased'); AutoModel.from_pretrained('bert-base-uncased')"

# Copy source code
COPY . .

# Fix permissions
RUN chmod +x ./start.sh

# Expose ports
EXPOSE 8000
EXPOSE 10000

# Start Engine
CMD ["./start.sh"]
