# Windows Run PowerShell Script
Write-Host "=== Running Multi-Agent RAG AMIKOM Server ==="
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
