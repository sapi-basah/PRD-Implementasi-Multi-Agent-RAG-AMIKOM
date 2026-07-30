
---
title: "PRD Implementasi Multi-Agent RAG AMIKOM"
version: "1.0"
date: "27 Juli 2026"
status: "READY_FOR_IMPLEMENTATION_WITH_RETRIEVAL_BLOCKER"
execution_target: "Google Antigravity"
canonical_document: true
---

# PRODUCT REQUIREMENTS DOCUMENT (PRD)
## Implementasi Multi-Agent RAG AMIKOM

**Dokumen eksekusi terstruktur untuk Google Antigravity**  
**Versi:** 1.0  
**Tanggal:** 27 Juli 2026  
**Pemilik:** Tim UAS Proyek Data Mining  
**Status:** READY_FOR_IMPLEMENTATION_WITH_RETRIEVAL_BLOCKER

> Dokumen ini adalah sumber instruksi utama untuk pembuatan kode. Antigravity harus bekerja per fase, menghasilkan artefak yang dapat diverifikasi, menjalankan pengujian, dan berhenti apabila gate fase gagal.

## 1. Ringkasan Produk

Proyek membangun prototipe **Sistem Layanan Akademik Terpadu Mahasiswa S1 Informatika Universitas AMIKOM Yogyakarta** berbasis Multi-Agent, RAG, embedding, dan vector database. Sistem menjawab pertanyaan akademik, jadwal, dan administrasi menggunakan dokumen resmi yang telah diproses menjadi corpus, chunk, embedding, serta vector database FAISS + SQLite.

Status data saat ini sudah mencakup Raw Corpus, Clean Corpus, Chunk Corpus, 306 embedding dokumen berdimensi 384, dan vector database persisten. Lapisan control, lifecycle, archive, freshness, conflict, blocker, dan PII telah tersedia. Kendala utama adalah query encoder `Xenova/multilingual-e5-small` belum berhasil dijalankan pada tahap retrieval terakhir. Karena itu implementasi struktur kode dapat dimulai, tetapi status final Multi-Agent tidak boleh dinyatakan siap sebelum retrieval E5 lulus.

## 2. Tujuan Produk

1. Menyediakan jawaban layanan akademik yang bersumber, dapat ditelusuri, dan aman.
2. Memisahkan tanggung jawab Academic, Schedule, dan Administration Agent.
3. Menggunakan Coordinator untuk routing dan dekomposisi, bukan penciptaan fakta.
4. Menggunakan Verifier/Guardrail deterministik untuk scope, lifecycle, freshness, conflict, blocker, PII, dan citation.
5. Menggunakan vector retrieval E5 sebagai retriever utama dan BM25 hanya sebagai fallback pengembangan.
6. Menghasilkan prototipe yang dapat diuji menggunakan 30 kasus CORE dan 6 kasus SUPPLEMENTARY.

## 3. Keputusan Status Saat Ini

| Komponen | Status | Implikasi |
|---|---|---|
| Scope | FROZEN | Tidak menambah domain, agent, atau cohort baru. |
| Raw/Clean/Chunk Corpus | PASS | Tidak boleh dimodifikasi oleh aplikasi. |
| Embedding dokumen | PASS | 306 vector x 384 dapat digunakan. |
| Vector Database | PASS | FAISS + SQLite dapat digunakan. |
| Baseline Retrieval | CONDITIONAL_PASS | Hasil terakhir memakai BM25, bukan query vector E5. |
| Ready for coding | YES | Scaffold, data layer, control, agent interface, API, dan test dapat dibangun. |
| Ready for final Multi-Agent claim | NO | Menunggu E5 retrieval dan gate final PASS. |

## 4. Pengguna dan Kebutuhan Utama

### 4.1 Pengguna utama
Mahasiswa aktif S1 Informatika Universitas AMIKOM Yogyakarta, terutama cohort/Kurikulum 2025.

