# Metodologi Pengujian — Multi-Agent RAG AMIKOM V1.1

## Metodologi

1. **Pengujian Unit (Unit Testing)**:
   - Pengujian terisolasi untuk encoder E5, metadata SQLite filter, FAISS candidate search, BM25 fallback labeling, routing multi-intent, verifier guardrails, dan PII checker.

2. **Pengujian Integrasi (Integration Testing)**:
   - Pengujian alur end-to-end: `E5 -> SQLite -> FAISS -> Specialist Agent -> LLM/Fallback -> Guardrail Verifier`.

3. **Pengujian API & Smoke Test**:
   - Memastikan response status HTTP 200/400/404 dan struktur JSON sesuai dengan pydantic schema.

4. **Pengujian Evaluasi Komprehensif (17 Dimensi)**:
   - Evaluasi otomatis terhadap 30 CORE questions, 6 SUPPLEMENTARY questions, dan 6 Held-out questions.
