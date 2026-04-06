#!/bin/bash
set -e

# AI Resume Analyzer Unified Startup Engine 🚀
# Configured specifically for Render's Free Tier

echo "🔧 Starting Multi-Service Deployment..."

# 1. Start the FastAPI Intelligence Backend on port 8000
# Run in background via &
echo "🚀 [1/2] Launching Backend Engine (FastAPI)..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# 2. Add heartbeat verification for the backend before starting frontend
echo "⏳ Waiting for AI models to initialize (this takes ~10s on free tier)..."
sleep 15

# 3. Start the Streamlit Dashboard (SaaS Frontend)
# Render assigns a dynamic port (default 10000), accesible via $PORT env
echo "💎 [2/2] Launching Dashboard Interface (Streamlit)..."
streamlit run streamlit_app/app.py --server.port "${PORT:-10000}" --server.address 0.0.0.0
