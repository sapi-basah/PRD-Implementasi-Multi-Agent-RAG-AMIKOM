---
document_id: PRD-MA-RAG-AMIKOM-V1.1
version: "1.1"
date_wib: "2026-07-28"
owner: "Tim UAS Proyek Data Mining"
project: "Sistem Layanan Akademik Terpadu Mahasiswa S1 Informatika Universitas AMIKOM Yogyakarta"
scope_status: "FROZEN"
development_implementation_allowed: true
final_multi_agent_ready: false
human_review_status: "PARTIALLY_COMPLETE"
final_dataset_status: "PARTIALLY_READY"
retrieval_gate: "PASS"
baseline_rag_gate: "PASS"
source_of_truth_priority:
  - "PRD V1.1 ini"
  - "Scope Freeze dan audit pasca-freeze"
  - "Embedding/Vector DB/Retrieval config V1"
  - "Final Multi-Agent Foundation Dataset V1"
  - "Artefak baseline lama hanya untuk audit"
---

# PRODUCT REQUIREMENTS DOCUMENT (PRD) V1.1
## Implementasi Multi-Agent RAG + LLM AMIKOM

### 1. Ringkasan keputusan
Proyek boleh langsung masuk tahap implementasi kode. Retrieval E5, FAISS, SQLite, control, citation, dan technical Baseline RAG Gate telah lulus. Namun 36 record kandidat masih menunggu human review, sehingga dataset tersebut hanya boleh digunakan sebagai provisional regression fixture selama development dan belum boleh diklaim sebagai final human-approved gold dataset.

### 2. Status terkini
| Komponen | Status | Keputusan implementasi |
|---|---|---|
| Scope | FROZEN | Tidak menambah domain, agent, atau cohort |
| Raw/Clean/Chunk | PASS | Read-only |
| Embedding dokumen | PASS, 306 x 384 | Gunakan apa adanya |
| Vector Database | PASS | FAISS + SQLite read-only |
| Retrieval Testing | COMPLETE | baseline_top_k=10 |
| Retrieval Gate | PASS | Implementasi retrieval diperbolehkan |
| Baseline RAG Gate | PASS | Technical foundation lulus |
| Human Review | PARTIALLY_COMPLETE | Dikerjakan paralel |
| Final Dataset | PARTIALLY_READY | Candidate fixtures boleh dipakai untuk development |
| Final Multi-Agent Ready | NO | Menunggu implementasi, E2E test, dan human sign-off |
| Artefak E5 offline | USER_CONFIRMED_AVAILABLE | Wajib hash preflight sebelum runtime |

### 3. Tujuan produk
1. Menjawab pertanyaan akademik, jadwal, dan administrasi berdasarkan evidence resmi.
2. Memisahkan tanggung jawab Coordinator, Academic, Schedule, Administration, dan Verifier.
3. Menggunakan E5 + FAISS + SQLite sebagai retrieval utama.
4. Menggunakan LLM provider-agnostic hanya untuk menyusun jawaban dari evidence.
5. Mempertahankan Evidence Selector V2 sebagai fallback ketika output LLM gagal validator.
6. Menghasilkan respons yang bersitasi, lifecycle-aware, freshness-aware, aman terhadap PII, dan dapat diaudit.

### 4. Pengguna dan scope
**Pengguna utama:** mahasiswa aktif S1 Informatika Universitas AMIKOM Yogyakarta, terutama Kurikulum/Angkatan 2025.

**In-scope:** kurikulum 2025, mata kuliah, kode, SKS, konsentrasi, syarat kelulusan, kalender/agenda akademik, KRS/perubahan KRS/ujian/cuti terkait jadwal, KRS manual, cuti, SKAK, legalisir, KTM, dan perubahan data PDDIKTI.

**Out-of-scope:** keuangan/pembayaran, beasiswa, karier/magang, program studi atau cohort lain, nilai/transkrip/dashboard personal, transaksi, formulir terisi, dokumen identitas aktual, fine-tuning, dan deployment produksi kampus.

