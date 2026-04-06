#!/bin/bash
# start.sh — Production startup script for Streamlit on Render
streamlit run app.py --server.port="${PORT:-8501}" --server.address=0.0.0.0