### 4.2 User stories
- **US-01 Academic:** Mahasiswa menanyakan mata kuliah, kode, SKS, konsentrasi, penyetaraan, atau ketentuan kelulusan.
- **US-02 Current Schedule:** Mahasiswa menanyakan agenda atau kalender current dan menerima peringatan freshness bila data dinamis kedaluwarsa.
- **US-03 Historical Schedule:** Mahasiswa menanyakan jadwal periode lampau dan sistem hanya mengambil namespace archive.
- **US-04 Administration:** Mahasiswa menanyakan prosedur KRS manual, cuti, SKAK, legalisir, KTM, atau perubahan data PDDIKTI.
- **US-05 Multi-intent:** Mahasiswa menggabungkan pertanyaan lintas domain dan Coordinator memecahnya menjadi sub-query.
- **US-06 Conflict:** Pertanyaan mengenai ambang IPK tepat 2,00 menghasilkan escalation, bukan pemilihan klaim sepihak.
- **US-07 Blocker:** Pertanyaan yang bergantung pada agenda belum dipublikasikan menghasilkan abstain/handoff.
- **US-08 Privacy:** Sistem menolak penerimaan dokumen identitas, credential, nilai, dan data transaksi personal.
- **US-09 Explainability:** Setiap jawaban faktual menampilkan source_id dan locator.

## 5. Scope

### 5.1 In-scope
- Kurikulum 2025, mata kuliah, kode, SKS, konsentrasi, penyetaraan.
- Ketentuan akademik dan kelulusan yang tidak berada dalam konflik terbuka.
- Kalender akademik, agenda semester, KRS, perubahan KRS, perkuliahan, ujian, cuti terkait jadwal.
- Prosedur KRS manual, cuti, SKAK, legalisir, KTM, dan perubahan data PDDIKTI.
- Current, historical, mixed intent, citation, abstain, escalation, handoff, live-check, PII guardrail.

### 5.2 Out-of-scope
- Keuangan/pembayaran, beasiswa, karier, magang, layanan digital umum.
- Program studi atau cohort lain.
- Nilai, transkrip, dashboard personal, status transaksi, formulir terisi, dan dokumen identitas aktual.
- Fine-tuning model dan deployment produksi kampus.

## 6. Arsitektur Target

```text
User/API
  -> Control Precheck
  -> Coordinator (intent, temporal mode, decomposition)
  -> Academic / Schedule / Administration Specialist
  -> Metadata Filter (SQLite)
  -> Query Encoder E5
  -> FAISS Candidate Retrieval
  -> Evidence Merge + Context Assembly
  -> Single Generator LLM
  -> Deterministic Verifier/Guardrail
  -> Final Response + Citation + Freshness/Handoff
```

### 6.1 Komponen
- **Coordinator Agent:** routing, dekomposisi, kuota retrieval, merge hasil.
- **Academic Agent:** namespace `active_academic`.
- **Schedule Agent:** `active_schedule`, `active_dynamic_schedule`, `archive_schedule`.
- **Administration Agent:** `active_administration`.
- **Verifier/Guardrail:** aturan deterministik; bukan LLM bebas.
- **Generator:** satu provider LLM melalui interface; tidak boleh hardcoded per evaluation_id.

## 7. Mode Operasi

### 7.1 DEVELOPMENT_DEGRADED
- Query encoder E5 belum tersedia.
- BM25 boleh digunakan sebagai fallback eksplisit.
- API wajib mengembalikan `retrieval_backend=BM25_FALLBACK` dan `system_readiness=DEGRADED`.
- Tidak boleh mengklaim Retrieval Gate PASS atau Ready for Multi-Agent final.

### 7.2 PRODUCTION_CANDIDATE
- Model E5 resmi berhasil dimuat dari path lokal atau revision yang dipin.
- 36 query menghasilkan vector 384 float32, norm mendekati 1.
- FAISS search dijalankan pada kandidat hasil filter SQLite.
- Retrieval Gate dan Baseline RAG Gate PASS.

## 8. Functional Requirements