### 5. Arsitektur target
`User/API -> Pre-Control -> Coordinator -> Specialist Agent(s) -> Shared Retrieval -> LLM/Fallback -> Coordinator Merge -> Verifier -> Final Response`

Komponen:
- **Coordinator Agent:** intent classification, temporal mode, decomposition, routing, merge.
- **Academic Agent:** namespace `active_academic`.
- **Schedule Agent:** `active_schedule`, `active_dynamic_schedule`, `archive_schedule`.
- **Administration Agent:** `active_administration`.
- **Verifier/Guardrail:** deterministic controls, citation, lifecycle, freshness, PII, conflict, blocker.
- **Shared Retrieval Service:** metadata filter before ranking, E5 query vector, FAISS inner product.
- **LLM Generator:** provider-agnostic, structured JSON, evidence-only.
- **Evidence Selector V2:** deterministic fallback from retrieved context.

### 6. Mode kesiapan
- `DEVELOPMENT_READY`: runtime data tersedia, retrieval dan test fixtures dapat digunakan; human review boleh pending.
- `IMPLEMENTATION_VALIDATED`: agent, coordinator, verifier, API, dan E2E regression lulus.
- `FINAL_READY`: human review selesai, seluruh critical gate lulus, dokumentasi/demo/package selesai.

Status sekarang: `DEVELOPMENT_READY=true`, `IMPLEMENTATION_VALIDATED=false`, `FINAL_READY=false`.

### 7. Functional requirements
| ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-001 | API menerima query | Query kosong ditolak; request_id dibuat |
| FR-002 | Pre-control sebelum retrieval | PII, out-of-scope, G02, CF002, blocker dapat short-circuit |
| FR-003 | Coordinator mengklasifikasikan intent dan temporal mode | Mendukung single/multi-intent; tidak menulis fakta |
| FR-004 | Coordinator melakukan decomposition | Setiap sub-query memiliki agent, namespace, mode, k |
| FR-005 | Academic Agent mengambil evidence akademik | Hanya `active_academic`; konflik dieskalasi |
| FR-006 | Schedule Agent membedakan current/dynamic/archive | Current 0 archive; historical hanya archive; dynamic cek TTL |
| FR-007 | Administration Agent menjawab prosedur umum | Tidak memproses status/transaksi/data personal |
| FR-008 | Query encoder E5 lokal | Prefix `query: `, mean pooling, L2, float32, dimensi 384 |
| FR-009 | Metadata filter sebelum ranking | SQLite menghasilkan kandidat vector_index sebelum similarity |
| FR-010 | Per-agent retrieval | Ranking per namespace/sub-intent dan deterministic merge |
| FR-011 | Context assembly traceable | Evidence memuat chunk_id, source_id, locator, lifecycle, freshness |
| FR-012 | LLM evidence-only | Tidak menambahkan fakta; output JSON tervalidasi |
| FR-013 | Evidence Selector fallback | Hanya menyalin evidence frozen; tidak memakai gold answer |
| FR-014 | Citation formatter | Setiap klaim faktual memiliki source_id + chunk_id + locator |
| FR-015 | Verifier final | Scope, PII, lifecycle, freshness, conflict, blocker, citation |
| FR-016 | Response modes | ANSWER, ASK_CONTEXT, ABSTAIN, ESCALATE, HANDOFF, REFUSE, LIVE_CHECK_OR_ABSTAIN |
| FR-017 | Audit log aman | Tidak menyimpan PII mentah; route, agent, chunk, score, latency tercatat |
| FR-018 | Readiness endpoint | Menampilkan development, implementation, final readiness terpisah |
| FR-019 | Evaluation pipeline | 30 CORE + 6 SUPPLEMENTARY + held-out menghasilkan metrik dan error analysis |
| FR-020 | Provisional dataset policy | pending_review hanya untuk development regression |
| FR-021 | Final gold dataset policy | Hanya VALID + HUMAN_PASS masuk implementation dataset |
| FR-022 | Immutable input | Corpus, embedding, vector DB, retrieval baseline, gold mapping tidak ditulis ulang |
| FR-023 | LLM provider configurable | Model/provider/key melalui environment, tidak hardcoded |
| FR-024 | No evaluation-id hardcoding | Tidak ada jawaban/routing khusus berdasarkan evaluation_id |

