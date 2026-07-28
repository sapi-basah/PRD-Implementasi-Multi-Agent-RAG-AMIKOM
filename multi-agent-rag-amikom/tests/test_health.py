import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import QueryRequest, FinalResponse, Citation, VerificationResult
from app.observability import redact_pii

class TestHealthAndSchemas(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["service"], "Multi-Agent RAG AMIKOM")

    def test_health_endpoint(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("database_checks", data)
        self.assertTrue(data["database_checks"]["faiss_index_exists"])
        self.assertTrue(data["database_checks"]["sqlite_db_exists"])

    def test_readiness_endpoint(self):
        response = self.client.get("/api/v1/readiness")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["system_readiness"], ["PRODUCTION_CANDIDATE", "DEGRADED"])
        self.assertIn(data["retrieval_backend"], ["E5_FAISS", "BM25_FALLBACK"])
        self.assertEqual(data["vector_database_status"], "PASS")

    def test_query_request_schema(self):
        req = QueryRequest(query="Bagaimana cara pengajuan cuti?")
        self.assertEqual(req.query, "Bagaimana cara pengajuan cuti?")
        self.assertEqual(req.session_id, "demo-session")

    def test_pii_redaction(self):
        text_with_nim = "Mahasiswa NIM 23.11.5887 menanyakan jadwal."
        redacted = redact_pii(text_with_nim)
        self.assertIn("[REDACTED_NIM]", redacted)
        self.assertNotIn("23.11.5887", redacted)

if __name__ == "__main__":
    unittest.main()