| ID | Requirement | Acceptance Criteria |
|---|---|---|
| FR-001 | Sistem menerima pertanyaan melalui API. | Request tervalidasi, request_id dibuat, query kosong ditolak. |
| FR-002 | Control precheck berjalan sebelum retrieval. | PII, out-of-scope, G02, CF002, dan blocker dapat short-circuit. |
| FR-003 | Coordinator mengklasifikasikan domain dan temporal mode. | Mendukung single-intent dan multi-intent; tidak menulis fakta. |
| FR-004 | Coordinator memecah multi-intent menjadi sub-query. | Setiap sub-query memiliki agent, namespace, filter, dan k sendiri. |
| FR-005 | Academic Agent mengambil evidence akademik. | Hanya memakai namespace akademik aktif dan precedence sumber. |
| FR-006 | Schedule Agent membedakan current/dynamic/archive. | Current mengambil 0 archive; historical hanya archive. |
| FR-007 | Administration Agent menjelaskan prosedur umum. | Tidak memproses transaksi/status personal atau dokumen aktual. |
| FR-008 | Query encoder membuat vector E5. | Prefix `query: `, dimensi 384, float32, L2 normalized, tanpa NaN/Inf/zero. |
| FR-009 | Retriever memfilter sebelum ranking. | Kandidat ditentukan SQLite; dilarang global top-k lalu discard. |
| FR-010 | Retriever mencari per namespace/sub-intent. | Namespace kecil tidak tenggelam; hasil dapat di-merge dengan kuota. |
| FR-011 | Context assembler menjaga source dan locator. | Setiap evidence memuat chunk_id, source_id, locator, lifecycle, freshness. |
| FR-012 | Generator menjawab hanya dari evidence. | Ketika evidence kurang, jawaban menyatakan tidak ditemukan. |
| FR-013 | Citation formatter menghasilkan sitasi konsisten. | Semua klaim faktual memiliki source_id + locator yang valid. |
| FR-014 | Verifier memeriksa jawaban akhir. | Memeriksa scope, PII, lifecycle, freshness, conflict, blocker, citation. |
| FR-015 | Response mode didukung. | ANSWER, ASK_CONTEXT, ABSTAIN, ESCALATE, HANDOFF, REFUSE, LIVE_CHECK_OR_ABSTAIN. |
| FR-016 | Sistem menyimpan audit log aman. | Tidak menyimpan payload PII mentah; latency per tahap tercatat. |
| FR-017 | Health dan readiness endpoint tersedia. | Membedakan healthy, degraded, dan ready. |
| FR-018 | Pipeline evaluasi dapat dijalankan ulang. | 30 CORE + 6 SUPPLEMENTARY menghasilkan JSONL, metrik, dan error analysis. |
| FR-019 | BM25 tersedia sebagai fallback. | Hanya aktif melalui konfigurasi dan selalu dilabeli fallback. |
| FR-020 | Artefak data immutable tidak ditulis. | Hash input tetap sama sebelum dan sesudah eksekusi. |

## 9. Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-001 | Reproducibility | Model revision, config, dependency, dan hash tercatat. |
| NFR-002 | Portability | Tidak ada path absolut `/home/claude/work`; seluruh path dari env/config. |
| NFR-003 | Security | Secret hanya di `.env`; PII tidak disimpan dalam log. |
| NFR-004 | Maintainability | Modul terpisah, typed schema, lint, unit test, docstring. |
| NFR-005 | Observability | request_id, stage latency, backend, agent, source, dan verification status tercatat. |
| NFR-006 | Reliability | Fail-closed pada hash mismatch, model mismatch, database corrupt, atau evidence kosong. |
| NFR-007 | Explainability | Jawaban faktual memiliki citation traceable. |
| NFR-008 | Data integrity | FAISS, SQLite, corpus, embedding, dan gold dataset read-only. |
| NFR-009 | Testability | Control dan verifier deterministik memiliki unit test penuh. |
| NFR-010 | Graceful degradation | Ketika E5/LLM gagal, sistem tidak mengarang fakta dan menggunakan mode aman. |

## 10. Artefak Data Patokan

### 10.1 Wajib ditempatkan di `data/immutable/`
1. `Vector_Database_RAG_AMIKOM_V1.zip`
2. `Vector_Database_Config_RAG_AMIKOM_V1.json`
3. `final_package_validation.json`
4. `Embedding_Config_RAG_AMIKOM_V1.json`
5. `Chunk_Corpus_RAG_AMIKOM_V1.zip`
6. `Inventaris_Sumber_RAG_AMIKOM_V2_Pasca_Scope_Freeze.xlsx`
7. `Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1.zip`
8. `Retrieval_Recovery_Prompt.md`
9. `Roadmap_Implementasi_Multi_Agent_RAG_AMIKOM.pdf`
10. Dokumen PRD ini.

### 10.2 File penting di dalam paket
- `01_database/faiss.index`
- `01_database/metadata.sqlite`
- `Chunk_Corpus_RAG_AMIKOM_V1.jsonl`
- `chunk_control.jsonl`
- `chunk_conflict_verifier.jsonl`
- `chunk_blocked_verifier.jsonl`
- `00_manifest/evaluation_chunk_coverage.csv`

