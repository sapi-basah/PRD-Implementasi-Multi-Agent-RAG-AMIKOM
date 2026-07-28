# Decision Log - Multi-Agent RAG AMIKOM

## Decision 001: Operational Mode `DEVELOPMENT_DEGRADED`
- **Tanggal**: 2026-07-28
- **Konteks**: Model query encoder `Xenova/multilingual-e5-small` belum ter-mount di `models/e5/`.
- **Keputusan**: Sistem berjalan dalam mode `DEVELOPMENT_DEGRADED` dengan `retrieval_backend="BM25_FALLBACK"` dan `system_readiness="DEGRADED"`. Gate final Multi-Agent tetap BLOCKED sampai model E5 valid.

## Decision 002: Dynamic Portability & Immutable Storage
- **Tanggal**: 2026-07-28
- **Konteks**: NFR-002 melarang hardcoded path absolut.
- **Keputusan**: Seluruh konfigurasi path dimuat relatif menggunakan `pydantic-settings` atau `.env`. Folder `data/immutable/` diperlakukan secara strictly read-only.

## Decision 003: Safe Observability (PII Redaction)
- **Tanggal**: 2026-07-28
- **Konteks**: NFR-003 & FR-016 melarang penyimpanan data pribadi/PII (NIM, KTP, Nilai, dll) di dalam log.
- **Keputusan**: Modul logging menggunakan PII redactor deterministik sebelum mencatat payload request/response.
