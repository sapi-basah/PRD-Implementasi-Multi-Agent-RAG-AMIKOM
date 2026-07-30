#!/bin/bash
set -e

echo "=== Running Multi-Agent RAG AMIKOM Server ==="
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