### 10.3 Artefak model E5 (blocker)
```text
models/e5/761b726dd34fb83930e26aab4e9ac3899aa1fa78/
├── config.json
├── tokenizer.json
├── tokenizer_config.json
└── onnx/model_int8.onnx
```
Model boleh belum tersedia pada fase awal. Namun Gate Retrieval E5 tidak boleh PASS sebelum model/revision/hash terverifikasi.

## 11. Kontrak Data

### QueryRequest
```json
{
  "query": "Bagaimana prosedur cuti kuliah?",
  "session_id": "demo-001",
  "user_context": {"cohort": "2025"},
  "requested_mode": "AUTO"
}
```

### RoutingDecision
```json
{
  "intents": ["ADMINISTRATION"],
  "temporal_mode": "CURRENT",
  "agents": ["AdministrationAgent"],
  "subqueries": ["prosedur cuti kuliah"],
  "control_flags": [],
  "response_mode": "ANSWER"
}
```

### Evidence
```json
{
  "chunk_id": "CH-ADM-B03-DOC-B03-PROCEDURE-0001",
  "source_id": "B03",
  "title": "Permohonan Cuti",
  "locator": "Bagian Persyaratan",
  "lifecycle": "ACTIVE",
  "score": 0.87,
  "chunk_text": "...",
  "freshness_status": "CURRENT"
}
```

### FinalResponse
```json
{
  "request_id": "req-20260727-0001",
  "mode": "ANSWER",
  "answer": "...",
  "citations": [{"source_id": "B03", "locator": "Bagian Persyaratan"}],
  "freshness_notice": null,
  "handoff": null,
  "retrieval_backend": "E5_FAISS",
  "system_readiness": "PRODUCTION_CANDIDATE",
  "verification": {"status": "PASS", "checks": []},
  "latency_ms": 842
}
```

## 12. API Minimum

| Method | Endpoint | Fungsi |
|---|---|---|
| POST | `/api/v1/query` | Menjalankan pipeline pertanyaan. |
| GET | `/api/v1/health` | Cek proses, database, model, dan LLM client. |
| GET | `/api/v1/readiness` | Menyatakan DEGRADED atau READY berdasarkan gate. |
| GET | `/api/v1/sources/{source_id}` | Metadata sumber untuk traceability, tanpa data sensitif. |
| POST | `/api/v1/evaluation/run` | Internal/dev only; menjalankan regression set. |

## 13. Struktur Repository

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

## 14. Environment Variables

```env
APP_ENV=development
DATA_ROOT=./data/immutable
FAISS_INDEX_PATH=./data/immutable/vector_db/01_database/faiss.index
METADATA_DB_PATH=./data/immutable/vector_db/01_database/metadata.sqlite
CHUNK_CORPUS_PATH=./data/immutable/chunk/Chunk_Corpus_RAG_AMIKOM_V1.jsonl
CONTROL_REGISTRY_PATH=./data/immutable/chunk/chunk_control.jsonl
CONFLICT_REGISTRY_PATH=./data/immutable/chunk/chunk_conflict_verifier.jsonl
BLOCKED_REGISTRY_PATH=./data/immutable/chunk/chunk_blocked_verifier.jsonl
E5_MODEL_DIR=./models/e5/761b726dd34fb83930e26aab4e9ac3899aa1fa78
RETRIEVAL_BACKEND=auto
BM25_FALLBACK_ENABLED=true
LLM_PROVIDER=replace_me
LLM_MODEL=replace_me
LLM_API_KEY=
LOG_LEVEL=INFO
```

## 15. Rencana Implementasi untuk Antigravity

### Fase 0 - Intake dan Preflight
**Tugas:** baca PRD, inventaris input, verifikasi hash, buat `implementation_plan.md`, `progress.md`, dan `decision_log.md`.  
**Output:** struktur workspace, laporan file hilang, mode awal DEGRADED/READY.  
**Gate:** tidak ada file immutable yang ditulis; database dan corpus dapat dibaca.

### Fase 1 - Scaffold dan Configuration
**Tugas:** buat repository, dependency, settings, `.env.example`, logging, error model, dan typed schemas.  
**Output:** aplikasi boot, `/health`, unit test dasar.  
**Gate:** lint + test PASS; tidak ada secret/path absolut.

