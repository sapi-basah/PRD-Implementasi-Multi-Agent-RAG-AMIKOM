# Dokumentasi API & UI — Multi-Agent RAG AMIKOM V1.1

## Endpoint REST API (`/api/v1/`)

### 1. `POST /api/v1/query`
Mengirimkan pertanyaan ke sistem Multi-Agent RAG.

**Request Body**:
```json
{
  "query": "Berapa SKS minimum untuk kelulusan S1 Informatika?",
  "session_id": "demo-session",
  "requested_mode": "AUTO"
}
```

**Response**:
```json
{
  "request_id": "8f3b2a...",
  "mode": "ANSWER",
  "answer": "Berdasarkan pedoman akademik...",
  "citations": [
    {
      "source_id": "B01",
      "chunk_id": "chunk-academic-001",
      "locator": "Bab 2 Halaman 15"
    }
  ],
  "retrieval_backend": "E5_FAISS",
  "generation_backend": "EVIDENCE_SELECTOR_V2",
  "agents_involved": ["AcademicAgent"],
  "latency_ms": 45.2
}
```

### 2. `GET /api/v1/health`
Mengecek status kesehatan database SQLite, FAISS index, corpus, dan E5 model.

### 3. `GET /api/v1/readiness`
Mengecek status kesiapan sistem dalam 3 level (`development_ready`, `implementation_validated`, `final_ready`).

### 4. `GET /api/v1/sources/{source_id}`
Mengambil informasi detail dokumen sumber dan daftar chunk yang dimilikinya.

### 5. `POST /api/v1/evaluation/run`
Memicu eksekusi evaluasi komprehensif pada latar belakang.

---

## Web UI

Akses antarmuka web melalui peramban pada URL: `http://localhost:8000/ui`
Dokumentasi Swagger OpenAPI tersedia pada: `http://localhost:8000/docs`
