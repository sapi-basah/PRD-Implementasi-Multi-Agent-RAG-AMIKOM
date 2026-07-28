# Vector Database RAG AMIKOM V1

## Status

- Scope Status: FROZEN
- Embedding Gate: PASS
- Vector Database Status: COMPLETE
- Vector Database Gate: PASS
- Ready for Retrieval Testing: YES
- Retrieval Testing Executed: NO
- Baseline RAG Executed: NO
- Generation Test Executed: NO
- Ready for Multi-Agent: NO

## Backend

- Database: FAISS IndexIDMap2(IndexFlatIP) + SQLite metadata store
- FAISS version: 1.14.3
- SQLite version: 3.50.4
- Index: `IndexIDMap2(IndexFlatIP)`
- Metric: cosine via inner product on the already L2-normalized vectors
- Persistence: `01_database/faiss.index` and `01_database/metadata.sqlite`
- Records: 306
- Dimension: 384 float32

No embedding was recomputed. Stable vector IDs and vector_index 0-305 were reused.

## Namespace

- active_academic: 243
- active_schedule: 3
- active_administration: 25
- active_dynamic_schedule: 10
- archive_schedule: 25

The FAISS vector index is physically shared. Namespace, lifecycle, archive, and freshness
isolation are enforced by indexed SQLite metadata filters before retrieval. Archive records
are never included by the current filter.

## Persistence and reload

Open `metadata.sqlite` with SQLite and `faiss.index` with FAISS 1.14.3. Join them using
`vector_index`, which is also the deterministic FAISS int64 ID. Reload verification,
sample lookup, and filter smoke tests are recorded in `05_qa/`.

## Isi paket

- `00_manifest/`: manifest Excel, CSV registries, change log, dan hash registry.
- `01_database/`: `faiss.index` dan `metadata.sqlite`.
- `02_config/`: konfigurasi dan environment.
- `03_metadata/`: snapshot metadata + chunk text untuk 306 record.
- `04_checkpoint/`: 10 checkpoint batch COMPLETE dan batch vector.
- `05_qa/`: reload test, resume test, QA Q01–Q18, smoke test, dan gate.
- `06_logs/`: indexing log dan resolved error log.
- Laporan PDF dan recovery prompt.

## Boundary

This package does not evaluate retrieval quality, determine final top-k, run a question
set, generate answers, build baseline RAG, or implement multi-agent behavior.
