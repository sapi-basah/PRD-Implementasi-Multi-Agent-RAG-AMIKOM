from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_query_endpoint():
    response = client.post("/api/query", json={"query": "kapan uas?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert data["metadata"]["response_mode"] == "ANSWER"


def test_query_v1_endpoint():
    response = client.post("/api/v1/query", json={"query": "apa itu kurikulum 2025?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "agents_involved" in data


def test_query_pii_refusal():
    response = client.post("/api/query", json={"query": "NIM saya 23.11.5887"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["response_mode"] == "REFUSE"


def test_query_cf002_escalation():
    response = client.post(
        "/api/query",
        json={"query": "Kalau IPK 2.00 apakah bisa lulus? syarat kelulusan batas minimum"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["response_mode"] == "ESCALATE"
    assert "CF002" in data["metadata"]["control_flags"]


def test_query_empty():
    response = client.post("/api/query", json={"query": "   "})
    assert response.status_code in (400, 422)


def test_query_g02_abstain():
    response = client.post(
        "/api/query", json={"query": "jadwal uas belum keluar ya?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["response_mode"] == "ABSTAIN"