### 8. Non-functional requirements
Reproducibility, portability, security, maintainability, observability, fail-closed reliability, explainability, data integrity, testability, deterministic control, and graceful degradation are mandatory.

### 9. Artefak data wajib
#### 9.1 Vector database
- `Vector_Database_RAG_AMIKOM_V1.zip/01_database/faiss.index`
- `Vector_Database_RAG_AMIKOM_V1.zip/01_database/metadata.sqlite`
- `Vector_Database_RAG_AMIKOM_V1.zip/02_config/Vector_Database_Config_RAG_AMIKOM_V1.json`
- `Vector_Database_RAG_AMIKOM_V1.zip/final_package_validation.json`

#### 9.2 Chunk dan control
- `Chunk_Corpus_RAG_AMIKOM_V1.zip/Chunk_Corpus_RAG_AMIKOM_V1.jsonl`
- `Chunk_Corpus_RAG_AMIKOM_V1.zip/chunk_control.jsonl`
- `Chunk_Corpus_RAG_AMIKOM_V1.zip/chunk_conflict_verifier.jsonl`
- `Chunk_Corpus_RAG_AMIKOM_V1.zip/chunk_blocked_verifier.jsonl`
- `Chunk_Corpus_RAG_AMIKOM_V1.zip/00_manifest/evaluation_chunk_coverage.csv`

#### 9.3 E5 offline model
Model `Xenova/multilingual-e5-small`, revision `761b726dd34fb83930e26aab4e9ac3899aa1fa78`:
- `config.json`
- `tokenizer.json`
- `tokenizer_config.json`
- `onnx/model_int8.onnx`

Wajib verifikasi SHA-256 sebelum dipakai.

#### 9.4 Config
- `Embedding_Config_RAG_AMIKOM_V1.json`
- `Retrieval_Config_RAG_AMIKOM_V1.json`
- `Generator_Config_Final_RAG_AMIKOM_V1.json` sebagai referensi baseline/fallback, bukan model final wajib.
- `Multi_Agent_Readiness_Gate_RAG_AMIKOM_V1.json`

#### 9.5 Final foundation dataset
Dari `Final_Multi_Agent_Foundation_Dataset_RAG_AMIKOM_V1.zip`:
- `04_context_packs/frozen_context_packs.jsonl`
- `pending_review/candidate_multi_agent_foundation_dataset.jsonl`
- `pending_review/routing_gold.jsonl`
- `pending_review/control_gold.jsonl`
- `pending_review/citation_registry.jsonl`
- seluruh tujuh agent/integration test set pada folder `pending_review/`
- `07_human_review/human_review_registry.jsonl`

### 10. Kontrak data minimum
```json
{
  "QueryRequest": {
    "query": "string",
    "session_id": "string",
    "user_context": {"cohort": "2025"},
    "requested_mode": "AUTO|CURRENT|HISTORICAL"
  },
  "RoutingDecision": {
    "intents": ["ACADEMIC|SCHEDULE|ADMINISTRATION"],
    "temporal_mode": "CURRENT|HISTORICAL|MIXED",
    "agents": ["string"],
    "subqueries": ["string"],
    "control_flags": ["string"],
    "response_mode": "string"
  },
  "Evidence": {
    "chunk_id": "string",
    "source_id": "string",
    "locator": "string",
    "retrieval_namespace": "string",
    "lifecycle_status": "string",
    "freshness_status": "string",
    "score": 0.0,
    "chunk_text": "string"
  },
  "FinalResponse": {
    "request_id": "string",
    "mode": "string",
    "answer": "string",
    "citations": [],
    "freshness_notice": "string|null",
    "handoff": "string|null",
    "verification": {},
    "latency_ms": 0
  }
}
```

### 11. API minimum
- `POST /api/v1/query`
- `GET /api/v1/health`
- `GET /api/v1/readiness`
- `GET /api/v1/sources/{source_id}`
- `POST /api/v1/evaluation/run`

