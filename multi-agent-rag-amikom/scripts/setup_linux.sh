#!/bin/bash
set -e

echo "=== Setup Environment Multi-Agent RAG AMIKOM (Linux) ==="
python3 -m venv venv || true
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Setup selesai."
