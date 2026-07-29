from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_query_endpoint():
    response = client.post("/api/query", json={"query": "kapan uas?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert data["metadata"]["response_mode"] == "AUTO"

def test_query_pii_refusal():
    response = client.post("/api/query", json={"query": "NIM saya 23.11.5887"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["response_mode"] == "REFUSE"

def test_query_cf002_escalation():
    response = client.post("/api/query", json={"query": "IPK saya 2.00 apakah aman?"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["response_mode"] == "ESCALATE"
    assert "CF002" in data["metadata"]["control_flags"]

def test_query_empty():
    response = client.post("/api/query", json={"query": "   "})
    assert response.status_code == 400