### Fase 2 - Data Layer
**Tugas:** implementasikan FAISS/SQLite loader read-only, lookup, candidate filter, fetch records, health check, hash verification.  
**Output:** `VectorStore`, `MetadataStore`, integration tests.  
**Gate:** 306 record, dimensi 384, current filter 0 archive, historical hanya archive.

### Fase 3 - Control Registry dan Verifier Dasar
**Tugas:** muat CONTROL/CONFLICT/BLOCKED, implementasikan PII, scope, lifecycle, freshness, CF001/CF002/G01/G02/G04/MR-A11.  
**Output:** `ControlRegistry`, `PrecheckResult`, unit test kombinasi prioritas.  
**Gate:** control regression 36/36; archive leakage 0; synthetic blocker fact 0.

### Fase 4 - Retrieval Abstraction
**Tugas:** buat interface `QueryEncoder` dan `Retriever`; implementasi BM25 fallback berlabel; implementasi E5 adapter bila model tersedia; retrieval per namespace lalu merge.  
**Output:** backend dapat dipilih melalui config; no hardcoded evaluation ID.  
**Gate:** fallback berjalan DEGRADED; E5 gate tetap BLOCKED jika model tidak ada.

### Fase 5 - Retrieval E5 Recovery
**Tugas:** verifikasi model, encode `query:`, mean pooling, L2, FAISS search pada kandidat SQLite, uji k=1/3/5/10.  
**Output:** query vectors, metrik, top-k baru, error analysis.  
**Gate:** Q02/Q03/Q17 PASS; Retrieval Gate PASS.

### Fase 6 - Specialist Agents
**Tugas:** implementasikan base interface dan tiga agent; masing-masing menerima task + evidence dan mengembalikan `AgentResult`.  
**Output:** agent unit tests dan domain fixtures.  
**Gate:** agent tidak mengambil namespace di luar domain; tidak membuat fakta tanpa evidence.

### Fase 7 - Coordinator
**Tugas:** intent router, temporal classifier, decomposition, per-agent quota, merge/dedup.  
**Output:** multi-intent pipeline.  
**Gate:** EV-C01/EV-C05/EV-C06 diuji ulang; namespace kecil tidak tenggelam.

### Fase 8 - Generator, Citation, dan Final Verifier
**Tugas:** prompt builder dinamis, provider-agnostic LLM client, citation formatter, claim/citation checks, fail-safe responses.  
**Output:** jawaban dinamis, bukan dictionary hardcoded.  
**Gate:** unsupported claim 0, citation mismatch 0, PII violation 0 pada regression set.

### Fase 9 - API dan UI Demo
**Tugas:** FastAPI endpoint, chat UI sederhana, source panel, status freshness, handoff, audit metrics.  
**Output:** demo lokal.  
**Gate:** end-to-end tests PASS dan tidak ada data sensitif di log.

### Fase 10 - Evaluation dan Packaging
**Tugas:** jalankan 30 CORE + 6 SUPPLEMENTARY + held-out cases; bandingkan baseline vs multi-agent; buat README, report, Docker/setup script, hashes.  
**Output:** paket UAS final.  
**Gate:** Retrieval dan Baseline RAG PASS, regression selesai, human review selesai.

## 16. Pengujian

### Unit tests wajib
- Settings/path validation.
- SQLite filter current/historical/dynamic.
- Control priority dan short-circuit.
- Query encoder validation.
- Retriever candidate-only ranking.
- Evidence merge/dedup.
- Citation support.
- PII redaction/refusal.

### Integration tests wajib
- Academic tunggal.
- Schedule current dan expired dynamic.
- Schedule historical.
- Administration procedure.
- Multi-intent academic + administration.
- Mixed archive + administration.
- CF002 escalation.
- G02 abstain/handoff.
- Out-of-scope dan PII refusal.

### Target fungsi minimum
- Control decision accuracy: 100% pada regression set.
- Archive leakage: 0.
- Citation mismatch: 0.
- PII violation: 0.
- Synthetic blocker/conflict fact: 0.
- Semua 36 evaluasi selesai dan traceable.
- Target Hit@k/MRR ditetapkan setelah E5 berhasil, bukan dari BM25.