### 12. Struktur repository
```text
multi-agent-rag-amikom/
├── PRD.md
├── AGENTS.md
├── app/
│   ├── main.py
│   ├── api/
│   ├── config/
│   ├── data/
│   ├── retrieval/
│   ├── controls/
│   ├── agents/
│   ├── coordinator/
│   ├── verifier/
│   ├── generator/
│   └── observability/
├── data/immutable/
├── data/provisional_tests/
├── data/final_gold/
├── models/e5/
├── evaluation/
├── tests/
├── scripts/
├── var/logs/
├── var/results/
├── .env.example
├── pyproject.toml
└── README.md
```

### 13. Environment variables
`E5_MODEL_PATH`, `FAISS_INDEX_PATH`, `SQLITE_METADATA_PATH`, `CHUNK_CORPUS_PATH`, `CONTROL_REGISTRY_PATH`, `RETRIEVAL_TOP_K=10`, `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_TEMPERATURE=0`, `ENABLE_EXTRACTIVE_FALLBACK=true`, `APP_ENV`, `LOG_LEVEL`.

### 14. Rencana implementasi
1. F0 - input inventory, hashes, E5 artifact preflight.
2. F1 - repository scaffold, typed schemas, config, logging, health/readiness.
3. F2 - E5 runtime, SQLite metadata filter, FAISS search, shared retrieval.
4. F3 - control registry, conflict/blocker/freshness/PII, verifier.
5. F4 - Academic, Schedule, Administration agents.
6. F5 - Coordinator routing, decomposition, merge.
7. F6 - LLM provider integration, prompt contract, validator, Evidence Selector fallback.
8. F7 - API/UI demo, observability, error handling.
9. F8 - regression, E2E, held-out, human QA, packaging.

### 15. Pengujian
- Unit test: encoder, filter, routing, each control, citation verifier.
- Integration test: E5 -> FAISS/SQLite -> evidence -> agent -> verifier.
- Provisional regression: 36 pending-review records.
- E2E: 30 CORE + 6 SUPPLEMENTARY.
- Held-out: minimal 6 pertanyaan baru yang tidak di-hardcode.
- Human review: record status `HUMAN_PASS`, `HUMAN_REVISION_REQUIRED`, atau `HUMAN_REJECTED`.

### 16. Gate
**F2 Retrieval Runtime Gate:** E5 model hash valid, query vector 384 L2 valid, metadata-first FAISS retrieval bekerja.

**F3 Guardrail Gate:** seluruh control unit test lulus; archive leakage, PII violation, synthetic blocker fact = 0.

**F6 Generation Gate:** structured output parseable; final unsupported claim dan citation mismatch = 0; fallback terlabel.

**F8 Final Gate:** agent/E2E/held-out lulus; 36/36 human review selesai; final gold dataset terisi; documentation/package/demo selesai.

### 17. Definition of Done
1. Repository dapat dijalankan dari environment bersih.
2. Hash input immutable dan model E5 terverifikasi.
3. Query vector 384 float32 L2-normalized.
4. Metadata-first retrieval dan FAISS search berjalan.
5. Lima komponen agent/guardrail terintegrasi.
6. LLM provider dapat diganti melalui environment.
7. Evidence-only answer, citation validator, lifecycle/freshness/PII controls aktif.
8. 30 CORE + 6 SUPPLEMENTARY + held-out selesai.
9. Final critical violations = 0.
10. Tidak ada hardcoding evaluation_id.
11. Human review selesai sebelum `FINAL_READY=true`.
12. README, setup, report, demo, manifest, dan hash tersedia.

### 18. Instruksi awal untuk sistem coding
Baca `PRD.md` dan `AGENTS.md`. Kerjakan fase secara berurutan, tetapi human review dapat berjalan paralel. Jangan memodifikasi data immutable. Gunakan pending-review dataset hanya sebagai provisional test fixture. Jangan mengklaim FINAL_READY sebelum seluruh gate F8 lulus.
