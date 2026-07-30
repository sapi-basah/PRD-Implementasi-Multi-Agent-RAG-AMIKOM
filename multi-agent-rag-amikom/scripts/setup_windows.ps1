# Windows Setup PowerShell Script
Write-Host "=== Setup Environment Multi-Agent RAG AMIKOM (Windows) ==="
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "Setup selesai."