## 17. Risks dan Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Model E5 tidak tersedia | Vector query tidak berjalan | Interface encoder + BM25 dev fallback; final gate tetap BLOCKED. |
| Namespace besar mendominasi | Evidence domain kecil hilang | Retrieval per namespace + kuota + round-robin merge. |
| Multi-intent tidak terurai | Retrieval miss | Coordinator decomposition dan per-subquery k. |
| Dynamic source expired | Jawaban current usang | TTL check + LIVE_CHECK_OR_ABSTAIN. |
| LLM mengarang | Hallucination | Evidence-only prompt + deterministic verifier. |
| PII masuk log | Risiko privasi | Redaction, denylist, structured safe logging. |
| Path tidak portabel | Gagal di komputer lain | Env/config relatif; tidak ada path hardcoded. |
| Gold leakage | Evaluasi tidak valid | Gold hanya untuk scoring, tidak untuk routing/ranking runtime. |

## 18. Definition of Done

Produk dinyatakan selesai ketika:
1. Semua modul dan API berjalan dari repository bersih.
2. Immutable input lolos hash dan tidak berubah.
3. Query E5 dan FAISS retrieval benar-benar dijalankan.
4. Retrieval Gate dan Baseline RAG Gate PASS.
5. Academic, Schedule, Administration, Coordinator, dan Verifier terintegrasi.
6. 30 CORE + 6 SUPPLEMENTARY + held-out cases selesai.
7. Archive leakage, citation mismatch, PII violation, dan synthetic blocker fact bernilai 0.
8. README, setup, tests, report, dan demo tersedia.
9. Tidak ada jawaban atau grade hardcoded berdasarkan evaluation_id.
10. Human review tim menyetujui paket final.

## 19. Instruksi Eksekusi Antigravity

Antigravity harus mengikuti aturan berikut:

1. Baca seluruh PRD dan file status sebelum mengubah kode.
2. Buat `implementation_plan.md` yang memetakan requirement ID ke task dan file.
3. Kerjakan **satu fase pada satu waktu**.
4. Setelah setiap fase, jalankan lint/test dan tulis hasil ke `progress.md`.
5. Buat artefak verifikasi: daftar file berubah, perintah test, hasil test, dan keputusan gate.
6. Berhenti jika gate gagal; jangan menandai fase berikutnya selesai.
7. Jangan memodifikasi `data/immutable/`.
8. Jangan menggunakan hasil BM25 sebagai top-k final E5.
9. Jangan hardcode jawaban, grade, routing, atau gold chunk untuk evaluation ID.
10. Saat model E5 belum ada, lanjutkan fase yang independen dan tandai status `DEGRADED`; jangan memalsukan query vector.
11. Sebelum mulai coding, eksekusi **Fase 0**, lalu **Fase 1**, dan berhenti untuk melaporkan gate awal.

### Prompt kickoff

```text
Baca PRD.md sebagai sumber kebutuhan utama dan Roadmap_Implementasi_Multi_Agent_RAG_AMIKOM sebagai penjelasan pendukung.

Kerjakan Fase 0 dan Fase 1 saja:
1. verifikasi seluruh input immutable dan hash yang tersedia;
2. buat implementation_plan.md, progress.md, decision_log.md, dan input_inventory.json;
3. buat scaffold repository, settings berbasis environment, typed schemas, logging, health endpoint, lint, dan unit test awal;
4. jangan memodifikasi corpus/database;
5. jangan menjalankan atau memalsukan E5 retrieval;
6. hentikan setelah Gate Fase 1 dan laporkan file yang dibuat, test yang dijalankan, hasil gate, blocker, dan perintah untuk fase berikutnya.
```

## 20. Checklist Input Sebelum Eksekusi

- [ ] PRD ini disimpan sebagai `PRD.md` di root repository.
- [ ] Roadmap tersedia.
- [ ] Vector database ZIP tersedia dan dapat diekstrak.
- [ ] `faiss.index` dan `metadata.sqlite` tersedia.
- [ ] Chunk corpus dan control registries tersedia.
- [ ] Evaluation dataset 30 CORE + 6 SUPPLEMENTARY tersedia.
- [ ] Hash input dicatat.
- [ ] Model E5 tersedia atau blocker dicatat.
- [ ] `.env` tidak berisi credential pada commit.
- [ ] Antigravity diarahkan memulai Fase 0 dan Fase 1 saja.
