# Arsitektur Sistem — Multi-Agent RAG AMIKOM V1.1

## Ringkasan Eksekutif
Sistem Layanan Akademik Terpadu S1 Informatika Universitas AMIKOM Yogyakarta mengadopsi arsitektur **Multi-Agent Retrieval-Augmented Generation (RAG)** terintegrasi dengan **Deterministic Guardrail Verifier**.

## Diagram Alur Arsitektur
```
[User / Web UI / API Client]
             │
             ▼
      ┌──────────────┐
      │  Pre-Control │ ──(Short-circuit: PII / Out-of-Scope / G02 / Personal)──► [Response Refuse/Abstain/Handoff]
      └──────────────┘
             │ PASS
             ▼
     ┌───────────────┐
     │  Coordinator  │ ──(Intent & Temporal Classification + Decomposition)
     └───────────────┘
             │
     ┌───────┴────────────────────────┬────────────────────────┐
     ▼                                ▼                        ▼
┌──────────────┐             ┌────────────────┐       ┌────────────────────┐
│AcademicAgent │             │ ScheduleAgent  │       │ AdministrationAgent│
└──────────────┘             └────────────────┘       └────────────────────┘
     │ (active_academic)              │ (active/archive)       │ (active_admin)
     └───────┬────────────────────────┴────────────────────────┘
             ▼
 ┌───────────────────────┐
 │ Shared Retrieval      │ ──► [SQLite Metadata Filter] ──► [E5 Query Encoder / ONNX]
 └───────────────────────┘                                        │
             │                                                    ▼
             │                                           [FAISS Search / Indexing]
             ▼
 ┌───────────────────────┐
 │ LLM / Fallback        │ ──► [LLM Provider / Evidence Selector V2]
 └───────────────────────┘
             │
             ▼
 ┌───────────────────────┐
 │ Coordinator Merge     │ ──► [Deterministic Merge & Dedup]
 └───────────────────────┘
             │
             ▼
 ┌───────────────────────┐
 │ Final Verifier        │ ──► [13 Guardrail Checks: PII, Citation, Leakage, Date]
 └───────────────────────┘
             │
             ▼
     [Final Response]
```

## Komponen Utama
1. **Pre-Control**: Short-circuit deterministik untuk PII, topik di luar cakupan (out-of-scope), konflik (CF002), dan blocker (G02).
2. **Coordinator Agent**: Mengklasifikasikan intent (Academic, Schedule, Administration) dan temporal mode (CURRENT, HISTORICAL, MIXED), serta melakukan query decomposition.
3. **Specialist Agents**:
   - `AcademicAgent`: Domain kurikulum, SKS, konsentrasi, penyetaraan, kelulusan (`active_academic`).
   - `ScheduleAgent`: Domain kalender, jadwal KRS, perkuliahan, ujian (`active_schedule`, `active_dynamic_schedule`, `archive_schedule`).
   - `AdministrationAgent`: Prosedur KRS manual, cuti, SKAK, legalisir, KTM, PDDIKTI (`active_administration`).
4. **Shared Retrieval Service**: Query encoder E5 (multilingual-e5-small ONNX) + SQLite metadata candidate filtering + FAISS inner product ranking. BM25 digunakan sebagai fallback jika E5 tidak tersedia.
5. **LLM & Evidence Selector V2**: LLM provider-agnostic menyusun jawaban hanya berdasarkan evidence. Evidence Selector V2 memproses fallback deterministik.
6. **Final Verifier**: Verifikasi post-generation terhadap 13 kategori guardrail.
